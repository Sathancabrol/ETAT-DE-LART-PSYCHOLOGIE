"""
Registre des corps célestes du système Cognitorium.

SOL ☉ (étoile, centre) orchestre les planètes :
  • MARS ♂ — l'armurier : création & innovation d'outils (Phobos = software,
    Deimos = conception) pour les problèmes des autres agents ;
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
    "laplace": {
        "name": "Laplace", "symbol": "✳", "kind": "nebuleuse", "orbit_r": -1,
        "role": "Créateur — nébuleuse du savoir : conçoit, modifie, améliore et teste "
                "des agents à tous les niveaux, jusqu'à des systèmes solaires entiers. "
                "(Pierre-Simon Laplace : hypothèse nébulaire de formation du système solaire.)",
        "color": "#c084fc",
    },
    "sebas": {
        "name": "Sebas", "symbol": "◉", "kind": "executeur", "orbit_r": -1,
        "role": "Exécutant de Laplace — homme de terrain connecté aux capteurs "
                "(webcam, wifi, téléphone) ; remonte des observations et agit sur site.",
        "color": "#34d399",
        "sensors": ["webcam", "wifi", "telephone"],
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
    "mars": {
        "name": "Mars", "symbol": "♂", "kind": "planet", "orbit_r": 1.5,
        "role": "Armurier du système solaire — passe son temps à chercher des "
                "solutions aux problèmes des autres agents : quand un agent a "
                "besoin d'un outil spécifique pour calculer et visualiser des "
                "données complexes, Mars cherche d'abord un outil open source à "
                "reproduire et utiliser ; sinon Deimos conçoit la maquette et "
                "Phobos forge l'outil.",
        "color": "#f87171",
        "satellites": [
            {"id": "phobos", "name": "Phobos ◂", "distance_km": 9376,
             "role": "Création de software — forge les outils fonctionnels de "
                     "l'armurerie (code, calculs réels, visualisations)."},
            {"id": "deimos", "name": "Deimos ◦", "distance_km": 23463,
             "role": "Innovation & conception — dessine les maquettes et imagine "
                     "les solutions originales avant la forge."},
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


def creators() -> List[Dict[str, Any]]:
    """Niveau au-dessus de SOL : Laplace (nébuleuse créatrice) et Sebas (exécutant capteurs)."""
    return [b for b in BODIES.values() if b["kind"] in {"nebuleuse", "executeur"}]


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
        if "sensors" in b:
            entry["sensors"] = b["sensors"]
        out.append(entry)
    return out


def known_body_ids() -> set:
    """IDs de corps connus : corps, satellites et cours, y compris ceux
    créés dynamiquement par Laplace (nébuleuse)."""
    ids = set(BODIES.keys())
    for b in BODIES.values():
        for s in b.get("satellites", []) or []:
            ids.add(s["id"])
        for s in b.get("court", []) or []:
            ids.add(s["id"])
    try:
        from cosmos.nebula import list_agents
        ids.update(a["id"] for a in list_agents())
    except Exception:
        pass
    return ids
