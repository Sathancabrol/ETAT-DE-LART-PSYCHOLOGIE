"""
Cerveau LLM optionnel (hybride).

Si une clé API est présente dans l'environnement :
  - OPENAI_API_KEY  → https://api.openai.com/v1/chat/completions
  - ANTHROPIC_API_KEY → https://api.anthropic.com/v1/messages
l'agent peut l'utiliser pour (a) affiner le plan à partir du catalogue
des compétences et (b) rédiger des paragraphes narratifs de synthèse.

Principes : dépendances zéro (requests uniquement), timeouts courts,
et repli systématique sur le planificateur à règles en cas d'erreur.
Sans clé : llm_available() = False et l'agent reste 100 % déterministe.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests

TIMEOUT = 30

# Journal des consommations LLM réelles (remontées au grand livre de Vénus)
USAGE: list = []


def llm_status() -> Dict[str, Any]:
    """Décrit la disponibilité du LLM sans divulguer les clés."""
    provider = None
    if os.environ.get("ANTHROPIC_API_KEY"):
        provider = "anthropic"
    elif os.environ.get("OPENAI_API_KEY"):
        provider = "openai"
    model = os.environ.get("AGENT_LLM_MODEL") or (
        "claude-sonnet-4-20250514" if provider == "anthropic" else "gpt-4o-mini")
    enabled = os.environ.get("AGENT_USE_LLM", "1").strip() not in {"0", "false", "FALSE"}
    return {"available": bool(provider) and enabled, "provider": provider or "aucun",
            "model": model if provider else None,
            "hint": "Définissez OPENAI_API_KEY ou ANTHROPIC_API_KEY pour activer le cerveau LLM "
                    "(le planificateur à règles reste utilisé par défaut et en secours)."}


def _chat(system: str, user: str, max_tokens: int = 1200) -> Optional[str]:
    st = llm_status()
    if not st["available"]:
        return None
    try:
        if st["provider"] == "anthropic":
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                         "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": st["model"], "max_tokens": max_tokens,
                      "system": system, "messages": [{"role": "user", "content": user}]},
                timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            u = data.get("usage") or {}
            USAGE.append({"model": st["model"], "in": u.get("input_tokens", 0),
                          "out": u.get("output_tokens", 0)})
            return "".join(b.get("text", "") for b in data.get("content", []))
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json={"model": st["model"], "max_tokens": max_tokens,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
            timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        u = data.get("usage") or {}
        USAGE.append({"model": st["model"], "in": u.get("prompt_tokens", 0),
                      "out": u.get("completion_tokens", 0)})
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None


def plan_with_llm(task: str, catalog: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """Demande au LLM un plan JSON {steps:[{skill,params,reason}]}.

    Retourne None si indisponible/erreur/JSON invalide → l'appelant
    retombe sur le planificateur à règles.
    """
    system = (
        "Tu es le planificateur d'un agent scientifique. Choisis UNIQUEMENT des compétences "
        "parmi le catalogue fourni. Réponds STRICTEMENT en JSON valide, sans texte autour : "
        '{"steps": [{"skill": "<nom>", "params": {...}, "reason": "<justification courte en français>"}]}. '
        "Maximum 6 étapes, ordonnées de façon logique."
    )
    user = f"Tâche : « {task} »\n\nCatalogue des compétences :\n{json.dumps(catalog, ensure_ascii=False)}"
    raw = _chat(system, user)
    if not raw:
        return None
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
        steps = []
        for s in data.get("steps", [])[:6]:
            name = s.get("skill", "")
            if get_skill(name) and name not in {x["skill"] for x in steps}:
                params = s.get("params") if isinstance(s.get("params"), dict) else {}
                steps.append({"skill": name, "params": params,
                              "reason": str(s.get("reason", "choix LLM"))[:200]})
        return steps or None
    except Exception:
        return None


def narrative(prompt: str) -> Optional[str]:
    """Génère un court paragraphe narratif (utilisé en option par synthesize)."""
    return _chat("Tu es un chercheur en psychologie cognitive. Rédige un paragraphe court, "
                 "factuel, en français, sans inventer de références.", prompt, max_tokens=500)


from agent.core.registry import get_skill  # noqa: E402  (import bas pour éviter cycle)
