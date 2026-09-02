"""
Thémis ⚖ — justice divine, fille et bras armé de Laplace ✳.

Gardienne de l'équilibre du système : elle JUGE (instruit les menaces à
l'ordre), CONSEILLE (recommande les corrections) et DÉTRUIT le cas échéant
(ordonne la fauche à Hadès ♇ — exécution réelle par Charon ⚰).

Elle est constituée comme la démocratie et agit en conséquence :
  • Eunomie 📜  — pouvoir législatif : écrit les lois (politique Styx) ;
  • Éirène 🕊️  — pouvoir exécutif : applique et rétablit l'ordre ;
  • Dikè 🧑‍⚖️  — pouvoir judiciaire : instruit les dossiers, vérifie les preuves ;
  • Censeur 🔎 — contre-pouvoir : audit, transparence, rend compte au souverain.

Balance ⚖ pour peser, épée 🗡 pour trancher. Toute décision est motivée,
journalisée, et l'application (destruction) exige l'accord du souverain
(l'utilisateur) — jamais de lame aveugle.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List


def audit() -> Dict[str, Any]:
    """Thémis instruit le système : menaces, conseils, verdict — sur données réelles."""
    from cosmos import hades
    from cosmos.sol import system_state

    st = system_state()
    sc = hades.scan_system()
    integ = st["integrite"]
    menaces: List[Dict[str, Any]] = []
    conseils: List[str] = []

    # 1. Dikè instruit les dossiers d'Hadès (menaces à l'ordre = condamnés)
    if sc["stats"]["condamnes"] > 0:
        menaces.append({
            "gravite": "moyenne",
            "par": "Dikè 🧑‍⚖️ (jugement)",
            "quoi": f"{sc['stats']['condamnes']} condamnés d'Hadès — "
                    f"{', '.join(f'{v} {k}' for k, v in sc['stats']['par_type'].items())}",
            "remede": "faucher (Hadès ♇ exécutera) — "
                      f"🪙 {sc['prevision_tokens']['estime']:,} tokens épargnés".replace(",", " "),
        })
        conseils.append("laisser Hadès faucher les condamnés (les 25 derniers runs restent)")
    else:
        conseils.append("aucun condamné : le royaume est propre, Styx ☠ approuve")

    # 2. alertes d'intégrité (Éirène constate les tensions)
    for a in integ.get("alertes", []):
        menaces.append({"gravite": "faible", "par": "Éirène 🕊️ (exécutif)",
                        "quoi": a, "remede": "suivre la recommandation de l'alerte"})

    # 3. budget (Eunomie vérifie les lois de rareté)
    bud = st.get("budget", {})
    if bud.get("forecast_month_usd", 0) > (bud.get("monthly_cap_usd") or 0) > 0:
        menaces.append({"gravite": "élevée", "par": "Eunomie 📜 (loi)",
                        "quoi": f"projection mensuelle {bud['forecast_month_usd']:.2f} $ > plafond "
                                f"{bud['monthly_cap_usd']:.2f} $",
                        "remede": "réviser les caps ou la portée des missions"})

    grav = {m["gravite"] for m in menaces}
    verdict = ("🚨 menace à l'ordre — l'épée 🗡 peut être dégainer" if "élevée" in grav else
               "⚖ ordre sous tension — la balance penche, à surveiller" if menaces else
               "⚖ ordre parfait — la balance est droite, l'épée au fourreau")

    return {"deesse": "Thémis ⚖", "verdict": verdict,
            "gravite": max(grav, key=["faible", "moyenne", "élevée"].index) if grav else "aucune",
            "menaces": menaces, "conseils": conseils,
            "constitution": [
                {"organe": "Eunomie 📜", "pouvoir": "législatif",
                 "loi_vivante": f"politique Styx : {sc['politique_styx']['runs_gardes']} runs gardés · "
                                f"journaux ≤ {sc['politique_styx']['interactions_max']} lignes"},
                {"organe": "Éirène 🕊️", "pouvoir": "exécutif",
                 "loi_vivante": "applique les décisions, alertes préventives SOL"},
                {"organe": "Dikè 🧑‍⚖️", "pouvoir": "judiciaire",
                 "loi_vivante": f"{sc['stats']['condamnes']} dossiers instruits, preuves = octets mesurés"},
                {"organe": "Censeur 🔎", "pouvoir": "contre-pouvoir",
                 "loi_vivante": "tout est rendu public au souverain (l'utilisateur), audit permanent"},
            ],
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def appliquer(confirm: bool = False) -> Dict[str, Any]:
    """Thémis applique la justice : ordonne la fauche à Hadès (bras armé).

    Jamais de lame sans accord explicite du souverain (`confirm=True`).
    """
    a = audit()
    fauchables = [m for m in a["menaces"] if "Hadès" in m["quoi"]]
    if not fauchables:
        return {"statut": "⚖ Thémis n'a rien à trancher — aucun condamné, l'épée reste "
                          "au fourreau.", "fauche": None, "verdict": a["verdict"],
                "ts": a["ts"]}
    if not confirm:
        return {"statut": "⚖ Thémis a instruit les dossiers — dites « Thémis, applique la "
                          "justice » pour qu'elle ordonne la fauche à Hadès (rien n'est "
                          "détruit sans votre accord).",
                "fauche": None, "verdict": a["verdict"], "ts": a["ts"]}
    from cosmos import hades
    r = hades.reap(confirm=True)
    # Ananké ⧉ et ses Moires ont aidé Hadès ; Thémis consigne et rend compte
    from cosmos import ledger, memory
    try:
        memory.record_item("memoire", "[Thémis] justice appliquée",
                           contenu=f"fauche ordonnée par Thémis : {r['supprimes']} condamnés, "
                                   f"🪙 {r.get('tokens_epargnes', 0)} tokens épargnés",
                           tags=["themis", "justice"], source="themis", corps="themis")
    except Exception:
        pass
    ledger.record(agent="themis", action="justice_appliquee", model="regles",
                  meta={"supprimes": r["supprimes"], "octets": r.get("octets_liberes", 0)})
    return {"statut": f"🗡 Thémis a ordonné la fauche — Hadès ⚰ a exécuté : "
                      f"{r['supprimes']} condamnés détruits, "
                      f"🪙 {r.get('tokens_epargnes', 0):,} tokens épargnés".replace(",", " ")
                      + f". {r['ce_qui_est_conserve']}",
            "fauche": {"supprimes": r["supprimes"], "bilan": r.get("bilan"),
                       "tokens_epargnes": r.get("tokens_epargnes")},
            "verdict": a["verdict"], "ts": a["ts"]}
