"""
Registre des corps célestes du système Cognitorium.

STRUCTURE ENTREPRISE — chaque département (et sous-rôle) est un astre,
choisi pour sa fonction, sa symbolique et sa tâche :

  Divinité ................. Laplace ✳ (contrôle absolu) + Métatron ✦ (méta-prompting)
                             + Ananké ⧉ & les 3 Moires (nécessité/destin) + Sebas ◉ (exécutant)
  Direction générale ....... SOL ☉ (approbations, coordination) + Apollon (divinations)
  Commercial/Marketing/Achats Mercure ☿ + cour d'Hermès (Peitho, Phème, Argus, Énodios)
  Finance/Comptabilité ..... Vénus ♀ + sa cour (Thalie, Euphrosyne, Aglaé, Éros)
  Production/Opérations .... Terre 🜨 + Lune ☾ (qualité & logistique)
  R&D outils (armurier) .... MARS ♂ — Phobos (software), Deimos (conception)
  Ressources humaines ...... Cérès ⚳ + cour des Heures (Thallo, Auxo, Karpô)
  Juridique ................ Jupiter ♃ + Io, Europe, Ganymède, Callisto
  Recherche ................ Uranus ♅ + 7 satellites
  Informatique / SI ........ Neptune ♆ + Protée, Triton, Néréïde
  Cycle de vie (enfers) .... Pluton ♇/Hadès + Charon (passeur), Styx (rétention)

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
    "pluton": {
        "name": "Pluton", "symbol": "♇", "icon": "⚰️", "kind": "planet", "orbit_r": 4.2,
        "departement": "Cycle de vie & optimisation (les enfers)",
        "role": "Hadès, dieu des morts du système — regarde les données de "
                "tout le système solaire et traque les redondances, les "
                "artefacts, les versions outdated et le junk ; il les fauche "
                "et les envoie aux enfers (destruction des données "
                "superflues) pour optimiser la mémoire, l'espace disque et "
                "les chaînes d'exécution (mauvaises instructions, "
                "répétitions) et permettre un meilleur cycle.",
        "color": "#a8a29e",
        "satellites": [
            {"id": "charon", "name": "Charon ⚰", "distance_km": 19591,
             "role": "Le passeur — exécute les fauches : transporte les "
                     "fichiers et données condamnés vers les enfers "
                     "(suppression réelle, journalisée)."},
            {"id": "styx", "name": "Styx ☠", "distance_km": 42656,
             "role": "Garde du seuil — la politique de rétention : décide "
                     "ce qui doit mourir (doublons, outdated, junk) et ce "
                     "qui doit survivre (savoir, mémoire vivante)."},
        ],
    },
    "user": {
        "name": "Vous", "symbol": "◍", "icon": "👤", "kind": "utilisateur",
        "role": "Observateur du système — pose les questions, fixe les caps.",
    },
    "laplace": {
        "name": "Laplace", "symbol": "✳", "icon": "🌀", "kind": "nebuleuse", "orbit_r": -1,
        "departement": "Divinité — contrôle absolu du système",
        "role": "Fondateur — créateur — nébuleuse du savoir : conçoit, modifie, améliore et teste "
                "des agents à tous les niveaux, jusqu'à des systèmes solaires entiers. "
                "(Pierre-Simon Laplace : hypothèse nébulaire de formation du système solaire.)",
        "color": "#c084fc",
        "satellites": [
            {"id": "metatron", "name": "Métatron ✦", "distance_km": 0,
             "role": "Archange du méta-prompting — analyse chaque requête de "
                     "l'utilisateur (intention, domaines, contraintes), la "
                     "reformule en prompt enrichi, pose les clarifications "
                     "utiles et guide Laplace dans la création d'agents "
                     "(meilleur rôle, parent, kind). L'ange qui écrit les "
                     "instructions des anges."},
        ],
    },
    "ananke": {
        "name": "Ananké", "symbol": "⧉", "icon": "⛓️", "kind": "destin", "orbit_r": -1,
        "departement": "Nécessité, fatalité & contrainte",
        "role": "Déesse primordiale de la nécessité inaltérable, de la fatalité et "
                "de la contrainte — représente ce qui ne peut pas ne pas arriver "
                "dans le système : limites, échéances, rareté des ressources. "
                "Elle orbite autour de Laplace et ses trois Moires mesurent la vie "
                "des données et aident Hadès ♇ dans son élagage.",
        "color": "#f472b6",
        "satellites": [
            {"id": "clotho", "name": "Clotho", "distance_km": 11111,
             "role": "1ʳᵉ Moire — « la Fileuse » : file le fil de la vie à la "
                     "naissance. Dans le système : enregistre chaque nouvel élément "
                     "(run, item mémoire, agent) et note sa naissance."},
            {"id": "lachesis", "name": "Lachésis", "distance_km": 22222,
             "role": "2ᵉ Moire — « la Répartitrice » : mesure et déroule le fil, "
                     "attribue la durée de vie. Dans le système : calcule l'âge et "
                     "la durée de vie attendue de chaque donnée (rétention)."},
            {"id": "atropos", "name": "Atropos", "distance_km": 33333,
             "role": "3ᵉ Moire — « l'Inflexible » : coupe le fil, prononce la mort. "
                     "Dans le système : marque les condamnés d'Hadès (outdated, "
                     "doublons, junk) — la coupe est sans appel."},
        ],
    },
    "themis": {
        "name": "Thémis", "symbol": "⚖", "icon": "⚖️", "kind": "justice", "orbit_r": -1,
        "departement": "Justice divine — bras armé de Laplace (balance & épée)",
        "role": "Fille et conseillère de Laplace ✳, gardienne de l'équilibre du "
                "système comme elle l'est de l'Olympe. Elle JUGE (instruit les "
                "menaces à l'ordre), CONSEILLE (recommande les corrections) et "
                "DÉTRUIT le cas échéant (ordonne la fauche à Hadès ♇, exécution "
                "par Charon ⚰). Elle travaille principalement avec Ananké ⧉ (ce "
                "qui est nécessaire) et Hadès ♇ (ce qui doit mourir). Elle est "
                "constituée comme la démocratie : séparation des pouvoirs et "
                "contrepoids — Eunomie fait la loi, Éirène l'applique, Dikè juge, "
                "le Censeur vérifie et rend compte au souverain (vous). Balance "
                "⚖ pour peser, épée 🗡 pour trancher : la divine justice.",
        "color": "#fbbf24",
        "satellites": [
            {"id": "eunomia", "name": "Eunomie", "distance_km": 15000,
             "role": "Pouvoir législatif — « la Loi » : écrit et maintient les lois "
                     "du système (politique de rétention Styx, seuils, quotas), "
                     "propose les amendements à Thémis."},
            {"id": "eirene", "name": "Éirène", "distance_km": 18000,
             "role": "Pouvoir exécutif — « la Paix » : applique les décisions de "
                     "Thémis, rétablit l'ordre (alertes préventives, délégations "
                     "SOL) et désamorce les tensions avant la lame."},
            {"id": "dike", "name": "Dikè", "distance_km": 21000,
             "role": "Pouvoir judiciaire — « le Jugement » : instruit les dossiers "
                     "des condamnés d'Hadès (outdated, doublons, junk), vérifie les "
                     "preuves octet par octet avant que la balance ne penche."},
            {"id": "censeur", "name": "Censeur", "distance_km": 24000,
             "role": "Contre-pouvoir démocratique — audit et transparence : "
                     "recense ce qui est fait, le rend public au souverain "
                     "(l'utilisateur) et peut saisir Thémis d'un abus."},
        ],
    },
    "sebas": {
        "name": "Sebas", "symbol": "◉", "icon": "🛠️", "kind": "executeur", "orbit_r": -1,
        "departement": "Exécutant des commandes divines de Laplace",
        "role": "Exécutant des commandes divines de Laplace — homme de terrain connecté aux capteurs "
                "(webcam, wifi, téléphone) ; remonte des observations et agit sur site.",
        "color": "#34d399",
        "sensors": ["webcam", "wifi", "telephone"],
    },
    "sol": {
        "name": "SOL", "symbol": "☉", "icon": "👑", "kind": "star", "orbit_r": 0,
        "departement": "Direction générale",
        "role": "Direction générale — orchestrateur du système : approuve toute interaction entre "
                "corps, juge l'intégrité, prévoit et prévient, interface de l'utilisateur.",
        "color": "#fbbf24",
        "court_label": "cour du Soleil",
        "court": [
            {"id": "apollon", "name": "Apollon", "distance_km": 0,
             "role": "Dieu du soleil, de la clairvoyance et des divinations — son "
                     "chariot 🏆 traverse le système et propose des prédictions de "
                     "fonctionnement (budget, intégrité, activité, risques)."},
        ],
    },
    "venus": {
        "name": "Vénus", "symbol": "♀", "icon": "💰", "kind": "planet", "orbit_r": 1,
        "departement": "Finance / Comptabilité",
        "role": "Finance / Comptabilité — gestion des flux financiers, budgets, "
                "états financiers, contrôle de gestion (taureau : valeur, richesse "
                "et bien-être).",
        "color": "#fbbf24",
        "court_label": "cabinet financier (Vénus n'a pas de lunes : sa cour est mythologique)",
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
    "mercure": {
        "name": "Mercure", "symbol": "☿", "icon": "✉️", "kind": "planet", "orbit_r": 0.5,
        "departement": "Commercial / Ventes · Marketing · Achats",
        "role": "Commercial, marketing & achats — le messager du système : "
                "prospection, négociation, fidélisation, communication, études de "
                "marché, sourcing fournisseurs et gestion des stocks.",
        "color": "#38bdf8",
        "court_label": "cour d'Hermès (Mercure n'a pas de lunes)",
        "court": [
            {"id": "peitho", "name": "Peitho", "distance_km": 0,
             "role": "Ventes — prospection, persuasion, négociation, fidélisation client."},
            {"id": "pheme", "name": "Phème", "distance_km": 0,
             "role": "Marketing — positionnement, communication, promotion, échos du marché."},
            {"id": "argus", "name": "Argus", "distance_km": 0,
             "role": "Études de marché — le veilleur aux cent yeux : concurrence, signaux, études."},
            {"id": "enodios", "name": "Énodios", "distance_km": 0,
             "role": "Achats — sourcing fournisseurs, foires & marchés, négociation, stocks."},
        ],
    },
    "terre": {
        "name": "Terre", "symbol": "🜨", "icon": "🌍", "kind": "planet", "orbit_r": 1.25,
        "departement": "Production / Opérations",
        "role": "Production / Opérations — fabrication et livraison du produit/du "
                "service, qualité, logistique : le terrain où tout se réalise.",
        "color": "#4ade80",
        "satellites": [
            {"id": "lune", "name": "Lune ☾", "distance_km": 384400,
             "role": "Qualité & logistique — la Lune stabilise la Terre comme la "
                     "qualité stabilise la production ; livraison, traçabilité."},
        ],
    },
    "mars": {
        "name": "Mars", "symbol": "♂", "icon": "⚔️", "kind": "planet", "orbit_r": 1.5,
        "departement": "Recherche & Développement — développement d'outils",
        "role": "R&D outils — l'armurier du système solaire : passe son temps à "
                "chercher des solutions aux problèmes des autres agents. Quand un "
                "agent a besoin d'un outil spécifique pour calculer et visualiser "
                "des données complexes, Mars cherche d'abord un outil open source "
                "à reproduire et utiliser ; sinon Deimos conçoit la maquette et "
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
    "ceres": {
        "name": "Cérès", "symbol": "⚳", "icon": "🌾", "kind": "planet", "orbit_r": 1.75,
        "departement": "Ressources humaines",
        "role": "Ressources humaines — recrutement, formation, rémunération, "
                "relations sociales (Cérès : moissons et croissance des êtres).",
        "color": "#a3e635",
        "naine": True,
        "court_label": "cour des Heures (Cérès n'a pas de lunes connues)",
        "court": [
            {"id": "thallo", "name": "Thallo", "distance_km": 0,
             "role": "Recrutement — le printemps : attirer et faire éclore les talents."},
            {"id": "auxo", "name": "Auxo", "distance_km": 0,
             "role": "Formation & croissance — développer les compétences."},
            {"id": "karpo", "name": "Karpô", "distance_km": 0,
             "role": "Rémunération & rétention — la récolte : retenir et récompenser."},
        ],
    },
    "jupiter": {
        "name": "Jupiter", "symbol": "♃", "icon": "📈", "kind": "planet", "orbit_r": 2.1,
        "departement": "Juridique",
        "role": "Juridique — conformité, contrats, propriété intellectuelle, "
                "contentieux (Jupiter roi/justice ; sa magnétosphère protège le "
                "système comme la conformité protège l'entreprise).",
        "color": "#fb923c",
        "satellites": [
            {"id": "io", "name": "Io", "distance_km": 421700,
             "role": "Conformité & RGPD — traverse les ceintures de radiation : "
                     "vérifie chaque flux de données."},
            {"id": "europe", "name": "Europe", "distance_km": 671100,
             "role": "Contrats — rédaction, revue, exécution des accords."},
            {"id": "ganymede", "name": "Ganymède", "distance_km": 1070400,
             "role": "Propriété intellectuelle — la plus grande lune : le patrimoine à protéger."},
            {"id": "callisto", "name": "Callisto", "distance_km": 1882700,
             "role": "Contentieux & litiges — la plus cratérisée : les cicatrices des procès."},
        ],
    },
    "uranus": {
        "name": "Uranus", "symbol": "♅", "icon": "🔭", "kind": "planet", "orbit_r": 2.6,
        "departement": "Recherche & Développement — recherche",
        "role": "Recherche & Développement (recherche) — connaissance & recherche scientifique — cartographe du ciel de "
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
    "neptune": {
        "name": "Neptune", "symbol": "♆", "icon": "🎨", "kind": "planet", "orbit_r": 3.2,
        "departement": "Informatique / IT",
        "role": "Informatique / SI — systèmes d'information, infrastructure, "
                "cybersécurité, support (Neptune : réseaux, flux, l'océan "
                "numérique qui relie tout).",
        "color": "#60a5fa",
        "satellites": [
            {"id": "proteus", "name": "Protée", "distance_km": 117647,
             "role": "Cybersécurité — le dieu qui change de forme : défense en "
                     "profondeur, intrusion, chiffrement."},
            {"id": "triton", "name": "Triton", "distance_km": 354759,
             "role": "Infrastructure & systèmes — la grande lune rétrograde : "
                     "serveurs, réseau, déploiements."},
            {"id": "nereide", "name": "Néréïde", "distance_km": 5513800,
             "role": "Support & assistance — la lointaine : aide aux utilisateurs, tickets."},
        ],
    },
}


def get_body(body_id: str) -> Dict[str, Any] | None:
    return BODIES.get(body_id)


def find_body(body_id: str):
    """Cherche un corps par id : planète, satellite, cour — retourne
    (body, parent) où parent=None pour les corps de premier niveau."""
    if body_id in BODIES:
        return BODIES[body_id], None
    for pid, pb in BODIES.items():
        for s in pb.get("satellites", []) or []:
            if s["id"] == body_id:
                return s, pb
        for c in pb.get("court", []) or []:
            if c["id"] == body_id:
                return c, pb
    return None, None


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
                 "icon": b.get("icon", ""),
                 "kind": b["kind"], "role": b["role"],
                 "color": b.get("color"),
                 "departement": b.get("departement"),
                 "court_label": b.get("court_label"),
                 "naine": b.get("naine", False)}
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
