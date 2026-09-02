"""
Compétence : enrichissement par DOI (Crossref + OpenAlex).

À partir d'un ou plusieurs DOI, produit une ébauche de ligne au format
42 champs de la base (mêmes conventions que scripts/add_entry.py) et
récupère les métriques de citations / accès ouvert.
"""

from __future__ import annotations

import csv
import re
from datetime import date
from typing import Any, Dict, List

from agent.core.registry import skill, SkillResult
from agent.core.context import ROOT, DATA_CSV, extract_dois


def _crossref_to_draft(doi: str, msg: Dict[str, Any]) -> Dict[str, str]:
    title = msg.get("title") or [""]
    if isinstance(title, list):
        title = title[0] if title else ""
    year_parts = ((msg.get("issued") or {}).get("date-parts") or [[None]])[0]
    year = year_parts[0] if year_parts else ""
    authors = msg.get("author", [])
    first = authors[0]["family"].lower() if authors else "anonyme"
    journal = (msg.get("container-title") or [""])[0] if msg.get("container-title") else ""
    keyword = re.sub(r"[^a-z0-9]+", "_", title.lower().split()[0] if title else doi)[:12]
    ident = re.sub(r"[^a-z0-9_]+", "", f"{first}{year}_{keyword}")[:50]
    today = date.today().isoformat()
    return {
        "id": ident,
        "grand_domaine": "Psychologie",
        "domaine": "à_compléter",
        "sous_domaine": "à_compléter",
        "theme": (title or "")[:80],
        "question_scientifique": f"Quelle est la contribution de « {title} » ?",
        "reference_courte": f"{first.capitalize()} et al. {year}",
        "reference_complete": f"{', '.join(a.get('family', '') for a in authors)} ({year}). {title}. {journal}. https://doi.org/{doi}",
        "doi": doi,
        "annee": str(year),
        "type_publication": "article_empirique",
        "journal": journal,
        "url": f"https://doi.org/{doi}",
        "niveau_preuve": "à_compléter",
        "sources_triangulation": "Crossref+OpenAlex+à_compléter",
        "citations_crossref": str(msg.get("is-referenced-by-count", 0)),
        "peer_reviewed": "TRUE" if journal else "FALSE",
        "open_access": "à_compléter",
        "data_open": "à_compléter",
        "code_open": "à_compléter",
        "preregistration": "à_compléter",
        "consensus_actuel": "à_compléter",
        "gap_actuel": "à_compléter",
        "last_gap": "à_compléter",
        "trust_factor": "0",
        "trust_niveau": "faible",
        "trust_justification": "ébauche auto-générée, à évaluer",
        "tags": "à_compléter,à_compléter,à_compléter",
        "date_ajout": today,
        "date_mise_a_jour": today,
        "ajoute_par": "agent_chercheur",
    }


@skill(
    name="enrich_doi",
    description="Enrichit un ou plusieurs DOI via Crossref/OpenAlex et produit une ébauche de ligne 42 champs prête à compléter (option : l'ajouter à la base).",
    category="recherche",
    triggers=[r"\bdoi\b", r"10\.\d{4}/", r"enrichi", r"m[ée]tadonn[ée]es\s+publi"],
    examples=[
        "enrichir le DOI 10.1037/bul0000439",
        "ajouter la référence 10.1002/wps.21203 à la base",
    ],
    params={"dois": "liste de DOI", "append": "si true, ajoute l'ébauche à data/nodes_etat_art_psychologie.csv"},
    defaults={"append": False},
    order=15,
)
def enrich_doi(ctx, dois: List[str] | None = None, append: bool = False, **_) -> SkillResult:
    dois = dois or extract_dois(ctx.state.get("task", ""))
    if not dois:
        return SkillResult(ok=False, summary="Aucun DOI fourni ni détecté dans la tâche.")

    drafts, offline, errors = [], False, []
    for doi in dois[:10]:
        res = ctx.http_get(f"https://api.crossref.org/works/{doi}", fixture=f"crossref_doi.json")
        if not res["ok"]:
            errors.append(f"{doi} : {res['error']}")
            continue
        offline = offline or res["offline"]
        msg = res["json"]["message"]
        draft = _crossref_to_draft(doi, msg)

        # Complément OpenAlex : citations + accès ouvert
        res2 = ctx.http_get("https://api.openalex.org/works/doi:" + doi,
                            fixture="openalex_work.json")
        if res2["ok"] and res2["json"]:
            offline = offline or res2["offline"]
            draft["citations_openalex"] = str(res2["json"].get("cited_by_count", 0))
            oa = res2["json"].get("open_access") or {}
            if oa.get("is_oa") is not None:
                draft["open_access"] = "TRUE" if oa.get("is_oa") else "FALSE"
        drafts.append(draft)

    artifacts: List[str] = []
    if drafts:
        artifacts.append(ctx.save_json("enrichissement_doi.json", drafts))

    appended = 0
    if append and drafts:
        headers = ctx.data_headers()
        existing = {r.get("doi") for r in ctx.read_data_rows()}
        with open(DATA_CSV, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            for d in drafts:
                if d["doi"] in existing:
                    continue
                w.writerow({h: d.get(h, "") for h in headers})
                appended += 1

    details = [f"DOI traités : {', '.join(dois[:10])}"] + errors[:3]
    if append:
        details.append(f"{appended} ébauche(s) ajoutée(s) à {DATA_CSV.relative_to(ROOT)} — "
                       f"champs « à_compléter » à finaliser puis revalider (validate_entries).")
    summary = (f"{len(drafts)} ébauche(s) 42 champs générée(s)"
               + (f", {appended} ajoutée(s) à la base" if append else "")
               + (" [MODE DÉGRADÉ hors-ligne]" if offline else ""))
    return SkillResult(ok=bool(drafts), summary=summary, degraded=offline,
                       data={"drafts": drafts}, artifacts=artifacts, details=details)
