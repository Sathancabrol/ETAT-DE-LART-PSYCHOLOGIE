"""Outils de recherche — clients des API scientifiques gratuites (sans clé).

Sources live :
    - OpenAlex  (https://api.openalex.org)   : métadonnées, citations, OA, abstracts
    - Crossref  (https://api.crossref.org)   : métadonnées + confirmation DOI
    - arXiv     (http://export.arxiv.org)    : préprints
    - Semantic Scholar (option, AGENT_S2_ENABLED=1) : citations + abstracts (rate-limité)

En mode démo (--demo), le pipeline utilise agent/fixtures/demo_results.json
(données réelles capturées d'OpenAlex) sans aucun appel réseau.
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET

import requests

from .models import Paper, deduplicate

log = logging.getLogger("agent.tools")

UA = "CognitoriumAgent/1.0 (mailto:{email})"
TIMEOUT = 20


# ---------------------------------------------------------------- OpenAlex --
def reconstruct_abstract(inv_index: dict | None) -> str:
    """Reconstruit un abstract depuis l'abstract_inverted_index d'OpenAlex."""
    if not inv_index:
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inv_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def search_openalex(query: str, year_min: int, year_max: int, limit: int, email: str) -> list[Paper]:
    try:
        r = requests.get(
            "https://api.openalex.org/works",
            params={
                "search": query,
                "filter": (
                    f"from_publication_date:{year_min}-01-01,"
                    f"to_publication_date:{year_max}-12-31,type:article"
                ),
                "per-page": min(max(limit, 1), 50),
                "select": (
                    "id,doi,title,publication_year,cited_by_count,open_access,"
                    "primary_location,authorships,abstract_inverted_index"
                ),
                "mailto": email,
            },
            headers={"User-Agent": UA.format(email=email)},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        papers = []
        for item in r.json().get("results", []):
            loc = item.get("primary_location") or {}
            src = (loc.get("source") or {}).get("display_name", "")
            authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])]
            papers.append(Paper(
                doi=item.get("doi") or "",
                title=item.get("title") or "",
                year=item.get("publication_year"),
                journal=src,
                authors=[a for a in authors if a],
                cited_by_count=item.get("cited_by_count"),
                is_oa=bool((item.get("open_access") or {}).get("is_oa")),
                oa_url=(item.get("open_access") or {}).get("oa_url") or "",
                url=loc.get("landing_page_url") or "",
                abstract=reconstruct_abstract(item.get("abstract_inverted_index")),
                openalex_id=(item.get("id") or "").rsplit("/", 1)[-1],
                sources=["OpenAlex"],
            ))
        return papers
    except Exception as exc:  # noqa: BLE001
        log.warning("OpenAlex indisponible : %s", exc)
        return []


# ---------------------------------------------------------------- Crossref --
_JATS = re.compile(r"<[^>]+>")


def _strip_jats(text: str) -> str:
    text = _JATS.sub(" ", text or "")
    return re.sub(r"\s+", " ", text.replace("<jats:p>", " ")).strip()


def search_crossref(query: str, year_min: int, year_max: int, limit: int, email: str) -> list[Paper]:
    try:
        r = requests.get(
            "https://api.crossref.org/works",
            params={
                "query.bibliographic": query,
                "filter": f"from-pub-date:{year_min}-01-01,until-pub-date:{year_max}-12-31,type:journal-article",
                "rows": min(max(limit, 1), 40),
                "select": "DOI,title,abstract,is-referenced-by-count,issued,container-title,author,URL",
                "mailto": email,
            },
            headers={"User-Agent": UA.format(email=email)},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        papers = []
        for item in r.json().get("message", {}).get("items", []):
            year = None
            parts = (item.get("issued") or {}).get("date-parts") or [[None]]
            if parts and parts[0] and parts[0][0]:
                year = parts[0][0]
            authors = [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", []) if a.get("family") or a.get("given")
            ]
            titles = item.get("title") or [""]
            papers.append(Paper(
                doi=item.get("DOI") or "",
                title=titles[0],
                year=year,
                journal=(item.get("container-title") or [""])[0],
                authors=authors,
                cited_by_count=item.get("is-referenced-by-count"),
                url=item.get("URL") or (f"https://doi.org/{item.get('DOI')}" if item.get("DOI") else ""),
                abstract=_strip_jats(item.get("abstract") or ""),
                sources=["Crossref"],
            ))
        return papers
    except Exception as exc:  # noqa: BLE001
        log.warning("Crossref indisponible : %s", exc)
        return []


def confirm_doi_crossref(doi: str, email: str) -> bool:
    """Confirme l'existence d'un DOI auprès de Crossref (3e source de triangulation)."""
    try:
        r = requests.get(
            f"https://api.crossref.org/works/{doi}",
            headers={"User-Agent": UA.format(email=email)},
            timeout=TIMEOUT,
        )
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


# ------------------------------------------------------------------- arXiv --
def search_arxiv(query: str, year_min: int, year_max: int, limit: int) -> list[Paper]:
    try:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        q = re.sub(r"\s+", "+AND+", query.strip())
        r = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{q}", "max_results": min(max(limit, 1), 20)},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        root = ET.fromstring(r.text)
        papers = []
        for entry in root.findall("a:entry", ns):
            year = int((entry.findtext("a:published", default="") or "")[:4] or 0)
            if year and not (year_min <= year <= year_max):
                continue
            arxiv_id = (entry.findtext("a:id", default="") or "").rsplit("/", 1)[-1]
            abstract = re.sub(r"\s+", " ", entry.findtext("a:summary", default="") or "").strip()
            papers.append(Paper(
                title=re.sub(r"\s+", " ", entry.findtext("a:title", default="") or "").strip(),
                year=year or None,
                journal=f"arXiv ({arxiv_id})",
                authors=[(a.findtext("a:name", default="") or "") for a in entry.findall("a:author", ns)],
                cited_by_count=None,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                abstract=abstract,
                arxiv_id=arxiv_id,
                type_hint="preprint",
                sources=["arXiv"],
            ))
        return papers
    except Exception as exc:  # noqa: BLE001
        log.warning("arXiv indisponible : %s", exc)
        return []


# ---------------------------------------------------- Semantic Scholar (opt.) --
def search_semanticscholar(query: str, year_min: int, year_max: int, limit: int) -> list[Paper]:
    try:
        r = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={
                "query": query,
                "year": f"{year_min}-{year_max}",
                "limit": min(max(limit, 1), 20),
                "fields": "title,abstract,year,citationCount,externalIds,venue,authors.name,isOpenAccess,openAccessPdf",
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 429:  # rate-limit : on ignore silencieusement
            log.warning("Semantic Scholar rate-limité — source ignorée")
            return []
        r.raise_for_status()
        papers = []
        for item in r.json().get("data", []):
            ext = item.get("externalIds") or {}
            papers.append(Paper(
                doi=ext.get("DOI") or "",
                title=item.get("title") or "",
                year=item.get("year"),
                journal=item.get("venue") or "",
                authors=[a.get("name", "") for a in item.get("authors", [])],
                cited_by_count=item.get("citationCount"),
                is_oa=bool(item.get("isOpenAccess")),
                abstract=item.get("abstract") or "",
                sources=["SemanticScholar"],
            ))
        return papers
    except Exception as exc:  # noqa: BLE001
        log.warning("Semantic Scholar indisponible : %s", exc)
        return []


# --------------------------------------------------------------- Recherche --
def search_all(query: str, year_min: int, year_max: int, limit: int = 15,
               email: str = "agent-demo@example.org", s2_enabled: bool = False) -> list[Paper]:
    """Interroge toutes les sources, fusionne et déduplique (tri = pertinence)."""
    papers: list[Paper] = []
    papers += search_openalex(query, year_min, year_max, limit, email)
    papers += search_crossref(query, year_min, year_max, limit, email)
    papers += search_arxiv(query, year_min, year_max, min(limit, 10))
    if s2_enabled:
        papers += search_semanticscholar(query, year_min, year_max, limit)
    return deduplicate(papers)
