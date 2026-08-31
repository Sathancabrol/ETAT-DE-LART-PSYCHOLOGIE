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

from cosmos import mars, metatron

TOOL_RE = re.compile(
    r"\boutil\b|armurer|maquette|forge?r?\b|phobos|deimos|\bmars\b|"
    r"calcul(er|ez)?\b.*\bvisualis|visualis.*\bcalcul", re.IGNORECASE)

# « armurerie » seul = inventaire ; accompagné d'un vrai besoin = routage outil
INVENTORY_RE = re.compile(r"\barmurerie\b|\binventaire\b|outils?\s+disponibles",
                          re.IGNORECASE)
NEED_WORDS = re.compile(r"calcul|visualis|besoin|pour\s|donne|cr[ée]{1,2}|forge|maquette",
                        re.IGNORECASE)


# enfers / corbeille → Underworld 🔥 (royaume d'Hadès)
INFERNO_RE = re.compile(r"enfers?|underworld|inferno|tartare|[ée]lys[ée]es|asphod|cerb|[cç]erbère|pers[ée]phone|corbeille|r[ée]suscit", re.IGNORECASE)

# justice / équilibre → Thémis ⚖ (bras armé de Laplace)
THEMIS_RE = re.compile(r"th[ée]mis|justice|balance|équilibre|jugement|\bjuge\b|divine justice", re.IGNORECASE)

# commandes divines → Sebas ◉ ; chariot → Apollon
SEBAS_RE = re.compile(r"\bsebas\b|commande\s+divine|ord(on|re)\s+(à|a|de)", re.IGNORECASE)
CHARIOT_RE = re.compile(r"chariot|divination|pr[ée]sage|oracle|apollon|pr[ée]vi(s|tion)", re.IGNORECASE)

HADES_RE = re.compile(r"fauch(e|age)|nettoy|purge|redondan|junk|obsol[èe]te|outdated|"
                      r"optimis.*\b(espace|m[ée]moire)\b|aux\s+enfers|had[èe]s|pluton|"
                      r"\bmoires?\b|anank|[ée]ligib|condamn|scan\s+(de\s+|le\s+|l')?"
                      r"(had|pluton|syst)", re.IGNORECASE)
PROFIL_RE = re.compile(r"mon\s+profil|profil\s+cognitif|qui\s+suis.?je|mes\s+informations|"
                       r"mes\s+donn[ée]es\s+cognitiv", re.IGNORECASE)


