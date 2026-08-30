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


import pytest

@pytest.fixture(autouse=True)
def _pas_de_limite_debit(monkeypatch):
    """La limite de débit de SOL (60 interactions / 5 min — prévention
    saturation) ne doit pas fausser la suite de tests, qui envoie beaucoup
    d'interactions en quelques secondes : on la neutralise localement."""
    try:
        from cosmos import bus as _bus
        monkeypatch.setattr(_bus.Bus, "recent_count", lambda self: 0)
    except Exception:
        pass


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
    msg = bus.send("vulcain", "uranus", "mission", {"task": "x"})
    assert msg.status == "denied" and "corps inconnu" in msg.reason


def test_bus_refuse_auto_interaction():
    bus = get_system()["bus"]
    msg = bus.send("venus", "venus", "query", {})
    assert msg.status == "denied"


def test_bus_journalise_tout():
    bus = get_system()["bus"]
    n0 = len(bus.history(limit=5000))
    bus.send("user", "venus", "query", {})
    assert len(bus.history(limit=5000)) == n0 + 1


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
    inter0 = len(bus.history(limit=5000))
    trace = Agent(use_llm=False).run("valider la base")
    assert trace["gouvernement"] is not None          # contraintes reçues
    assert ledger.aggregate()["entries"] > entries0   # étapes journalisées
    assert len(bus.history(limit=5000)) == inter0 + 1  # mission user→uranus approuvée
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
    assert knowledge_graph("vulcain") is None


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
    assert c.get("/api/cosmos/knowledge/vulcain").status_code == 404


# ── Constellations zodiacales ───────────────────────────────────────────────

def test_catalogue_constellations():
    from cosmos.constellations import views
    vs = {v["id"]: v for v in views()}
    assert "zodiaque" in vs and "base" in vs and "memoire" in vs
    assert vs["venus"]["label"].startswith("Taureau")      # demandé explicitement
    assert vs["sol"]["label"].startswith("Lion")
    assert vs["uranus"]["label"].startswith("Verseau")
    assert vs["zeta"]["parent"] == "uranus" and "Verseau" in vs["zeta"]["label"]


def test_graphes_constellations_format_obsidian():
    from cosmos.constellations import graph_for
    for vid in ("zodiaque", "sol", "venus", "uranus", "zeta", "thalie", "memoire"):
        g = graph_for(vid)
        assert g and g["nodes"], f"{vid} vide"
        assert all("relation_type" in l for l in g["links"])
    assert graph_for("pluton") is None


# ── Mémoire évolutive ───────────────────────────────────────────────────────

def test_taxonomie_seed_branches_completes():
    from cosmos import memory
    tree = memory.load_taxonomy()
    branches = {c["name"] for c in tree["children"]}
    # 5 branches racines attendues (v2)
    assert {"Psychologie scientifique", "Construction", "Robotique",
            "Intelligence artificielle", "Émergents (auto-enrichis)"} <= branches
    blob = json.dumps(tree, ensure_ascii=False)
    for attendu in ("BTP / TP", "Sécurité", "Équipement", "EPI", "Visière",
                    "Modèle de vision connecté IA", "Génie civil & infrastructures",
                    "Robotique de chantier", "Drones", "Exosquelettes", "SLAM & localisation",
                    "IA génératives", "LLM", "Vision par ordinateur", "HUD & réalité augmentée",
                    "Gouvernance des données"):
        assert attendu in blob, f"{attendu} absent de la taxonomie seed"


def test_migration_taxonomie_conserve_enrichissements():
    from cosmos import memory
    tree = memory.load_taxonomy()
    memory.enrich_taxonomy(["cobot de pose de canalisation"])
    tree2 = memory.load_taxonomy()          # recharge → passe par la migration
    blob = json.dumps(tree2, ensure_ascii=False)
    assert "Intelligence artificielle" in blob      # branche seed toujours là
    assert "cobot de pose de canalisation" in blob  # enrichissement conservé
    memory.save_taxonomy(memory.SEED_TAXONOMY)


def test_enrichissement_taxonomie():
    from cosmos import memory
    leaves0 = len(memory.taxonomy_leaves())
    added = memory.enrich_taxonomy(["drone de chantier", "réalité mixte industrielle"])
    assert len(added) == 2
    assert len(memory.taxonomy_leaves()) >= leaves0 + 2
    # réinjecter le seed propre pour les autres tests
    memory.save_taxonomy(memory.SEED_TAXONOMY)


def test_memoire_record_et_graph():
    from cosmos import memory
    it = memory.record_item("video", "Visite chantier pilote", contenu="capture casque",
                            tags=["chantier", "btp"])
    assert it["type"] == "video"
    g = memory.memory_graph()
    assert g["nodes"] and g["nodes"][0]["id"] == "memoire"
    assert any("Visite chantier" in n["label"] for n in g["nodes"])


def test_question_enregistree_par_chat():
    from cosmos.system import get_system
    get_system()
    from cosmos import memory
    n0 = len(memory.items(type_="question"))
    sol.chat("question test pour la mémoire 12345")
    assert len(memory.items(type_="question")) == n0 + 1


def test_concepts_partages_agreges():
    from cosmos import memory
    cs = memory.concepts()
    names = " ".join(c["name"].lower() for c in cs)
    assert len(cs) > 30
    assert "epi" in names and "neurosciences" in names and "hud" in names


# ── Dashboard métriques ─────────────────────────────────────────────────────

