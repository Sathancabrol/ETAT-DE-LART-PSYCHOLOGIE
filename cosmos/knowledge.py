"""
Constellations de connaissances par corps du système.

Chaque corps (Uranus, ses satellites, Vénus et sa cour, SOL) expose un
graphe {nodes, links} pour la visualisation D3 :
  • Uranus      : références de la base 42 champs + concepts (tags) + domaines ;
  • satellites  : concepts de leur domaine + références matchées ;
  • Vénus       : constellation financière (caps, modèles, tarifs, agents) ;
  • SOL         : constellation de gouvernance (corps, approbations, journaux).

Déterministe : tout est dérivé de la base CSV et du registre des corps.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

from cosmos.bodies import BODIES, celestial_registry
from agent.core.context import DATA_CSV

# Concepts par satellite (domaine de mission)
SATELLITE_CONCEPTS: Dict[str, List[str]] = {
    "zeta": ["Neurosciences", "Interfaces homme-machine", "HUD augmenté",
             "Réalité mixte", "Cognition incarnée", "Interaction homme-environnement-IA",
             "Adaptation temps réel"],
    "puck": ["Veille scientifique", "Signaux faibles", "Détection de nouveautés",
             "Métriques d'impact", "Citations"],
    "miranda": ["Exploration de frontière", "Sujets émergents", "Risques épistémiques",
                "Préenregistrement", "Réplication"],
    "ariel": ["Cognition", "Éducation", "Apprentissage autorégulé", "Métacognition",
              "Motivation"],
    "umbriel": ["Clinique", "Santé mentale", "Psychothérapies", "TCC", "Prévention"],
    "titania": ["Revue systématique", "Méta-analyse", "PRISMA", "Hétérogénéité",
                "Synthèse cumulative"],
    "oberon": ["Méthodologie", "Open science", "Biais de publication", "Trust factor",
               "Réplication"],
}

# ── Concepts des corps « entreprise » (mercure, terre, ceres, jupiter, neptune, mars) ──
DEPT_CONCEPTS: Dict[str, List[str]] = {
    "mercure": ["prospection", "négociation", "fidélisation client", "chiffre d'affaires",
                "positionnement", "communication", "étude de marché", "promotion",
                "sourcing fournisseurs", "appels d'offres", "gestion des stocks"],
    "peitho": ["prospection", "persuasion", "négociation commerciale", "fidélisation"],
    "pheme": ["positionnement", "communication", "promotion", "branding"],
    "argus": ["étude de marché", "veille concurrentielle", "signaux faibles", "sondages"],
    "enodios": ["sourcing fournisseurs", "appels d'offres", "stocks", "logistique d'achat"],
    "terre": ["fabrication", "livraison de service", "qualité", "logistique",
              "traçabilité", "lean", "sécurité production"],
    "lune": ["assurance qualité", "contrôle", "logistique", "stabilité du processus"],
    "ceres": ["recrutement", "formation", "rémunération", "relations sociales",
              "fidélisation des talents", "bien-être au travail"],
    "thallo": ["recrutement", "marque employeur", "onboarding"],
    "auxo": ["formation", "montée en compétences", "gestion des carrières"],
    "karpo": ["rémunération", "rétention", "reconnaissance"],
    "jupiter": ["conformité", "RGPD", "contrats", "propriété intellectuelle",
                "contentieux", "réglementation", "audit"],
    "io": ["conformité", "RGPD", "protection des données", "audit"],
    "europe": ["contrats", "clauses", "exécution des accords"],
    "ganymede": ["propriété intellectuelle", "brevets", "licences"],
    "callisto": ["contentieux", "litiges", "arbitrage"],
    "neptune": ["systèmes d'information", "infrastructure", "cybersécurité",
                "support", "réseau", "sauvegardes", "déploiement continu"],
    "proteus": ["cybersécurité", "chiffrement", "intrusion", "défense en profondeur"],
    "triton": ["infrastructure", "serveurs", "réseau", "déploiement"],
    "nereide": ["support", "assistance utilisateurs", "tickets"],
    "mars": ["outils sur mesure", "open source", "maquette", "forge", "calcul",
             "visualisation de données"],
    "phobos": ["création de software", "forge d'outils", "calculs temps réel"],
    "deimos": ["innovation", "conception", "maquette", "prototypage"],
    "laplace": ["création d'agents", "architecture du système", "amélioration continue"],
    "apollon": ["divination", "prévision", "clairvoyance", "oracle", "prophétie",
                "projection budget", "tendance intégrité", "risques"],
    "themis": ["justice divine", "équilibre", "jugement", "balance", "épée",
               "conseil", "menaces à l'ordre", "lois du système", "séparation des pouvoirs"],
    "eunomia": ["pouvoir législatif", "loi", "politique de rétention", "seuils", "amendements"],
    "eirene": ["pouvoir exécutif", "application des décisions", "rétablissement de l'ordre",
               "alertes préventives"],
    "dike": ["pouvoir judiciaire", "instruction des dossiers", "preuves", "jugement des condamnés"],
    "censeur": ["contre-pouvoir", "audit", "transparence", "rendre compte au souverain"],
    "ananke": ["nécessité", "fatalité", "contrainte", "limites", "échéance",
               "destin", "inévitabilité"],
    "clotho": ["naissance des données", "filage", "enregistrement"],
    "lachesis": ["durée de vie", "rétention", "mesure du fil", "répartition"],
    "atropos": ["coupe du fil", "fin de vie", "condamnation", "élagage"],
    "metatron": ["méta-prompting", "analyse d'intention", "reformulation", "enrichissement de requête",
                 "clarification", "ingénierie d'instructions", "profil cognitif",
                 "spécification d'agents", "décomposition de tâche"],
    "pluton": ["redondances", "données obsolètes", "junk", "fauche", "cycle de vie",
               "optimisation de l'espace", "rétention", "nettoyage", "chaînes d'exécution"],
    "charon": ["suppression", "passeur", "transport des condamnés"],
    "styx": ["politique de rétention", "seuils", "que garder", "que détruire"],
    "sebas": ["capteurs", "observations terrain", "webcam", "wifi", "téléphone"],
}

COUR_CONCEPTS: Dict[str, List[str]] = {
    "thalie": ["Grand livre", "Tokens entrée/sortie", "Coût par requête", "Journal JSONL"],
    "euphrosyne": ["Arbitrage", "Rendement par dollar", "Choix de modèle", "Réduction de portée"],
    "aglae": ["Prévisions", "Projection linéaire", "Caps budgétaires", "Alertes de dérive"],
    "eros": ["Contrats inter-planètes", "Accords de service", "Négociation", "SLA"],
}

# Mots-clés de rattachement des références aux satellites
SATELLITE_MATCH: Dict[str, List[str]] = {
    "zeta": ["attention", "neural", "neuro", "fmri", "perception", "interface", "hud",
             "embodied", "incarn", "affordance", "vision", "motor"],
    "puck": ["citations", "veille", "metric", "altmetric"],
    "miranda": ["preregist", "replicat", "crisis", "emerg"],
    "ariel": ["education", "learning", "metacogn", "motivation", "scolaire", "élève",
              "enseign", "srl", "autodétermin"],
    "umbriel": ["psychoth", "depres", "anxi", "clinic", "thérap", "santé mentale",
                "mental health"],
    "titania": ["meta-anal", "meta anal", "systematic review", "umbrella", "prisma"],
    "oberon": ["open science", "bias", "biais", "trust", "method", "preregist"],
}


def _read_refs() -> List[Dict[str, str]]:
    import csv
    if not DATA_CSV.exists():
        return []
    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _node(id_: str, label: str, type_: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    n = {"id": id_, "label": label, "type": type_}
    if extra:
        n.update(extra)
    return n


def uranus_graph() -> Dict[str, Any]:
    """Uranus : références + concepts (tags) + domaines + satellites."""
    refs = _read_refs()
    nodes, links = [], []
    nodes.append(_node("uranus", "♅ Uranus", "planet", {"color": "#818cf8"}))
    tag_count: Counter = Counter()
    ref_by_id = {}
    for r in refs:
        rid = r.get("id", "")
        ref_by_id[rid] = r
        nodes.append(_node(rid, r.get("reference_courte", rid), "reference",
                           {"trust": r.get("trust_factor"), "annee": r.get("annee"),
                            "doi": r.get("doi"), "color": "#38bdf8"}))
        links.append({"source": "uranus", "target": rid, "type": "possede"})
        dom = r.get("domaine")
        if dom:
            did = "dom:" + dom
            if not any(n["id"] == did for n in nodes):
                nodes.append(_node(did, dom, "domaine", {"color": "#c084fc"}))
            links.append({"source": rid, "target": did, "type": "appartient"})
        for t in [t.strip() for t in (r.get("tags") or "").split(",") if t.strip()]:
            tag_count[t] += 1
    for tag, cnt in tag_count.most_common(24):
        tid = "tag:" + tag
        nodes.append(_node(tid, tag, "concept", {"poids": cnt, "color": "#34d399"}))
    # ref → concepts par correspondance de tags
    for r in refs:
        rid = r.get("id")
        for t in [t.strip() for t in (r.get("tags") or "").split(",") if t.strip()]:
            tid = "tag:" + t
            if any(n["id"] == tid for n in nodes):
                links.append({"source": rid, "target": tid, "type": "tague"})
    # satellites et leurs domaines
    for s in BODIES["uranus"]["satellites"]:
        nodes.append(_node(s["id"], s["name"], "satellite", {"color": "#a5b4fc"}))
        links.append({"source": "uranus", "target": s["id"], "type": "orbite"})
    return {"nodes": nodes, "links": links}


def satellite_graph(sat_id: str) -> Dict[str, Any]:
    """Constellation d'un satellite : concepts du domaine + références matchées."""
    sat = next((s for s in BODIES["uranus"]["satellites"] if s["id"] == sat_id), None)
    concepts = SATELLITE_CONCEPTS.get(sat_id, [])
    nodes, links = [], []
    color = "#818cf8"
    nodes.append(_node(sat_id, (sat or {}).get("name", sat_id), "satellite", {"color": color}))
    for c in concepts:
        cid = f"{sat_id}:c:{c}"
        nodes.append(_node(cid, c, "concept", {"color": "#34d399"}))
        links.append({"source": sat_id, "target": cid, "type": "concept"})
    for i in range(len(concepts) - 1):
        links.append({"source": f"{sat_id}:c:{concepts[i]}",
                      "target": f"{sat_id}:c:{concepts[i+1]}", "type": "associe"})
    # références de la base matchées par mots-clés
    kws = SATELLITE_MATCH.get(sat_id, [])
    matched = 0
    for r in _read_refs():
        blob = " ".join([(r.get(k) or "").lower() for k in
                         ("theme", "tags", "question_scientifique", "reference_courte")])
        if any(k in blob for k in kws):
            rid = r.get("id")
            nodes.append(_node(rid, r.get("reference_courte", rid), "reference",
                               {"doi": r.get("doi"), "trust": r.get("trust_factor"),
                                "color": "#38bdf8"}))
            # rattacher au concept le plus proche (premier match de mot-clé)
            links.append({"source": sat_id, "target": rid, "type": "source"})
            for c in concepts:
                cl = c.lower()
                if any(w in cl and w in blob for w in blob.split()[:40]):
                    links.append({"source": f"{sat_id}:c:{c}", "target": rid, "type": "eclaire"})
                    break
            matched += 1
        if matched >= 12:
            break
    return {"nodes": nodes, "links": links}


