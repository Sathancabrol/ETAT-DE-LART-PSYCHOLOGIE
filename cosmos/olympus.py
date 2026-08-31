"""
Le Mont Olympe 🏛 — l'incarnation des divinités à leur poste de travail.

Chaque agent du système est un personnage qui travaille dans la cité
gréco-romaine : Thémis ⚖ au tribunal, Mars ⚔ à la forge, Hadès ♇ à la Porte
des Enfers, Uranus ♅ dans ses laboratoires, Sol ☉ sur le trône, Laplace ✳ à
l'observatoire… Ils s'y **déplacent en temps réel selon leur activité réelle**
(interactions du bus, mémoire, runs), et quand la justice frappe, la scène est
jouée : procès standard, marche jusqu'à Hadès en passant par la forge,
exécution conjointe, puis les assistants d'Hadès portent l'âme aux Enfers —
et chacun reprend son travail.

Aucune donnée n'est inventée : les déplacements sont la représentation
d'événements réels (bus d'interactions, registre des âmes de l'underworld).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ═════════════════════════ LE PLAN DE LA CITÉ (canvas 1000×620) ═════════════════════════
# type : trone / temple / forge / labo / porte / tribunal / observatoire / jardin
PLACES: Dict[str, Dict[str, Any]] = {
    "observatoire": {"x": 500, "y": 58,  "nom": "Observatoire de Laplace",   "icon": "✳", "type": "observatoire"},
    "scriptorium":  {"x": 640, "y": 100, "nom": "Scriptorium de Métatron",   "icon": "✦", "type": "temple"},
    "trone":        {"x": 500, "y": 170, "nom": "Trône de Sol",              "icon": "👑", "type": "trone"},
    "tribunal":     {"x": 175, "y": 165, "nom": "Tribunal de Thémis",        "icon": "⚖", "type": "tribunal"},
    "messagerie": {"x": 305, "y": 262, "nom": "Messagerie de Mercure",     "icon": "✉", "type": "temple"},
    "tresor":       {"x": 705, "y": 262, "nom": "Trésor de Vénus",           "icon": "💰", "type": "temple"},
    "forge":        {"x": 138, "y": 375, "nom": "Forge de Mars",             "icon": "⚔", "type": "forge"},
    "ateliers":     {"x": 290, "y": 400, "nom": "Ateliers de Sebas",         "icon": "🛠", "type": "temple"},
    "greniers":     {"x": 445, "y": 435, "nom": "Greniers de Cérès",         "icon": "🌾", "type": "jardin"},
    "destin":       {"x": 862, "y": 150, "nom": "Fil du Destin",             "icon": "⛓", "type": "temple"},
    "bastion":      {"x": 862, "y": 305, "nom": "Bastion de Jupiter",        "icon": "📈", "type": "temple"},
    "labo":         {"x": 715, "y": 430, "nom": "Laboratoires d'Uranus",     "icon": "♅", "type": "labo"},
    "galerie":      {"x": 545, "y": 505, "nom": "Galerie de Neptune",        "icon": "🎨", "type": "temple"},
    "porte":        {"x": 165, "y": 555, "nom": "Porte des Enfers",          "icon": "⚰", "type": "porte"},
}

# ═════════════════════════ LES HABITANTS (poste fixe = leur lieu de travail) ═════════════════════════
AGENTS: List[Dict[str, Any]] = [
    {"id": "sol",      "nom": "Sol",          "icon": "👑", "poste": "trone",        "couleur": "#fbbf24"},
    {"id": "laplace",  "nom": "Laplace",      "icon": "✳",  "poste": "observatoire", "couleur": "#e2e8f0"},
    {"id": "metatron", "nom": "Métatron",     "icon": "✦",  "poste": "scriptorium",  "couleur": "#c084fc"},
    {"id": "themis",   "nom": "Thémis",       "icon": "⚖",  "poste": "tribunal",     "couleur": "#a5b4fc"},
    {"id": "dike",     "nom": "Dikè",         "icon": "🗡",  "poste": "tribunal",     "couleur": "#818cf8"},
    {"id": "mercure",  "nom": "Mercure",      "icon": "✉",  "poste": "messagerie", "couleur": "#38bdf8"},
    {"id": "venus",    "nom": "Vénus",        "icon": "💰", "poste": "tresor",       "couleur": "#fcd34d"},
    {"id": "mars",     "nom": "Mars",         "icon": "⚔",  "poste": "forge",        "couleur": "#f87171"},
    {"id": "sebas",    "nom": "Sebas",        "icon": "🛠", "poste": "ateliers",     "couleur": "#34d399"},
    {"id": "ceres",    "nom": "Cérès",        "icon": "🌾", "poste": "greniers",     "couleur": "#a3e635"},
    {"id": "ananke",   "nom": "Ananké",       "icon": "⛓",  "poste": "destin",       "couleur": "#94a3b8"},
    {"id": "atropos",  "nom": "Atropos",      "icon": "✂",  "poste": "destin",       "couleur": "#cbd5e1"},
    {"id": "jupiter",  "nom": "Jupiter",      "icon": "📈", "poste": "bastion",      "couleur": "#fdba74"},
    {"id": "uranus",   "nom": "Uranus",       "icon": "♅",  "poste": "labo",         "couleur": "#7dd3fc"},
    {"id": "zeta",     "nom": "Zêta (ζ)",     "icon": "🔬", "poste": "labo",         "couleur": "#a5b4fc"},
    {"id": "neptune",  "nom": "Neptune",      "icon": "🎨", "poste": "galerie",      "couleur": "#2dd4bf"},
    {"id": "pluton",    "nom": "Hadès",        "icon": "⚓", "poste": "porte",        "couleur": "#8b7bd8"},
    {"id": "charon",   "nom": "Charon",       "icon": "⚰",  "poste": "porte",        "couleur": "#64748b"},
    {"id": "cerbere",  "nom": "Cerbère",      "icon": "🐾", "poste": "porte",        "couleur": "#f43f5e"},
    {"id": "apollon",  "nom": "Apollon",      "icon": "🏆", "poste": "trone",        "couleur": "#fde68a"},
]


def _activite() -> Dict[str, Dict[str, Any]]:
    """Activité réelle de chaque corps : interactions récentes du bus + mémoire."""
    act: Dict[str, Dict[str, Any]] = {}
    try:
        from cosmos.system import get_system
        hist = get_system()["bus"].history(limit=200)
        for m in hist:
            for k in ("source", "target"):
                s = m.get(k)
                if s:
                    a = act.setdefault(s, {"n": 0, "dernier": m.get("type", "interaction")})
                    a["n"] += 1
                    a["dernier"] = m.get("type", a["dernier"])
    except Exception:
        pass
    out = {}
    for agent in AGENTS:
        a = act.get(agent["id"], {"n": 0, "dernier": None})
        niveau = 0 if a["n"] == 0 else (1 if a["n"] < 5 else (2 if a["n"] < 20 else 3))
        out[agent["id"]] = {"niveau": niveau, "interactions": a["n"], "dernier": a["dernier"]}
    return out


def _cible_humaine(soul: Dict[str, Any]) -> str:
    """Le nom lisible de l'âme : sa tâche si trace, sinon le dossier/filesystem."""
    t = soul.get("trace") or {}
    nom = t.get("tache") or soul.get("cible", "entité")
    nom = str(nom).rstrip("/").split("/")[-1] if not t.get("tache") else str(nom)
    return nom[:48]