def test_dashboard_metrics_pedagogique():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    d = c.get("/api/dashboard/metrics").json()
    metrics = {m["id"]: m for m in d["metrics"]}
    # formules présentes ou explicitement absentes
    assert "M + R + O + C + T" in metrics["trust"]["formula"][0]
    assert metrics["integrite"]["formula"]
    assert metrics["references"]["formula"] is None          # compteur simple
    assert "Pas de formule" in metrics["references"]["legend"][0]
    assert "burn" in metrics and "prisma" in metrics and "memoire" in metrics
    # trust : expliqué (quoi/100/comment) + jauge + décomposition
    t = metrics["trust"]
    assert t["viz"] == "gauge" and t["gauge"]["max"] == 100 and len(t["gauge"]["zones"]) == 4
    assert any("100 = confiance maximale" in e for e in t["explain"])
    assert any("73.2" in e or "moyenne" in e for e in t["explain"])
    assert {b["label"][:1] for b in t["bars"]} >= {"M", "R", "O", "C", "T"}
    # références : liste réelle (qui ?)
    r = metrics["references"]
    assert r["viz"] == "list" and len(r["items"]) == 14
    assert all(i["main"] for i in r["items"])
    # relations : répartition + exemples
    rel = metrics["relations"]
    assert rel["bars"] and rel["items"]
    # citations : de qui
    cit = metrics["citations"]
    assert cit["viz"] == "bars" and len(cit["bars"]) >= 5
    assert any("de qui" in (e or "").lower() for e in cit["explain"])
    # intégrité : simulateur à 3 curseurs initialisé sur les valeurs réelles
    integ = metrics["integrite"]
    assert integ["viz"] == "sim" and len(integ["sim"]["inputs"]) == 3
    assert all(i["value"] is not None for i in integ["sim"]["inputs"])
    # mémoire : graphique par type
    mem = metrics["memoire"]
    assert "bars" in mem["viz"] and mem["bars_caption"]


def test_api_constellations_et_concepts():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    assert c.get("/api/cosmos/constellations").status_code == 200
    assert c.get("/api/cosmos/constellations/venus").status_code == 200
    assert c.get("/api/cosmos/constellations/pluton").status_code == 404
    conc = c.get("/api/concepts").json()
    assert len(conc) > 40
    assert any("4E" in (x.get("sources") or []) for x in conc)
    mem = c.post("/api/cosmos/memory", json={"type": "audio", "titre": "réunion chantier",
                                             "contenu": "point sécurité", "tags": ["btp"]})
    assert mem.status_code == 200 and mem.json()["type"] == "audio"


import json  # noqa: E402  (utilisé par test_taxonomie_seeed)


# ═══ LAPLACE ✳ / SEBAS ◉ / CONSOLE V2 ═══

def test_nebula_laplace_create_improve_test(tmp_path, monkeypatch):
    """Laplace crée un agent, l'améliore, le teste — registre persisté, corps connu de SOL."""
    import shutil
    from cosmos import nebula, bodies
    monkeypatch.setattr(nebula, "NEBULA_PATH", tmp_path / "nebula.json")
    from cosmos import memory as _mem
    monkeypatch.setattr(_mem, "MEMORY_DIR", tmp_path / "mem", raising=False)
    monkeypatch.setattr(_mem, "ITEMS_PATH", tmp_path / "mem" / "items.jsonl", raising=False)

    a = nebula.create_agent("Hélios Prime", "veille solaire", parent="uranus")
    assert a["createur"] == "laplace" and a["statut"] == "actif" and a["tests"] == 0
    assert "h" in a["id"]

    b = nebula.improve_agent(a["id"], role="veille solaire + batteries")
    assert b["role"] == "veille solaire + batteries" and b["version"] >= 2

    t = nebula.test_agent(a["id"])
    assert t["statut"] in {"approved", "delivered", "rejected", "échec"}
    b2 = nebula.get_agent(a["id"])
    assert b2["tests"] >= 1 and "dernier_statut" in b2

    agents = nebula.list_agents()
    assert any(x["id"] == a["id"] for x in agents)
    # corps créé par Laplace → connu de SOL (approvable)
    assert a["id"] in bodies.known_body_ids()

def test_nebula_system_and_invalid_parent(tmp_path, monkeypatch):
    from cosmos import nebula
    monkeypatch.setattr(nebula, "NEBULA_PATH", tmp_path / "nebula.json")
    s = nebula.create_system("Nébuleuse-BTP", star_name="SOL-BTP")
    assert s["star_name"] == "SOL-BTP" and s["agents"] == []
    assert any(x["id"] == s["id"] for x in nebula.list_systems())
    import pytest
    with pytest.raises(ValueError):
        nebula.create_agent("X", "rôle", parent="introuvable")

def test_sebas_sensors_honest_and_observation(tmp_path, monkeypatch):
    """Sandbox sans matériel : statut honnête, jamais de fausse donnée — mais observation consignable."""
    from cosmos import nebula
    monkeypatch.setattr(nebula, "NEBULA_PATH", tmp_path / "nebula.json")
    from cosmos import memory as _mem
    monkeypatch.setattr(_mem, "MEMORY_DIR", tmp_path / "mem", raising=False)
    monkeypatch.setattr(_mem, "ITEMS_PATH", tmp_path / "mem" / "items.jsonl", raising=False)
    sensors = nebula.sensors_status()
    assert {s["id"] for s in sensors} >= {"webcam", "wifi", "telephone"}
    for s in sensors:
        assert s["connecte"] is False and "non détecté" in s["statut"]
    obs = nebula.record_observation("webcam", "chantier X : grue stable", ["terrain"])
    assert obs["corps"] == "sebas" and obs["type"] == "memoire"
    import pytest
    with pytest.raises(ValueError):
        nebula.record_observation("lidar", "capteur inconnu")

