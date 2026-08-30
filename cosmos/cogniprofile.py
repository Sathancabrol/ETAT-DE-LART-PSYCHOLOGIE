"""
Profil cognitif — induire un maximum d'informations sur l'utilisateur à
partir de ses schémas d'utilisation (interactions, questions, missions,
données produites). Inspiré des approches de data-science comportementale
(The Sapien Company, Palantir, agences marketing) — appliquée à soi-même,
avec honnêteté : heuristiques statistiques, pas un test clinique validé.
"""

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO / "output" / "agent_runs"

#词汇
STYLE_MOTS = {
    "visionnaire": ["imaginer", "futur", "vision", "innovation", "révolutionner", "créer", "inventer"],
    "analyste": ["analyser", "données", "méta-analyse", "statistique", "vérifier", "valider", "preuve"],
    "bâtisseur": ["construire", "implémenter", "intégrer", "déployer", "btp", "infrastructure", "système"],
    "explorateur": ["explorer", "chercher", "découvrir", "veille", "nouveau", "émergent"],
    "organisateur": ["organiser", "structurer", "plan", "roadmap", "dossier", "architect"],
}


def _questions() -> List[Dict[str, Any]]:
    try:
        from cosmos import memory
        return [i for i in memory.items(limit=1000) if i.get("source") == "user"
                or i.get("type") == "question"]
    except Exception:
        return []


def _runs() -> List[Dict[str, Any]]:
    out = []
    if RUNS_DIR.exists():
        for d in sorted(RUNS_DIR.iterdir(), reverse=True)[:200]:
            tj = d / "trace.json"
            if tj.exists():
                try:
                    out.append(json.loads(tj.read_text(encoding="utf-8")))
                except Exception:
                    continue
    return out


def build_profile() -> Dict[str, Any]:
    """Construit le profil cognitif induit : dimensions, traits, rythme,
    domaines, style — à partir des données d'utilisation réelles."""
    questions = _questions()
    runs = _runs()
    corpus = [q.get("titre", "") for q in questions] + [r.get("tache", "") for r in runs]
    blobs = " ".join(corpus).lower()

    # ── domaines explorés (match taxonomie) ──
    domaines = []
    try:
        from cosmos import memory
        for leaf in memory.taxonomy_leaves():
            if len(leaf) > 4 and leaf.lower() in blobs:
                domaines.append(leaf)
    except Exception:
        pass

    # ── dimensions 0-100 (heuristiques de comptage — pas de formule secrète) ──
    n_act = len(questions) + len(runs)
    curiosite = min(100, len(set(domaines)) * 9 + 18)
    # profondeur : suivi moyen d'un même run (étapes) + refs par run
    prof_runs = sum(len(r.get("steps", [])) for r in runs) / max(1, len(runs))
    profondeur = min(100, int(prof_runs * 11) + (25 if len(runs) > 10 else 10))
    # créativité : proportion de tâches hors sentiers battus (domaines Émergents / visée création)
    crea = sum(1 for c in corpus if re.search(r"cr[ée]{1,2}|imagin|innov|prototype|outil", c.lower()))
    creativite = min(100, int(crea * 100 / max(1, len(corpus))) + 30)
    # méthode : usage des compétences imposées / sujets (structure volontaire)
    methode_runs = sum(1 for r in runs if "imposé" in (r.get("rationale") or ""))
    methode = min(100, int(methode_runs * 100 / max(1, len(runs))) + 40)
    # activité : volume global (échelle logarithmique honnête)
    activite = min(100, int(12 * (1 + n_act ** 0.5)))

    dims = [
        {"id": "curiosite", "label": "Curiosité", "valeur": curiosite,
         "explication": f"{len(set(domaines))} domaines distincts explorés "
                        "(matchés sur la taxonomie vivante)."},
        {"id": "profondeur", "label": "Profondeur", "valeur": profondeur,
         "explication": f"{prof_runs:.1f} étapes par mission en moyenne — "
                        "les missions vont au bout des chaînes."},
        {"id": "creativite", "label": "Créativité", "valeur": creativite,
         "explication": f"{crea} requêtes à visée de création/innovation "
                        f"sur {len(corpus)}."},
        {"id": "methode", "label": "Méthode", "valeur": methode,
         "explication": f"{methode_runs} missions lancées avec compétences "
                        "imposées (plan structuré volontaire)."},
        {"id": "activite", "label": "Activité", "valeur": activite,
         "explication": f"{len(questions)} questions · {len(runs)} missions — "
                        "échelle logarithmique."},
    ]

    # ── rythme circadien ──
    heures = Counter()
    for q in questions:
        try:
            heures[int(q["ts"][11:13])] += 1
        except Exception:
            continue
    for r in runs:
        try:
            heures[int(r["date"][11:13])] += 1
        except Exception:
            continue
    rythme = dict(sorted(heures.items()))
    pic = heures.most_common(1)[0][0] if heures else None
    moment = ("lève-tôt (matin)" if pic is not None and 5 <= pic < 12 else
              "après-midi" if pic is not None and 12 <= pic < 18 else
              "oiseau de nuit" if pic is not None else "indéterminé")

    # ── style cognitif dominant (vocabulaire) ──
    scores_style = {s: sum(blobs.count(m) for m in mots)
                    for s, mots in STYLE_MOTS.items()}
    style_dom = max(scores_style, key=scores_style.get) if any(scores_style.values()) else "équilibré"

    # ── traits dérivés ──
    traits = [
        f"Profil d'activité : **{moment}** (pic à {pic}h)" + ("" if pic is None else " — rythme régulier détecté" if len(rythme) > 4 else " — sessions concentrées"),
        f"Style cognitif dominant : **{style_dom}** (empreinte lexicale : "
        + ", ".join(f"{s} {n}" for s, n in Counter(scores_style).most_common(3) if n > 0) + ")",
        f"Amplitude d'exploration : {len(set(domaines))} domaines — "
        + ("exploration large (téléscope)" if len(set(domaines)) > 8 else "exploration ciblée (laser)"),
        f"Relation au système : " + ("utilisateur structureur — impose des plans" if methode > 60
                                     else "utilisateur explorateur — laisse le système planifier"),
    ]
    if domaines:
        traits.append("Domaines récurrents : " + ", ".join(domaines[:6]))

    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_donnees": {"questions": len(questions), "missions": len(runs),
                           "domaines": len(set(domaines))},
        "dimensions": dims,
        "traits": traits,
        "rythme": rythme,
        "style_scores": scores_style,
        "domaines": sorted(set(domaines))[:15],
        "avertissement": [
            "⚠️ Profil **statistique induit** à partir de vos interactions avec le "
            "système — ce n'est **pas un test psychométrique validé**.",
            "Méthode : comptage d'intentions, de domaines matchés sur la taxonomie, "
            "d'heures d'activité et d'empreinte lexicale. **Pas de formule secrète** — "
            "chaque score est un compteur simple, transparent dans ses explications.",
        ],
    }
