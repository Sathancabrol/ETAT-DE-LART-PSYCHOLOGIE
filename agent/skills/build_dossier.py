"""
Compétence : dossier stratégique (plan d'implémentation en crescendo).

Pour les questions ouvertes de transformation (« améliorer X avec l'IA »),
génère un dossier complet et visualisable :
  • dossier_plan.md    — plan phasé (crescendo organique) : phases, actions,
                         outils, prérequis, KPI, risques, quick wins ;
  • dossier.md         — synthèse documentaire (sources si recherche faite) ;
  • dossier_graph.json — graphe de concepts/feuilles de route pour D3.

Déterministe : structure robuste adaptée au sujet par extraction de mots-clés ;
s'enrichit automatiquement d'une recherche documentaire si aucune n'a été faîte.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from agent.core.registry import skill, SkillResult
from agent.core.context import extract_query

PHASE_HINTS = {
    1: [r"admin", r"bureau", r"document", r"factur", r"rapport", r"gestion", r"erp", r"crm"],
    2: [r"visi[èe]re", r"hud", r"tablet", r"terrain", r"mobile", r"r[ée]alit[ée] (augment|mixte)", r"tuto"],
    3: [r"robot", r"autonom", r"exosquel", r"drone", r"implant", r"iot", r"capteur", r"jumeau num"],
}
STOP = set("le la les de des du un une et en dans pour avec sur par au aux ce cette que qui est sont je tu il nous vous ils me my te se y a à d l s c n m t qu".split())


def _key_terms(task: str, n: int = 8) -> List[str]:
    words = [w for w in re.findall(r"[a-zà-ÿœ-]{3,}", task.lower()) if w not in STOP]
    return list(dict.fromkeys(words))[:n]


def _detect_phases(task: str) -> List[int]:
    phases = []
    for ph, patterns in PHASE_HINTS.items():
        if any(re.search(p, task.lower()) for p in patterns):
            phases.append(ph)
    return phases or [1, 2, 3]


PHASE_TEMPLATES = {
    1: ("Phase 1 — Socle administratif automatisé",
        "Automatiser les tâches bureautiques répétitives pour libérer le temps des cadres "
        "et assistants, avec transparence totale (documents visibles, expliqués, validés par l'humain).",
        ["Cartographie des tâches répétitives (facturation, rapports journaliers, planning, "
         "suivi matériaux, conformité)",
         "Assistants documentaires génératifs intégrés aux outils existants",
         "Tableaux de bord partagés temps réel (direction ↔ terrain)",
         "Formation courte des équipes : lire, corriger, approuver les documents générés"],
        ["Temps administratif par semaine (-30 à -50 % visé)", "Taux d'adoption hebdomadaire",
         "Erreurs documentaires détectées"]),
    2: ("Phase 2 — Augmentation sur le terrain",
        "Équiper les équipes terrain d'assistants contextuels (visières/tablettes connectées) "
        "avec HUD pédagogique : tutoriels pas-à-pas, contrôle qualité guidé, sécurité renforcée.",
        ["Visières connectées / tablettes avec HUD : plans, checklist, tuto immersif",
         "Assistance photo-vidéo : « ce que je vois » analysé (conformité, défauts)",
         "Mode tutorat pour intérimaires et montée en compétence accélérée",
         "Remontée terrain automatique (avancement, incidents, météo chantier)"],
        ["Temps de formation d'un nouvel arrivant", "Défauts détectés avant réception",
         "Incidents de sécurité évités"]),
    3: ("Phase 3 — Chantiers augmentés puis autonomes",
        "Introduire progressivement robotique, exosquelettes, drones et coordination par IA "
        "— sur des lots pilotes à faible risque, en parallèle du socle humain.",
        ["Lots pilotes robotisés (terrassement, ferraillage, contrôle)",
         "Drones de suivi de chantier (photogrammétrie, avancement 3D)",
         "Exosquelettes pour postes pénibles (prévention TMS)",
         "Jumeau numérique du chantier alimenté en continu"],
        ["% du lot exécuté sans intervention", "Coût au m² du lot pilote vs référence",
         "Taux de disponibilité machines"]),
}


@skill(
    name="build_dossier",
    description="Génère un dossier stratégique complet pour une question de transformation : plan phasé en crescendo (actions, KPI, risques), synthèse documentaire et graphe de concepts visualisable.",
    category="synthese",
    triggers=[r"dossier", r"plan\b", r"strat[ée]gie", r"roadmap", r"am[ée]liorer", r"impl[ée]menter",
              r"int[ée]grer|int[ée]gration", r"transformer|transformation", r"organiser|organisation"],
    examples=[
        "dossier : améliorer l'infrastructure du BTP avec l'IA, implémentation en crescendo",
        "je veux intégrer l'IA dans mon entreprise — établis le plan",
    ],
    params={},
    defaults={},
    order=72,
)
def build_dossier(ctx, **_) -> SkillResult:
    task = ctx.state.get("task", "")
    subject = re.sub(r"^dossier\s*[:\-]?\s*", "", task, flags=re.I).strip() or task
    terms = _key_terms(subject)
    phases = _detect_phases(subject)

    # Recherche documentaire si aucune n'a été faite dans ce run
    results: List[Dict[str, Any]] = ctx.state.get("search_results") or []
    did_search = False
    if not results:
        from agent.core.registry import get_skill
        search = get_skill("search_literature")
        if search:
            q = extract_query(subject)
            res = search.fn(ctx, query=q)
            did_search = True
            results = ctx.state.get("search_results") or []

    degraded = ctx.offline_hits > 0
    years = sorted({str(r.get("annee")) for r in results if r.get("annee")})

    plan = [
        f"# Dossier stratégique — {subject[:100]}",
        "",
        f"> Généré par Uranus ♅ sous gouvernance SOL ☉ / Vénus ♀ · run `{ctx.run_id}`",
        "",
        "## Principe directeur : crescendo organique",
        "",
        "Commencer simple (socle administratif, gains immédiats, confiance des équipes), "
        "puis augmenter le terrain, puis introduire l'autonomie — chaque phase finance "
        "et légitime la suivante. L'humain voit, comprend et valide à chaque étape.",
        "",
        "## Portrait de la demande",
        "",
        f"- Mots-clés extraits : {', '.join(terms)}",
        f"- Phases activées : {', '.join(f'Phase {p}' for p in phases)}",
        (f"- Assise documentaire : {len(results)} références"
         + (f" ({years[0]}–{years[-1]})" if years else "")
         + (" — fixtures de démonstration (hors-ligne)" if degraded else " — recherche réelle")
         if results else "- Assise documentaire : à compléter par une recherche"),
        "",
        "## Plan de déploiement",
        "",
    ]
    for ph in phases:
        title, goal, actions, kpis = PHASE_TEMPLATES[ph]
        plan += [f"### {title}", "", f"**Objectif.** {goal}", "", "**Actions :**"]
        plan += [f"- {a}" for a in actions]
        plan += ["", "**Indicateurs (KPI) :**"] + [f"- {k}" for k in kpis]
        plan += ["", "**Risques & parades :**",
                 "- Adoption faible → co-construction avec les utilisateurs dès la semaine 1 ;",
                 "- Données sensibles → hébergement maîtrisé, journalisation, réversibilité ;",
                 "- Sur-promesse technologique → lots pilotes courts, critères d'arrêt explicites.",
                 ""]
    plan += [
        "## Quick wins (30 jours)",
        "",
        "1. Choisir UNE tâche administrative répétitive et l'automatiser avec supervision humaine ;",
        "2. Mesurer le temps gagné et le présenter aux équipes (transparence = confiance) ;",
        "3. Identifier un chantier pilote bienveillant pour la phase 2 ;",
        "4. Documenter chaque étape (le système le fait — voir dossier_graph.json).",
        "",
        "## Prochaines missions à confier au système",
        "",
        "- « mission : recherche systématique <sujet précis> » — assise documentaire ;",
        "- « mission : dossier <volet spécifique> » — déclinaison par lot ;",
        "- « veille <sujet> » — signaux faibles hebdomadaires.",
    ]

    synth = [
        f"# Synthèse documentaire — {subject[:100]}",
        "",
    ]
    if results:
        synth += [f"{len(results)} références mobilisées"
                  + (f" ({years[0]}–{years[-1]})" if years else "") + " :", ""]
        for r in sorted(results, key=lambda x: -int(x.get("citations") or 0))[:12]:
            synth.append(f"- ({r.get('annee')}, {r.get('citations', 0)} cit.) "
                         f"**{str(r.get('titre', ''))[:90]}** — {str(r.get('auteurs', ''))[:50]} · "
                         f"DOI: {r.get('doi', 'n/a')}")
        if degraded:
            synth += ["", "> ⚠️ Réseau indisponible : références de démonstration (fixtures). "
                          "Relancer la mission avec accès réseau pour des données réelles."]
    else:
        synth += ["Aucune référence mobilisée — lancer une recherche systématique en mission préalable."]

    # Graphe de concepts (visualisable en D3)
    g_nodes = [{"id": "sujet", "label": subject[:48], "type": "racine", "color": "#818cf8"}]
    g_links = []
    for ph in phases:
        pid = f"phase{ph}"
        g_nodes.append({"id": pid, "label": PHASE_TEMPLATES[ph][0].split("—")[1].strip(),
                        "type": "phase", "color": "#fbbf24"})
        g_links.append({"source": "sujet", "target": pid, "type": "phase"})
        for a in PHASE_TEMPLATES[ph][2]:
            aid = f"{pid}:{a[:36]}"
            g_nodes.append({"id": aid, "label": a[:60], "type": "action", "color": "#38bdf8"})
            g_links.append({"source": pid, "target": aid, "type": "action"})
    for r in results[:10]:
        rid = f"ref:{r.get('doi', r.get('titre', '')[:20])}"
        g_nodes.append({"id": rid, "label": str(r.get("titre", ""))[:60], "type": "reference",
                        "color": "#34d399", "doi": r.get("doi")})
        g_links.append({"source": "sujet", "target": rid, "type": "source"})
    graph = {"nodes": g_nodes, "links": g_links}

    artifacts = [ctx.save_md("dossier_plan.md", "\n".join(plan)),
                 ctx.save_md("dossier.md", "\n".join(synth)),
                 ctx.save_json("dossier_graph.json", graph)]

    details = [f"Plan en {len(phases)} phase(s) : "
               + " → ".join(f"Phase {p}" for p in phases),
               f"{len(g_nodes)} nœuds de feuille de route (visualisable en graphe)"]
    if did_search:
        details.append(f"Recherche documentaire automatique : {len(results)} références")
    if degraded:
        details.append("⚠️ Mode dégradé : références de démonstration")

    return SkillResult(ok=True, degraded=degraded,
                       summary=(f"Dossier stratégique généré : plan {len(phases)} phases, "
                                f"{len(g_nodes)} nœuds de graphe, {len(results)} références"),
                       artifacts=artifacts, details=details,
                       data={"phases": phases, "graph_nodes": len(g_nodes),
                             "references": len(results)})
