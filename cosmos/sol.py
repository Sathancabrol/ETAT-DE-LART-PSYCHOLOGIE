"""
SOL ☉ — orchestrateur général du système.

Responsabilités :
  • APPROBATION : toute interaction entre corps passe par SOL (politique :
    corps connus, limite de débit, garde-fou budgétaire via Vénus) ;
  • INTÉGRITÉ : juge le système à partir des interactions (taux d'échec,
    débit, burn rate budgétaire, part de mode dégradé) → statut stable /
    vigilance / alerte, avec alertes préventives ;
  • PRÉVOIR & PRÉVENIR : projette les dépenses (via Vénus) et remonte les
    dérives avant qu'elles ne surviennent ;
  • INTERFACE : chat déterministe ancré sur les données réelles du système
    (état, budget, interactions, constellation) — un LLM peut être branché
    en option pour enrichir la rédaction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from cosmos import ledger, venus
from cosmos.bodies import BODIES, celestial_registry
from cosmos.bus import Bus, Message

# ────────────────────────── Politique d'approbation ──────────────────────────

def approve(msg: Message) -> Tuple[bool, str]:
    """Politique SOL : corps connus + débit + budget."""
    if msg.source not in BODIES or msg.target not in BODIES:
        return False, f"corps inconnu dans l'échange {msg.source}→{msg.target}"
    if msg.source == msg.target:
        return False, "auto-interaction interdite"
    # Débit (prévention saturation)
    if _bus and _bus.recent_count() > 60:
        return False, "limite de débit atteinte (60 interactions / 5 min) — ralentir"
    # Budget pour les missions coûteuses
    est = msg.payload.get("cost_estimate_usd")
    if est:
        ok, reason = venus.check_mission(float(est))
        if not ok:
            return False, f"refus budgétaire (Vénus) : {reason}"
    return True, "politique SOL satisfaite"


_bus: Optional[Bus] = None


def bind_bus(bus: Bus) -> None:
    global _bus
    _bus = bus
    bus.set_approver(approve)


# ────────────────────────── Intégrité du système ──────────────────────────

def integrity() -> Dict[str, Any]:
    """Jugement d'intégrité : erreurs réelles, refus de politique, budget, mode dégradé.

    NB : un refus (`denied`) est la politique qui fonctionne (garde-fou),
    pas un échec ; seules les erreurs d'exécution (`failed`) pèsent sur
    le taux d'échec.
    """
    interactions = _bus.history(limit=200) if _bus else []
    total = len(interactions)
    failed = sum(1 for m in interactions if m.get("status") == "failed")
    denied = sum(1 for m in interactions if m.get("status") == "denied")
    denied_budget = sum(1 for m in interactions if "budgétaire" in (m.get("reason") or ""))
    agg = ledger.aggregate()
    budget = venus.load_budget()
    burn = (agg["spend_today"] / budget["daily_cap_usd"]) if budget["daily_cap_usd"] else 0
    degraded_share = 0.0
    for m in interactions:
        res = m.get("result")
        if isinstance(res, dict) and res.get("mode_degrade"):
            degraded_share += 1
    degraded_share = round(degraded_share / total, 2) if total else 0.0

    score = 100
    alerts: List[str] = []
    if total:
        fail_rate = failed / total
        score -= int(min(40, fail_rate * 100))
        if fail_rate > 0.2:
            alerts.append(f"Taux d'erreur élevé des interactions : {fail_rate:.0%}")
        if denied / total > 0.5:
            alerts.append(f"Beaucoup de refus de politique ({denied}/{total}) — vérifier la "
                          "cohérence des demandes ou assouplir les caps")
    else:
        fail_rate = 0.0
    if burn >= 0.8:
        alerts.append(f"Burn rate budgétaire : {burn:.0%} du cap journalier déjà consommé")
        score -= 15
    if degraded_share >= 0.5 and total >= 3:
        alerts.append(f"Mode dégradé fréquent ({degraded_share:.0%} des missions) — "
                      "vérifier l'accès réseau aux bases scientifiques")
        score -= 10
    if denied_budget >= 3:
        alerts.append("Plusieurs missions refusées pour budget : revoir les caps ou la portée des missions")

    status = "stable" if score >= 85 and not alerts else ("vigilance" if score >= 60 else "alerte")
    return {"score": max(0, score), "statut": status, "interactions_total": total,
            "taux_echec": round(fail_rate, 2), "taux_refus": round(denied / total, 2) if total else 0.0,
            "burn_rate_budget": round(burn, 2),
            "part_mode_degrade": degraded_share, "alertes": alerts}


def system_state() -> Dict[str, Any]:
    integ = integrity()
    ven = venus.status()
    interactions = _bus.history(limit=10) if _bus else []
    return {
        "corps": celestial_registry(),
        "integrite": integ,
        "budget": {"spend_today_usd": ven["spend_today_usd"],
                   "daily_cap_usd": ven["budget"]["daily_cap_usd"],
                   "forecast_month_usd": ven["forecast"]["monthly_projection_usd"]},
        "interactions_recentes": [
            {"ts": m.get("ts"), "source": m.get("source"), "target": m.get("target"),
             "type": m.get("type"), "status": m.get("status"),
             "raison": (m.get("reason") or "")[:120]} for m in interactions],
        "ledger_entries": ven["by_day"] and ledger.aggregate()["entries"] or 0,
    }


# ────────────────────────── Chat SOL (interface utilisateur) ──────────────

INTENTS = [
    ("dossier", r"dossier|strat[ée]gie|roadmap|am[ée]liorer|impl[ée]menter|int[ée]grer|int[ée]gration|transform|organiser|d[ée]ployer|mise\s+en\s+place"),
    ("etat", r"[ée]tat|syst[èe]me|int[ée]grit|status|sant|comment va"),
    ("budget", r"budget|co[uû]t|d[ée]pense|argent|token|tarif|prix|financ|pr[ée]voi|projection|rentre"),
    ("interactions", r"interaction|message|historique|[ée]change|journal|activit"),
    ("constellation", r"constellation|plan[èe]te|satellite|lune|corps|agent|z[êe]ta|v[ée]nus|uranus|cour|analyste"),
    ("mission", r"mission|recherch|cherche|analyse|synth[ée]tis|[ée]tudie"),
    ("aide", r"aide|help|que (peux|sais)|capacit|comment .*(utiliser|marche)"),
]


def _mission_artifacts(trace: Dict[str, Any]) -> list:
    """Collecte les artefacts produits par les étapes d'une mission."""
    arts = []
    for s in trace.get("steps", []):
        for a in s.get("artifacts", []) or []:
            name = a.split("/")[-1]
            icon = "📄"
            if a.endswith("_graph.json"):
                icon = "🗺️"
            elif a.endswith(".json"):
                icon = "🧾"
            elif a.endswith(".csv"):
                icon = "📊"
            elif a.endswith(".html"):
                icon = "🖥️"
            arts.append({"path": a, "name": name, "icon": icon, "skill": s.get("skill")})
    return arts


