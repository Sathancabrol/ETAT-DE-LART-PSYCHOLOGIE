"""
Compétence : Trust Factor.

Deux fonctions :
  1. audit de cohérence des trust_factor existants (niveau vs valeur,
     justification présente) ;
  2. re-calcul heuristique M+R+O+C+T-P à partir des champs open science
     disponibles (open_access, data_open, code_open, preregistration,
     type de publication, triangulation, peer review) avec justification
     détaillée ligne par ligne.

Le score heuristique est un dépistage : il ne remplace pas le jugement
expert codé dans trust_justification.
"""

from __future__ import annotations

from typing import Dict, List

from agent.core.registry import skill, SkillResult


def _bool(v: str) -> bool:
    return str(v).strip().upper() == "TRUE"


def _heuristic_trust(row: Dict[str, str]) -> Dict:
    """Score heuristique M(0-30) + R(0-20) + O(0-20) + C(0-15) + T(0-15) - P."""
    j: List[str] = []

    # M — méthodologie (0-30)
    m = 10
    tp = row.get("type_publication", "")
    if tp == "meta_analyse":
        m, _ = 30, j.append("M+20 : méta-analyse")
    elif tp == "revue_systematique":
        m, _ = 25, j.append("M+15 : revue systématique")
    elif tp == "article_empirique":
        m = 15
        j.append("M+5 : article empirique")
    st = row.get("sources_triangulation", "")
    if len([p for p in st.split("+") if p.strip()]) >= 3:
        m = min(30, m + 5)
        j.append("M+5 : triangulation ≥3 sources")
    if "random" in (row.get("study_design") or "").lower():
        j.append("M note : design randomisé détecté")

    # R — réplication (0-20)
    r = 8
    if row.get("sample_size", "").isdigit() and int(row["sample_size"]) >= 1000:
        r = 14
        j.append("R+6 : grand échantillon (N≥1000)")

    # O — open science (0-20)
    o = 0
    if _bool(row.get("open_access", "")):
        o += 6; j.append("O+6 : accès ouvert")
    if _bool(row.get("data_open", "")):
        o += 7; j.append("O+7 : données ouvertes")
    if _bool(row.get("code_open", "")):
        o += 3; j.append("O+3 : code ouvert")
    if _bool(row.get("preregistration", "")):
        o += 4; j.append("O+4 : préenregistrement")

    # C — cohérence (0-15)
    c = 10
    if row.get("question_scientifique", "").strip().endswith("?"):
        c += 2; j.append("C+2 : question scientifique explicite")
    if len([t for t in row.get("tags", "").split(",") if t.strip()]) >= 3:
        c += 3; j.append("C+3 : tags ≥3")

    # T — transparence (0-15)
    t = 8
    if _bool(row.get("peer_reviewed", "")):
        t += 5; j.append("T+5 : peer review")
    if row.get("trust_justification", "").strip() and row.get("trust_justification") != "ébauche auto-générée, à évaluer":
        t += 2; j.append("T+2 : justification trust fournie")

    # P — pénalités (0-50)
    p = 0
    if not _bool(row.get("peer_reviewed", "")) and row.get("peer_reviewed") == "FALSE":
        p += 15; j.append("P+15 : non peer review")
    if row.get("type_publication") == "preprint":
        p += 10; j.append("P+10 : preprint")

    total = max(0, min(100, m + r + o + c + t - p))
    return {"total": total, "detail": {"M": m, "R": r, "O": o, "C": c, "T": t, "P": p},
            "justification": j}


def _niveau(score: int) -> str:
    if score <= 29: return "faible"
    if score <= 59: return "modere"
    if score <= 84: return "eleve"
    return "tres_eleve"


@skill(
    name="trust_scoring",
    description="Audit et re-calcul heuristique du Trust Factor (M+R+O+C+T-P) avec justification détaillée par référence ; détecte les incohérences trust_niveau/trust_factor.",
    category="qualite",
    triggers=[r"trust", r"confiance", r"fiabilit"],
    examples=[
        "calculer le trust factor de la base",
        "auditer la fiabilité des références",
    ],
    params={"file": "chemin du CSV (défaut : base 42 champs)"},
    defaults={},
    order=45,
)
def trust_scoring(ctx, file: str = "", **_) -> SkillResult:
    rows = ctx.read_data_rows(file or None)
    if not rows:
        return SkillResult(ok=False, summary="Base vide ou introuvable.")

    report, incoherences = [], []
    for row in rows:
        heur = _heuristic_trust(row)
        tf = row.get("trust_factor", "")
        declared = None
        if tf.isdigit():
            declared = int(tf)
            if row.get("trust_niveau") and row["trust_niveau"] != _niveau(declared):
                incoherences.append(f"{row['id']} : trust_factor {declared} ↔ niveau « {row['trust_niveau']} » (attendu {_niveau(declared)})")
        ecart = None if declared is None else heur["total"] - declared
        report.append({
            "id": row.get("id"),
            "reference": row.get("reference_courte"),
            "trust_declare": declared,
            "trust_heuristique": heur["total"],
            "ecart": ecart,
            "detail": heur["detail"],
            "justification": heur["justification"],
        })

    avg_declared = sum(r["trust_declare"] for r in report if r["trust_declare"] is not None) / max(1, sum(1 for r in report if r["trust_declare"] is not None))
    avg_heur = sum(r["trust_heuristique"] for r in report) / len(report)
    big_gaps = [r for r in report if r["ecart"] is not None and abs(r["ecart"]) >= 15]

    lines = ["# Rapport Trust Factor (heuristique M+R+O+C+T-P)", "",
             f"- Références analysées : **{len(report)}**",
             f"- Trust déclaré moyen : **{avg_declared:.1f}** | heuristique moyen : **{avg_heur:.1f}**",
             f"- Écarts ≥15 points : **{len(big_gaps)}** | incohérences niveau : **{len(incoherences)}**", "",
             "| Référence | Déclaré | Heuristique | Écart | M | R | O | C | T | P |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in report:
        d = r["detail"]
        lines.append(f"| {r['reference']} | {r['trust_declare']} | {r['trust_heuristique']} | {r['ecart']} | {d['M']} | {d['R']} | {d['O']} | {d['C']} | {d['T']} | -{d['P']} |")
    if incoherences:
        lines += ["", "## Incohérences détectées", ""] + [f"- {i}" for i in incoherences]
    lines += ["", "> ⚠️ Score heuristique = dépistage automatique. Ne remplace pas l'évaluation experte (RoB2/AMSTAR2/GRADE)."]
    artifacts = [ctx.save_md("trust_rapport.md", "\n".join(lines)),
                 ctx.save_json("trust_rapport.json", report)]

    ctx.state["trust"] = {"moyen_declare": round(avg_declared, 1), "moyen_heuristique": round(avg_heur, 1)}
    details = [f"Trust déclaré moyen : {avg_declared:.1f} / heuristique : {avg_heur:.1f}",
               f"Écarts ≥15 points : {len(big_gaps)} — à examiner manuellement"] + incoherences[:5]
    summary = f"Trust factor audité sur {len(report)} références (écart moyen déclaré/heuristique : {avg_heur - avg_declared:+.1f})"
    return SkillResult(ok=True, summary=summary, artifacts=artifacts, details=details,
                       data={"rapport": report[:20], "moyennes": ctx.state["trust"]})
