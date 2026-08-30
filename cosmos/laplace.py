"""
Laplace ✳ — interlocuteur principal du système (remplace SOL en façade).

Laplace est le créateur de nébuleuse du savoir : c'est désormais LUI que
l'utilisateur voit en priorité (chat flottant, boutons d'appel). SOL ☉ reste
l'orchestrateur qui approuve les interactions — Laplace est la porte d'entrée.

Routage spécifique : les demandes d'outils (« calculer et visualiser des
données complexes ») partent à l'armurerie de Mars ♂ (Phobos ◂ forge,
Deimos ◦ conçoit) — recherche open source d'abord, maquette sinon.
"""

import re
from typing import Any, Dict

from cosmos import mars

TOOL_RE = re.compile(
    r"\boutil\b|armurer|maquette|forge?r?\b|phobos|deimos|\bmars\b|"
    r"calcul(er|ez)?\b.*\bvisualis|visualis.*\bcalcul", re.IGNORECASE)

# « armurerie » seul = inventaire ; accompagné d'un vrai besoin = routage outil
INVENTORY_RE = re.compile(r"\barmurerie\b|\binventaire\b|outils?\s+disponibles",
                          re.IGNORECASE)
NEED_WORDS = re.compile(r"calcul|visualis|besoin|pour\s|donne|cr[ée]{1,2}|forge|maquette",
                        re.IGNORECASE)


def chat(message: str) -> Dict[str, Any]:
    """Réponse de Laplace ✳ — délègue l'état réel au moteur de SOL, route les outils vers Mars."""
    m = (message or "").strip()
    if not m:
        return {"reply": "✳ Laplace vous écoute.", "intent": "vide",
                "speaker": "laplace", "data": {}}

    # ── Intention INVENTAIRE → état de l'armurerie ───────────────────────
    if INVENTORY_RE.search(m) and not NEED_WORDS.search(m):
        reqs = mars.list_requests()
        if not reqs:
            reply = ("♂ L'armurerie de Mars est vide — aucun agent n'a encore demandé "
                     "d'outil. Décrivez un besoin (« outil pour calculer et visualiser… ») "
                     "et Deimos ◦ / Phobos ◂ s'y mettent.")
        else:
            lines = [f"♂ Armurerie de Mars — {len(reqs)} demande(s) :"]
            for r in reqs[-8:]:
                icon = {"opensource recommandé": " libre ♻", "maquette conçue": " 📐",
                        "outil livré": " ⚒"}[r["statut"]]
                lines.append(f"• {r['id']} — {r['besoin'][:60]}{icon}")
            catalogue = ", ".join(t["name"] for t in mars.OSS_CATALOG[:6])
            lines.append(f"Catalogue open source de référence : {catalogue}…")
            reply = "\n".join(lines)
        return {"reply": reply, "intent": "armurerie", "speaker": "laplace",
                "data": {"requests": [{k: r.get(k) for k in ("id", "statut", "data_kind",
                                                            "maquette", "outil")}
                                      for r in reqs[-8:]]}}

    # ── Forge explicite : « forger <id> » ────────────────────────────────
    mfor = re.match(r"\s*forge?r\s+(.+)$", m, flags=re.IGNORECASE)
    if mfor:
        rid = mfor.group(1).strip().strip("`\"'").split()[0]
        try:
            req = mars.forge_tool(rid)
            return {"reply": (f"⚒ Phobos ◂ a forgé l'outil `{req['id']}_outil.html` "
                              f"(calculs réels + visualisation {req['data_kind']}) — "
                              f"livré à {req['agent']}, approuvé par SOL ☉."),
                    "intent": "forge", "speaker": "laplace",
                    "data": {"request": {"id": req["id"], "statut": req["statut"],
                                         "outil": req.get("outil")}}}
        except ValueError:
            pass  # ce n'était pas une demande de forge → moteur général

    # ── Intention OUTIL → armurerie de Mars ──────────────────────────────
    if TOOL_RE.search(m):
        besoin = re.sub(r"^(je\s+(veux|voudrais|besoin)|il\s+me\s+faut|"
                        r"peux[- ]tu|j'?ai\s+besoin\s+de|donne[- ]moi|"
                        r"cr[ée]{1,2}|fabrique|trouve)\s+", "", m,
                        flags=re.IGNORECASE).strip() or m
        try:
            req = mars.request_tool("user", besoin[:400])
        except ValueError as e:
            return {"reply": f"✳ Laplace — {e}", "intent": "outil",
                    "speaker": "laplace", "data": {}}
        if req.get("recommandation"):
            rec = req["recommandation"]
            reply = ("♂ Mars a trouvé un outil libre — inutile de réinventer :\n"
                     f"• **{rec['outil']}** ({rec['licence']}) — {rec['pourquoi']}.\n"
                     f"• Consigne de l'armurier : {rec['consigne']}.\n"
                     "Si l'intégration te résiste, demande une maquette à Deimos ◦ "
                     "(« maquette : … ») et Phobos ◂ la forgera.")
        else:
            reply = ("♂ Mars, l'armurier du système, a pris la demande en charge :\n"
                     f"• Recherche open source : aucun outil libre ne couvre « {besoin[:70]} ».\n"
                     f"• ◦ Deimos (innovation & conception) a dessiné la **maquette** "
                     f"`{req['id']}_maquette.html`.\n"
                     f"• ▂ Dis-moi « forger {req['id']} » et Phobos ◂ (création de software) "
                     "forge l'outil fonctionnel (calculs réels + visualisation).")
        return {"reply": reply, "intent": "outil", "speaker": "laplace",
                "data": {"request": {k: req[k] for k in
                                     ("id", "statut", "data_kind", "opensource",
                                      "maquette", "outil") if k in req}}}

    # ── Intention générale : moteur réel de SOL, signature de Laplace ────
    from cosmos import sol
    r = sol.chat(m)
    r["speaker"] = "laplace"
    r["via"] = "✳ Laplace (interlocuteur principal) · ☉ SOL approuve"
    return r
