"""
Planificateur à règles (cerveau par défaut, sans clé API).

Étapes :
  1. Extraction de paramètres depuis la tâche (DOI, années, fenêtre,
     bases mentionnées, sujet).
  2. Sélection des compétences par motifs déclencheurs (score de match).
  3. Composition du pipeline : le vocabulaire « systématique / état de
     l'art / revue » déclenche l'enchaînement canonique
     recherche → déduplication → PRISMA → synthèse.
  4. Tri par ordre canonique des compétences.

Garanties : toujours au moins une étape ; toute compétence inconnue
est ignorée ; le plan est déterministe et traçable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from agent.core.context import extract_dois, extract_query, extract_years
from agent.core.registry import get_skill, list_skills

SYSTEMATIC_RE = re.compile(r"syst[ée]matique|état\s+de\s+l.art|revue\s+de\s+litt[ée]rature|cartographie|exhausti", re.I)
PIPELINE_RE = re.compile(r"pipeline|complet|cha[îi]ne|tout\s+le\s+processus|workflow", re.I)
PAPER_RE = re.compile(r"m[ée]ta.?analys|papier|paper|article\s+scientifique|r[ée]dige|publication", re.I)
DOSSIER_RE = re.compile(r"dossier|strat[ée]gie|roadmap|am[ée]liorer|impl[ée]menter|int[ée]grer|transformation", re.I)


@dataclass
class Step:
    skill: str
    params: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"skill": self.skill, "params": self.params, "reason": self.reason}


@dataclass
class Plan:
    steps: List[Step] = field(default_factory=list)
    brain: str = "regles"           # regles | llm
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"brain": self.brain, "rationale": self.rationale,
                "steps": [s.to_dict() for s in self.steps]}


def _detect_bases(task: str) -> Optional[List[str]]:
    t = task.lower()
    bases = []
    if "pubmed" in t:
        bases.append("pubmed")
    if "crossref" in t:
        bases.append("crossref")
    if "openalex" in t:
        bases.append("openalex")
    return bases or None


def build_plan(task: str) -> Plan:
    task_low = task.lower()

    # 1. Sélection par déclencheurs
    scored = [(s.match_score(task_low), s) for s in list_skills()]
    selected = {s.name for score, s in scored if score > 0}

    # 2. Vocabulaire de pipeline
    if SYSTEMATIC_RE.search(task_low):
        selected |= {"search_literature", "deduplicate", "prisma_flow", "synthesize"}
    if PIPELINE_RE.search(task_low):
        selected |= {"validate_entries", "trust_scoring", "bias_assessment", "synthesize"}
    if PAPER_RE.search(task_low):
        selected |= {"search_literature", "deduplicate", "synthesize", "write_paper"}
    if DOSSIER_RE.search(task_low):
        selected |= {"build_dossier"}

    # 3. Paramètres communs extraits de la tâche
    common: Dict[str, Any] = {}
    years = extract_years(task)
    if years:
        common.update({"from_year": years["from"], "to_year": years["to"]})
    dois = extract_dois(task)
    if dois:
        selected.add("enrich_doi")
    bases = _detect_bases(task)
    if bases:
        common["bases"] = bases

    # 4. Construire les étapes dans l'ordre canonique
    steps: List[Step] = []
    for spec in list_skills():
        if spec.name not in selected:
            continue
        params: Dict[str, Any] = {**spec.defaults, **common}
        if spec.name == "search_literature":
            params["query"] = extract_query(task)
            steps.append(Step(spec.name, params, "recherche documentaire multi-bases"))
        elif spec.name == "enrich_doi":
            steps.append(Step(spec.name, {"dois": dois, "append": bool(re.search(r"ajouter?\s+.+(base|csv)|\bappend\b", task_low))},
                              "DOI détecté(s) dans la tâche"))
        elif spec.name == "monitor_watch":
            steps.append(Step(spec.name, {}, "demande de veille"))
        else:
            steps.append(Step(spec.name, params, f"déclencheur : {spec.name}"))

    # 5. Garantie : au moins une étape (défaut : recherche + synthèse)
    if not steps:
        steps = [Step("search_literature", {"query": extract_query(task), **common}, "compétence par défaut"),
                 Step("synthesize", {"source": "search"}, "synthèse des résultats")]

    rationale = (f"{len(steps)} compétence(s) sélectionnée(s) sur {len(list_skills())} "
                 f"par motifs déclencheurs" + (" + composition pipeline systématique" if SYSTEMATIC_RE.search(task_low) else ""))
    return Plan(steps=steps, brain="regles", rationale=rationale)
