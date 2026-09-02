"""
Grand livre des coûts du système (tenu par Thalie, comptable de Vénus).

Chaque action d'un agent y est journalisée avec : moteur utilisé (règles
ou LLM), tokens entrée/sortie (réels si l'API les renvoie, estimés sinon),
et coût en USD selon la grille tarifaire.

Sans LLM actif, le coût réel est 0 — mais Vénus calcule aussi le coût
*estimé* qu'aurait occasionné la même mission avec un LLM, pour éclairer
les décisions.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
COSMOS_DIR = ROOT / "output" / "cosmos"
LEDGER_PATH = COSMOS_DIR / "ledger.jsonl"
MAX_LINES = 5000  # rotation simple

# Grille tarifaire indicative (USD / 1M tokens, entrée / sortie).
# À vérifier périodiquement auprès des fournisseurs.
PRICING: Dict[str, tuple] = {
    "regles": (0.0, 0.0),
    "ollama-local": (0.0, 0.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "claude-sonnet-4": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
}

APPROX_TOKENS_PER_CHAR = 0.25  # ~4 caractères / token


def cost_of(model: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRICING.get(model, (0.0, 0.0))
    return round(tokens_in / 1e6 * pin + tokens_out / 1e6 * pout, 6)


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) * APPROX_TOKENS_PER_CHAR))


def estimate_mission_cost(task: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Estimation a priori du coût LLM d'une mission (plan + rédaction)."""
    tin = 900 + estimate_tokens(task)          # prompt système + catalogue + tâche
    tout = 700 + estimate_tokens(task) // 2    # plan + rédaction
    return {"model": model, "tokens_in": tin, "tokens_out": tout,
            "cost_usd": cost_of(model, tin, tout)}


def record(agent: str, action: str, model: str = "regles",
           tokens_in: int = 0, tokens_out: int = 0,
           cost_usd: float | None = None, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent": agent, "action": action, "model": model,
        "tokens_in": int(tokens_in), "tokens_out": int(tokens_out),
        "cost_usd": cost_of(model, tokens_in, tokens_out) if cost_usd is None else round(cost_usd, 6),
        "meta": meta or {},
    }
    COSMOS_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    if LEDGER_PATH.exists():
        lines = LEDGER_PATH.read_text(encoding="utf-8").splitlines()
    lines.append(json.dumps(entry, ensure_ascii=False))
    if len(lines) > MAX_LINES:
        lines = lines[-MAX_LINES:]
    LEDGER_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return entry


def read_ledger() -> List[Dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    out = []
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def aggregate() -> Dict[str, Any]:
    """Agrégats pour Vénus : dépenses du jour, du mois, par agent/modèle."""
    entries = read_ledger()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    month = today[:7]
    by_day: Dict[str, float] = {}
    by_agent: Dict[str, float] = {}
    by_model: Dict[str, float] = {}
    tokens = {"in": 0, "out": 0}
    for e in entries:
        d = e["ts"][:10]
        by_day[d] = round(by_day.get(d, 0.0) + e["cost_usd"], 6)
        if d == today:
            by_agent[e["agent"]] = round(by_agent.get(e["agent"], 0.0) + e["cost_usd"], 6)
            by_model[e["model"]] = round(by_model.get(e["model"], 0.0) + e["cost_usd"], 6)
            tokens["in"] += e["tokens_in"]
            tokens["out"] += e["tokens_out"]
    month_spend = round(sum(v for d, v in by_day.items() if d.startswith(month)), 6)
    return {
        "entries": len(entries),
        "spend_today": round(by_day.get(today, 0.0), 6),
        "spend_month": month_spend,
        "tokens_today": tokens,
        "by_day": dict(sorted(by_day.items())[-14:]),
        "by_agent_today": by_agent,
        "by_model_today": by_model,
        "last_entry_age_s": (time.time() - _parse_ts(entries[-1]["ts"])) if entries else None,
    }


def _parse_ts(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return time.time()
