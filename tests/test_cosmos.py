"""
Tests du système COSMOS (SOL, Vénus, bus, grand livre) — 100 % hors-ligne.

Lancement : python -m pytest tests/ -v
"""

import os
import sys
from pathlib import Path

os.environ["AGENT_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from cosmos import ledger, venus, sol
from cosmos.bodies import BODIES, celestial_registry
from cosmos.system import get_system, clear_mission, complete_mission


@pytest.fixture(scope="module", autouse=True)
def wired():
    get_system()   # câble le bus + SOL une seule fois
    return get_system()


# ── Registre des corps ──────────────────────────────────────────────────────

def test_registre_corps_complet():
    for bid in ("sol", "uranus", "venus", "user"):
        assert bid in BODIES
    reg = celestial_registry()
    assert any(b["id"] == "sol" and b["kind"] == "star" for b in reg)


def test_satellites_ordonnes_zeta_premier():
    sats = BODIES["uranus"]["satellites"]
    assert sats[0]["id"] == "zeta"
    dists = [s["distance_km"] for s in sats]
    assert dists == sorted(dists), "les satellites doivent être ordonnés du plus proche au plus lointain"
    assert len(sats) == 7


def test_venus_cour_sans_lunes():
    """Vénus n'a pas de lunes : sa cour est constituée des Charites + Éros."""
    court = BODIES["venus"]["court"]
    assert {c["id"] for c in court} >= {"thalie", "euphrosyne", "aglae"}


# ── Grand livre (Thalie) ────────────────────────────────────────────────────

def test_grand_livre_record_et_agregats():
    before = ledger.aggregate()["entries"]
    ledger.record(agent="uranus", action="skill:test", model="regles")
    after = ledger.aggregate()
    assert after["entries"] == before + 1
    assert after["spend_today"] >= 0.0


def test_grille_tarifaire_et_estimation():
    # gpt-4o-mini : 0.15 $/1M in, 0.60 $/1M out
    assert ledger.cost_of("gpt-4o-mini", 1_000_000, 0) == pytest.approx(0.15)
    assert ledger.cost_of("gpt-4o-mini", 0, 1_000_000) == pytest.approx(0.60)
    assert ledger.cost_of("regles", 999_999, 999_999) == 0.0
    est = ledger.estimate_mission_cost("analyser les méta-analyses attention")
    assert est["tokens_in"] > 0 and est["cost_usd"] > 0


# ── Vénus : budget, garde-fous, prévisions ──────────────────────────────────

def test_venus_garde_fou_budget():
    venus.set_caps(daily_cap_usd=1.0, per_mission_cap_usd=0.25)
    ok, _ = venus.check_mission(0.01)
    assert ok
    ok, raison = venus.check_mission(5.0)
    assert not ok and "cap par mission" in raison


def test_venus_prevision_et_conseils():
    f = venus.forecast(days=7)
    assert len(f["projection_cumulee"]) == 7
    assert "monthly_projection_usd" in f
    assert isinstance(venus.advise(), list) and venus.advise()


def test_venus_status_complet():
    st = venus.status()
    for k in ("budget", "spend_today_usd", "forecast", "advice", "pricing"):
        assert k in st


# ── Bus d'interactions + approbation SOL ────────────────────────────────────

def test_bus_refuse_corps_inconnu():
    bus = get_system()["bus"]
    msg = bus.send("pluton", "uranus", "mission", {"task": "x"})
    assert msg.status == "denied" and "corps inconnu" in msg.reason


def test_bus_refuse_auto_interaction():
    bus = get_system()["bus"]
    msg = bus.send("venus", "venus", "query", {})
    assert msg.status == "denied"


def test_bus_journalise_tout():
    bus = get_system()["bus"]
    n0 = len(bus.history(limit=200))
    bus.send("user", "venus", "query", {})
    assert len(bus.history(limit=200)) == n0 + 1


def test_refus_budgetaire_via_sol():
    """Une mission avec un coût estimé dépassant les caps est refusée par SOL sur conseil de Vénus."""
    bus = get_system()["bus"]
    msg = bus.send("sol", "uranus", "mission",
                   {"task": "mission très coûteuse", "execute": False,
                    "cost_estimate_usd": 99.0})
    assert msg.status == "denied" and "budgétaire" in msg.reason


# ── Intégrité et état système ───────────────────────────────────────────────

def test_integrite_calculee():
    integ = sol.integrity()
    assert integ["statut"] in {"stable", "vigilance", "alerte"}
    assert 0 <= integ["score"] <= 100
    assert isinstance(integ["alertes"], list)


def test_system_state_structure():
    st = sol.system_state()
    assert "corps" in st and "integrite" in st and "budget" in st
    assert any(b["id"] == "zeta" for b in st["corps"][0].get("satellites", [])
               if isinstance(st["corps"][0], dict) and "satellites" in st["corps"][0]) or True
    # vérification directe via le registre
    uranus = next(b for b in st["corps"] if b["id"] == "uranus")
    assert any(s["id"] == "zeta" for s in uranus["satellites"])


# ── Chat SOL ────────────────────────────────────────────────────────────────

def test_chat_intents():
    assert sol.detect_intent("état du système") == "etat"
    assert sol.detect_intent("où en est le budget ?") == "budget"
    assert sol.detect_intent("montre-moi les interactions") == "interactions"
    assert sol.detect_intent("décris la constellation") == "constellation"
    assert sol.detect_intent("mission : valider la base") == "mission"
    assert sol.detect_intent("bonjour") in {"aide", "inconnu"}


def test_chat_reponses_ancrées():
    r = sol.chat("état du système")
    assert "intégrité" in r["reply"].lower() or "système" in r["reply"].lower()
    r = sol.chat("constellation")
    assert "Zêta" in r["reply"] and "Vénus" in r["reply"]
    r = sol.chat("budget")
    assert "Vénus" in r["reply"]


def test_chat_mission_transmise_a_uranus():
    r = sol.chat("mission : valider la base")
    assert r["intent"] == "mission" and r["data"].get("ok") is True
    trace = r["data"]["trace"]
    assert trace["statut"] in {"succès", "partiel"}
    assert trace["gouvernement"]["source"] == "sol"


# ── Uranus gouverné ─────────────────────────────────────────────────────────

def test_uranus_run_gouverne():
    """Un run direct d'Uranus passe par SOL (approbation) et alimente le grand livre."""
    from agent import Agent
    entries0 = ledger.aggregate()["entries"]
    bus = get_system()["bus"]
    inter0 = len(bus.history(limit=300))
    trace = Agent(use_llm=False).run("valider la base")
    assert trace["gouvernement"] is not None          # contraintes reçues
    assert ledger.aggregate()["entries"] > entries0   # étapes journalisées
    assert len(bus.history(limit=300)) == inter0 + 1  # mission user→uranus approuvée
    last = bus.history(limit=1)[0]
    assert last["source"] == "user" and last["target"] == "uranus" and last["status"] == "delivered"


def test_clear_mission_contraintes():
    c = clear_mission("rechercher l'attention", use_llm=False)
    assert c["gouverne"] is True and c["allow_llm"] is False


# ── API web ─────────────────────────────────────────────────────────────────

def test_api_cosmos():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert c.get("/sol").status_code == 200
    assert "SOL" in c.get("/sol").text
    assert c.get("/api/cosmos/bodies").status_code == 200
    st = c.get("/api/cosmos/state").json()
    assert "integrite" in st
    assert c.get("/api/cosmos/interactions").status_code == 200
    assert "spend_today_usd" in c.get("/api/cosmos/budget").json()
    chat = c.post("/api/cosmos/chat", json={"message": "état du système"})
    assert chat.status_code == 200 and "intent" in chat.json()
    # mise à jour des caps
    upd = c.post("/api/cosmos/budget", json={"daily_cap_usd": 2.5})
    assert upd.status_code == 200 and upd.json()["daily_cap_usd"] == 2.5
    venus.set_caps(daily_cap_usd=1.0)   # restaurer


# ── Constellations de connaissances ─────────────────────────────────────────

def test_knowledge_graphs_par_corps():
    from cosmos.knowledge import knowledge_graph
    for bid, min_nodes in [("uranus", 30), ("zeta", 8), ("venus", 15),
                           ("thalie", 3), ("sol", 8), ("titania", 5)]:
        g = knowledge_graph(bid)
        assert g and len(g["nodes"]) >= min_nodes, f"{bid} trop pauvre"
        assert all("source" in l and "target" in l for l in g["links"])


def test_knowledge_graph_corps_inconnu():
    from cosmos.knowledge import knowledge_graph
    assert knowledge_graph("pluton") is None


def test_zeta_graph_contient_ses_concepts():
    from cosmos.knowledge import knowledge_graph
    g = knowledge_graph("zeta")
    labels = " ".join(n["label"] for n in g["nodes"])
    assert "Neurosciences" in labels and "HUD" in labels


# ── Papier scientifique généré ──────────────────────────────────────────────

def test_pipeline_meta_analyse_genere_papier():
    r = sol.chat("mission : méta-analyse sur l'attention 2024-2026, génère le papier scientifique")
    assert r["intent"] == "mission" and r["data"]["ok"]
    arts = [a["name"] for a in r["data"]["artifacts"]]
    assert "paper.md" in arts and "paper_documentation.md" in arts
    tr = r["data"]["trace"]
    assert any(s["skill"] == "write_paper" and s["ok"] for s in tr["steps"])
    from pathlib import Path as P
    paper = P(tr["steps"][-1]["artifacts"][0])
    content = paper.read_text(encoding="utf-8")
    for section in ("Résumé", "Méthodologie", "Résultats", "Discussion", "Références"):
        assert section in content


# ── Dossier stratégique (cas BTP) ───────────────────────────────────────────

def test_dossier_btp_complet():
    msg = ("je veux améliorer l'infrastructure du btp avec l'ia : administratif automatisé, "
           "puis visière hud sur terrain, puis robotique et chantiers autonomes")
    r = sol.chat(msg)
    assert r["intent"] == "dossier" and r["data"]["ok"]
    arts = [a["name"] for a in r["data"]["artifacts"]]
    assert "dossier_plan.md" in arts and "dossier_graph.json" in arts and "dossier.md" in arts
    step = next(s for s in r["data"]["trace"]["steps"] if s["skill"] == "build_dossier")
    assert step["data"]["phases"] == [1, 2, 3]          # crescendo détecté
    assert step["data"]["graph_nodes"] >= 15
    assert r["data"]["graph"] and r["data"]["graph"].endswith("dossier_graph.json")


def test_plan_btp_detecte_les_trois_phases():
    from agent.skills.build_dossier import _detect_phases
    assert _detect_phases("administratif puis visière hud puis robotique autonome") == [1, 2, 3]
    assert _detect_phases("de la bureautique") == [1]


# ── API connaissances ───────────────────────────────────────────────────────

def test_api_knowledge():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/api/cosmos/knowledge/uranus")
    assert r.status_code == 200 and len(r.json()["nodes"]) >= 30
    assert c.get("/api/cosmos/knowledge/zeta").status_code == 200
    assert c.get("/api/cosmos/knowledge/pluton").status_code == 404
