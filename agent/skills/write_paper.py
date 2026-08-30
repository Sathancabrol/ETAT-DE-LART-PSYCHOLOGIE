"""
Compétence : rédaction d'un papier scientifique (synthèse générée par le système).

À partir des résultats de recherche du run (ou de la base), produit :
  • paper.md            — article structuré : titre, résumé, méthodologie
                          (PRISMA), résultats (tableau + métriques), discussion
                          (gaps), références (DOI) ;
  • paper_documentation.md — guide de lecture : comment évaluer, limites,
                          liens vers la base et les rapports de trust/biais.

Le papier est une SYNTHÈSE DOCUMENTAIRE générée : il est signalé comme tel,
avec ses limites (mode dégradé, couverture des bases) — jamais une fausse
publication primaire.
"""

from __future__ import annotations

from typing import Dict, List

from agent.core.registry import skill, SkillResult


def _is_meta(r: Dict) -> bool:
    blob = (str(r.get("titre", "")) + " " + str(r.get("type", ""))).lower()
    return "meta" in blob or "systematic" in blob or "umbrella" in blob or "revue" in blob


@skill(
    name="write_paper",
    description="Génère un papier scientifique (synthèse structurée : résumé, méthode PRISMA, résultats, discussion, références DOI) + sa documentation de lecture, à partir des résultats du run ou de la base.",
    category="synthese",
    triggers=[r"m[ée]ta.?analys", r"papier", r"paper", r"article\s+scientifique", r"r[ée]dige", r"publication"],
    examples=[
        "méta-analyse sur l'attention — génère le papier scientifique",
        "rédiger le papier de synthèse des résultats",
    ],
    params={},
    defaults={},
    order=75,
)
def write_paper(ctx, **_) -> SkillResult:
    results: List[Dict] = (ctx.state.get("search_results_dedup")
                           or ctx.state.get("search_results") or [])
    source = "recherche du run"
    if not results:
        results = ctx.read_data_rows()
        source = "base 42 champs"
    if not results:
        return SkillResult(ok=False, summary="Aucune donnée : lancez d'abord une recherche.")

    query = ctx.state.get("search_query", "cartographie")
    prisma = ctx.state.get("prisma") or {}
    degraded = ctx.state.get("degraded") or ctx.offline_hits > 0
    metas = [r for r in results if _is_meta(r)]
    total_cit = sum(int(r.get("citations") or 0) for r in results)
    top = sorted(results, key=lambda r: -int(r.get("citations") or 0))[:10]
    years = sorted({str(r.get("annee")) for r in results if r.get("annee")})

    lines = [
        f"# {query[:80].capitalize()} — synthèse documentaire générée",
        "",
        "> ⚠️ **Document généré par le système Uranus/Cognitorium** : synthèse "
        "documentaire automatique à partir de bases bibliographiques. Ce n'est ni une "
        "publication primaire ni une méta-analyse originale — voir la documentation associée.",
        "",
        "## Résumé",
        "",
        (f"Cette synthèse porte sur **{len(results)} références**"
         + (f" ({len(metas)} revues/méta-analyses)" if metas else "")
         + f" couvrant la période {years[0] if years else 'n/a'}–{years[-1] if years else 'n/a'}, "
         f"pour un total de **{total_cit} citations cumulées**. "
         f"Source des données : {source}." + (" Les données proviennent de fixtures de "
         "démonstration (réseau indisponible au moment du run)." if degraded else "")),
        "",
        "## 1. Introduction",
        "",
        f"Question documentaire : *{query}*.",
        " L'objectif est de cartographier les travaux disponibles, hiérarchiser par "
        "niveau de preuve et citations, et identifier les écarts (gaps) documentés.",
        "",
        "## 2. Méthodologie",
        "",
        "- Bases interrogées : " + ", ".join(sorted({str(r.get("base", "base")) for r in results})),
        f"- Références identifiées : {prisma.get('identifies', len(results))}",
        f"- Après déduplication : {prisma.get('apres_deduplication', len(results))}",
        "- Critères : articles à comité de lecture priorisés, tri par citations décroissantes,",
        "  DOI vérifiés par expression régulière.",
        "",
        "## 3. Résultats",
        "",
        "| # | Référence | Année | Citations | DOI |",
        "|---|-----------|-------|-----------|-----|",
    ]
    for i, r in enumerate(top, 1):
        lines.append(f"| {i} | {str(r.get('titre') or r.get('theme', ''))[:70]} "
                     f"| {r.get('annee', '')} | {r.get('citations', r.get('citations_google_scholar', ''))} "
                     f"| {r.get('doi', 'n/a')} |")
    lines += [
        "",
        "### 3.1 Répartition",
        "",
        f"- Revues systématiques / méta-analyses : **{len(metas)}**",
        f"- Autres publications : **{len(results) - len(metas)}**",
        f"- Citations cumulées : **{total_cit}**",
        "",
        "## 4. Discussion",
        "",
        "### 4.1 Convergences",
        "",
        "Les références les plus citées dominent la littérature du domaine ; les revues "
        "cumulatives (méta-analyses) fournissent les estimations d'effet les plus robustes.",
        "",
        "### 4.2 Limites de cette synthèse",
        "",
        "- Couverture limitée aux bases interrogées et à la fenêtre temporelle du run ;",
        "- Pas d'extraction à deux évaluateurs indépendants (Kappa) ;",
        "- Les scores de confiance (trust factor) des nouvelles entrées restent à évaluer.",
        "",
        "## 5. Références",
        "",
    ]
    for r in results:
        doi = r.get("doi") or ""
        ref = (r.get("auteurs") or r.get("reference_courte") or "")[:60]
        title = str(r.get("titre") or r.get("theme") or "")[:90]
        lines.append(f"- {ref} — *{title}* "
                     f"({r.get('annee', 'n/a')}). https://doi.org/{doi}" if doi
                     else f"- {ref} — *{title}* ({r.get('annee', 'n/a')}).")
    lines += [
        "",
        "---",
        f"*Généré par Uranus ♅ sous gouvernance SOL ☉ / Vénus ♀ — run `{ctx.run_id}`.*",
    ]

    doc = [
        "# Documentation — comment lire ce papier généré",
        "",
        "## Statut épistémique",
        "Synthèse **documentaire** : agrégation et hiérarchisation de références réelles.",
        "Elle ne remplace ni une revue systématique préenregistrée (2 évaluateurs, Kappa),",
        "ni une méta-analyse originale (extraction d'effets, hétérogénéité I², biais de publication).",
        "",
        "## Comment évaluer chaque référence",
        "1. **Trust factor** (0-100) : méthodo + réplication + open science + cohérence + transparence ;",
        "2. **Niveau de preuve** : méta-analyse > revue systématique > expérimental > corrélationnel > théorique ;",
        "3. **Recoupement** : `sources_triangulation ≥ 3` exigé dans la base 42 champs.",
        "",
        "## Données et reproductibilité",
        f"- Run complet : `output/agent_runs/{ctx.run_id}/trace.json` ;",
        "- Résultats bruts : `recherche_resultats.csv` / `.json` dans le même dossier ;",
        "- Base 42 champs : `data/nodes_etat_art_psychologie.csv`.",
        "",
        "## Prolonger le travail",
        "- Demander l'enrichissement des DOI retenus (`enrich_doi`) ;",
        "- Lancer l'audit trust + biais (`trust_scoring`, `bias_assessment`) ;",
        "- Programmer une veille sur le sujet (`monitor_watch`).",
    ]

    artifacts = [ctx.save_md("paper.md", "\n".join(lines)),
                 ctx.save_md("paper_documentation.md", "\n".join(doc))]
    summary = (f"Papier de synthèse généré ({len(results)} réf., {len(metas)} méta-analyses, "
               f"{total_cit} citations) + documentation de lecture")
    return SkillResult(ok=True, summary=summary, degraded=bool(degraded),
                       artifacts=artifacts,
                       details=[f"paper.md : {len(lines)} sections (résumé, méthode, résultats, discussion, références)",
                                "paper_documentation.md : statut épistémique, évaluation, reproductibilité"],
                       data={"paper": "paper.md", "documentation": "paper_documentation.md",
                             "references": len(results), "meta_analyses": len(metas)})
