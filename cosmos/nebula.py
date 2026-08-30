"""
LAPLACE ✳ — nébuleuse du savoir (créateur) et SEBAS ◉ (exécutant capteurs).

Laplace est le niveau au-dessus de SOL : il crée des agents à tous les
niveaux (satellites, analystes, planètes), peut engendrer des systèmes
solaires complets supplémentaires, les modifier, les améliorer et les
tester. Le registre dynamique est persistant (output/cosmos/nebula.json)
et fusionné au registre des corps (bodies.known_body_ids).

Sebas est l'homme de terrain de Laplace : il est connecté à des capteurs
(webcam, wifi, téléphone). En l'absence de matériel (sandbox), les
interfaces sont déclarées « prêtes — périphérique non détecté » ; chaque
observation reçue est versée à la mémoire du système.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from cosmos import ledger

NEBULA_PATH = ledger.COSMOS_DIR / "nebula.json"

VALID_KINDS = {"satellite", "analyste", "planet", "agent", "star"}
# Parents valides : tous les corps de premier niveau du registre (planètes,
# créateurs, étoile) — dynamique, donc les futures planètes sont incluses.
def _valid_parents_base() -> set:
    try:
        from cosmos.bodies import BODIES
        return {k for k in BODIES if k != "user"}
    except Exception:
        return {"sol", "uranus", "venus", "mars", "laplace", "sebas"}

VALID_PARENTS_BASE = _valid_parents_base()

SENSORS: List[Dict[str, str]] = [
    {"id": "webcam", "label": "Webcam", "icon": "📷",
     "desc": "Flux vidéo — analyse d'images, de scènes et de chantiers."},
    {"id": "wifi", "label": "WiFi / réseau", "icon": "📶",
     "desc": "Scan réseau — équipements connectés, qualité de lien, présence."},
    {"id": "telephone", "label": "Téléphone", "icon": "📱",
     "desc": "Mobile — notifications, SMS, capteurs embarqués (GPS, accéléromètre)."},
]


# ── Registre ────────────────────────────────────────────────────────────────

def _load() -> Dict[str, Any]:
    if NEBULA_PATH.exists():
        try:
            return json.loads(NEBULA_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"agents": [], "systems": [{"id": "cognitorium", "name": "Cognitorium",
                                       "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                       "star": "sol", "createur": "laplace"}]}


def _save(data: Dict[str, Any]) -> None:
    ledger.COSMOS_DIR.mkdir(parents=True, exist_ok=True)
    NEBULA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "agent"


def list_agents() -> List[Dict[str, Any]]:
    return _load()["agents"]


def list_systems() -> List[Dict[str, Any]]:
    return _load()["systems"]


def get_agent(agent_id: str) -> Dict[str, Any] | None:
    return next((a for a in _load()["agents"] if a["id"] == agent_id), None)


def create_agent(name: str, role: str, parent: str = "uranus",
                 kind: str = "satellite", system: str = "cognitorium") -> Dict[str, Any]:
    """Laplace crée un agent (satellite/analyste/planète/agent libre)."""
    name = name.strip()[:60]
    if not name:
        raise ValueError("nom requis")
    if kind not in VALID_KINDS:
        raise ValueError(f"kind invalide : {kind} (attendu parmi {sorted(VALID_KINDS)})")
    known_parents = VALID_PARENTS_BASE | {a["id"] for a in list_agents()}
    if parent not in known_parents:
        raise ValueError(f"parent inconnu : {parent}")
    data = _load()
    base = _slug(name)
    aid, n = base, 2
    while any(a["id"] == aid for a in data["agents"]):
        aid = f"{base}-{n}"
        n += 1
    agent = {"id": aid, "name": name, "symbol": "✦",
             "role": (role or "Agent créé par Laplace — rôle à préciser.")[:300],
             "kind": kind, "parent": parent, "system": system,
             "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "tests": 0, "statut": "actif", "createur": "laplace"}
    data["agents"].append(agent)
    _save(data)
    ledger.record(agent="laplace", action=f"create_agent:{aid}", model="regles",
                  meta={"name": name, "parent": parent, "kind": kind})
    return agent


def improve_agent(agent_id: str, role: str | None = None, name: str | None = None) -> Dict[str, Any]:
    """Modifie / améliore un agent existant du registre dynamique."""
    data = _load()
    agent = next((a for a in data["agents"] if a["id"] == agent_id), None)
    if agent is None:
        raise ValueError(f"agent inconnu : {agent_id}")
    if role:
        agent["role"] = role[:300]
    if name:
        agent["name"] = name.strip()[:60]
    agent["ameliorations"] = agent.get("ameliorations", 0) + 1
    agent["version"] = 1 + agent["ameliorations"]
    _save(data)
    ledger.record(agent="laplace", action=f"improve_agent:{agent_id}", model="regles")
    return agent


def create_system(name: str, star_name: str = "SOL-jumeau") -> Dict[str, Any]:
    """Laplace engendre un système solaire complet supplémentaire."""
    name = name.strip()[:60]
    if not name:
        raise ValueError("nom requis")
    data = _load()
    base = _slug(name)
    sid, n = base, 2
    while any(s["id"] == sid for s in data["systems"]):
        sid = f"{base}-{n}"
        n += 1
    system = {"id": sid, "name": name, "star": star_name[:40], "star_name": star_name[:40],
              "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "createur": "laplace", "agents": []}
    data["systems"].append(system)
    _save(data)
    ledger.record(agent="laplace", action=f"create_system:{sid}", model="regles",
                  meta={"name": name})
    return system


def test_agent(agent_id: str) -> Dict[str, Any]:
    """Test d'un agent : message de test via le bus (approbation SOL incluse)."""
    from cosmos.bodies import known_body_ids
    if agent_id not in known_body_ids():
        return {"ok": False, "raison": f"agent inconnu : {agent_id}"}
    from cosmos.system import get_system
    sysdict = get_system()
    msg = sysdict["bus"].send("laplace", agent_id, "test",
                              {"contenu": "ping — test d'intégrité Laplace"})
    data = _load()
    agent = next((a for a in data["agents"] if a["id"] == agent_id), None)
    if agent is not None:
        agent["tests"] = agent.get("tests", 0) + 1
        agent["dernier_test"] = msg.ts
        agent["dernier_statut"] = msg.status
        _save(data)
    return {"ok": msg.status in {"approved", "delivered"},
            "statut": msg.status, "raison": msg.reason,
            "message_id": msg.id}


# ── Sebas : capteurs & observations ─────────────────────────────────────────

def sensors_status() -> List[Dict[str, Any]]:
    """État des capteurs de Sebas. Sans matériel branché : interface prête,
    périphérique non détecté (honnêteté du système — jamais de fausses données)."""
    out = []
    for s in SENSORS:
        out.append({**s, "connecte": False,
                    "statut": "interface prête — périphérique non détecté (démonstration)"})
    return out


def record_observation(sensor: str, contenu: str, tags: List[str] | None = None) -> Dict[str, Any]:
    """Sebas verse une observation de capteur à la mémoire partagée."""
    if not any(s["id"] == sensor for s in SENSORS):
        raise ValueError(f"capteur inconnu : {sensor}")
    if not (contenu or "").strip():
        raise ValueError("contenu requis")
    from cosmos import memory
    item = memory.record_item("memoire", f"[{sensor}] observation terrain",
                              contenu=contenu.strip()[:2000],
                              tags=[sensor] + (tags or [])[:5],
                              source="sebas", corps="sebas",
                              meta={"sensor": sensor})
    ledger.record(agent="sebas", action=f"observation:{sensor}", model="regles",
                  meta={"item": item["id"]})
    return item
