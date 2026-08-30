"""
Sebas ◉ — exécutant des commandes divines de Laplace ✳.

Laplace (ou l'utilisateur) prononce une commande ; Sebas l'exécute sur le
terrain, dans les limites honnêtes de la sandbox (aucun périphérique réel →
jamais de fausses données de capteur).
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict

ACTIONS = {
    "observer": r"observ|regarde|photographi|filme|d[ée]crit",
    "ecouter": r"[ée]coute|scan.{0,12}wifi|r[ée]seau",
    "faucher": r"fauche|nettoi|purge",
    "etat": r"[ée]tat|o[ùu] en|situation",
    "consigner": r"consign|note\b|enregistre",
}


def execute(commande: str, agent: str = "laplace") -> Dict[str, Any]:
    """Exécute une commande divine — routage règles + journal + mémoire."""
    cmd = (commande or "").strip()
    if not cmd:
        return {"ok": False, "reponse": "commande vide — Laplace n'a rien ordonné."}
    low = cmd.lower()

    action = next((a for a, pat in ACTIONS.items() if re.search(pat, low)), "consigner")
    try:
        from cosmos import memory
        item = memory.record_item("memoire", f"[commande divine] {cmd[:90]}",
                                  contenu=f"ordonnée par {agent} · exécutée par Sebas (action : {action})",
                                  tags=["commande", action], source=agent, corps="sebas",
                                  meta={"action": action})
        idt = item["id"]
    except Exception:
        idt = None
    from cosmos import ledger
    ledger.record(agent="sebas", action=f"commande_divine:{action}", model="regles",
                  meta={"par": agent, "commande": cmd[:120]})

    if action == "faucher":
        from cosmos import hades
        r = hades.reap(confirm=True)
        reponse = (f"◉ Sebas a exécuté l'ordre divin : la fauche a emporté {r['supprimes']} "
                   f"condamnés ({round(r['octets_liberes']/1024,1)} Ko libérés).")
    elif action == "etat":
        from cosmos.sol import system_state
        st = system_state()
        reponse = (f"◉ Sebas rapporte : intégrité {st['integrite']['score']}/100 "
                   f"({st['integrite']['statut']}), {len(st['corps'])} corps en ligne, "
                   f"dépense du jour {st['budget']['spend_today_usd']:.4f} $.")
    else:
        capteur = "webcam" if re.search(r"photographi|filme|image|vid[ée]o", low) else (
                  "wifi" if "wifi" in low or "réseau" in low or "reseau" in low else "telephone")
        reponse = (f"◉ Sebas a exécuté l'ordre divin sur le terrain ({action} · capteur {capteur}) : "
                   f"« {cmd[:120]} » consigné en mémoire"
                   + (f" (item {idt})" if idt else "")
                   + ". Capteurs physiques non détectés en sandbox — observation déclarative, "
                     "aucune donnée fabriquée.")

    try:
        from cosmos.system import get_system
        get_system()["bus"].send(agent, "sebas", "commande_divine", {"contenu": cmd[:200]})
    except Exception:
        pass
    return {"ok": True, "action": action, "reponse": reponse,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "item": idt}
