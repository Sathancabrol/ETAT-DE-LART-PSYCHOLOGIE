#!/usr/bin/env bash
# Amorçage de l'environnement du système Cognitorium (SOL · Uranus · Vénus)
# Usage : bash scripts/bootstrap.sh
set -e
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "→ Création du venv…"
  python3 -m venv .venv
fi
echo "→ Installation des dépendances…"
.venv/bin/pip install -q fastapi uvicorn requests pandas jinja2 python-multipart httpx pytest
echo "→ Tests (hors-ligne)…"
AGENT_OFFLINE=1 .venv/bin/python -m pytest tests/ -q
echo
echo "✅ Environnement prêt :"
echo "   • Console Uranus :  .venv/bin/python -m agent run \"valider la base\""
echo "   • Serveur web     : .venv/bin/python -m uvicorn app.main:app  → http://localhost:8000/sol"