def venus_graph() -> Dict[str, Any]:
    """Constellation financière de Vénus (données réelles du budget)."""
    from cosmos import venus as v
    st = v.status()
    nodes, links = [], []
    nodes.append(_node("venus", "♀ Vénus", "planet", {"color": "#fbbf24"}))
    for c in BODIES["venus"]["court"]:
        nodes.append(_node(c["id"], c["name"], "analyste", {"color": "#fcd34d"}))
        links.append({"source": "venus", "target": c["id"], "type": "court"})
        for concept in COUR_CONCEPTS.get(c["id"], [])[:3]:
            cid = f"{c['id']}:{concept}"
            nodes.append(_node(cid, concept, "concept", {"color": "#34d399"}))
            links.append({"source": c["id"], "target": cid, "type": "concept"})
    b = st["budget"]
    caps = [("cap jour", b["daily_cap_usd"]), ("cap mission", b["per_mission_cap_usd"]),
            ("cap mois", b["monthly_cap_usd"])]
    for label, val in caps:
        nid = "cap:" + label
        nodes.append(_node(nid, f"{label} : {val} $", "cap", {"color": "#fb7185"}))
        links.append({"source": "thalie", "target": nid, "type": "plafond"})
    nodes.append(_node("dep_jour", f"dépensé aujourd'hui : {st['spend_today_usd']:.4f} $",
                       "montant", {"color": "#fbbf24"}))
    links.append({"source": "thalie", "target": "dep_jour", "type": "constate"})
    nodes.append(_node("proj_mois", f"projection mois : {st['forecast']['monthly_projection_usd']:.2f} $",
                       "montant", {"color": "#fbbf24"}))
    links.append({"source": "aglae", "target": "proj_mois", "type": "projette"})
    for model, prices in st["pricing"].items():
        if prices["in_per_m"] == 0 and prices["out_per_m"] == 0:
            label = f"{model} : 0 $ (moteur règles)"
        else:
            label = f"{model} : {prices['in_per_m']}/{prices['out_per_m']} $/1M tok"
        nodes.append(_node("model:" + model, label, "modele", {"color": "#38bdf8"}))
        links.append({"source": "euphrosyne", "target": "model:" + model, "type": "arbitre"})
    return {"nodes": nodes, "links": links}


