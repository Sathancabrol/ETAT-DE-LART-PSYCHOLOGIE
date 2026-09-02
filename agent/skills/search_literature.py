"""
Compétence : recherche documentaire multi-bases (Crossref, OpenAlex, PubMed).

Normalise les résultats dans un schéma commun et produit un CSV + JSON
dans le répertoire du run. Les résultats sont stockés dans l'état partagé
(ctx.state["search_results"]) pour les compétences aval (déduplication,
PRISMA, synthèse).
"""

from __future__ import annotations

import csv
from typing import Any, Dict, List

from agent.core.registry import skill, SkillResult
from agent.core.context import ROOT, extract_query, extract_years


def _norm_openalex(w: Dict[str, Any]) -> Dict[str, Any]:
    host_venue = (w.get("primary_location") or {}).get("source") or {}
    authors = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
    oa = (w.get("open_access") or {})
    return {
        "titre": (w.get("title") or "").strip(),
        "auteurs": ", ".join(authors[:6]),
        "annee": w.get("publication_year"),
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "journal": host_venue.get("display_name") or "",
        "type": (w.get("type") or "").replace("article-", "").replace("-", " "),
        "citations": w.get("cited_by_count", 0),
        "open_access": "TRUE" if oa.get("is_oa") else "FALSE",
        "base": "OpenAlex",
    }


def _norm_crossref(it: Dict[str, Any]) -> Dict[str, Any]:
    title = it.get("title") or [""]
    if isinstance(title, list):
        title = title[0] if title else ""
    authors = ", ".join(f"{a.get('family', '')} {a.get('given', '')}".strip()
                        for a in (it.get("author") or [])[:6])
    issued = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
    return {
        "titre": (title or "").strip(),
        "auteurs": authors,
        "annee": issued[0] if issued else None,
        "doi": it.get("DOI", ""),
        "journal": (it.get("container-title") or [""])[0] if it.get("container-title") else "",
        "type": (it.get("type") or "").replace("journal-article", "article"),
        "citations": it.get("is-referenced-by-count", 0),
        "open_access": "",
        "base": "Crossref",
    }


def _norm_pubmed(summary: Dict[str, Any]) -> Dict[str, Any]:
    """esummaryresult → schéma commun."""
    authors = ", ".join(a.get("name", "") for a in summary.get("authors", [])[:6])
    doi = ""
    for aid in summary.get("articleids", []):
        if aid.get("idtype") == "doi":
            doi = aid.get("value", "")
    pubdate = summary.get("pubdate", "")
    year = int(pubdate[:4]) if pubdate[:4].isdigit() else None
    return {
        "titre": summary.get("title", "").rstrip("."),
        "auteurs": authors,
        "annee": year,
        "doi": doi,
        "journal": summary.get("fulljournalname") or summary.get("source", ""),
        "type": "pubmed",
        "citations": 0,
        "open_access": "",
        "base": "PubMed",
    }