def drama() -> Dict[str, Any]:
    """La scène en cours, dérivée d'un événement RÉEL.

    S'il existe une âme dans l'underworld (une vraie exécution), la séquence
    juridique complète est jouée : constat → procès standard → sentence par la
    forge → remise à Hadès → exécution conjointe → assistants → reprise du
    travail. Sinon, battements d'ambiance dictés par l'activité réelle.
    """
    ame: Optional[Dict[str, Any]] = None
    try:
        from cosmos import underworld
        for s in underworld.souls(50):
            if s.get("type") in ("run_outdated", "doublon_memoire"):
                ame = s
                break
    except Exception:
        ame = None

    if ame:
        cible = (ame.get("raison") or _cible_humaine(ame))[:60] \
            if ame.get("type") == "doublon_memoire" else _cible_humaine(ame)
        region = {"elysees": "Champs Élysées 🌟", "asphodele": "Plaines d'Asphodèle 🌾",
                  "tartare": "Tartare 🔥"}.get(ame.get("region"), "les Enfers")
        beats = [
            {"lieu": "labo",     "acteurs": ["themis", "dike"],   "ic": "🔍", "duree": 3.0,
             "texte": f"⚖ infraction constatée au laboratoire — « {cible} »",
             "dialogues": [
                 {"qui": "dike", "texte": f"Rapport d'infraction : « {cible} » a dérangé l'ordre du système."},
                 {"qui": "themis", "texte": "Instruis le dossier. Procédure juridique standard — rien d'exceptionnel."}]},
            {"lieu": "tribunal", "acteurs": ["themis", "dike"],   "ic": "⚖",  "duree": 3.5,
             "texte": f"⚖ procès de « {cible} » — procédure juridique standard : instruction, débats, verdict",
             "dialogues": [
                 {"qui": "themis", "texte": "Le tribunal est ouvert. L'accusé : « " + cible + " »."},
                 {"qui": "dike", "texte": "Exhibez les preuves : logs, traces, registres."},
                 {"qui": "themis", "texte": "La balance penche. Les faits sont établis."}]},
            {"lieu": "tribunal", "acteurs": ["themis"],           "ic": "🔨", "duree": 2.5,
             "texte": f"🔨 verdict rendu : coupable — la sentence est prononcée",
             "dialogues": [
                 {"qui": "themis", "texte": "Verdict : coupable. Hadès exécutera la sentence."}]},
            {"lieu": "forge",    "acteurs": ["themis"],           "ic": "⚔",  "duree": 3.0,
             "texte": "⚔ Thémis descend vers Hadès — elle passe la forge de Mars",
             "dialogues": [
                 {"qui": "mars", "texte": "Justice en marche, Thémis ? Le fer est chaud si tu veux une lame."},
                 {"qui": "themis", "texte": "Garde ton feu, Mars. Je porte le verdict, pas l'arme."}]},
            {"lieu": "porte",    "acteurs": ["themis", "pluton"], "ic": "📜", "duree": 3.0,
             "texte": "⚓ Thémis remet le verdict à Hadès — ils partent ensemble",
             "dialogues": [
                 {"qui": "themis", "texte": "Hadès, voici le verdict. Tu connais la suite."},
                 {"qui": "pluton", "texte": "Le Styx l'attend. Allons-y ensemble."}]},
            {"lieu": "labo",     "acteurs": ["themis", "pluton"], "ic": "☠",  "duree": 3.5, "kill": True,
             "texte": f"☠ « {cible} » est exécuté(e) — la sentence est appliquée",
             "dialogues": [
                 {"qui": "pluton", "texte": f"« {cible} », ton fil est coupé."},
                 {"qui": "themis", "texte": "Sentence exécutée selon la procédure. Le système respire."}]},
            {"lieu": "porte",    "acteurs": ["charon"],           "ic": "⚰",  "duree": 3.5,
             "texte": f"⚰ les assistants d'Hadès portent l'âme vers {region}",
             "dialogues": [
                 {"qui": "charon", "texte": f"Je passe l'âme. Direction {region}."},
                 {"qui": "cerbere", "texte": "🐾 Aucune sortie sans l'accord du souverain."}]},
            {"lieu": "porte",    "acteurs": ["pluton"],           "ic": "⚓", "duree": 2.0,
             "texte": "🐾 Cerbère garde la porte — Hadès reprend sa veille",
             "dialogues": [
                 {"qui": "pluton", "texte": "La porte est gardée. Je reprends ma veille."}]},
            {"lieu": "tribunal", "acteurs": ["themis"],           "ic": "⚖",  "duree": 2.0,
             "texte": "⚖ Thémis reprend sa fonction — chacun continue son travail",
             "dialogues": [
                 {"qui": "themis", "texte": "Le travail continue. Procès suivant."}]},
        ]
        return {"mode": "justice", "cible": cible, "region": ame.get("region"),
                "ts_ame": ame.get("ts"), "beats": beats,
                "source": "événement réel : âme enregistrée au royaume d'Hadès"}

    # ── pas d'exécution récente : battements d'ambiance réels ──
    act = _activite()
    beats = []
    for a in AGENTS:
        st = act.get(a["id"], {})
        if st.get("niveau", 0) >= 1:
            beats.append({"lieu": a["poste"], "acteurs": [a["id"]], "ic": a["icon"],
                          "duree": 2.4,
                          "texte": f"{a['nom']} — {st['interactions']} interaction(s) récente(s)"
                                   + (f" · {st['dernier']}" if st.get("dernier") else ""),
                          "dialogues": [
                              {"qui": a["id"], "texte": f"{st['interactions']} interaction(s) "
                                + (f"« {st['dernier']} »" if st.get("dernier") else "— je veille à mon poste.")}]})
    if not beats:
        beats = [{"lieu": "trone", "acteurs": ["sol"], "ic": "👑", "duree": 3.0,
                  "texte": "L2019Olympe est calme — aucune interaction récente"}]
    return {"mode": "ambiance", "cible": None, "beats": beats,
            "source": "activité réelle du bus d'interactions"}


