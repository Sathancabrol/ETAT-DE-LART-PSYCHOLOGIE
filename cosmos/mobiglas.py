"""
🥽 MobiGlas — l'instrument cognitif projeté du Cognitorium.

Un espace partagé entre un humain, une IA agentique (Laplace ✳), un
environnement capté (Sebas 🛠 / Sera 🕵), des modèles scientifiques (les
corps du système) et des observations transformées en features.

Le principe : l'interface n'est PAS un tableau de bord. C'est un instrument
cognitif — l'utilisateur voit **comment une conclusion émerge** :

    monde réel → capteurs → features → modèles → inférences → action humaine/IA

et chaque inférence reste **traçable** : observation source, feature
extraite, modèle consulté, conclusion, action proposée. Aucune étape n'est
simulée : les compteurs et les chaînes viennent des vrais registres (mémoire,
bus d'interactions, registre des corps).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

STAGES_META: List[Dict[str, Any]] = [
    {"id": "monde",       "icon": "🌍", "nom": "monde réel",  "couleur": "#94a3b8",
     "quoi": "l'environnement capté — temps réel, capteurs déclarés, veille OSINT de Sera"},
    {"id": "capteurs",    "icon": "📡", "nom": "capteurs",    "couleur": "#38bdf8",
     "quoi": "Sebas 🛠 — canaux d'observation déclarés (aucune donnée fabriquée)"},
    {"id": "features",    "icon": "🧬", "nom": "features",    "couleur": "#a78bfa",
     "quoi": "observations transformées : mémoire, concepts, références"},
    {"id": "modeles",     "icon": "🪐", "nom": "modèles",     "couleur": "#fbbf24",
     "quoi": "les corps du système — chaque planète est un modèle, un département"},
    {"id": "inferences",  "icon": "⚗️", "nom": "inférences",  "couleur": "#22d3ee",
     "quoi": "conclusions traçables : chaque inférence garde sa chaîne de provenance"},
    {"id": "action",      "icon": "🖐", "nom": "action",      "couleur": "#f472b6",
     "quoi": "humain ⇄ IA : l'espace partagé où la décision se prend"},
]


def _sensors() -> List[Dict[str, Any]]:
    try:
        from cosmos.nebula import SENSORS
        return SENSORS
    except Exception:
        return []


def _memoire(limit: int) -> List[Dict[str, Any]]:
    try:
        from cosmos import memory
        return memory.items(limit=limit)
    except Exception:
        return []


def _bus(limit: int) -> List[Dict[str, Any]]:
    try:
        from cosmos.system import get_system
        return get_system()["bus"].history(limit=limit)
    except Exception:
        return []


def traces(limit: int = 8) -> List[Dict[str, Any]]:
    """Inférences traçables : la chaîne complète de chaque conclusion.

    observation (source) → feature (titre extrait) → modèle (corps consulté)
    → inférence (contenu) → action (tags/proposition).
    """
    out: List[Dict[str, Any]] = []
    for it in _memoire(80):
        if len(out) >= limit:
            break
        out.append({
            "id": it.get("id"), "ts": it.get("ts"),
            "observation": f"source : {it.get('source') or 'utilisateur'}",
            "feature": (it.get("titre") or "—")[:72],
            "modele": it.get("corps") or "user",
            "inference": (it.get("contenu") or "—")[:180],
            "action": ", ".join(it.get("tags") or []) or "consignée",
        })
    return out


def state() -> Dict[str, Any]:
    from cosmos.bodies import BODIES
    mem = _memoire(4000)
    bus = _bus(600)
    sensors = _sensors()
    now = datetime.now(timezone.utc)
    valeurs = {
        "monde": now.strftime("%d %b · %H:%M") + " UTC",
        "capteurs": f"{len(sensors)} canaux déclarés",
        "features": f"{len(mem)} mémoires",
        "modeles": f"{len(BODIES)} corps",
        "inferences": f"{len(bus)} interactions",
        "action": "humain ⇄ IA",
    }
    stages = [{**s, "valeur": valeurs[s["id"]], "reel": True} for s in STAGES_META]
    derniere = mem[0] if mem else None
    conclusion = {
        "texte": (derniere or {}).get("titre") or "le système observe — aucune inférence récente",
        "provenance": (derniere or {}).get("corps") or "—",
        "ts": (derniere or {}).get("ts"),
    } if derniere else {"texte": "le système observe", "provenance": "—", "ts": None}
    return {
        "titre": "MobiGlas — instrument cognitif",
        "principe": "monde réel → capteurs → features → modèles → inférences → action "
                    "· chaque conclusion émerge d'une chaîne traçable, jamais d'une boîte noire",
        "stages": stages,
        "conclusion": conclusion,
        "observations": [{"ts": m.get("ts"), "source": m.get("source"),
                          "target": m.get("target"), "type": m.get("type")}
                         for m in bus[:12] if m.get("source")],
        "inferences": traces(8),
        "modeles": [{"id": bid, "nom": b["name"], "icon": b.get("icon") or b.get("symbol", "●"),
                     "pouvoir": (b.get("pouvoir") or "")[:80]}
                    for bid, b in BODIES.items()],
        "capteurs": sensors,
        "ts": now.isoformat(timespec="seconds"),
    }