def detect_intent(message: str) -> str:
    m = message.lower()
    for intent, pattern in INTENTS:
        if re.search(pattern, m):
            return intent
    return "inconnu"


def chat(message: str) -> Dict[str, Any]:
    """Réponse déterministe de SOL, ancrée sur les données réelles."""
    # Mémoire évolutive : chaque question enrichit la base du système
    try:
        from cosmos import memory
        memory.record_question(message)
    except Exception:
        pass
    intent = detect_intent(message)
    data: Dict[str, Any] = {}

    if intent == "etat":
        st = system_state()
        integ = st["integrite"]
        icons = {"stable": "🟢", "vigilance": "🟡", "alerte": "🔴"}
        reply = (f"{icons.get(integ['statut'], '⚪')} Système {integ['statut']} (score d'intégrité {integ['score']}/100).\n"
                 f"• {len(st['corps'])} corps enregistrés (2 planètes, leurs satellites et leur cour, SOL, vous).\n"
                 f"• Interactions journalisées : {integ['interactions_total']} (taux d'échec {integ['taux_echec']:.0%}).\n"
                 f"• Budget du jour : {st['budget']['spend_today_usd']:.4f} / {st['budget']['daily_cap_usd']:.2f} $.\n"
                 f"• Projection mensuelle : {st['budget']['forecast_month_usd']:.2f} $.")
        if integ["alertes"]:
            reply += "\n⚠️ Alertes préventives :\n" + "\n".join(f"  - {a}" for a in integ["alertes"])
        data = st

    elif intent == "budget":
        v = venus.status()
        f = v["forecast"]
        reply = (f"♀ Vénus rapporte — comptabilité du système :\n"
                 f"• Dépense aujourd'hui : {v['spend_today_usd']:.4f} $ (cap {v['budget']['daily_cap_usd']:.2f} $) "
                 f"| mois : {v['spend_month_usd']:.4f} $ (cap {v['budget']['monthly_cap_usd']:.2f} $)\n"
                 f"• Tokens consommés aujourd'hui : {v['tokens_today']['in']} entrée / {v['tokens_today']['out']} sortie\n"
                 f"• Projection 7 jours : {f['projection_cumulee'][-1]:.4f} $ cumulés ({f['basis']})\n"
                 f"• Projection mensuelle : {f['monthly_projection_usd']:.2f} $ "
                 f"| rentrées configurées : {v['budget']['income_monthly_usd']:.2f} $/mois\n"
                 f"• Modèle le plus économique : moteur à règles (0 $) — réservé à l'exploration massive.")
        if v["advice"]:
            reply += "\n⚖️ Arbitrage d'Euphrosyne :\n" + "\n".join(f"  - {a}" for a in v["advice"][:3])
        data = v

    elif intent == "interactions":
        hist = _bus.history(limit=12) if _bus else []
        reply = f"☰ {len(hist)} dernières interactions (toutes approuvées par SOL) :"
        for m in hist:
            mark = {"delivered": "✅", "approved": "✔︎", "denied": "⛔", "failed": "❌"}.get(m.get("status"), "•")
            reply += (f"\n{mark} {m.get('ts', '')[11:19]} {m.get('source', '')}→{m.get('target', '')} "
                      f"[{m.get('type')}] {(m.get('reason') or '')[:60]}")
        if not hist:
            reply += "\n(aucune interaction encore journalisée)"
        data = {"interactions": hist}

    elif intent == "constellation":
        lines = ["✦ Constellation du système :"]
        for b in celestial_registry():
            if b["kind"] == "star":
                lines.append(f"☉ SOL (centre) — {b['role']}")
            elif b["kind"] == "planet":
                sat = b.get("satellites") or []
                court = b.get("court") or []
                sub = sat or court
                label = "satellites" if sat else "cour d'analystes"
                lines.append(f"{b['symbol']} {b['name']} — {b['role'][:80]}…")
                if sub:
                    lines.append(f"   {label} : " + ", ".join(s["name"] for s in sub))
        reply = "\n".join(lines)
        data = {"corps": celestial_registry()}

    elif intent == "mission":
        task = _extract_task(message)
        if not task:
            reply = ("Pour lancer une mission : « mission : rechercher les méta-analyses "
                     "sur l'attention 2024-2026 ». Uranus et ses satellites s'en chargeront, "
                     "sous contraintes de Vénus.")
        else:
            result = launch_mission(task)
            if result.get("ok"):
                tr = result["trace"]
                arts = _mission_artifacts(tr)
                steps = [f"✅ {s['skill']} — {s['summary'][:80]}" for s in tr.get("steps", []) if s.get("ok")]
                steps += [f"❌ {s['skill']} — {s['summary'][:80]}" for s in tr.get("steps", []) if not s.get("ok")]
                reply = (f"♅ Mission Uranus accomplie ({tr.get('statut')}, run {tr.get('run_id')}):\n"
                         + "\n".join(steps[:8])
                         + f"\nRapport complet : output/agent_runs/{tr.get('run_id')}/report.md")
                if any(a["name"].startswith("paper") for a in arts):
                    reply += ("\n📄 Le système a généré un PAPIER SCIENTIFIQUE de synthèse "
                              "et sa documentation — cliquez ci-dessous pour les consulter.")
                if arts:
                    reply += "\n📁 Documents produits (cliquables) :\n" + \
                        "\n".join(f"  {a['icon']} {a['name']}" for a in arts[:8])
                result["artifacts"] = arts
                result["graph"] = next((a["path"] for a in arts if a["name"].endswith("_graph.json")), None)
            else:
                reply = f"⛔ Mission refusée : {result.get('raison')}"
            data = result

    elif intent == "dossier":
        task = _extract_task(message) or message.strip()
        result = launch_mission(f"dossier : {task}")
        if result.get("ok"):
            tr = result["trace"]
            arts = _mission_artifacts(tr)
            dossier_step = next((s for s in tr.get("steps", []) if s["skill"] == "build_dossier"), None)
            reply = ("☉ Dossier stratégique confié à Uranus — accompli "
                     f"({tr.get('statut')}, run {tr.get('run_id')}) :\n")
            if dossier_step:
                d = dossier_step.get("data") or {}
                reply += f"• Plan en {len(d.get('phases', []))} phases (crescendo organique) : " + \
                    " → ".join(f"Phase {p}" for p in d.get("phases", [])) + "\n"
                reply += f"• {d.get('graph_nodes', 0)} nœuds de feuille de route visualisables\n"
                reply += f"• {d.get('references', 0)} références mobilisées\n"
            if arts:
                reply += "📁 Documents produits (cliquables) :\n" + \
                    "\n".join(f"  {a['icon']} {a['name']}" for a in arts[:8]) + "\n"
            reply += f"Rapport complet : output/agent_runs/{tr.get('run_id')}/report.md"
            result["artifacts"] = arts
            result["graph"] = next((a["path"] for a in arts if a["name"] == "dossier_graph.json"), None)
        else:
            reply = f"⛔ Dossier refusé : {result.get('raison')}"
        data = result

    elif intent == "aide":
        reply = ("☉ Je suis SOL, orchestrateur du système. Je peux :\n"
                 "• vous donner l'état du système et son intégrité — « état du système »\n"
                 "• rendre compte du budget et des coûts tokens — « budget »\n"
                 "• lister les interactions entre corps — « interactions »\n"
                 "• décrire la constellation (Uranus ♅ et ses satellites, Vénus ♀ et sa cour) — « constellation »\n"
                 "• transmettre une mission à Uranus — « mission : <votre tâche> »\n"
                 "Toute interaction entre planètes m'est soumise pour approbation.")
    else:
        reply = ("☉ SOL à l'écoute. Essayez : « état du système », « budget », « interactions », "
                 "« constellation », ou « mission : <tâche pour Uranus> ».")

    return {"reply": reply, "intent": intent, "data": data}


def _extract_task(message: str) -> str:
    m = re.search(r"mission\s*[:\-]?\s*(.+)$", message, re.I)
    if m:
        return m.group(1).strip()
    if re.search(r"mission|recherch|cherche|synth[ée]tis|[ée]tudie|analyse", message, re.I):
        return message.strip()
    return ""


def launch_mission(task: str) -> Dict[str, Any]:
    """SOL transmet la mission à Uranus via le bus (approbation + budget)."""
    if _bus is None:
        return {"ok": False, "raison": "bus non initialisé"}
    est = ledger.estimate_mission_cost(task)
    msg = _bus.send("sol", "uranus", "mission",
                    {"task": task, "cost_estimate_usd": est["cost_usd"],
                     "estimation": est})
    if msg.status in {"denied", "failed"}:
        return {"ok": False, "raison": msg.reason}
    return {"ok": True, "trace": msg.result, "message_id": msg.id}
