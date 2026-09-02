"""
Cognitorium — Uranus ♅, l'agent scientifique chercheur
======================================================
Uranus (Ouranos, divinité primordiale du ciel) est un agent hybride
(règles par défaut, LLM optionnel) qui planifie et exécute des tâches de
recherche scientifique via des compétences (skills) :

  recherche documentaire → enrichment DOI → métriques de citations →
  déduplication → validation 42 champs → trust factor → évaluation
  heuristique des biais → flux PRISMA → synthèse par domaine →
  visualisation → veille scientifique.

Usage CLI :
    python -m agent run "rechercher les méta-analyses attention 2024-2026"
    python -m agent skills
    python -m agent runs

Usage Python :
    from agent import Agent
    result = Agent().run("valider la base et calculer le trust factor")
"""

from agent.core.registry import skill, SkillResult, list_skills, get_skill
from agent.core.agent import Agent

__all__ = ["skill", "SkillResult", "list_skills", "get_skill", "Agent"]

# Importer les modules de compétences pour déclencher l'enregistrement
import agent.skills  # noqa: F401,E402
