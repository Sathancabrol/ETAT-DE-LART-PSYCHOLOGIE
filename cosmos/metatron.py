"""
Métatron ✦ — archange du méta-prompting, satellite de Laplace ✳.

Métatron aide Laplace à mieux comprendre les requêtes de l'utilisateur et à
donner de meilleures instructions :
  • analyse d'intention (mission, outil, question, état, création d'agent) ;
  • extraction des domaines (matchés sur la taxonomie vivante) ;
  • reformulation en prompt enrichi (contraintes, livrables, critères) ;
  • clarifications utiles quand la requête est ambiguë ;
  • spécification d'agents (meilleur rôle, parent, kind) pour Laplace.

Moteur à règles, ancré sur la taxonomie et le registre réels (0 token).
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List

# ── Intentions fines ─────────────────────────────────────────────────────────

INTENTIONS: List[Dict[str, Any]] = [
    ("outil", r"\boutil\b|armurer|maquette|forge?r?|calcul(er|ez)?.*visualis|visualis.*calcul"),
    ("creation_agent", r"cr[ée]{1,2}\s+(un\s+)?agent|nouvel\s+agent|cr[ée]{1,2}\s+un\s+(syst[èe]me|astre)"),
    ("mission_recherche", r"recherch|m[ée]ta[- ]analys|revue|paper|papier|[ée]tat\s+de\s+l.art|veille"),
    ("mission_synthese", r"synth[ée]tis|dossier|strat[ée]gie|roadmap|comparer|am[ée]liorer|impl[ée]menter|int[ée]grer"),
    ("nettoyage", r"fauche|nettoy|purge|redondan|junk|obsol[èe]te|outdated|optimis.*espace"),
    ("profil", r"mon\s+profil|profil\s+cognitif|qui\s+suis.?je|mes\s+donn[ée]es"),
    ("etat", r"[ée]tat\s+du\s+syst|sant[ée]|budget|interactions|constellation"),
    ("question", r"^\s*(qu|comment|pourquoi|est[- ]ce|qui|o[ùu]|combien|que\s+)"),
]

LIVRABLES = {
    "papier scientifique": r"papier|paper|article|publication",
    "dossier stratégique": r"dossier|strat[ée]gie|roadmap|plan",
    "graphique / visualisation": r"graph|visualis|figure|diagramme|carte",
    "tableau de données": r"tableau|csv|donn[ée]es\s+structur",
    "rapport de veille": r"veille|surveill|alerte",
    "maquette d'outil": r"maquette|prototype|mockup",
}

TEMPORALITE = re.compile(r"\b(19|20)\d{2}\b|derni[èe]res?\s+\d+|\b\d+\s+(jours?|ans?|mois|semaines?)\b")

QUESTION_COURTE = 25      # en dessous : ambiguïté probable


def _taxonomy_domains() -> List[str]:
    try:
        from cosmos import memory
        return memory.taxonomy_leaves() or []
    except Exception:
        return []


def analyze_request(message: str) -> Dict[str, Any]:
    """Analyse méta-prompting d'une requête : intention, domaines, prompt
    enrichi, clarifications. Retourne un dictionnaire exploitable par
    Laplace et par l'interface."""
    m = (message or "").strip()
    low = m.lower()

    # 1. intention (la première qui matche gagne, ordre = priorité)
    intention = "question"
    for name, pat in INTENTIONS:
        if re.search(pat, low):
            intention = name
            break

    # 2. domaines matchés sur la taxonomie vivante
    domains = []
    for leaf in _taxonomy_domains():
        ll = leaf.lower()
        if len(ll) > 4 and ll in low:
            domains.append(leaf)
    domains = domains[:6]

    # 3. livrable attendu
    livrable = next((label for label, pat in LIVRABLES.items()
                     if re.search(pat, low)), None)

    # 4. contraintes temporelles
    tempo = TEMPORALITE.search(low)

    # 5. ambiguïté → clarifications
    clarifications = []
    if len(m) < QUESTION_COURTE and intention in ("mission_recherche",
                                                  "mission_synthese"):
        clarifications.append("Préciser le sujet exact (population, "
                              "intervention, mesure) ?")
    if intention == "mission_recherche" and not tempo:
        clarifications.append("Période visée (ex : 2024-2026, 30 derniers "
                              "jours) ?")
    if intention == "mission_recherche" and not livrable:
        clarifications.append("Livrable attendu : papier scientifique, "
                              "dossier, graphe ?")
    if intention == "outil" and not re.search(r"calcul|visualis", low):
        clarifications.append("L'outil doit-il calculer, visualiser, ou les "
                              "deux ? Sur quelles données ?")

    # 6. prompt enrichi (le méta-prompt que Métatron rédige pour le système)
    morceaux = []
    if intention == "mission_recherche":
        morceaux.append("Mission de recherche scientifique")
    elif intention == "mission_synthese":
        morceaux.append("Mission de synthèse stratégique")
    elif intention == "outil":
        morceaux.append("Demande d'outil — router vers l'armurerie de Mars ♂")
    elif intention == "creation_agent":
        morceaux.append("Création d'agent — Laplace ✳ + spécification Métatron ✦")
    elif intention == "nettoyage":
        morceaux.append("Fauche — router vers Pluton ♇ / Hadès")
    elif intention == "profil":
        morceaux.append("Profil cognitif — vue d'analyse")
    if domains:
        morceaux.append("domaines : " + ", ".join(domains[:4]))
    if livrable:
        morceaux.append(f"livrable : {livrable}")
    if tempo:
        morceaux.append(f"période : {tempo.group(0)}")
    morceaux.append("qualité : sources réelles triangulées, trust factor, "
                    "moteur à règles d'abord (0 token)")
    meta_prompt = " · ".join(morceaux)

    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requete": m[:400],
        "intention": intention,
        "domaines": domains,
        "livrable": livrable,
        "contrainte_temporelle": tempo.group(0) if tempo else None,
        "ambigu": bool(clarifications),
        "clarifications": clarifications[:3],
        "meta_prompt": meta_prompt[:600],
        "longueur": len(m),
        "style": "impératif" if re.match(r"^\s*(je\s+veux|donne|cr[ée]|fais|g[ée]n[èe]re|trouve|va)", low)
                 else "interrogatif" if m.endswith("?") else "déclaratif",
    }