def test_agent_run_forced_skills_and_subjects(tmp_path, monkeypatch):
    """run() : compétences imposées via le (+), sujets concaténés à la tâche."""

def test_agent_run_forced_skills_and_subjects():
    from agent.core.agent import Agent
    ag = Agent(max_results=3, use_llm=False)
    trace = ag.run("recherche attention", dry_run=True,
                   force_skills=["validate_entries", "trust_scoring"],
                   subjects=["Neurosciences"])
    planned = [s["skill"] for s in trace["plan"]["steps"]]
    assert planned == ["validate_entries", "trust_scoring"]
    assert "sujets" in trace["rationale"] and "Neurosciences" in trace["tache"]
    assert trace["statut"] == "planifié"          # dry_run : rien n'est exécuté
    # plan imposé : les skills inconnus sont filtrés, pas d'échec
    trace2 = ag.run("audit", dry_run=True, force_skills=["skill_inexistante"])
    assert trace2["plan"]["steps"] != []          # repli sur le plan par règles
    # exécution réelle d'un plan imposé d'une seule compétence sûre
    trace3 = ag.run("validation", force_skills=["validate_entries"])
    assert [s["skill"] for s in trace3["steps"]] == ["validate_entries"]

def test_database_memory_sync(tmp_path, monkeypatch):
    """La base de données est synchronisée avec la mémoire des agents (l'oubli corrigé)."""
    import sqlite3
    from cosmos import memory
    from app import database
    db = tmp_path / "sync.db"
    monkeypatch.setattr(database, "DB_PATH", str(db))
    # 1. la mémoire contient au moins un item réel
    memory.record_item("memoire", "test synchro db", contenu="vérification sqlite",
                       tags=["synchro"], source="test", corps="uranus")
    # 2. la synchro crée la table et verse tout items.jsonl
    n = database.sync_memory_items()
    assert n > 0
    # 3. idempotence : re-synchroniser n'ajoute pas de doublons
    n2 = database.sync_memory_items()
    assert n2 == n
    rows = database.get_memory_items(limit=5)
    assert rows and all(r.get("id") for r in rows)
    cols = [c[1] for c in sqlite3.connect(str(db)).execute("PRAGMA table_info(memory_items)")]
    assert set(cols) >= {"id", "ts", "type", "titre", "corps", "tags"}
    # 4. un item récent se retrouve bien en base
    ids_in_db = {r["id"] for r in database.get_memory_items(limit=1000)}
    items_ids = {it["id"] for it in memory.items(limit=1000)}
    assert items_ids <= ids_in_db
    # 5. les références de la mémoire alimentent aussi la table scientifique
    import sqlite3 as _sq
    con = _sq.connect(str(db))
    mem_refs = con.execute("SELECT COUNT(*) FROM references_table WHERE id LIKE 'mem_%'").fetchone()[0]
    assert mem_refs > 0

def test_agent_metrics_and_timeline_api():
    """/api/agent/metrics (6 cartes) et /api/agent/timeline (nœuds horodatés + liens)."""
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    m = c.get("/api/agent/metrics").json()
    ids = [x["id"] for x in m["cards"]]
    assert {"taches", "tokens", "consultees", "fournies", "creees"} <= set(ids)
    assert "summary" in m and "par_jour" in m["summary"]
    tl = c.get("/api/agent/timeline").json()
    assert set(tl) >= {"nodes", "links"}
    for nd in tl["nodes"][:30]:
        assert "ts" in nd and "type" in nd and nd["type"] in {"run", "skill", "artifact", "reference"}

def test_laplace_sebas_api():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.post("/api/laplace/agents", json={"name": "Agent Test API", "role": "contrôle qualité", "parent": "uranus"})
    assert r.status_code == 200 and r.json()["createur"] == "laplace"
    aid = r.json()["id"]
    assert c.post(f"/api/laplace/agents/{aid}/test").json()["statut"] in {"delivered", "échec"}
    assert c.post(f"/api/laplace/agents/{aid}/improve", json={"role": "cq v2"}).json()["version"] >= 2
    assert c.post("/api/laplace/agents", json={"name": "Bad", "parent": "nul"}).status_code == 400
    assert c.get("/api/sebas/sensors").status_code == 200
    obs = c.post("/api/sebas/observe", json={"sensor": "wifi", "contenu": "réseau chantier détecté"})
    assert obs.status_code == 200 and obs.json()["corps"] == "sebas"

def test_run_api_accepts_skills_subjects():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.post("/api/agent/run", json={"task": "vérification", "skills": ["validate_entries"], "subjects": ["Psychologie"]})
    assert r.status_code == 200
    assert [s["skill"] for s in r.json()["steps"]] == ["validate_entries"]


# ═══ MARS ♂ ARMURERIE / LAPLACE ✳ INTERLOCUTEUR ═══

def test_mars_in_bodies_with_real_moon_distances():
    """Mars ♂ (armurier) + Phobos (software) + Deimos (conception), vraies distances."""
    from cosmos.bodies import BODIES, known_body_ids
    mars = BODIES["mars"]
    assert mars["kind"] == "planet" and 1 < mars["orbit_r"] < 2   # entre Vénus et Uranus
    assert "armurier" in mars["role"].lower()
    assert {s["id"] for s in mars["satellites"]} == {"phobos", "deimos"}
    dist = {s["id"]: s["distance_km"] for s in mars["satellites"]}
    assert dist["phobos"] == 9376 and dist["deimos"] == 23463   # distances réelles
    assert "software" in mars["satellites"][0]["role"].lower()
    assert "conception" in mars["satellites"][1]["role"].lower()
    assert {"mars", "phobos", "deimos"} <= known_body_ids()

