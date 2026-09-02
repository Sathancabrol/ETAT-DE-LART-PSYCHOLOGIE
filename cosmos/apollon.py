"""
Apollon — dieu du soleil, de la clairvoyance et des divinations (cour de SOL ☉).

Le chariot d'Apollon 🏆 traverse le système et propose une divination :
une prévision de fonctionnement fondée sur des données réelles (budget de
Vénus, intégrité de SOL, activité d'Uranus, condamnés d'Hadès) — moteur à
règles, chaque prédiction cite ses données.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


def divination(question: str = "") -> Dict[str, Any]:
    """Prononce une prévision de fonctionnement du système (données réelles)."""
    from cosmos import venus, hades
    from cosmos.sol import system_state
    v = venus.status()
    st = system_state()
    integ = st["integrite"]
    sc = hades.scan_system()

    f = v["forecast"]
    presages: List[Dict[str, Any]] = []

    # 1. trésor (budget)
    proj = f.get("monthly_projection_usd", 0.0)
    cap = v["budget"]["monthly_cap_usd"]
    presages.append({"titre": "Trésor du royaume (Vénus ♀)",
                     "lecture": f"projection mensuelle {proj:.2f} $ / plafond {cap:.2f} $ "
                                f"({(proj / cap * 100 if cap else 0):.0f} %)",
                     "oracle": "années fastes" if proj < cap * .5 else
                               "vigilance sur les dépenses" if proj < cap else
                               "dépense au-delà du plafond — arbitrage d'Euphrosyne requis",
                     "ton": "bon" if proj < cap * .5 else "moyen" if proj < cap else "mauvais"})

    # 2. santé (intégrité)
    presages.append({"titre": "Santé du corps céleste (SOL ☉)",
                     "lecture": f"intégrité {integ['score']}/100 · {integ['statut']} · "
                                f"{integ['interactions_total']} interactions, "
                                f"taux d'échec {integ['taux_echec']:.0%}",
                     "oracle": "le système tient" if integ["statut"] == "stable" else
                               "fatigue perceptible — Hadès et les Moires veillent",
                     "ton": "bon" if integ["statut"] == "stable" else
                            "moyen" if integ["statut"] == "vigilance" else "mauvais"})

    # 3. fardeau (Hadès + Moires)
    presages.append({"titre": "Fardeau des mortels (Hadès ♇ & Moires)",
                     "lecture": f"{sc['stats']['condamnes']} condamnés · "
                                f"{sc['stats']['ko']} Ko libérables · "
                                f"{sc['moires']['clotho']['naissance_24h']} naissances/24 h",
                     "oracle": "un fauche allégera le cycle" if sc["stats"]["condamnes"] > 20 else
                               "le royaume est léger — bon présage pour le cycle",
                     "ton": "moyen" if sc["stats"]["condamnes"] > 20 else "bon"})

    # 4.activité ( rythme )
    try:
        from cosmos import cogniprofile
        pr = cogniprofile.build_profile()
        act = next(d for d in pr["dimensions"] if d["id"] == "activite")
        pic = max(pr["rythme"], key=pr["rythme"].get) if pr["rythme"] else None
        presages.append({"titre": "Feu des mortels (votre activité)",
                         "lecture": f"activité {act['valeur']}/100 · pic à {pic}h",
                         "oracle": "l'élan est fort — les missions aboutiront vite" if act["valeur"] > 60
                                   else "ryme posé — privilégier les missions ciblées",
                         "ton": "bon" if act["valeur"] > 60 else "moyen"})
    except Exception:
        pass

    tons = [p["ton"] for p in presages]
    verdict = ("☀️ Présage faste — le système fonctionnera harmonieusement." if tons.count("bon") >= tons.count("mauvais") + 2
               else "🌤 Présage mitigé — vigilance sur les points cités." if tons.count("mauvais") == 0
               else "⛈ Présage sombre — agir sur les points cités avant de lancer de grandes missions.")
    if question:
        verdict += f"\nSur « {question[:80]} » : le chariot conseille de lancer la mission après lecture des présages."

    return {"devin": "apollon", "chariot": "🏆",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "presages": presages, "verdict": verdict,
            "methode": "moteur à règles — chaque présage cite ses données réelles "
                       "(budget Vénus, intégrité SOL, scan Hadès/Moires, profil d'activité). "
                       "Pas d'oracle aléatoire : pas de formule cachée."}