def suggest_agent_spec(mission: str) -> Dict[str, Any]:
    """Spécification d'agent proposée par Métatron pour Laplace :
    meilleur parent, kind et rôle selon la mission décrite."""
    a = analyze_request(mission)
    low = (a["requete"] or "").lower()
    domains = a["domaines"]

    parent, kind = "uranus", "satellite"
    if a["intention"] == "outil" or re.search(r"outil|software|forge|code", low):
        parent, kind = "mars", "satellite"
        role_base = "forge d'outils sur mesure (calcul & visualisation)"
    elif re.search(r"donn[ée]es|base|sql|archiv|stockage", low):
        parent, kind = "neptune", "satellite"
        role_base = "gestion des données et de l'infrastructure"
    elif re.search(r"juridique|rgpd|contrat|conformit", low):
        parent, kind = "jupiter", "satellite"
        role_base = "conformité et protection juridique"
    elif re.search(r"recrut|formation|comp[ée]tence|talent", low):
        parent, kind = "ceres", "court"
        role_base = "développement des talents"
    elif re.search(r"vendre|march[ée]|client|communication", low):
        parent, kind = "mercure", "court"
        role_base = "développement commercial"
    elif re.search(r"qualit|production|livraison|logistique", low):
        parent, kind = "terre", "satellite"
        role_base = "qualité et logistique"
    elif re.search(r"cr[ée]{1,2}r?|innov|concept", low):
        parent, kind = "laplace", "agent"
        role_base = "création et innovation d'agents"
    else:
        role_base = ("recherche & synthèse "
                     + ("— " + domains[0] if domains else "scientifique"))

    name = re.sub(r"[^a-z0-9]+", "-", low).strip("-")[:22] or "agent-nouveau"
    return {"name": name, "role": role_base[:300], "parent": parent,
            "kind": kind, "raison": f"intention détectée : {a['intention']}"
            + (f" · domaines : {', '.join(domains[:3])}" if domains else ""),
            "meta_prompt": a["meta_prompt"]}
