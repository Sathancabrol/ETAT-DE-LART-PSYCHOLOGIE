"""
Registre de compétences (skills) de l'agent chercheur.

Chaque compétence est une fonction Python décorée par @skill qui :
  - reçoit un AgentContext (accès aux chemins du projet, état partagé du run,
    répertoire d'artefacts) et des paramètres extraits de la tâche ;
  - retourne un SkillResult (statut, résumé, données, artefacts produits).

Le registre alimente : le planificateur à règles, le planificateur LLM,
la CLI (`agent skills`) et l'API web (`/api/agent/skills`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# ────────────────────────── Résultat de compétence ──────────────────────────

@dataclass
class SkillResult:
    ok: bool                                  # la compétence a-t-elle réussi
    summary: str                              # résumé une ligne (FR)
    data: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)  # chemins de fichiers produits
    details: List[str] = field(default_factory=list)    # lignes de détail pour le rapport
    degraded: bool = False                    # True si exécuté en mode dégradé (hors-ligne/fixtures)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "summary": self.summary,
            "degraded": self.degraded,
            "details": self.details,
            "artifacts": self.artifacts,
            "data": self.data,
        }


# ────────────────────────── Contexte d'exécution ──────────────────────────

# Défini ici pour éviter les imports circulaires ; enrichi dans context.py
class SkillContext:
    pass


# ────────────────────────── Métadonnées de compétence ──────────────────────────

@dataclass
class SkillSpec:
    name: str                       # identifiant unique (snake_case)
    fn: Callable[..., SkillResult]  # implémentation
    description: str = ""           # description FR
    category: str = "general"       # recherche | donnees | qualite | synthese | veille
    triggers: List[str] = field(default_factory=list)   # regex déclenchant la compétence
    examples: List[str] = field(default_factory=list)   # exemples de tâches
    params: Dict[str, str] = field(default_factory=dict)  # nom → description
    defaults: Dict[str, Any] = field(default_factory=dict)
    order: int = 50                 # ordre canonique dans un pipeline (0 = tôt)

    def match_score(self, task: str) -> int:
        """Score de pertinence (nb de motifs déclenchés) pour une tâche donnée."""
        task_low = task.lower()
        score = 0
        for pattern in self.triggers:
            if re.search(pattern, task_low):
                score += 1
        return score

    def catalog(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "examples": self.examples,
            "params": self.params,
            "defaults": self.defaults,
            "triggers": [t.replace("\\b", "") for t in self.triggers],
        }


# ────────────────────────── Registre global ──────────────────────────

_REGISTRY: Dict[str, SkillSpec] = {}


def skill(name: str, description: str = "", category: str = "general",
          triggers: Optional[List[str]] = None, examples: Optional[List[str]] = None,
          params: Optional[Dict[str, str]] = None, defaults: Optional[Dict[str, Any]] = None,
          order: int = 50) -> Callable:
    """Décorateur d'enregistrement d'une compétence."""
    def decorator(fn: Callable[..., SkillResult]) -> Callable[..., SkillResult]:
        if name in _REGISTRY:
            raise ValueError(f"Skill '{name}' déjà enregistrée")
        _REGISTRY[name] = SkillSpec(
            name=name, fn=fn, description=description or (fn.__doc__ or "").strip().split("\n")[0],
            category=category, triggers=triggers or [], examples=examples or [],
            params=params or {}, defaults=defaults or {}, order=order,
        )
        return fn
    return decorator


def get_skill(name: str) -> Optional[SkillSpec]:
    return _REGISTRY.get(name)


def list_skills() -> List[SkillSpec]:
    return sorted(_REGISTRY.values(), key=lambda s: (s.order, s.name))


def catalog() -> List[Dict[str, Any]]:
    return [s.catalog() for s in list_skills()]
