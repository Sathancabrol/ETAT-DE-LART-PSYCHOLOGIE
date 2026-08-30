"""
Câblage du système : bus + SOL + Vénus + Uranus.

`get_system()` retourne le singleton. Il expose :
  • clear_mission(task)  — approbation SOL + contraintes Vénus avant une
    mission d'Uranus (utilisé par agent/core/agent.py) ;
  • charge_step(...)     — journalisation d'une étape au grand livre ;
  • complete_mission(..) — clôture (coût réel vs estimé).

Uranus devient ainsi gouverné : il reçoit l'aide de Vénus et accepte ses
contraintes (bascule moteur à règles, réduction de portée) ; SOL journalise
tout et juge l'intégrité.
"""

from __future__ import annotations

import threading
from typing import Any, Dict

from cosmos import ledger, sol, venus
from cosmos.bus import Bus, Message

_lock = threading.Lock()
_state: Dict[str, Any] = {"bus": None, "wired": False}


def _uranus_handler(msg: Message) -> Any:
    """Exécute une mission Uranus transmise par le bus (déjà approuvée).

    payload.execute=False → simple approbation/journalisation, l'exécution
    est faite par l'Agent appelant (cas d'une mission lancée par l'utilisateur
    via la CLI/web d'Uranus, pour éviter la double exécution).
    """
    if not msg.payload.get("execute", True):
        return {"approuve": True, "note": "mission approuvée — exécution directe par Uranus"}
    from agent import Agent
    task = msg.payload.get("task", "")
    est = msg.payload.get("estimation", {})
    llm_allowed, max_results = _constraints(est)
    agent = Agent(max_results=max_results, use_llm=llm_allowed if llm_allowed else False)
    _state["in_bus_mission"] = True
    try:
        trace = agent.run(task)
        trace["gouvernement"] = {"message_id": msg.id, "source": msg.source,
                                 "contraintes": {"llm_allowed": llm_allowed,
                                                 "max_results": max_results}}
        return trace
    finally:
        _state["in_bus_mission"] = False


def _venus_handler(msg: Message) -> Any:
    """Vénus traite un rapport de coûts ou une demande de devis."""
    if msg.type == "cost_report":
        entry = ledger.record(agent=msg.source, action=msg.payload.get("action", "run"),
                              model=msg.payload.get("model", "regles"),
                              tokens_in=msg.payload.get("tokens_in", 0),
                              tokens_out=msg.payload.get("tokens_out", 0))
        return {"recorded": entry["cost_usd"]}
    if msg.type == "query":
        return venus.status()
    return {"ack": True}


def _constraints(est: Dict[str, Any]) -> tuple:
    """Vénus fixe les contraintes de la mission (aide + limites)."""
    from agent.core import llm as llm_mod
    st = llm_mod.llm_status()
    llm_allowed = bool(st["available"])
    if llm_allowed and est:
        ok, _ = venus.check_mission(est.get("cost_usd", 0))
        llm_allowed = ok
    max_results = 10
    return llm_allowed, max_results


def get_system() -> Dict[str, Any]:
    """Singleton du système (initialisation paresseuse, thread-safe)."""
    with _lock:
        if _state["bus"] is None:
            bus = Bus()
            sol.bind_bus(bus)
            bus.on("uranus", _uranus_handler)
            bus.on("venus", _venus_handler)
            _state["bus"] = bus
        return _state


# ── Interface consommée par Uranus (gouverneur optionnel) ──────────────────

def clear_mission(task: str, use_llm: bool) -> Dict[str, Any]:
    """Appelé par Agent.run avant exécution. Retourne les contraintes."""
    sysdict = get_system()
    if sysdict.get("in_bus_mission"):
        # Mission déjà approuvée par SOL via le bus — ne pas re-soumettre.
        return {"gouverne": True, "allow_llm": use_llm, "max_results": None, "via": "bus"}
    est = ledger.estimate_mission_cost(task) if use_llm else None
    msg = sysdict["bus"].send("user", "uranus", "mission",
                              {"task": task, "execute": False,
                               "cost_estimate_usd": est["cost_usd"] if est else 0.0,
                               "estimation": est or {}})
    if msg.status in {"denied", "failed"}:
        return {"gouverne": True, "allow_llm": False, "max_results": 5,
                "raison": msg.reason, "via": "sol"}
    llm_allowed, max_results = _constraints(est or {})
    return {"gouverne": True, "allow_llm": llm_allowed and use_llm,
            "max_results": max_results, "via": "sol"}


def charge_step(skill: str, ok: bool, duration_s: float, degraded: bool) -> None:
    """Journalise une étape de mission au grand livre (Thalie)."""
    ledger.record(agent="uranus", action=f"skill:{skill}", model="regles",
                  meta={"ok": ok, "duree_s": duration_s, "degrade": degraded})


def complete_mission(run_id: str, statut: str, steps: int, tokens_in: int = 0,
                     tokens_out: int = 0, model: str = "regles") -> None:
    ledger.record(agent="uranus", action=f"mission:{run_id}", model=model,
                  tokens_in=tokens_in, tokens_out=tokens_out,
                  meta={"statut": statut, "etapes": steps})
