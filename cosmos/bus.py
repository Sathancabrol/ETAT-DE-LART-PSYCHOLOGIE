"""
Bus d'interactions du système — toute communication entre corps célestes
passe par ici et DOIT être approuvée par SOL avant d'être délivrée.

Chaque message est journalisé (output/cosmos/interactions.jsonl) :
source, cible, type, charge, statut (approuvé/refusé), raison, durée.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from cosmos import ledger

INTERACTIONS_PATH = ledger.COSMOS_DIR / "interactions.jsonl"
MAX_LINES = 5000
RATE_LIMIT = 60           # messages / fenêtre
RATE_WINDOW_S = 300       # fenêtre de 5 min


@dataclass
class Message:
    id: str
    ts: str
    source: str
    target: str
    type: str                        # mission | cost_report | alert | query | constraint | info
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"          # pending | approved | denied | delivered | failed
    reason: str = ""
    duration_s: float = 0.0
    result: Any = None

    def to_log(self) -> Dict[str, Any]:
        d = asdict(self)
        d["result"] = _slim(self.result)
        return d


def _slim(result: Any, limit: int = 600) -> Any:
    if isinstance(result, str) and len(result) > limit:
        return result[:limit] + "…"
    if isinstance(result, dict):
        return {k: _slim(v, 200) for k, v in list(result.items())[:12]}
    return result


class Bus:
    """Bus à approbation SOL. `approver(message) -> (ok, raison)`."""

    def __init__(self) -> None:
        self.approver: Optional[Callable[[Message], tuple]] = None
        self.handlers: Dict[str, Callable[[Message], Any]] = {}

    def set_approver(self, approver: Callable[[Message], tuple]) -> None:
        self.approver = approver

    def on(self, target: str, handler: Callable[[Message], Any]) -> None:
        """Enregistre le traitement des messages destinés à `target`."""
        self.handlers[target] = handler

    def send(self, source: str, target: str, type_: str,
             payload: Dict[str, Any] | None = None) -> Message:
        msg = Message(id=uuid.uuid4().hex[:10],
                      ts=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      source=source, target=target, type=type_,
                      payload=payload or {})
        t0 = time.time()
        # 1. Approbation SOL
        if self.approver is not None:
            ok, reason = self.approver(msg)
        else:
            ok, reason = True, "aucun approbateur configuré"
        if not ok:
            msg.status, msg.reason = "denied", reason
            self._log(msg)
            return msg
        msg.status, msg.reason = "approved", reason
        # 2. Délivrance
        handler = self.handlers.get(target)
        if handler is not None:
            try:
                msg.result = handler(msg)
                msg.status = "delivered"
            except Exception as e:
                msg.status, msg.reason = "failed", f"erreur handler : {e}"
        else:
            msg.status = "delivered"
            msg.reason = (msg.reason + " ; " if msg.reason else "") + "aucun handler — journalisé"
        msg.duration_s = round(time.time() - t0, 3)
        self._log(msg)
        return msg

    def _log(self, msg: Message) -> None:
        ledger.COSMOS_DIR.mkdir(parents=True, exist_ok=True)
        lines = []
        if INTERACTIONS_PATH.exists():
            lines = INTERACTIONS_PATH.read_text(encoding="utf-8").splitlines()
        lines.append(json.dumps(msg.to_log(), ensure_ascii=False))
        if len(lines) > MAX_LINES:
            lines = lines[-MAX_LINES:]
        INTERACTIONS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def history(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not INTERACTIONS_PATH.exists():
            return []
        out = []
        for line in INTERACTIONS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        out.reverse()
        return out

    def recent_count(self, window_s: int = RATE_WINDOW_S) -> int:
        now = time.time()
        return sum(1 for m in self.history(limit=200)
                   if m.get("status") in {"approved", "delivered"}
                   and (now - _ts_age(m.get("ts", ""))) < window_s)


def _ts_age(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0
