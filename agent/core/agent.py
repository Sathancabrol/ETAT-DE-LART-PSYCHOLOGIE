"""
Orchestrateur de l'agent chercheur.

Cycle : tâche → plan (règles, éventuellement affiné par LLM) →
exécution séquentielle des compétences (état partagé) → traçabilité
complète (trace.json + report.md dans output/agent_runs/<run_id>/).

Chaque exécution est : déterministe par défaut, traçable (artefacts
horodatés), dégradable (hors-ligne signalé), stoppée proprement sur
erreur d'une compétence sans casser le run entier.
"""

from __future__ import annotations

import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from agent.core import llm as llm_mod
from agent.core.context import AgentContext, ROOT
from agent.core.planner import Plan, build_plan
from agent.core.registry import catalog, get_skill, list_skills


class Agent:
    """Agent scientifique chercheur du Cognitorium."""

    def __init__(self, max_results: int = 10, use_llm: Optional[bool] = None, timeout: int = 15):
        self.max_results = max_results
        self.use_llm = use_llm  # None = auto (si clé dispo)
        self.timeout = timeout

    # ── Planification ──────────────────────────────────────────────────────

    def plan(self, task: str) -> Plan:
        plan = build_plan(task)
        status = llm_mod.llm_status()
        want_llm = self.use_llm if self.use_llm is not None else status["available"]
        if want_llm and status["available"]:
            llm_steps = llm_mod.plan_with_llm(task, catalog())
            if llm_steps:
                from agent.core.planner import Step
                plan = Plan(steps=[Step(s["skill"], s["params"], s["reason"]) for s in llm_steps],
                            brain="llm",
                            rationale=f"plan LLM ({status['provider']}/{status['model']}), validé contre le registre")
        return plan

    # ── Exécution ──────────────────────────────────────────────────────────

    def run(self, task: str, dry_run: bool = False) -> Dict[str, Any]:
        started = time.time()
        ctx = AgentContext(max_results=self.max_results, timeout=self.timeout)
        ctx.state["task"] = task

        plan = self.plan(task)

        steps_report: List[Dict[str, Any]] = []
        if not dry_run:
            for i, step in enumerate(plan.steps, start=1):
                spec = get_skill(step.skill)
                entry: Dict[str, Any] = {"n": i, "skill": step.skill,
                                         "description": spec.description if spec else "",
                                         "reason": step.reason, "params": step.params}
                t0 = time.time()
                try:
                    result = spec.fn(ctx, **step.params)
                    entry.update(result.to_dict())
                except Exception as e:
                    entry.update({"ok": False, "summary": f"erreur d'exécution : {e}",
                                  "degraded": False, "details": [traceback.format_exc(limit=3)],
                                  "artifacts": [], "data": {}})
                entry["duration_s"] = round(time.time() - t0, 2)
                steps_report.append(entry)

        duration = round(time.time() - started, 2)
        ok_steps = sum(1 for s in steps_report if s.get("ok"))
        status = "succès" if steps_report and ok_steps == len(steps_report) else (
            "partiel" if ok_steps else ("planifié" if dry_run else "échec"))

        # Trace JSON complète
        trace = {
            "run_id": ctx.run_id,
            "date": datetime.now(timezone.utc).isoformat(),
            "tache": task,
            "cerveau": plan.to_dict()["brain"],
            "rationale": plan.rationale,
            "llm": llm_mod.llm_status(),
            "statut": status,
            "duree_s": duration,
            "mode_degrade": ctx.offline_hits > 0,
            "plan": plan.to_dict(),
            "steps": steps_report,
        }
        ctx.save_json("trace.json", trace)

        # Rapport markdown lisible
        if not dry_run:
            report = _build_report(task, trace)
            ctx.save_md("report.md", report)

        return trace


def _build_report(task: str, trace: Dict[str, Any]) -> str:
    icon = {"succès": "✅", "partiel": "⚠️", "échec": "❌", "planifié": "📋"}
    lines = [
        "# Rapport d'exécution — Agent Chercheur Cognitorium", "",
        f"- **Tâche** : {task}",
        f"- **Statut** : {icon.get(trace['statut'], '')} {trace['statut']}",
        f"- **Cerveau** : {trace['cerveau']}" + (f" ({trace['llm']['provider']}/{trace['llm']['model']})" if trace['cerveau'] == 'llm' else " — déterministe"),
        f"- **Durée** : {trace['duree_s']} s",
        f"- **Run** : `{trace['run_id']}`",
    ]
    if trace["mode_degrade"]:
        lines.append("- **⚠️ Mode dégradé** : une ou plusieurs compétences ont utilisé des fixtures "
                     "de démonstration (réseau indisponible). Les données correspondantes ne sont PAS réelles.")
    lines += ["", "## Plan exécuté", ""]
    for s in trace["steps"]:
        mark = "✅" if s["ok"] else "❌"
        lines.append(f"{s['n']}. {mark} **{s['skill']}** — {s['summary']} ({s['duration_s']} s)")
    lines += ["", "## Détail par compétence", ""]
    for s in trace["steps"]:
        lines += [f"### {s['n']}. {s['skill']}", "", f"*{s['description']}*", "",
                  f"→ {s['summary']}", ""]
        for d in s.get("details", [])[:12]:
            lines.append(f"- {d}")
        if s.get("artifacts"):
            lines += ["", "**Artefacts :**"]
            lines += [f"- `{a}`" for a in s["artifacts"]]
        lines.append("")
    lines += ["---", "*Généré automatiquement par l'agent chercheur — traçabilité complète dans `trace.json`.*"]
    return "\n".join(lines)