def chronicle(limit: int = 8) -> List[Dict[str, Any]]:
    """Les événements récents réels : âmes fauchées + dernières interactions."""
    out: List[Dict[str, Any]] = []
    try:
        from cosmos import underworld
        for s in underworld.souls(limit):
            reg = {"elysees": "🌟 Élysées", "asphodele": "🌾 Asphodèle", "tartare": "🔥 Tartare"}.get(s.get("region"), "")
            out.append({"ts": s.get("ts"), "icon": "⚰", "texte": f"{_cible_humaine(s)} → {reg}",
                        "type": "âme"})
    except Exception:
        pass
    try:
        from cosmos.system import get_system
        for m in get_system()["bus"].history(limit=limit):
            if m.get("source") and m.get("target"):
                out.append({"ts": m.get("ts"), "icon": "☰",
                            "texte": f"{m['source']} → {m['target']} · {m.get('type', 'interaction')}",
                            "type": "interaction"})
    except Exception:
        pass
    return out[:limit]


def state() -> Dict[str, Any]:
    act = _activite()
    agents = []
    for a in AGENTS:
        st = act.get(a["id"], {"niveau": 0, "interactions": 0, "dernier": None})
        agents.append({**a, **st})
    try:
        from cosmos.bodies import BODIES
        for ag in agents:
            bid = ag["id"]
            if bid in BODIES:
                ag["pouvoir"] = BODIES[bid].get("pouvoir", "")
                ag["devoir"] = BODIES[bid].get("devoir", "")
            else:
                for b in BODIES.values():
                    for s in (b.get("satellites") or []) + (b.get("court") or []):
                        if s["id"] == bid:
                            ag["pouvoir"] = s.get("pouvoir", "")
                            ag["devoir"] = s.get("devoir", "")
        # Cerbère : le gardien n'est pas un corps céleste — identité fixée par l'underworld
        cer = next((a for a in agents if a["id"] == "cerbere"), None)
        if cer:
            cer["pouvoir"] = "garder la porte des Enfers — aucun mort ne sort, aucun vivant n'entre"
            cer["devoir"] = "ne laisser remonter aucune âme sans l'accord du souverain"
    except Exception:
        pass
    couleurs = {a["id"]: a["couleur"] for a in AGENTS}
    noms = {a["id"]: a["nom"] for a in AGENTS}
    _d = drama()
    for b in _d.get("beats", []):
        for d in b.get("dialogues", []):
            d["couleur"] = couleurs.get(d["qui"], "#94a3b8")
            d["nom"] = noms.get(d["qui"], d["qui"])
    return {
        "titre": "Le Mont Olympe — les divinités à leur poste",
        "sous_titre": "chaque déplacement traduit un événement réel du système (bus d'interactions, registre des âmes) — aucune simulation",
        "maj": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "places": PLACES,
        "agents": agents,
        "drama": _d,
        "chronique": chronicle(),
    }