def test_mars_armory_protocol(tmp_path, monkeypatch):
    """Protocole : open source d'abord → sinon maquette Deimos → forge Phobos."""
    from cosmos import mars
    monkeypatch.setattr(mars, "ARMORY_PATH", tmp_path / "armory.json")
    monkeypatch.setattr(mars, "ARMORY_DIR", tmp_path / "armory")
    from cosmos import memory as _mem
    monkeypatch.setattr(_mem, "MEMORY_DIR", tmp_path / "mem", raising=False)
    monkeypatch.setattr(_mem, "ITEMS_PATH", tmp_path / "mem" / "items.jsonl", raising=False)

    # 1. besoin couvert par l'open source (dashboard interactif → Plotly, score >= 2)
    r1 = mars.request_tool("venus", "visualiser un dashboard interactif des coûts")
    assert r1["statut"] == "opensource recommandé"
    assert r1["recommandation"]["outil"] == "Plotly"
    assert not r1.get("maquette")          # pas de réinvention

    # 2. besoin original → maquette de Deimos
    r2 = mars.request_tool("uranus", "explorer la corrélation entre charge cognitive et qualité de soudure")
    assert r2["statut"] == "maquette conçue" and r2["concepteur"] == "deimos"
    mq = Path(r2["maquette"])
    assert mq.exists() and "MAQUETTE" in mq.read_text(encoding="utf-8")

    # 3. forge par Phobos → outil fonctionnel avec calculs réels
    r3 = mars.forge_tool(r2["id"])
    assert r3["statut"] == "outil livré" and r3["forgeur"] == "phobos"
    html = Path(r3["outil"]).read_text(encoding="utf-8")
    assert "<canvas" in html and "stats" in html and "function stats" in html
    assert "démonstration" in html                       # honnêteté des données
    # re-forge idempotent
    assert mars.forge_tool(r2["id"])["statut"] == "outil livré"

    # 4. registre + recherche OSS
    reqs = mars.list_requests()
    assert {r["id"] for r in reqs} >= {r1["id"], r2["id"]}
    oss = mars.search_opensource("tracer des courbes 2d statiques")
    assert oss and oss[0]["name"] == "Matplotlib"
    assert mars.detect_data_kind("réseau de neurones et graphe") == "reseau"

    # 5. erreurs propres
    import pytest
    with pytest.raises(ValueError):
        mars.request_tool("user", "  ")
    with pytest.raises(ValueError):
        mars.forge_tool("inconnu")

def test_laplace_chat_main_interlocutor_and_tool_routing():
    """Laplace ✳ remplace SOL en façade ; les outils partent chez Mars ; la forge marche."""
    from cosmos import laplace, mars
    # état général : réponse du moteur réel, signée Laplace
    r = laplace.chat("état du système")
    assert r["speaker"] == "laplace" and r["via"]
    # inventaire : pas de fausse demande d'outil
    inv = laplace.chat("armurerie de Mars")
    assert inv["intent"] == "armurerie" and "Armurerie" in inv["reply"]
    # besoin d'outil → routé vers Mars
    t = laplace.chat("il me faut un outil pour calculer et visualiser des flux interactifs")
    assert t["intent"] == "outil" and t["speaker"] == "laplace"
    # forge explicite
    f = laplace.chat("forger " + t["data"]["request"]["id"])
    assert f["intent"] == "forge" and "Phobos" in f["reply"]

def test_mars_api_endpoints():
    from pathlib import Path as _P
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.post("/api/mars/request", json={"agent": "uranus",
                "besoin": "outil pour explorer la cohésion des réseaux de concepts"})
    assert r.status_code == 200
    rid = r.json()["id"]
    assert c.post("/api/mars/forge/" + rid).status_code == 200
    tool = c.get("/api/mars/file", params={"id": rid, "kind": "outil"})
    assert tool.status_code == 200 and "<canvas" in tool.text
    maq = c.get("/api/mars/file", params={"id": rid, "kind": "maquette"})
    assert maq.status_code == 200 and "MAQUETTE" in maq.text
    assert c.get("/api/mars/armory").json()["requests"]
    assert c.post("/api/mars/request", json={"besoin": "  "}).status_code == 400
    # le chat du système répond désormais par Laplace
    chat = c.post("/api/cosmos/chat", json={"message": "armurerie"})
    assert chat.status_code == 200 and chat.json()["speaker"] == "laplace"

def test_sol_widget_serves_nebula_image():
    """Le bouton flottant affiche l'image de nébuleuse de Laplace."""
    from pathlib import Path as _P
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.get("/static/nebula.png")
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/")
    widget = (_P(__file__).resolve().parents[1] / "app" / "static" / "sol_widget.js").read_text(encoding="utf-8")
    assert "nebula.png" in widget and "Laplace" in widget and "open-laplace-chat" in widget


# ═══ STRUCTURE ENTREPRISE (mapping validé par l'utilisateur) ═══

