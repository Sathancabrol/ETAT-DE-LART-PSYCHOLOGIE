"""
Compétence : déduplication.

Deux sources possibles :
  1. les résultats de recherche du run (ctx.state["search_results"]) —
     déduplication inter-bases par DOI exact + similarité de titre ;
  2. la base 42 champs elle-même (doublons de DOI/id).

Produit un rapport de déduplication et met à jour les compteurs PRISMA
dans l'état partagé.
"""

from __future__ import annotations

import csv
import re
from difflib import SequenceMatcher
from typing import Dict, List

from agent.core.registry import skill, SkillResult
from agent.core.context import ROOT


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()


def _title_dup(a: str, b: str, threshold: float = 0.93) -> bool:
    na, nb = _norm_title(a), _norm_title(b)
    if not na or not nb:
        return False
    return SequenceMatcher(None, na, nb).ratio() >= threshold


@skill(
    name="deduplicate",
    description="Déduplique les résultats de recherche du run (DOI exact + titres similaires) ou la base 42 champs ; alimente les compteurs PRISMA.",
    category="donnees",
    triggers=[r"d[ée]dup", r"doublons?", r"duplicate"],
    examples=[
        "dédupliquer les résultats de recherche",
        "vérifier les doublons dans la base",
    ],
    params={"source": "'search' (résultats du run) ou 'base' (CSV 42 champs)"},
    defaults={"source": "auto"},
    order=30,
)
def deduplicate(ctx, source: str = "auto", **_) -> SkillResult:
    search_results: List[Dict] = ctx.state.get("search_results") or []
    if source == "auto":
        source = "search" if search_results else "base"

    artifacts, details = [], []
    if source == "search" and search_results:
        unique, removed = [], []
        seen_dois, seen_titles = set(), []
        for r in search_results:
            doi = (r.get("doi") or "").lower()
            title = r.get("titre", "")
            if doi and doi in seen_dois:
                removed.append({"raison": "DOI identique", "titre": title, "doi": doi})
                continue
            if any(_title_dup(title, t) for t in seen_titles):
                removed.append({"raison": "titre similaire ≥0.93", "titre": title, "doi": doi})
                continue
            seen_dois.add(doi)
            seen_titles.append(title)
            unique.append(r)
        ctx.state["search_results_dedup"] = unique
        ctx.state["prisma"] = {"identifies": len(search_results), "apres_deduplication": len(unique)}
        details = [f"Identifiés (toutes bases) : {len(search_results)}",
                   f"Supprimés : {len(removed)} ({sum(1 for x in removed if 'DOI' in x['raison'])} DOI identiques, "
                   f"{sum(1 for x in removed if 'titre' in x['raison'])} titres similaires)",
                   f"Conservés : {len(unique)}"]
        artifacts.append(ctx.save_json("deduplication_rapport.json", {"conserves": unique, "supprimes": removed}))
        summary = f"{len(removed)} doublon(s) supprimé(s) sur {len(search_results)} résultats → {len(unique)} conservés"
    else:
        rows = ctx.read_data_rows()
        seen, dup = {}, []
        for i, r in enumerate(rows):
            key = (r.get("doi") or "").lower() or r.get("id")
            if key in seen:
                dup.append({"ligne": i + 2, "id": r.get("id"), "doi": r.get("doi"), "doublon_de": seen[key]})
            else:
                seen[key] = r.get("id")
        # titres quasi identiques
        titles = [(r.get("theme") or "", r.get("id")) for r in rows]
        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                if _title_dup(titles[i][0], titles[j][0]):
                    dup.append({"id": titles[j][1], "doublon_de": titles[i][1], "raison": "titre similaire"})
        details = [f"Lignes analysées : {len(rows)} | doublons détectés : {len(dup)}"]
        summary = f"{len(dup)} doublon(s) détecté(s) dans la base 42 champs"
        if dup:
            artifacts.append(ctx.save_json("deduplication_rapport.json", dup))

    return SkillResult(ok=True, summary=summary, artifacts=artifacts, details=details,
                       data={"source": source})