@skill(
    name="search_literature",
    description="Recherche documentaire multi-bases (Crossref, OpenAlex, PubMed) avec filtre d'années, résultats normalisés et export CSV/JSON.",
    category="recherche",
    triggers=[r"recherche?", r"cherche?", r"litt[ée]rature", r"publications?", r"articles?",
              r"papier", r"papers?", r"search", r"trouve?", r"recenser", r"recension"],
    examples=[
        "rechercher les méta-analyses sur l'attention 2024-2026",
        "chercher des articles sur la métacognition en éducation",
        "recenser les publications exercise cognition depuis 2023",
    ],
    params={
        "query": "requête ou mots-clés (défaut : extraits de la tâche)",
        "from_year": "année de début",
        "to_year": "année de fin",
        "bases": "liste de bases parmi crossref, openalex, pubmed",
        "max_results": "nb max de résultats par base",
    },
    defaults={"bases": ["crossref", "openalex"], "max_results": 10},
    order=10,
)
def search_literature(ctx, query: str = "", from_year: int = 2020, to_year: int = 2026,
                      bases: List[str] | None = None, max_results: int = 0,
                      **_) -> SkillResult:
    bases = [b.lower() for b in (bases or ["crossref", "openalex"])]
    limit = max(1, min(max_results or ctx.max_results, 50))
    q = (query or "").strip() or None

    if not q:
        # Extraire la requête de la dernière tâche enregistrée dans l'état
        task = ctx.state.get("task", "")
        q = extract_query(task)
        years = extract_years(task)
        if years:
            from_year, to_year = years["from"], years["to"]

    results: List[Dict[str, Any]] = []
    per_base: Dict[str, int] = {}
    errors: List[str] = []
    offline = False

    if "openalex" in bases:
        res = ctx.http_get(
            "https://api.openalex.org/works",
            params={"search": q, "per-page": limit,
                    "filter": f"from_publication_date:{from_year}-01-01,to_publication_date:{to_year}-12-31,type:article"},
            fixture="openalex_search.json")
        if res["ok"]:
            works = (res["json"] or {}).get("results", [])
            results.extend(_norm_openalex(w) for w in works)
            per_base["OpenAlex"] = len(works)
            offline = offline or res["offline"]
        else:
            errors.append(f"OpenAlex indisponible : {res['error']}")

    if "crossref" in bases:
        res = ctx.http_get(
            "https://api.crossref.org/works",
            params={"query": q, "rows": limit, "select": "DOI,title,author,issued,container-title,type,is-referenced-by-count",
                    "filter": f"from-pub-date:{from_year}-01-01,until-pub-date:{to_year}-12-31,type:journal-article"},
            fixture="crossref_search.json")
        if res["ok"]:
            items = (res["json"] or {}).get("message", {}).get("items", [])
            results.extend(_norm_crossref(it) for it in items)
            per_base["Crossref"] = len(items)
            offline = offline or res["offline"]
        else:
            errors.append(f"Crossref indisponible : {res['error']}")

    if "pubmed" in bases:
        res = ctx.http_get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "retmode": "json", "retmax": limit,
                    "term": f"{q} AND {from_year}:{to_year}[dp]"},
            fixture="pubmed_esearch.json")
        if res["ok"]:
            ids = (res["json"] or {}).get("esearchresult", {}).get("idlist", [])
            if ids:
                res2 = ctx.http_get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                    params={"db": "pubmed", "retmode": "json", "id": ",".join(ids)},
                    fixture="pubmed_esummary.json")
                if res2["ok"]:
                    vals = (res2["json"] or {}).get("result", {})
                    for uid in vals.get("uids", []):
                        results.append(_norm_pubmed(vals[uid]))
                    per_base["PubMed"] = len(vals.get("uids", []))
                    offline = offline or res2["offline"]
        else:
            errors.append(f"PubMed indisponible : {res['error']}")

    # Dédoublonnage inter-bases basique par DOI pour l'affichage final
    seen: set = set()
    unique: List[Dict[str, Any]] = []
    for r in results:
        key = (r["doi"] or r["titre"].lower()[:80])
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    unique.sort(key=lambda r: -(r.get("citations") or 0))

    # Exports
    artifacts = []
    if unique:
        csv_path = ctx.artifact_path("recherche_resultats.csv")
        cols = ["titre", "auteurs", "annee", "doi", "journal", "type", "citations", "open_access", "base"]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(unique)
        artifacts.append(str(csv_path.relative_to(ROOT)))
    ctx.save_json("recherche_resultats.json", {"query": q, "from": from_year, "to": to_year,
                                               "par_base": per_base, "resultats": unique})

    ctx.state["search_results"] = unique
    ctx.state["search_query"] = q

    details = [f"Requête : « {q} » | Période {from_year}–{to_year} | Limites : {limit}/base"]
    details += [f"{b} : {n} résultats" for b, n in per_base.items()]
    details += errors[:3]
    top3 = [f"• {r['titre'][:90]} ({r['annee']}) [{r['base']}]" for r in unique[:3]]
    summary = (f"{len(unique)} références uniques trouvées "
               f"({' + '.join(f'{b}:{n}' for b, n in per_base.items()) or 'aucune base'})"
               + (" [MODE DÉGRADÉ hors-ligne : fixtures démo]" if offline else ""))

    return SkillResult(ok=bool(unique) or not errors, summary=summary, degraded=offline,
                       data={"query": q, "total": len(unique), "par_base": per_base,
                             "resultats": unique[:25]},
                       artifacts=artifacts, details=details + top3)
