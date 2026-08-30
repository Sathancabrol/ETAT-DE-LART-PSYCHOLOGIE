"""
Registre des corps célestes du système Cognitorium.

SOL ☉ (étoile, centre) orchestre les planètes :
  • URANUS ♅ — connaissance & recherche scientifique, entouré de ses
    satellites (anneaux et lunes, du plus proche au plus lointain) ;
  • VÉNUS ♀ — finances, valeur & bien-être, entourée de sa cour
    (Vénus n'a pas de lunes : ses analystes sont les Charites/Grâces
    et Éros, sa cour mythologique).

Sémantique orbitale d'Uranus : PLUS PROCHE = plus sollicité et de
confiance (missions critiques fréquentes) ; PLUS LOINTAIN = missions
profondes et rares (grandes synthèses, méthodologie).

Les distances sont les vraies distances orbitales (km) des corps d'Uranus.
"""

from typing import Any, Dict, List

BODIES: Dict[str, Dict[str, Any]] = {
    "user": {
        "name": "Vous", "symbol": "◍", "kind": "utilisateur",
        "role": "Observateur du système — pose les questions, fixe les caps.",
    },
    "sol": {
        "name": "SOL", "symbol": "☉", "kind": "star", "orbit_r": 0,
        "role": "Orchestrateur du système : approuve toute interaction entre "
                "corps, juge l'intégrité, prévoit et prévient, interface de l'utilisateur.",
        "color": "#fbbf24",
    },
    "venus": {
        "name": "Vénus", "symbol": "♀", "kind": "planet", "orbit_r": 1,
        "role": "Finances, valeur, richesse & bien-être (taureau) : comptabilité "
                "tokens/coûts de chaque requête, budget, prévisions de dépenses "
                "et de rentrées, arbitrage monétaire expert.",
        "color": "#fbbf24",
        "court": [
            {"id": "thalie", "name": "Thalie", "distance_km": 0,
             "role": "Comptabilité des tokens et des coûts — tient le grand livre."},
            {"id": "euphrosyne", "name": "Euphrosyne", "distance_km": 0,
             "role": "Arbitrage & optimisation — meilleur rendement par dollar."},
            {"id": "aglae", "name": "Aglaé", "distance_km": 0,
             "role": "Prévisions & budget — projections, saisonnalité, alertes."},
            {"id": "eros", "name": "Éros", "distance_km": 0,
             "role": "Contrats & négociation — accords entre planètes."},
        ],
    },
    "uranus": {
        "name": "Uranus", "symbol": "♅", "kind": "planet", "orbit_r": 2,
        "role": "Connaissance & recherche scientifique — cartographe du ciel de "
                "la connaissance, agrandit sans cesse sa constellation.",
        "color": "#818cf8",
        "satellites": [
            {"id": "zeta", "name": "Zêta (ζ)", "distance_km": 37850,
             "role": "Premier lieutenant (anneau intérieur, nuage de poussière) : "
                     "recherche appliquée critique et fréquente — neurosciences, "
                     "interfaces homme-machine-environnement-IA."},
            {"id": "puck", "name": "Puck", "distance_km": 86000,
             "role": "Veille & signaux faibles — détection rapide de nouveautés."},
            {"id": "miranda", "name": "Miranda", "distance_km": 129900,
             "role": "Exploration de frontière — sujets émergents, risques."},
            {"id": "ariel", "name": "Ariel", "distance_km": 190900,
             "role": "Cognition, éducation & apprentissage."},
            {"id": "umbriel", "name": "Umbriel", "distance_km": 266000,
             "role": "Clinique & santé mentale."},
            {"id": "titania", "name": "Titania", "distance_km": 436300,
             "role": "Grandes synthèses profondes — revues systématiques majeures."},
            {"id": "oberon", "name": "Obéron", "distance_km": 583500,
             "role": "Méthodologie, open science & réplication."},
        ],
    },
}


def get_body(body_id: str) -> Dict[str, Any] | None:
    return BODIES.get(body_id)


def planets() -> List[Dict[str, Any]]:
    return [b for b in BODIES.values() if b["kind"] == "planet"]


def celestial_registry() -> List[Dict[str, Any]]:
    """Registre aplati pour l'UI et SOL."""
    out = []
    for bid, b in BODIES.items():
        entry = {"id": bid, "name": b["name"], "symbol": b["symbol"],
                 "kind": b["kind"], "role": b["role"],
                 "color": b.get("color")}
        if "satellites" in b:
            entry["satellites"] = b["satellites"]
        if "court" in b:
            entry["court"] = b["court"]
        out.append(entry)
    return out
