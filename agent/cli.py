"""
CLI de l'agent chercheur.

Usage :
    python -m agent run "rechercher les méta-analyses attention 2024-2026"
    python -m agent run "valider la base et calculer le trust" --no-llm
    python -m agent run "..." --dry-run        # affiche le plan sans exécuter
    python -m agent skills                     # catalogue des compétences
    python -m agent runs                       # historique des runs
    python -m agent status                     # cerveau LLM disponible ?
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agent.core.agent import Agent
from agent.core.context import RUNS_DIR
from agent.core import llm as llm_mod
from agent.core.registry import list_skills

CATEGORY_ICON = {"recherche": "🔎", "donnees": "🗃️", "qualite": "🛡️",
                 "synthese": "📝", "veille": "🔔", "general": "⚙️"}


def cmd_run(args):
    agent = Agent(max_results=args.max_results, use_llm=(False if args.no_llm else None))
    if args.dry_run:
        plan = agent.plan(args.task)
        print(f"🧠 Cerveau : {plan.brain} — {plan.rationale}\n")
        for i, s in enumerate(plan.steps, 1):
            print(f"  {i}. {s.skill}  {json.dumps(s.params, ensure_ascii=False)}")
            print(f"     └ {s.reason}")
        return 0
    print(f"▶ Exécution de la tâche : « {args.task} »\n")
    trace = agent.run(args.task)
    print(f"\n{'='*70}")
    for s in trace["steps"]:
        mark = "✅" if s["ok"] else "❌"
        print(f"{mark} {s['n']}. {s['skill']} — {s['summary']} ({s['duration_s']} s)")
        for d in s.get("details", [])[:5]:
            print(f"     {d}")
    print(f"{'='*70}")
    run_dir = RUNS_DIR / trace["run_id"]
    print(f"\n📊 Statut : {trace['statut']} | durée {trace['duree_s']}s | cerveau {trace['cerveau']}")
    print(f"📁 Rapport complet : {run_dir / 'report.md'}")
    return 0 if trace["statut"] in {"succès", "partiel"} else 1


def cmd_skills(_args):
    st = llm_mod.llm_status()
    print("🧠 Cerveau LLM : " + ("activé (%s, %s)" % (st["provider"], st["model"]) if st["available"] else "non configuré → règles déterministes"))
    print(f"\n📚 {len(list_skills())} compétences enregistrées :\n")
    by_cat = {}
    for s in list_skills():
        by_cat.setdefault(s.category, []).append(s)
    for cat, skills in by_cat.items():
        print(f"{CATEGORY_ICON.get(cat, '⚙️')}  {cat.upper()}")
        for s in skills:
            print(f"   • {s.name:<20} {s.description}")
            if s.examples:
                print(f"     ex : {s.examples[0]}")
        print()
    return 0


def cmd_runs(_args):
    if not RUNS_DIR.exists():
        print("Aucun run enregistré.")
        return 0
    runs = sorted(RUNS_DIR.iterdir(), reverse=True)
    print(f"🗂️  {len(runs)} run(s) dans {RUNS_DIR.relative_to(RUNS_DIR.parents[1])}\n")
    for r in runs[:20]:
        tj = r / "trace.json"
        if tj.exists():
            t = json.loads(tj.read_text(encoding="utf-8"))
            mark = {"succès": "✅", "partiel": "⚠️", "échec": "❌"}.get(t["statut"], "❔")
            print(f"{mark} {t['run_id']}  [{t['cerveau']}] {t['tache'][:60]}")
            print(f"   └ {len(t['steps'])} étapes, {t['duree_s']}s → {r / 'report.md'}")
    return 0


def cmd_status(_args):
    st = llm_mod.llm_status()
    print(json.dumps(st, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="agent", description="Agent scientifique chercheur — Cognitorium")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="exécuter une tâche")
    pr.add_argument("task", help="tâche en langue naturelle (FR)")
    pr.add_argument("--max-results", type=int, default=10, help="résultats max par base (défaut 10)")
    pr.add_argument("--no-llm", action="store_true", help="forcer le cerveau à règles")
    pr.add_argument("--dry-run", action="store_true", help="afficher le plan sans exécuter")
    pr.set_defaults(fn=cmd_run)

    ps = sub.add_parser("skills", help="lister les compétences")
    ps.set_defaults(fn=cmd_skills)

    pu = sub.add_parser("runs", help="historique des runs")
    pu.set_defaults(fn=cmd_runs)

    pst = sub.add_parser("status", help="disponibilité du cerveau LLM")
    pst.set_defaults(fn=cmd_status)

    args = p.parse_args(argv)
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