def chat(message: str) -> Dict[str, Any]:
    """Réponse de Laplace ✳ — délègue l'état réel au moteur de SOL, route les outils vers Mars."""
    m = (message or "").strip()
    if not m:
        return {"reply": "✳ Laplace vous écoute.", "intent": "vide",
                "speaker": "laplace", "data": {}}

    # ✦ Métatron pré-analyse chaque requête (méta-prompting)
    try:
        analyse = metatron.analyze_request(m)
    except Exception:
        analyse = None

    # ── Enfers → le royaume d'Hadès (rien ne disparaît vraiment) ─────────
    if INFERNO_RE.search(m):
        from cosmos import underworld as uw
        st = uw.state()
        lignes = [f"🔥 {st['royaume']}", st["loi"]]
        for rid, r in st["regions"].items():
            n = st["par_region"].get(rid, 0)
            lignes.append(f"• {r['icon']} {r['nom']} : {n} âme(s) — {r['desc']}")
        lignes.append(f"Total : {st['ames_total']} âmes · {st['octets_au_royaume']:,} octets au royaume.".replace(",", " "))
        lignes.append("Ouvre le bouton 🔥 INFERNO dans /sol pour voir le registre et ressusciter une âme (Cerbère 🐾 exigera ton accord).")
        return {"reply": "\n".join(lignes), "intent": "inferno", "speaker": "laplace",
                "data": {"par_region": st["par_region"], "ames": st["ames_total"]}}

    # ── Justice → Thémis ⚖ juge, conseille, et tranche le cas échéant ────
    if THEMIS_RE.search(m):
        from cosmos import themis
        if re.search(r"applique|tranche|ex[ée]cute|d[ée]truis|fauche", m, re.IGNORECASE):
            r = themis.appliquer(confirm=True)
            return {"reply": r["statut"], "intent": "justice_appliquee",
                    "speaker": "laplace", "data": {"fauche": r.get("fauche")}}
        a = themis.audit()
        lignes = [a["verdict"]]
        for mn in a["menaces"]:
            lignes.append(f"• [{mn['gravite']}] {mn['quoi']} — remède : {mn['remede']} ({mn['par']})")
        lignes += ["⚖ Constitution de Thémis (comme la démocratie) :"]
        lignes += [f"  {c['organe']} ({c['pouvoir']}) — {c['loi_vivante']}" for c in a["constitution"]]
        lignes.append("Dis « Thémis, applique la justice » pour qu'elle ordonne la fauche "
                      "(rien n'est détruit sans votre accord).")
        return {"reply": "\n".join(lignes), "intent": "justice", "speaker": "laplace",
                "data": {"menaces": a["menaces"], "gravite": a["gravite"]}}

    # ── Commande divine → Sebas ◉ exécute ─────────────────────────────────
    if SEBAS_RE.search(m):
        from cosmos import sebas
        ordre = re.sub(r"^\s*(sebas\s*,?\s*)?", "", m, flags=re.IGNORECASE).strip() or m
        r = sebas.execute(ordre, agent="user")
        return {"reply": r["reponse"] + "\n— exécution d'une commande divine (◉ Sebas, "
                "exécutant de ✳ Laplace), approuvée par ☉ SOL.",
                "intent": "commande_divine", "speaker": "laplace",
                "data": {"action": r["action"]}}

    # ── Chariot d'Apollon → divination ────────────────────────────────────
    if CHARIOT_RE.search(m):
        from cosmos import apollon
        d = apollon.divination(m)
        lignes = ["🏆 Le chariot d'Apollon traverse le système et prononce :"]
        for p in d["presages"]:
            icon = {"bon": "🟢", "moyen": "🟡", "mauvais": "🔴"}[p["ton"]]
            lignes.append(f"{icon} {p['titre']} — {p['lecture']}. Oracle : {p['oracle']}.")
        lignes.append(d["verdict"])
        return {"reply": "\n".join(lignes), "intent": "divination", "speaker": "laplace",
                "data": {"presages": d["presages"]}}

    # ── Intention FAUCHE → Hadès ♇ scanne et fauche ──────────────────────
    if HADES_RE.search(m):
        from cosmos import hades
        sc = hades.scan_system()
        st = sc["stats"]
        mo = sc["moires"]
        reply = ("♇ Hadès ⧉ secondé par les 3 Moires a inspecté tout le système :\n"
                 f"• {st['condamnes']} condamnés ({st['ko']} Ko) — "
                 + ", ".join(f"{v} {k}" for k, v in st["par_type"].items()) + ".\n"
                 f"• Traitement des données ({st['mo_octets']} Mo vus) : "
                 + " → ".join(t["etape"] for t in sc["traitement"]) + ".\n"
                 f"• 🧵 Clotho : {mo['clotho']['naissance_24h']} naissance(s)/24 h · "
                 f"📏 Lachésis : {mo['lachesis']['age_moyen_runs_jours']} j d'âge moyen · "
                 f"✂️ Atropos : {mo['atropos']['condamnes']} condamné(s).\n"
                 f"• 🪙 Prévision tokens épargnés par la fauche : {sc['prevision_tokens']['estime']:,} tokens" \
                 f" (ratio 1 token ≈ 4 octets — estimation, pas un compteur réel).\n"
                 f"• Politique de Styx ☠ : garder les {hades.POLITIQUE['runs_gardes']} runs les plus "
                 f"récents, faucher le surplus, les doublons et le junk.\n"
                 "• Dis « lance la fauche » (ou bouton ♇ dans /sol) et Charon ⚰ exécute réellement.")
        if re.search(r"fauche(r|z|s)?\b|ex[ée]cute\b|vas.y|d[ée]truis", m, re.IGNORECASE):
            r = hades.reap(confirm=True)
            reply = (f"♇ La fauche est exécutée — {r['supprimes']} condamnés envoyés aux enfers, "
                     f"{round(r['octets_liberes']/1024, 1)} Ko libérés. "
                     "Le cycle peut repartir plus léger.")
        return {"reply": reply, "intent": "fauche", "speaker": "laplace",
                "data": {"hades": {"stats": st}}}

    # ── Intention PROFIL → profil cognitif induit ────────────────────────
    if PROFIL_RE.search(m):
        from cosmos import cogniprofile
        pr = cogniprofile.build_profile()
        dims = " · ".join(f"{d['label']} {d['valeur']}" for d in pr["dimensions"])
        reply = ("✦ Votre profil cognitif (induit de vos interactions) :\n"
                 f"• {dims}\n" + "\n".join("• " + t for t in pr["traits"][:3])
                 + "\n• Vue complète : console /agent → onglet 🧠 Profil.\n"
                 "⚠️ Heuristiques statistiques — pas un test psychométrique validé.")
        return {"reply": reply, "intent": "profil", "speaker": "laplace",
                "data": {"profil": {d["id"]: d["valeur"] for d in pr["dimensions"]}}}

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
                                      "maquette", "outil") if k in req},
                         "metatron": analyse}}

    # ── Intention générale : moteur réel de SOL, signature de Laplace ────
    from cosmos import sol
    r = sol.chat(m)
    r["speaker"] = "laplace"
    r["via"] = "✳ Laplace (interlocuteur principal) · ☉ SOL approuve"
    if analyse:
        r["data"] = r.get("data") or {}
        r["data"]["metatron"] = analyse
    return r