def sol_graph() -> Dict[str, Any]:
    """Constellation de gouvernance de SOL."""
    nodes, links = [], []
    nodes.append(_node("sol", "☉ SOL", "star", {"color": "#fbbf24"}))
    for b in celestial_registry():
        if b["kind"] in {"planet", "utilisateur"}:
            nodes.append(_node(b["id"], f"{b['symbol']} {b['name']}", b["kind"],
                               {"color": "#fcd34d" if b["kind"] == "utilisateur" else
                                (BODIES.get(b["id"], {}).get("color") or "#818cf8")}))
            links.append({"source": "sol", "target": b["id"], "type": "gouverne"})
    for s in BODIES["uranus"]["satellites"]:
        nodes.append(_node(s["id"], s["name"], "satellite", {"color": "#a5b4fc"}))
        links.append({"source": "uranus", "target": s["id"], "type": "orbite"})
        links.append({"source": "sol", "target": s["id"], "type": "supervise"})
    return {"nodes": nodes, "links": links}


def knowledge_graph(body_id: str) -> Dict[str, Any] | None:
    if body_id == "uranus":
        return uranus_graph()
    if body_id in {s["id"] for s in BODIES["uranus"]["satellites"]}:
        return satellite_graph(body_id)
    if body_id == "venus":
        return venus_graph()
    if body_id in {c["id"] for c in BODIES["venus"]["court"]}:
        # constellation d'un analyste = Vénus filtrée sur son périmètre
        g = venus_graph()
        keep = {body_id} | {n["id"] for n in g["nodes"]
                            if n["id"].startswith(body_id + ":")} | {"venus"}
        return {"nodes": [n for n in g["nodes"] if n["id"] in keep],
                "links": [l for l in g["links"]
                          if l["source"] in keep and l["target"] in keep]}
    if body_id == "sol":
        return sol_graph()
    if body_id in BODIES or body_id in DEPT_CONCEPTS:
        return generic_graph(body_id)
    return None


