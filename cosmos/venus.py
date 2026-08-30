"""
VÉNUS ♀ — planète des finances, de la valeur et du bien-être.

Rôles :
  • comptabilité des requêtes (tokens / coûts) via le grand livre ;
  • garde-fous budgétaires (caps journalier / par mission / mensuel) ;
  • prévisions de dépenses et de rentrées (projection linéaire) ;
  • arbitrage : recommandations pour optimiser le rendement d'Uranus.

Ses analystes (la cour des Charites) : Thalie (comptabilité), Euphrosyne
(arbitrage), Aglaé (prévisions), Éros (contrats).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from cosmos import ledger

BUDGET_PATH = ledger.COSMOS_DIR / "budget.json"

DEFAULT_BUDGET: Dict[str, Any] = {
    "currency": "USD",
    "daily_cap_usd": 1.0,       # plafond de dépense LLM par jour
    "per_mission_cap_usd": 0.25,  # plafond par mission
    "monthly_cap_usd": 20.0,     # plafond mensuel
    "income_monthly_usd": 0.0,   # rentrées éventuelles (crédits, offres gratuites)
}


def load_budget() -> Dict[str, Any]:
    if BUDGET_PATH.exists():
        try:
            data = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
            return {**DEFAULT_BUDGET, **data}
        except Exception:
            pass
    return dict(DEFAULT_BUDGET)


def save_budget(budget: Dict[str, Any]) -> Dict[str, Any]:
    ledger.COSMOS_DIR.mkdir(parents=True, exist_ok=True)
    BUDGET_PATH.write_text(json.dumps(budget, ensure_ascii=False, indent=2), encoding="utf-8")
    return budget


def set_caps(daily_cap_usd: float | None = None, per_mission_cap_usd: float | None = None,
             monthly_cap_usd: float | None = None, income_monthly_usd: float | None = None) -> Dict[str, Any]:
    b = load_budget()
    if daily_cap_usd is not None:
        b["daily_cap_usd"] = max(0.0, float(daily_cap_usd))
    if per_mission_cap_usd is not None:
        b["per_mission_cap_usd"] = max(0.0, float(per_mission_cap_usd))
    if monthly_cap_usd is not None:
        b["monthly_cap_usd"] = max(0.0, float(monthly_cap_usd))
    if income_monthly_usd is not None:
        b["income_monthly_usd"] = max(0.0, float(income_monthly_usd))
    return save_budget(b)


def check_mission(est_cost_usd: float) -> Tuple[bool, str]:
    """Garde-fou : une mission prévue à X $ est-elle finançable ?"""
    b = load_budget()
    agg = ledger.aggregate()
    if est_cost_usd > b["per_mission_cap_usd"]:
        return False, (f"coût estimé ({est_cost_usd:.4f} $) > cap par mission "
                       f"({b['per_mission_cap_usd']:.2f} $) — réduire la portée ou le modèle")
    if agg["spend_today"] + est_cost_usd > b["daily_cap_usd"]:
        return False, (f"cap journalier atteint ({agg['spend_today']:.4f} + {est_cost_usd:.4f} $ "
                       f"> {b['daily_cap_usd']:.2f} $) — mission LLM refusée, bascule règles")
    if agg["spend_month"] + est_cost_usd > b["monthly_cap_usd"]:
        return False, f"cap mensuel presque atteint ({agg['spend_month']:.4f} $)"
    return True, "budget ok"


def forecast(days: int = 7) -> Dict[str, Any]:
    """Projection linéaire de la dépense sur N jours (Aglaé)."""
    agg = ledger.aggregate()
    by_day = agg["by_day"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    spend_today = agg["spend_today"]
    if len(by_day) >= 2:
        known = [d for d in by_day if d < today]
        last7 = [by_day[d] for d in sorted(known)[-7:]] or [spend_today]
        daily_avg = sum(last7) / len(last7)
        basis = "moyenne des 7 derniers jours actifs"
    else:
        daily_avg = spend_today
        basis = "dépense du jour (historique court)"
    b = load_budget()
    projection = [round(daily_avg * (i + 1), 4) for i in range(days)]
    horizon_dates = [(datetime.now(timezone.utc) + timedelta(days=i + 1)).strftime("%Y-%m-%d")
                     for i in range(days)]
    runout = None
    if daily_avg > 0 and b["daily_cap_usd"] > 0:
        runout = f"rythme {daily_avg:.4f} $/jour vs cap {b['daily_cap_usd']:.2f} $/jour"
    return {"daily_avg_usd": round(daily_avg, 6), "basis": basis,
            "projection_cumulee": projection, "dates": horizon_dates,
            "monthly_projection_usd": round(daily_avg * 30, 4),
            "monthly_cap_usd": b["monthly_cap_usd"],
            "income_monthly_usd": b["income_monthly_usd"],
            "net_monthly_usd": round(b["income_monthly_usd"] - daily_avg * 30, 4),
            "runout": runout}


def advise() -> List[str]:
    """Recommandations d'Euphrosyne pour optimiser les rendements."""
    agg = ledger.aggregate()
    b = load_budget()
    tips: List[str] = []
    if agg["spend_today"] >= 0.8 * b["daily_cap_usd"]:
        tips.append("Dépense du jour ≥ 80 % du cap : basculer les missions non critiques "
                    "sur le moteur à règles (coût nul) ou un modèle léger (haiku/4o-mini).")
    if agg["by_model_today"].get("gpt-4o", 0) or agg["by_model_today"].get("claude-sonnet-4", 0):
        tips.append("Des missions utilisent un modèle premium : réserver aux synthèses "
                    "finales, planifier avec des modèles légers.")
    if agg["entries"] and agg["spend_today"] == 0:
        tips.append("Moteur à règles actif : coût nul — c'est le régime optimal pour "
                    "l'exploration massive ; n'activer le LLM que pour la rédaction experte.")
    if b["income_monthly_usd"] <= 0:
        tips.append("Aucune rentrée configurée : crédits API gratuits / offres étudiants "
                    "peuvent être déclarés via income_monthly_usd.")
    tips.append("Uranus : limiter max_results par base (10→5) divise le coût d'extraction "
                "sans dégrader la couverture des méta-analyses majeures.")
    return tips[:5]


def status() -> Dict[str, Any]:
    agg = ledger.aggregate()
    b = load_budget()
    return {
        "budget": b,
        "spend_today_usd": agg["spend_today"],
        "spend_month_usd": agg["spend_month"],
        "tokens_today": agg["tokens_today"],
        "by_agent_today": agg["by_agent_today"],
        "by_model_today": agg["by_model_today"],
        "by_day": agg["by_day"],
        "forecast": forecast(),
        "advice": advise(),
        "pricing": {k: {"in_per_m": v[0], "out_per_m": v[1]} for k, v in ledger.PRICING.items()},
    }
