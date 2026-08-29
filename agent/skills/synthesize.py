"""
Compétence : synthèse par domaine.

Groupe les références (base 42 champs ou résultats de recherche du run)
par domaine/sous-domaine, calcule les statistiques (effectifs, trust
moyen, distribution du niveau de preuve) et agrège les gaps déclarés
pour déboucher sur des questions de recherche. Génère un markdown.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List

from agent.core.registry import skill, SkillResult

GAP_REPLACEMENTS = {
    "": "non renseigné",
}


@skill(
    name="synthesize",
    description="Synthétise les références par domaine : effectifs, trust moyen, niveaux de preuve, gaps agrégés → rapport markdown avec questions de recherche émergentes.",
    category="synthese",
    triggers=[r"synth[ée]s", r"synth[ée]tise?r?", r"r[ée]sum", r"[ée]tat\s+des\s+lieux", r"cartograph"],
    examples=[
        "synthétiser les références par domaine",
        "faire une synthèse des gaps identifiés",
    ],
    params={"source": "'base' (CSV 42 champs) ou 'search' (résultats du run)"},
    defaults={"source": "auto"},
    order=70,
)
def synthesize(ctx, source: str = "auto", **_) -> SkillResult:
    search_results: List[Dict] = ctx.state.get("search_results_dedup") or ctx.state.get("search_results") or []
    if source == "auto":
        source = "search" if search_results else "base"

    if source == "search" and search_results:
        groups: Dict[str, List[Dict]] = defaultdict(list)
        for r in search_results:
            groups["Résultats de recherche"].append(r)
        lines = ["# Synthèse — résultats de recherche du run", "",
                 f"Requête : « {ctx.state.get('search_query', '')} » — {len(search_results)} références.", ""]
        for g, items in groups.items():
            by_year = Counter(str(r.get("annee")) for r in items if r.get("annee"))
            total_cit = sum(r.get("citations") or 0 for r in items)
            lines += [f"## {g} ({len(items)} réf.)", "",
                      f"- Répartition par année : {dict(sorted(by_year.items()))}",
                      f"- Citations cumulées : {total_cit}", "",
                      "### Top citations", ""]
            for r in sorted(items, key=lambda x: -(x.get("citations") or 0))[:10]:
                lines.append(f"- **{r.get('titre', '')[:100]}** — {r.get('auteurs', '')[:60]} ({r.get('annee')}) · {r.get('citations', 0)} cit. · DOI: {r.get('doi', 'n/a')}")
        lines += ["", "### Questions émergentes (automatique)", "",
                  "- Quelles références méritent une extraction complète (42 champs) ?",
                  "- Quels gaps du domaine ces résultats couvrent-ils / laissent-ils ouverts ?"]
        artifacts = [ctx.save_md("synthese.md", "\n".join(lines)),
                     ctx.save_json("synthese.json", search_results)]
        summary = f"Synthèse générée : {len(search_results)} références groupées (source : recherche du run)"
        data = {"groupes": {g: len(i) for g, i in groups.items()}, "total": len(search_results)}
        return SkillResult(ok=True, summary=summary, artifacts=artifacts,
                           details=[f"{len(search_results)} références, {sum(r.get('citations') or 0 for r in search_results)} citations cumulées"], data=data)

    # Source : base 42 champs
    rows = ctx.read_data_rows()
    if not rows:
        return SkillResult(ok=False, summary="Base vide : rien à synthétiser.")

    by_domain: Dict[str, List[Dict]] = defaultdict(list)
    for r in rows:
        by_domain[r.get("domaine") or r.get("grand_domaine") or "non classé"].append(r)

    lines = ["# Synthèse par domaine — Cognitorium", "",
             f"Base : {len(rows)} références · Trust moyen global : "
             f"{sum(int(r['trust_factor']) for r in rows if (r.get('trust_factor') or '').isdigit()) / max(1, len(rows)):.1f}", ""]
    all_gaps: Counter = Counter()
    for domain, items in sorted(by_domain.items(), key=lambda kv: -len(kv[1])):
        trusts = [int(r["trust_factor"]) for r in items if (r.get("trust_factor") or "").isdigit()]
        niv = Counter(r.get("niveau_preuve") for r in items if r.get("niveau_preuve"))
        lines += [f"## {domain} — {len(items)} réf.", "",
                  f"- Trust moyen : **{sum(trusts)/len(trusts):.1f}**" if trusts else "- Trust : n/d",
                  f"- Niveaux de preuve : {dict(niv)}",
                  f"- Sous-domaines : {', '.join(sorted({r.get('sous_domaine') for r in items if r.get('sous_domaine')}))[:180]}", "",
                  "**Gaps déclarés :**"]
        for r in items:
            gap = (r.get("gap_actuel") or "non renseigné").strip()
            lines.append(f"- ({r.get('reference_courte')}) {gap}")
            for kw in [g.strip() for g in gap.split(";") if len(g.strip()) > 8]:
                all_gaps[kw[:80]] += 1
        lines.append("")

    if all_gaps:
        lines += ["## Gaps transversaux les plus fréquents", ""]
        lines += [f"- {g} ({n}×)" for g, n in all_gaps.most_common(8)]
        lines += ["", "## Questions de recherche émergentes", ""]
        for g, n in all_gaps.most_common(3):
            lines.append(f"1. {g.capitalize()} : quelle opérationnalisation testable (design préenregistré, N≥1000) ?")

    artifacts = [ctx.save_md("synthese.md", "\n".join(lines)),
                 ctx.save_json("synthese.json", {"groupes": {d: [r["id"] for r in items] for d, items in by_domain.items()}})]
    ctx.state["synthese"] = {"domaines": {d: len(i) for d, i in by_domain.items()}}
    summary = f"Synthèse générée : {len(rows)} références réparties en {len(by_domain)} domaines"
    return SkillResult(ok=True, summary=summary, artifacts=artifacts,
                       details=[f"{len(by_domain)} domaines ; gaps transversaux : {len(all_gaps)}"],
                       data={"domaines": {d: len(i) for d, i in by_domain.items()}})