def generic_graph(body_id: str) -> Dict[str, Any]:
    """Constellation générique d'un corps « entreprise » : sous-rôles + concepts
    du département (+ références matchées de la base, comme les satellites)."""
    b = BODIES.get(body_id)
    concepts = DEPT_CONCEPTS.get(body_id, [])
    nodes, links = [], []
    color = (b or {}).get("color", "#818cf8")
    nodes.append(_node(body_id, (b or {}).get("name", body_id),
                       (b or {}).get("kind", "agent"), {"color": color}))
    for c in concepts:
        cid = f"{body_id}:c:{c}"
        nodes.append(_node(cid, c, "concept", {"color": "#34d399"}))
        links.append({"source": body_id, "target": cid, "type": "concept"})
    # sous-rôles : satellites ou cour
    for sub in (b or {}).get("satellites", []) or (b or {}).get("court", []) or []:
        sid = sub["id"]
        nodes.append(_node(sid, sub["name"], "satellite", {"color": "#a5b4fc"}))
        links.append({"source": body_id, "target": sid, "type": "orbite"})
        for c in DEPT_CONCEPTS.get(sid, [])[:3]:
            nodes.append(_node(f"{sid}:c:{c}", c, "concept", {"color": "#34d399"}))
            links.append({"source": sid, "target": f"{sid}:c:{c}", "type": "concept"})
    # références de la base matchées par mots-clés des concepts
    kws = [c.lower() for c in concepts][:10]
    for r in _read_refs():
        blob = " ".join([(r.get(k) or "").lower() for k in
                         ("theme", "tags", "question_scientifique", "reference_courte")])
        if any(k in blob for k in kws):
            rid = r.get("id")
            nodes.append(_node(rid, r.get("reference_courte", rid), "reference",
                               {"doi": r.get("doi"), "trust": r.get("trust_factor"),
                                "color": "#38bdf8"}))
            links.append({"source": body_id, "target": rid, "type": "source"})
    return {"nodes": nodes, "links": links}
