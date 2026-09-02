"""
Compétence : évaluation heuristique du risque de biais.

Dépistage automatisé (à distinguer d'une évaluation RoB2/ROBINS-I/AMSTAR2
complète réalisée par deux évaluateurs) :
  - revues systématiques / méta-analyses → grille AMSTAR2-lite (7 items) ;
  - articles empiriques → signaux RoB2-lite (randomisation, préenregistrement,
    données ouvertes, taille d'échantillon).

Chaque item est noté : faible / incertain / élevé, avec justification
issue des champs disponibles. Produit un rapport markdown + JSON.
"""

from __future__ import annotations

from typing import Dict, List

from agent.core.registry import skill, SkillResult


def _b(v: str) -> bool:
    return str(v).strip().upper() == "TRUE"


def _amstar2_lite(row: Dict[str, str]) -> Dict:
    items = []
    tri = len([p for p in (row.get("sources_triangulation") or "").split("+") if p.strip()])
    items.append(("Recherche ≥2 bases (triangulation)", "faible" if tri >= 3 else ("incertain" if tri == 2 else "élevé")))
    items.append(("Sélection 2 évaluateurs", "incertain"))  # non renseigné dans la base
    items.append(("Extraction données dupliquée", "incertain"))
    items.append(("Liste études exclues", "incertain"))
    items.append(("Biais publication testé", "incertain" if not (row.get("notes_internes") or "") else "faible"))
    items.append(("Financements déclarés", "incertain"))
    items.append(("Préenregistrement protocole", "faible" if _b(row.get("preregistration", "")) else "élevé"))
    n_low = sum(1 for _, r in items if r == "faible")
    n_high = sum(1 for _, r in items if r == "élevé")
    global_r = "élevé" if n_high >= 2 else ("modéré" if n_high == 1 else ("faible" if n_low >= 5 else "modéré"))
    return {"grille": "AMSTAR2-lite", "items": [{"item": i, "risque": r} for i, r in items],
            "risque_global": global_r}


def _rob2_lite(row: Dict[str, str]) -> Dict:
    items = []
    design = (row.get("study_design") or "").lower()
    items.append(("Biais de sélection (randomisation)", "faible" if "random" in design else "incertain"))
    items.append(("Biais de détection (aveugle)", "incertain"))
    items.append(("Données manquantes (attrition)", "incertain"))
    n = row.get("sample_size", "")
    items.append(("Puissance statistique", "faible" if n.isdigit() and int(n) >= 100 else "incertain"))
    items.append(("Préenregistrement", "faible" if _b(row.get("preregistration", "")) else "élevé"))
    items.append(("Vérifiabilité (données+code)", "faible" if _b(row.get("data_open", "")) and _b(row.get("code_open", "")) else "incertain"))
    n_high = sum(1 for _, r in items if r == "élevé")
    global_r = "élevé" if n_high >= 1 else ("faible" if sum(1 for _, r in items if r == "faible") >= 4 else "incertain")
    return {"grille": "RoB2-lite", "items": [{"item": i, "risque": r} for i, r in items],
            "risque_global": global_r}


@skill(
    name="bias_assessment",
    description="Dépistage heuristique du risque de biais : AMSTAR2-lite (revues/méta-analyses) et RoB2-lite (articles empiriques), rapport par référence avec justifications.",
    category="qualite",
    triggers=[r"biais", r"rob\s?2", r"amstar", r"risque", r"grade"],
    examples=[
        "évaluer le risque de biais des références",
        "dépister les biais avec AMSTAR2",
    ],
    params={"ids": "restreindre à certaines références (défaut : toute la base)"},
    defaults={},
    order=50,
)
def bias_assessment(ctx, ids: List[str] | None = None, **_) -> SkillResult:
    rows = ctx.read_data_rows()
    if ids:
        rows = [r for r in rows if r.get("id") in ids]
    if not rows:
        return SkillResult(ok=False, summary="Aucune référence à évaluer.")

    assessments = []
    for row in rows:
        tp = row.get("type_publication", "")
        if tp in {"revue_systematique", "meta_analyse"}:
            a = _amstar2_lite(row)
        elif tp in {"article_empirique", "conference"}:
            a = _rob2_lite(row)
        else:
            a = {"grille": "n/a", "items": [{"item": "type non évaluable", "risque": "incertain"}],
                 "risque_global": "incertain"}
        a.update({"id": row.get("id"), "reference": row.get("reference_courte"), "type": tp})
        assessments.append(a)

    dist = {}
    for a in assessments:
        dist[a["risque_global"]] = dist.get(a["risque_global"], 0) + 1

    lines = ["# Dépistage heuristique du risque de biais", "",
             f"- Références évaluées : **{len(assessments)}**",
             f"- Distribution des risques globaux : **{dist}**", ""]
    for a in assessments:
        lines.append(f"## {a['reference']} ({a['grille']}) — risque global : **{a['risque_global']}**")
        lines += [f"- {i['item']} : {i['risque']}" for i in a["items"]]
        lines.append("")
    lines.append("> ⚠️ Dépistage automatique sur métadonnées. Une évaluation complète exige " \
                 "RoB2/ROBINS-I (Cochrane) ou AMSTAR2 à deux évaluateurs indépendants + Kappa.")
    artifacts = [ctx.save_md("biais_rapport.md", "\n".join(lines)),
                 ctx.save_json("biais_rapport.json", assessments)]

    ctx.state["biais"] = {"distribution": dist}
    high = [a["reference"] for a in assessments if a["risque_global"] == "élevé"]
    details = [f"Distribution : {dist}"]
    if high:
        details.append(f"Risque élevé : {', '.join(high[:8])}")
    summary = f"Risque de biais dépisté sur {len(assessments)} références : {dist}"
    return SkillResult(ok=True, summary=summary, artifacts=artifacts, details=details,
                       data={"distribution": dist, "evaluations": assessments[:10]})
