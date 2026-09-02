"""
Constellations nommées du système — vues de graphe pour la visualisation.

Chaque planète porte le nom de sa constellation du zodiaque (maîtrise
astrologique classique/moderne) :
  • SOL ☉     → Lion (le Soleil maîtrise le Lion)
  • Vénus ♀   → Taureau (maîtrise classique — demandée explicitement)
  • Uranus ♅  → Verseau (maîtrise moderne)

Les satellites d'Uranus et la cour de Vénus sont proposés comme étoiles
de la constellation de leur planète (« ζ Zêta — du Verseau », « Thalie —
du Taureau »).

Toutes les vues sont servies au format Obsidian ({nodes, links} avec
relation_type) pour être rendues par le graphe D3 existant.
"""

from __future__ import annotations

from typing import Any, Dict, List

from cosmos import knowledge
from cosmos.bodies import BODIES

ZODIAC = {
    "sol": {"constellation": "Lion", "symbol": "♌", "theme": "gouvernance & orchestration"},
    "venus": {"constellation": "Taureau", "symbol": "♉", "theme": "finances, valeur & bien-être"},
    "uranus": {"constellation": "Verseau", "symbol": "♒", "theme": "connaissances & recherche"},
}

# Types connaissance → types obsidian
_TYPE_MAP = {"reference": "study"}


def _obsidianize(g: Dict[str, Any] | None) -> Dict[str, Any]:
    """Convertit un graphe knowledge au format attendu par le graphe Obsidian."""
    if not g:
        return {"nodes": [], "links": []}
    nodes = []
    for n in g.get("nodes", []):
        nodes.append({
            "id": n["id"], "label": n.get("label", n["id"]),
            "type": _TYPE_MAP.get(n.get("type"), n.get("type", "concept")),
            "group": n.get("type", ""),
            "desc": n.get("role", ""),
            "trust": int(n["trust"]) if str(n.get("trust", "")).isdigit() else None,
            "year": n.get("annee"), "doi": n.get("doi"),
            "citations": n.get("citations"),
        })
    links = [{"source": l["source"], "target": l["target"],
              "relation_type": l.get("type", "relates")} for l in g.get("links", [])]
    return {"nodes": nodes, "links": links}


def _merge(*graphs: Dict[str, Any]) -> Dict[str, Any]:
    nodes, links, seen = [], [], set()
    for g in graphs:
        for n in g.get("nodes", []):
            if n["id"] not in seen:
                seen.add(n["id"])
                nodes.append(n)
        links.extend(g.get("links", []))
    return {"nodes": nodes, "links": links}


def views() -> List[Dict[str, Any]]:
    """Catalogue des constellations proposées dans le sélecteur."""
    out = [{
        "id": "base", "symbol": "🗂️", "label": "Base de connaissances (42 champs)",
        "description": "Le graphe Obsidian historique : études, concepts, méthodes, théoriciens",
        "url": "/api/obsidian-graph", "parent": None,
    }, {
        "id": "zodiaque", "symbol": "✦", "label": "Le Zodiaque du système",
        "description": "Toutes les constellations : Lion (SOL), Taureau (Vénus), Verseau (Uranus) et leurs étoiles",
        "url": "/api/cosmos/constellations/zodiaque", "parent": None,
    }]
    for pid, z in ZODIAC.items():
        out.append({
            "id": pid, "symbol": z["symbol"], "label": f"{z['constellation']} — {pid.capitalize()}",
            "description": f"{BODIES[pid]['symbol']} {pid.capitalize()} · {z['theme']}",
            "url": f"/api/cosmos/constellations/{pid}", "parent": None,
        })
    for s in BODIES["uranus"]["satellites"]:
        out.append({"id": s["id"], "symbol": "♒", "label": f"{s['name']} — du Verseau",
                    "description": s["role"][:90], "url": f"/api/cosmos/constellations/{s['id']}",
                    "parent": "uranus"})
    for c in BODIES["venus"]["court"]:
        out.append({"id": c["id"], "symbol": "♉", "label": f"{c['name']} — du Taureau",
                    "description": c["role"][:90], "url": f"/api/cosmos/constellations/{c['id']}",
                    "parent": "venus"})
    out.append({"id": "memoire", "symbol": "🧠", "label": "Mémoire du système",
                "description": "Questions posées, documents reçus et générés, concepts émergents",
                "url": "/api/cosmos/constellations/memoire", "parent": None})
    return out


def graph_for(view_id: str) -> Dict[str, Any] | None:
    """Graphe (format obsidian) d'une constellation, ou None si inconnue."""
    if view_id == "zodiaque":
        return _merge(_obsidianize(knowledge.sol_graph()),
                      _obsidianize(knowledge.uranus_graph()),
                      _obsidianize(knowledge.venus_graph()))
    if view_id == "memoire":
        from cosmos.memory import memory_graph
        return _obsidianize(memory_graph())
    if view_id in ZODIAC or view_id in {"sol", "venus", "uranus"}:
        return _obsidianize(knowledge.knowledge_graph(view_id))
    if view_id in {s["id"] for s in BODIES["uranus"]["satellites"]} or \
       view_id in {c["id"] for c in BODIES["venus"]["court"]}:
        return _obsidianize(knowledge.knowledge_graph(view_id))
    return None