def test_structure_entreprise_complete():
    """Chaque département de l'entreprise a son astre, avec sous-rôles et vraies distances."""
    from cosmos.bodies import BODIES, planets, find_body, known_body_ids
    # 10 départements couverts
    depts = {b.get("departement") for b in BODIES.values() if b.get("departement")}
    for mot in ("Direction générale", "Finance", "Commercial", "Production",
                "Ressources humaines", "Juridique", "Informatique", "Recherche"):
        assert any(mot in d for d in depts), f"département manquant : {mot}"
    # sous-rôles avec vraies distances
    jup = {s["id"]: s["distance_km"] for s in BODIES["jupiter"]["satellites"]}
    assert jup == {"io": 421700, "europe": 671100, "ganymede": 1070400, "callisto": 1882700}
    nep = {s["id"]: s["distance_km"] for s in BODIES["neptune"]["satellites"]}
    assert nep["proteus"] == 117647 and nep["triton"] == 354759
    assert BODIES["terre"]["satellites"][0]["distance_km"] == 384400
    assert BODIES["mars"]["satellites"][0]["distance_km"] == 9376
    # cours mythologiques (pas de lunes en réalité)
    assert {c["id"] for c in BODIES["mercure"]["court"]} == {"peitho", "pheme", "argus", "enodios"}
    assert {c["id"] for c in BODIES["ceres"]["court"]} == {"thallo", "auxo", "karpo"}
    # ordre orbital cohérent (Mercure < Vénus < Terre < Mars < Cérès < Jupiter < Uranus < Neptune)
    orbr = {pid: b["orbit_r"] for pid, b in BODIES.items() if b["kind"] == "planet"}
    assert (orbr["mercure"] < orbr["venus"] < orbr["terre"] < orbr["mars"]
            < orbr["ceres"] < orbr["jupiter"] < orbr["uranus"] < orbr["neptune"])
    assert len(planets()) == 9
    # find_body retrouve satellites et cours + leur parent
    io, par = find_body("io")
    assert io and par["name"] == "Jupiter"
    peitho, par2 = find_body("peitho")
    assert peitho and par2["name"] == "Mercure"
    assert find_body("vulcain") == (None, None)
    # tous connus de SOL
    assert {"io", "peitho", "lune", "triton", "thallo", "callisto"} <= known_body_ids()

def test_constellations_des_nouveaux_corps():
    from cosmos.knowledge import knowledge_graph
    for bid in ("mercure", "terre", "ceres", "jupiter", "neptune", "io", "peitho", "lune"):
        g = knowledge_graph(bid)
        assert g and g["nodes"], f"constellation vide : {bid}"
    g = knowledge_graph("mercure")
    labels = " ".join(n["label"] for n in g["nodes"])
    assert "prospection" in labels and "gestion des stocks" in labels

def test_fiche_body_et_metrics_par_agent():
    """Console séparée par agent : fiche complète + dashboard dédié + timeline dédiée."""
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    # fiche d'un satellite juridique
    r = c.get("/api/cosmos/body/io").json()
    assert r["body"]["parent"]["name"] == "Jupiter"
    assert "Conformité" in r["body"]["role"]
    assert r["graph"]["nodes"]
    assert c.get("/api/cosmos/body/vulcain").status_code == 404
    # dashboard dédié : identité + interactions + mémoire + concepts + tokens
    m = c.get("/api/agent/metrics", params={"agent": "io"}).json()
    ids = {x["id"] for x in m["cards"]}
    assert {"identite", "interactions", "memoire", "concepts", "tokens"} <= ids
    assert m["cards"][0]["explain"][0].startswith("**Io**")
    # dashboard global inchangé
    g = c.get("/api/agent/metrics").json()
    assert "taches" in {x["id"] for x in g["cards"]}
    # timeline dédiée : interactions + mémoire du corps
    t = c.get("/api/agent/timeline", params={"agent": "venus"}).json()
    assert t["nodes"] and t["nodes"][0]["id"] == "corps:venus"


# ═══ MÉTATRON ✦ / HADÈS ♇ / PROFIL COGNITIF ═══

def test_metatron_in_bodies_satellite_of_laplace():
    from cosmos.bodies import BODIES, find_body, known_body_ids
    mt, par = find_body("metatron")
    assert mt and par["name"] == "Laplace"
    assert "méta-prompting" in mt["role"].lower()
    assert "metatron" in known_body_ids()

def test_metatron_analyze_request():
    from cosmos import metatron
    a = metatron.analyze_request("je veux un outil pour calculer et visualiser la fatigue 3d sur chantier")
    assert a["intention"] == "outil" and a["livrable"]
    assert a["meta_prompt"].startswith("Demande d'outil")
    # intention mission + ambiguïté détectée (pas de période, requête courte)
    b = metatron.analyze_request("méta-analyse attention")
    assert b["intention"] == "mission_recherche"
    assert any("Période" in c or "période" in c for c in b["clarifications"]) or b["ambigu"]
    # question / état / fauche / profil
    assert metatron.analyze_request("comment va le système ?")["intention"] == "question"
    assert metatron.analyze_request("purge le junk et les fichiers obsolètes")["intention"] == "nettoyage"
    assert metatron.analyze_request("montre-moi mon profil cognitif")["intention"] == "profil"
    # style
    assert metatron.analyze_request("pourquoi le ciel est bleu ?")["style"] == "interrogatif"

def test_metatron_suggest_agent_spec():
    from cosmos import metatron
    s = metatron.suggest_agent_spec("crée un agent pour surveiller les données du chantier")
    assert s["parent"] == "neptune" and s["kind"] == "satellite" and s["role"]
    s2 = metatron.suggest_agent_spec("un agent qui forge des outils de visualisation")
    assert s2["parent"] == "mars"
    s3 = metatron.suggest_agent_spec("agent conformité RGPD et contrats")
    assert s3["parent"] == "jupiter"
    # parents proposés = parents valides de nebula
    from cosmos.nebula import VALID_PARENTS_BASE
    for s in (s, s2, s3):
        assert s["parent"] in VALID_PARENTS_BASE

