"""
Compétence : métriques de citations (OpenAlex).

Met à jour citations_openalex, open_access et date_releve_citations pour
toutes les lignes de la base 42 champs (ou une liste de DOI fournie).
"""

from __future__ import annotations

from datetime import date
from typing import List

from agent.core.registry import skill, SkillResult
from agent.core.context import DATA_CSV, ROOT


@skill(
    name="citation_metrics",
    description="Met à jour les métriques de citations (OpenAlex : cited_by_count, accès ouvert) pour la base ou une liste de DOI.",
    category="donnees",
    triggers=[r"citations?", r"m[ée]triques?", r"impact", r"open.?alex", r"citation metrics"],
    examples=[
        "mettre à jour les métriques de citations de la base",
        "quel est le nombre de citations des références",
    ],
    params={"dois": "liste de DOI (défaut : toutes les lignes de la base)"},
    defaults={},
    order=20,
)
def citation_metrics(ctx, dois: List[str] | None = None, **_) -> SkillResult:
    rows = ctx.read_data_rows()
    targets = dois or [r["doi"] for r in rows if r.get("doi")]
    if not targets:
        return SkillResult(ok=False, summary="Aucun DOI à traiter (base vide ou aucun DOI fourni).")

    updated, offline, missing = {}, False, []
    for doi in targets[:40]:
        res = ctx.http_get("https://api.openalex.org/works/doi:" + doi,
                           fixture="openalex_work.json")
        if not res["ok"] or not res["json"]:
            missing.append(doi)
            continue
        offline = offline or res["offline"]
        j = res["json"]
        updated[doi] = {"citations": j.get("cited_by_count", 0),
                        "open_access": bool((j.get("open_access") or {}).get("is_oa"))}

    # Mise à jour du CSV si on a traité la base
    artifacts = []
    if not dois and updated:
        today = date.today().isoformat()
        for r in rows:
            if r.get("doi") in updated:
                r["citations_openalex"] = str(updated[r["doi"]]["citations"])
                r["open_access"] = "TRUE" if updated[r["doi"]]["open_access"] else "FALSE"
                r["date_releve_citations"] = today
        headers = ctx.data_headers()
        with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            w.writerows(rows)
        artifacts.append(str(DATA_CSV.relative_to(ROOT)))

    total_cit = sum(v["citations"] for v in updated.values())
    details = [f"DOI interrogés : {len(targets)} | mis à jour : {len(updated)} | introuvables : {len(missing)}",
               f"Total citations OpenAlex cumulées : {total_cit}"]
    if missing:
        details.append(f"Introuvables : {', '.join(missing[:5])}")
    summary = (f"{len(updated)}/{len(targets)} références mises à jour "
               f"({total_cit} citations cumulées)"
               + (" [MODE DÉGRADÉ hors-ligne]" if offline else ""))
    return SkillResult(ok=bool(updated), summary=summary, degraded=offline,
                       data={"updated": updated}, artifacts=artifacts, details=details)
