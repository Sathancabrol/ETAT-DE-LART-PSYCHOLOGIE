#!/usr/bin/env python3
"""CLI de l'agent de recherche littéraire.

Exemples :
    python -m agent.cli "métacognition et apprentissage autorégulé" --demo
    python -m agent.cli "effet de l'exercice sur les fonctions exécutives" --from-year 2020 --max 12
    AGENT_PROVIDER=ollama AGENT_MODEL=llama3 python -m agent.cli "..."
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from .config import AgentConfig
from .pipeline import run_research


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent de recherche littéraire scientifique (Cognitorium)")
    parser.add_argument("topic", help="Question ou sujet de recherche")
    parser.add_argument("--from-year", type=int, default=2020)
    parser.add_argument("--to-year", type=int, default=2026)
    parser.add_argument("--max", type=int, default=8, help="Nombre max d'articles retenus")
    parser.add_argument("--demo", action="store_true", help="Mode démo hors-ligne (fixtures réelles embarquées)")
    parser.add_argument("--out", default=None, help="Dossier de sortie (défaut: output/agent_reports/<slug>_<ts>)")
    parser.add_argument("--provider", choices=["none", "openai", "ollama"], default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    cfg = AgentConfig.from_env()
    if args.provider:
        cfg.provider = args.provider
    if args.model:
        cfg.model = args.model
    if cfg.provider == "openai" and not cfg.api_key:
        print("⚠️  AGENT_PROVIDER=openai mais aucune clé (AGENT_API_KEY / OPENAI_API_KEY) → repli heuristique.",
              file=sys.stderr)
        cfg.provider = "none"

    summary = run_research(
        topic=args.topic,
        year_min=args.from_year,
        year_max=args.to_year,
        max_papers=args.max,
        cfg=cfg,
        demo=args.demo,
        out_dir=args.out,
    )

    print("\n" + "=" * 72)
    print(f"🧠 Sujet          : {summary['topic']}")
    print(f"⚙️  Mode d'analyse : {summary['mode']}{' (démo hors-ligne)' if summary['demo'] else ''}")
    print(f"📚 Articles       : {summary['papers']} — Trust moyen {summary['trust_avg']}/100")
    print(f"🏆 Meilleur       : {summary['top_paper']}")
    print(f"⏱  Durée          : {summary['duration_s']} s")
    print("📁 Livrables :")
    for label, path in summary["files"].items():
        print(f"   - {label:<18} {path}")
    print("=" * 72 + "\n")
    print(json.dumps(summary["prisma"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