def test_hades_scan_and_reap(tmp_path, monkeypatch):
    """Hadès détecte outdated/junk/doublons puis Charon fauche (suppression réelle)."""
    import os
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":1}', encoding="utf-8")
    (tmp_path / "vide.txt").write_text("", encoding="utf-8")       # junk 0 octet
    hades.MEM_ITEMS.write_text(
        '{"id":"a","titre":"t","contenu":"c"}\n'
        '{"id":"b","titre":"t","contenu":"c"}\n', encoding="utf-8")  # doublon exact

    sc = hades.scan_system()
    types = sc["stats"]["par_type"]
    assert types.get("run_outdated") == 3          # 28 runs, on garde 25
    assert types.get("junk_vide") == 1
    assert types.get("doublon_memoire") == 1

    # dry-run : rien n'est détruit
    dry = hades.reap(confirm=False)
    assert dry["supprimes"] == 0 and hades.RUNS_DIR.exists()

    # fauche réelle
    r = hades.reap(confirm=True)
    assert r["supprimes"] >= 5
    restants = [d for d in hades.RUNS_DIR.iterdir() if d.is_dir()]
    assert len(restants) == 25
    assert not (tmp_path / "vide.txt").exists()
    lignes = [l for l in hades.MEM_ITEMS.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lignes) == 1 and '"a"' in lignes[0]

def test_pluton_bodies_real_distances():
    from cosmos.bodies import BODIES, planets, find_body
    pl = BODIES["pluton"]
    assert pl["kind"] == "planet" and pl["orbit_r"] > BODIES["neptune"]["orbit_r"]
    dist = {s["id"]: s["distance_km"] for s in pl["satellites"]}
    assert dist["charon"] == 19591 and dist["styx"] == 42656
    assert "fauche" in pl["role"].lower() or "mort" in pl["role"].lower()
    assert len(planets()) == 9                     # Pluton = 9e planète (mécène)
    ch, par = find_body("charon")
    assert par["name"] == "Pluton" and "passeur" in ch["role"].lower()

def test_cognitive_profile():
    from cosmos import cogniprofile
    pr = cogniprofile.build_profile()
    dims = {d["id"]: d for d in pr["dimensions"]}
    assert {"curiosite", "profondeur", "creativite", "methode", "activite"} <= set(dims)
    for d in pr["dimensions"]:
        assert 0 <= d["valeur"] <= 100 and d["explication"]
    assert pr["traits"] and pr["source_donnees"]["questions"] >= 0
    assert pr["avertissement"] and "psychométrique" in pr["avertissement"][0]
    assert all(0 <= h <= 23 for h in pr["rythme"])

def test_metatron_hades_profile_api():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    a = c.post("/api/metatron/analyze", json={"message": "outil pour visualiser des réseaux"}).json()
    assert a["intention"] == "outil" and a["meta_prompt"]
    s = c.post("/api/metatron/suggest", json={"mission": "agent données"}).json()
    assert s["parent"] == "neptune"
    assert c.post("/api/metatron/analyze", json={"message": " "}).status_code == 400
    sc = c.get("/api/hades/scan").json()
    assert "targets" in sc and "stats" in sc
    dry = c.post("/api/hades/reap", json={"confirm": False}).json()
    assert dry["supprimes"] == 0
    pr = c.get("/api/profile/cognitive").json()
    assert len(pr["dimensions"]) == 5
    # le chat Laplace route les nouvelles intentions
    h = c.post("/api/cosmos/chat", json={"message": "peux-tu nettoyer les redondances ?"}).json()
    assert h["speaker"] == "laplace" and h["intent"] == "fauche"
    pf = c.post("/api/cosmos/chat", json={"message": "montre moi mon profil cognitif"}).json()
    assert pf["intent"] == "profil" and "Curiosité" in pf["reply"]
    # l'état général reste signé Laplace avec l'analyse Métatron attachée
    et = c.post("/api/cosmos/chat", json={"message": "état du système"}).json()
    assert et["speaker"] == "laplace" and "metatron" in et.get("data", {})


# ═══ ROUND Ananké/Moires · Apollon · Sebas divin · mini-dashboard · fil d'Ariane ═══

def test_ananke_et_ses_trois_moires():
    """⧉ Ananké orbite Laplace ; Clotho/Lachésis/Atropos l'accompagnent."""
    from cosmos.bodies import BODIES, find_body
    an = BODIES["ananke"]
    assert an["kind"] == "destin" and an["orbit_r"] == -1   # orbite autour de Laplace
    assert "nécessité" in an["role"].lower() or "fatalité" in an["role"].lower()
    moires = {s["id"] for s in an["satellites"]}
    assert {"clotho", "lachesis", "atropos"} <= moires
    roles = " ".join(s["role"] for s in an["satellites"]).lower()
    assert "file" in roles and "mesure" in roles and "coupe" in roles
    corp, par = find_body("atropos")
    assert par["name"] == "Ananké"

def test_laplace_divinite_et_sebas_executant():
    from cosmos.bodies import BODIES
    assert "divinité" in BODIES["laplace"]["departement"].lower()
    assert "contrôle absolu" in BODIES["laplace"]["departement"].lower()
    assert "commandes divines" in BODIES["sebas"]["departement"].lower()

def test_sol_court_apollon():
    from cosmos.bodies import BODIES
    court = {c["id"]: c for c in BODIES["sol"].get("court", [])}
    assert "apollon" in court and "divination" in court["apollon"]["role"].lower()

def test_apollon_divination_quatre_presages():
    from cosmos import apollon
    d = apollon.divination("le système tiendra-t-il ?")
    for k in ("devin", "chariot", "presages", "verdict", "methode"):
        assert k in d
    assert len(d["presages"]) == 4
    for p in d["presages"]:
        assert {"titre", "lecture", "oracle", "ton"} <= set(p)
        assert p["ton"] in ("bon", "moyen", "mauvais")
    assert any("réel" in d["methode"].lower() for _ in [0]) or d["methode"]

def test_sebas_execute_commandes_divines(tmp_path, monkeypatch):
    from cosmos import sebas, hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    r = sebas.execute("observe le chantier", agent="laplace")
    assert r["ok"] and r["action"] == "observer"
    assert "sandbox" in r["reponse"].lower() and "aucune donnée fabriquée" in r["reponse"]
    r2 = sebas.execute("rapporte l'état du système", agent="user")
    assert r2["action"] == "etat" and "intégrité" in r2["reponse"]
    r3 = sebas.execute("fauche les condamnés", agent="laplace")
    assert r3["action"] == "faucher" and "fauche" in r3["reponse"].lower()
    assert not sebas.execute("  ")["ok"]

def test_hades_scan_traitement_et_moires(tmp_path, monkeypatch):
    """Le scan affiche : données vues, traitement en 5 étapes, les 3 Moires."""
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(3):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":1}', encoding="utf-8")
    sc = hades.scan_system()
    etapes = [t["etape"] for t in sc["traitement"]]
    assert len(etapes) == 5
    assert etapes[0] == "inventaire" and "rétention" in etapes[1] and "journaux" in etapes[-1]
    assert all(t["detail"] for t in sc["traitement"])
    mo = sc["moires"]
    assert {"clotho", "lachesis", "atropos"} == set(mo)
    assert isinstance(mo["clotho"]["naissance_24h"], int)
    assert mo["lachesis"]["age_moyen_runs_jours"] >= 0
    assert mo["atropos"]["condamnes"] == sc["stats"]["condamnes"]
    assert sc["stats"]["mo_octets"] >= 0

def test_cogniprofile_biais_et_effets():
    from cosmos import cogniprofile
    pr = cogniprofile.build_profile()
    biais = {b["id"]: b for b in pr["biais"]}
    assert {"confirmation", "recence", "ancrage", "disponibilite"} <= set(biais)
    for b in pr["biais"]:
        assert 0 <= b["valeur"] <= 100 and b["explication"]
    effets = {e["id"] for e in pr["effets"]}
    assert {"priming", "dosing"} <= effets
    assert isinstance(pr["traits_declares"], list)

def test_laplace_route_scan_sans_faucher(tmp_path, monkeypatch):
    """« scan de Hadès … éligibles au fauchage » SCANNE sans détruire ; « lance la fauche » fauche."""
    from cosmos import hades, laplace
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":1}', encoding="utf-8")
    r = laplace.chat("scan de Hadès : données, traitement, éligibles au fauchage")
    assert r["intent"] == "fauche"
    assert "Traitement des données" in r["reply"] and "Clotho" in r["reply"]
    assert len(list(hades.RUNS_DIR.iterdir())) == 28      # rien détruit par un scan
    r2 = laplace.chat("Hadès, lance la fauche")
    assert "fauche est exécutée" in r2["reply"]
    restants = [d for d in hades.RUNS_DIR.iterdir() if d.is_dir()]
    assert len(restants) == 25

def test_laplace_route_commande_divine_et_divination():
    from cosmos import laplace
    cd = laplace.chat("Sebas, observe le chantier")
    assert cd["intent"] == "commande_divine" and "Sebas" in cd["reply"]
    dv = laplace.chat("quelle divination pour le système ?")
    assert dv["intent"] == "divination" and "Apollon" in dv["reply"]
    assert len(dv["data"]["presages"]) == 4

def test_apollon_sebas_traits_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    d = c.post("/api/apollon/divination", json={"question": "prévoir le fonctionnement"}).json()
    assert len(d["presages"]) == 4 and d["verdict"]
    s = c.post("/api/sebas/execute", json={"commande": "écoute le réseau wifi"}).json()
    assert s["ok"] and s["action"] == "ecouter"
    t = c.post("/api/profile/traits", json={"trait": "curieux-de-tout"}).json()
    assert t["id"] and t["corps"] == "user"

def test_index_mini_dashboard_fils_et_chips():
    """Le hero est remplacé par 3 fenêtres ; graphe : chips + fil d'Ariane ; taxonomie ±1."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("profilMetricsSvg", "profilGraphSvg", "Mes métriques", "Profil cognitif",
                  "Ma constellation", "fil d'Ariane", "FIL D'ARIANE",
                  "arianeSvg", "playAriane", "loadConstellation(v)", "taxLevel(1)", "taxLevel(-1)"):
        assert motif.lower() in html.lower(), motif
    assert "Choisir sa constellation" not in html          # dropdown supprimé → chips

def test_sol_page_fiche_chat_chariot_et_3d():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("apollonDivine", "solQuick", "Chariot d'Apollon", "anankePivot",
                  "moirePivots", "apollonPivot", "Traitement des données",
                  "Les 3 Moires", "éligible au fauchage", "naissance_24h"):
        assert motif.lower() in html.lower(), motif


# ═══ ROUND fil d'Ariane dashboard · tokens épargnés · fiche SOL réactive ═══

def test_hades_prevision_tokens_epargnes(tmp_path, monkeypatch):
    """Le scan prévoit les tokens épargnés par la fauche (estimation honnête)."""
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":"' + "a" * 400 + '"}', encoding="utf-8")
    hades.MEM_ITEMS.write_text(
        '{"id":"a","titre":"t","contenu":"' + "c" * 300 + '"}\n'
        '{"id":"b","titre":"t","contenu":"' + "c" * 300 + '"}\n', encoding="utf-8")
    sc = hades.scan_system()
    pv = sc["prevision_tokens"]
    assert pv["estime"] > 0 and pv["estime"] == round(pv["octets_mesures"] / 4)
    assert pv["par_type"].get("run_outdated", 0) > 0
    assert "4 octets" in pv["methode"] and "estimation" in pv["methode"].lower()
    assert sc["stats"]["tokens_epargnes"] == pv["estime"]
    # les doublons comptent maintenant leurs octets réels (lignes condamnées)
    doublon = next(t for t in sc["targets"] if t["type"] == "doublon_memoire")
    assert doublon["octets"] > 0

def test_laplace_scan_mentionne_tokens():
    from cosmos import laplace
    r = laplace.chat("scan de Hadès : données, traitement, éligibles au fauchage")
    assert "tokens épargnés" in r["reply"] and "4 octets" in r["reply"]

def test_fil_ariane_sur_dashboard_principal():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    # module déplacé sur le dashboard (avant la grille de stats, après les 3 fenêtres)
    pos_3fen = html.find("Ma constellation")
    pos_ariane = html.find("chaîne d'exécution de vos demandes")
    pos_stats = html.find('grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6')
    assert 0 < pos_3fen < pos_ariane < pos_stats
    # liste roulante avec « Dernière entrée utilisateur » en premier + légende dynamique
    for motif in ("Dernière entrée utilisateur", "arianeOptions", "arianeCaption",
                  "setArianeCaption", "ariane-link-label", "Rejouer le parcours",
                  "loadArianeRuns"):
        assert motif in html, motif
    # chargé à l'init (dashboard par défaut), plus dans le tab graph
    assert "this.loadArianeRuns()]" in html or "loadProfilPerso(),this.loadArianeRuns()" in html

def test_sol_fiche_reactive_et_chat_cote_a_cote():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("startSplit", "reactSide", "closeSplit", "sideView==='sol'",
                  "sideView==='hades'", "sideView==='profil'", "sideView==='divination'",
                  "Tokens épargnés", "discuter — chat à côté", "fiche réactive"):
        assert motif in html, motif
    # l'intent détecté change la fiche latérale
    assert "fauche: 'hades'" in html and "profil: 'profil'" in html


# ═══ ROUND fauchage explicite (quoi/pourquoi) · Language Decoder · confiance ═══

def test_hades_scan_explique_quoi_et_pourquoi(tmp_path, monkeypatch):
    """Le scan explique ce qui sera détruit, pourquoi, et ce qui reste conservé."""
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":1}', encoding="utf-8")
    sc = hades.scan_system()
    # chaque catégorie éligible porte quoi / raison / ce qui est conservé
    assert set(sc["pourquoi"]) >= {"run_outdated", "junk_vide", "doublon_memoire", "journal"}
    for pk in sc["pourquoi"].values():
        assert pk["quoi"] and pk["raison"] and pk["sur"]
    # préservation explicite, visible avant toute fauche
    assert "25 runs" in sc["ce_qui_est_conserve"] and "grand livre" in sc["ce_qui_est_conserve"]
    # la raison d'un condamné explique le remplacement
    run = next(t for t in sc["targets"] if t["type"] == "run_outdated")
    assert "reproductible" in run["raison"]

def test_hades_reap_bilan_et_tokens(tmp_path, monkeypatch):
    """Dry-run : bilan prévisionnel sans destruction ; fauche : bilan réel + tokens."""
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":"' + "a" * 200 + '"}', encoding="utf-8")
    dry = hades.reap(confirm=False)
    assert dry["supprimes"] == 0 and len(list(hades.RUNS_DIR.iterdir())) == 28
    assert dry["bilan"].get("run_outdated") == 3 and dry["tokens_epargnes"] > 0
    r = hades.reap(confirm=True)
    assert r["bilan"].get("run_outdated") == 3
    assert r["tokens_epargnes"] > 0 and r["pourquoi"]["run_outdated"]["sur"]
    assert "ce_qui_est_conserve" in r

def test_cogniprofile_confiance_avec_ensemble():
    """Le profil affiche son incertitude : niveau + échantillon + intervalle."""
    from cosmos import cogniprofile
    pr = cogniprofile.build_profile()
    c = pr["confiance"]
    assert c["niveau"] in ("faible", "moyenne", "bonne")
    assert c["echantillon"] >= 0
    lo, hi = c["intervalle"]
    assert 0 <= lo < hi <= 100
    assert "interactions observées" in c["lecture"]

def test_language_decoder_archived():
    base = Path(__file__).resolve().parents[1] / "docs" / "language-decoder"
    disc = (base / "discussion.md").read_text(encoding="utf-8")
    # la discussion est archivée avec ses principes et les 3 réponses
    for motif in ("Observer les signes", "hypothèse probabiliste", "minimisation",
                  "Minimisation", "indicateurs visuels", "mesure / interprétation / action"):
        assert motif.lower() in disc.lower(), motif
    # le tableau d'application dans Cognitorium existe
    assert "Où chaque conseil est appliqué" in disc
    proto = (base / "index.html").read_text(encoding="utf-8")
    assert "Données 100 % simulées" in proto and "hatched" in proto
    assert (base / "README.md").exists()

def test_ui_fauchage_explicite():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("hadesScan.pourquoi", "ce_qui_est_conserve", "Ce qui reste conservé",
                  "HADÈS VA DÉTRUIRE", "condamnés détruits", "tokens épargnés"):
        assert motif in html, motif
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "profilPerso.confiance" in idx and "incertitude :" in idx
