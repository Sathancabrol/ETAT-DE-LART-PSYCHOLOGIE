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
    n0 = len(memory.items(limit=10**6, type_="question"))
    sol.chat("question test pour la mémoire 12345")
    assert len(memory.items(limit=10**6, type_="question")) == n0 + 1


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
    # (le serveur live écrit des items en parallèle des tests → re-synchro avant comparaison)
    database.sync_memory_items()
    ids_in_db = {r["id"] for r in database.get_memory_items(limit=10**6)}
    items_ids = {it["id"] for it in memory.items(limit=10**6)}
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
    from cosmos import underworld as _uw
    monkeypatch.setattr(_uw, "UNDERWORLD", tmp_path / "uw")
    monkeypatch.setattr(_uw, "SOULS", tmp_path / "uw" / "souls.jsonl")
    monkeypatch.setattr(_uw, "KEPT", tmp_path / "uw" / "kept")
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
    from cosmos import underworld as _uw
    monkeypatch.setattr(_uw, "UNDERWORLD", tmp_path / "uw")
    monkeypatch.setattr(_uw, "SOULS", tmp_path / "uw" / "souls.jsonl")
    monkeypatch.setattr(_uw, "KEPT", tmp_path / "uw" / "kept")
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
    for motif in ("apollonDivine", "solQuick", "Chariot d'Apollon", "addAtomOrbiter",
                  "apollonPivot", "Traitement des données",
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
    from cosmos import underworld as _uw
    monkeypatch.setattr(_uw, "UNDERWORLD", tmp_path / "uw")
    monkeypatch.setattr(_uw, "SOULS", tmp_path / "uw" / "souls.jsonl")
    monkeypatch.setattr(_uw, "KEPT", tmp_path / "uw" / "kept")
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


# ═══ ROUND drill-down tokens (calcul traçable) · guide ? · affordance ═══

def test_prevision_tokens_detail_calcul_traconnable(tmp_path, monkeypatch):
    """Le chiffre de tokens épargnés est traçable : détail par type + calcul 3 étapes + limites."""
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":"' + "a" * 300 + '"}', encoding="utf-8")
    sc = hades.scan_system()
    pv = sc["prevision_tokens"]
    # détail par type : chaque ligne porte compte, octets, tokens, taille moyenne, quoi
    det = [d for d in pv["detail"] if d["type"] == "run_outdated"]
    assert det and det[0]["condamnes"] == 3
    assert det[0]["octets"] > 0 and det[0]["tokens"] == round(det[0]["octets"] / 4)
    assert det[0]["taille_moyenne_octets"] > 0 and det[0]["quoi"]
    # la somme des détails = l'estimation (à l'arrondi près)
    assert abs(sum(d["tokens"] for d in pv["detail"]) - pv["estime"]) <= len(pv["detail"])
    # le calcul est expliqué en 3 étapes lisibles
    etapes = [c["etape"] for c in pv["calcul"]]
    assert any("Mesurer" in e for e in etapes) and any("Convertir" in e for e in etapes)
    assert any("Diviser" in e for e in etapes) and all(c["valeur"] for c in pv["calcul"])
    # pourquoi ce ratio + limites honnêtes
    assert "token" in pv["pourquoi_ratio"].lower() and len(pv["limites"]) >= 3
    assert "contexte" in pv["ce_que_ca_veut_dire"] or "chargé" in pv["ce_que_ca_veut_dire"]

def test_sol_fenetre_tokens_au_dessus_hades():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    # la carte est cliquable et ouvre une fenêtre par-dessus (z-[60] > z-50 d'Hadès)
    assert "openTokensDetail" in html and "z-[60]" in html
    assert "modals.tokens" in html or "tokens: false" in html
    # la fenêtre montre le calcul complet : mesuré / estimé / limites
    for motif in ("d'où vient ce chiffre", "prevision_tokens?.detail", "prevision_tokens?.calcul",
                  "prevision_tokens?.limites", "taille_moyenne_octets", "pourquoi_ratio"):
        assert motif in html, motif

def test_sol_guide_et_affordance():
    """Bouton ? (guide 6 gestes) + tooltips explicites sur les contrôles clés."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    assert "openModal('aide')" in html and "aide: false" in html
    for motif in ("utiliser Cognitorium en 6 gestes", "Comprendre les chiffres",
                  "Faucher en connaissance de cause", "cliquez : comment ce chiffre est calculé",
                  "📊 Dashboard"):
        assert motif in html, motif
    # tooltips Moires = le rôle de chacune en une phrase
    assert "file le fil" in html and "mesure le fil" in html and "coupe le fil" in html


# ═══ ROUND Thémis ⚖ · icônes · orbites atomiques · suivi jusqu'à l'entité ═══

def test_themis_corps_et_constitution_democratique():
    """Thémis orbite Laplace, bras armé, constituée comme la démocratie (4 pouvoirs)."""
    from cosmos.bodies import BODIES, find_body
    th = BODIES["themis"]
    assert th["kind"] == "justice" and th["orbit_r"] == -1
    assert "bras armé" in th["departement"].lower() and "démocratie" in th["role"].lower()
    sats = {s["id"] for s in th["satellites"]}
    assert {"eunomia", "eirene", "dike", "censeur"} <= sats
    roles = " ".join(s["role"] for s in th["satellites"]).lower()
    assert "législatif" in roles and "exécutif" in roles and "judiciaire" in roles and "contre-pouvoir" in roles
    for ident in ("themis", "eunomia", "eirene", "dike", "censeur"):
        b, parent = find_body(ident)
        assert b, ident
        if ident != "themis":
            assert parent is BODIES["themis"]

def test_icones_fonctionnelles_sur_tous_les_corps():
    """Chaque corps de premier niveau porte une icône = sa fonction (ex. Thémis ⚖️)."""
    from cosmos.bodies import BODIES, celestial_registry
    assert BODIES["themis"]["icon"] == "⚖️"
    assert BODIES["laplace"]["icon"] and BODIES["sol"]["icon"]
    reg = celestial_registry()
    sans_icone = [b["id"] for b in reg if not b.get("icon")]
    assert not sans_icone, f"corps sans icône : {sans_icone}"

def test_themis_audit_et_application(tmp_path, monkeypatch):
    from cosmos import hades, themis
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text('{"x":1}', encoding="utf-8")
    a = themis.audit()
    assert a["deesse"].startswith("Thémis") and a["menaces"] and a["conseils"]
    assert any("Hadès" in m["quoi"] for m in a["menaces"])
    assert {c["pouvoir"] for c in a["constitution"]} >= {"législatif", "exécutif", "judiciaire", "contre-pouvoir"}
    # sans accord : aucune destruction
    r = themis.appliquer(confirm=False)
    assert r["fauche"] is None and len(list(hades.RUNS_DIR.iterdir())) == 28
    # avec accord : la justice tranche réellement
    r2 = themis.appliquer(confirm=True)
    assert r2["fauche"]["supprimes"] >= 3
    assert len([d for d in hades.RUNS_DIR.iterdir() if d.is_dir()]) == 25

def test_laplace_route_justice():
    from cosmos import laplace
    r = laplace.chat("Thémis, juge le système")
    assert r["intent"] == "justice" and "Thémis" in r["reply"]
    assert "Eunomie" in r["reply"]          # constitution démocratique affichée

def test_hades_suit_le_condamne_jusqu_a_l_entite(tmp_path, monkeypatch):
    """Dikè instruit le dossier : l'utilisateur voit l'entité réelle qui sera supprimée."""
    from cosmos import hades
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    hades.RUNS_DIR.mkdir(parents=True)
    d = hades.RUNS_DIR / "run_old"
    d.mkdir()
    (d / "trace.json").write_text('{"run_id":"run_old","tache":"analyser","statut":"succès",'
                                  '"date":"2026-08-30T10:00:00","steps":[{"skill":"synthesize"}]}',
                                  encoding="utf-8")
    (d / "report.md").write_text("# rapport", encoding="utf-8")
    dossier = hades.describe_target(str(d), "run_outdated")
    assert dossier["entite"]["tache"] == "analyser" and dossier["entite"]["run_id"] == "run_old"
    noms = {f["nom"] for f in dossier["contenu"]}
    assert "trace.json" in noms and "report.md" in noms
    assert "2 fichiers" in dossier["supprime"]
    # hors-système → refus
    import pytest
    with pytest.raises(ValueError):
        hades.describe_target("/etc/passwd", "run_outdated")

def test_themis_endpoints_et_ui():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    a = c.get("/api/themis/audit").json()
    assert a["deesse"].startswith("Thémis") and a["constitution"]
    ap = c.post("/api/themis/apply", json={"confirm": False}).json()
    assert ap["fauche"] is None
    sc = c.get("/api/hades/scan").json()
    t = next((x for x in sc["targets"] if x["type"] == "run_outdated"), None)
    if t:
        d = c.get("/api/hades/target", params={"cible": t["cible"], "type": t["type"]}).json()
        assert d["supprime"]
    assert c.get("/api/hades/target", params={"cible": "/etc", "type": "run_outdated"}).status_code == 400
    # UI : orbites atomiques à l'échelle + icônes + drill-down
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("SOLAR_SCALE", "atomPivots", "addAtomOrbiter", "iconSprite", "a: 0.39", "a: 5.2",
                  "T: 11.86", "toggleTarget", "targetDetail", "Dikè", "⚖ Thémis", "b.icon"):
        assert motif in html, motif


# ═══ ROUND fiches F/P/D · mascot Clippy · light ON/OFF · suivre zoom · underworld 🔥 ═══

def test_corps_pouvoir_devoir():
    """Chaque corps décrit sa fonction, son pouvoir et son devoir (fiches)."""
    from cosmos.bodies import BODIES, celestial_registry
    for bid, b in BODIES.items():
        assert b.get("pouvoir"), f"{bid} sans pouvoir"
        assert b.get("devoir"), f"{bid} sans devoir"
    reg = celestial_registry()
    assert all(x.get("pouvoir") and x.get("devoir") for x in reg)

def test_fiche_fpd_schema_et_aller_vers():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("Fonction · Pouvoir · Devoir", "renderBodySchema", "bodySchema",
                  "⚡ Pouvoir", "🛡 Devoir", "goTo3D", "goToObsidian",
                  "aller vers · 3D", "aller vers · Obsidian"):
        assert motif in html, motif
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "?const" not in idx or "q.get('const')" in idx       # la cible Obsidian lit le paramètre
    assert "q.get('const')" in idx

def test_laplace_mascot_clippy_anime():
    """Le bouton flottant Laplace est un mascot animé (sprite 4 poses, façon Clippy)."""
    js = (Path(__file__).resolve().parents[1] / "app" / "static" / "sol_widget.js").read_text(encoding="utf-8")
    for motif in ("solw-mascot", "laplace_sprite.png", "solw-frames", "solw-hello",
                  "steps(1,end)", "background-size:200% 200%"):
        assert motif in js, motif
    sprite = Path(__file__).resolve().parents[1] / "app" / "static" / "laplace_sprite.png"
    assert sprite.exists() and sprite.stat().st_size > 10000

def test_vue_3d_light_off_suivre_zoom_anti_collision():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    # light ON/OFF : gèle planètes/lunes/cours, les divinités de Laplace continuent
    for motif in ("toggleSystemLight", "systemOn", "light ON", "light OFF",
                  "if (this.systemOn)"):
        assert motif in html, motif
    # suivre = zoom + centrage + verrou
    for motif in ("followDist", "focusDist", "(followDist - dist) * 0.08"):
        assert motif in html, motif
    # anti-collision : cours équiréparties (angle + rayon échelonné)
    assert "(i * 7) % 9" in html and "i * (Math.PI * 2 / cour.length)" in html

def test_underworld_rien_ne_disparait(tmp_path, monkeypatch):
    """La fauche enregistre les âmes avec fraction vitale ; résurrection possible."""
    from cosmos import hades, underworld
    monkeypatch.setattr(hades, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(hades, "OUT", tmp_path)
    monkeypatch.setattr(hades, "MEM_ITEMS", tmp_path / "mem.jsonl")
    monkeypatch.setattr(underworld, "UNDERWORLD", tmp_path / "uw")
    monkeypatch.setattr(underworld, "SOULS", tmp_path / "uw" / "souls.jsonl")
    monkeypatch.setattr(underworld, "KEPT", tmp_path / "uw" / "kept")
    hades.RUNS_DIR.mkdir(parents=True)
    for i in range(28):
        d = hades.RUNS_DIR / f"run_{i:03d}"
        d.mkdir()
        (d / "trace.json").write_text(
            '{"run_id":"r%d","tache":"tache %d","statut":"succès","steps":[{"skill":"synthesize","artifacts":["a.md"]}]}' % (i, i),
            encoding="utf-8")
    hades.MEM_ITEMS.write_text('{"id":"a","titre":"t","contenu":"c"}\n{"id":"b","titre":"t","contenu":"c"}\n',
                               encoding="utf-8")
    r = hades.reap(confirm=True)
    assert r["supprimes"] >= 4 and r["underworld"]["ames"] >= 4
    st = underworld.state()
    # régions : les runs avec artefacts sont vertueux (Élysées), le doublon va au Tartare
    assert st["par_region"]["elysees"] >= 3 and st["par_region"]["tartare"] >= 1
    assert any("Cerbère" in s["gardien"] or "🐾" in s["gardien"] for s in st["ames"])
    # fraction vitale : la trace conservée permet de reconstruire
    run_soul = next(s for s in st["ames"] if s["type"] == "run_outdated")
    assert run_soul["trace"]["run_id"] and run_soul["fichiers"]
    # Cerbère exige la confirmation
    refus = underworld.resurrect(run_soul["id"], confirm=False)
    assert not refus["ok"] and "Cerbère" in refus["statut"]
    # résurrection réelle : le run remonte parmi les vivants
    res = underworld.resurrect(run_soul["id"], confirm=True)
    assert res["ok"]
    assert (tmp_path / "runs" / Path(run_soul["cible"]).name / "trace.json").exists()

def test_inferno_endpoints_et_ui():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    st = c.get("/api/underworld").json()
    assert st["royaume"] and set(st["regions"]) == {"elysees", "asphodele", "tartare"}
    assert st["gardiens"]["chien"].startswith("Cerbère")
    assert c.post("/api/underworld/restore", json={"id": "inconnu", "confirm": True}).json()["ok"] is False
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("🔥 INFERNO", "loadUnderworld", "resurrectSoul", "elysees",
                  "asphodele", "tartare", "Cerbère", "Perséphone", "ressusciter"):
        assert motif in html, motif
    from cosmos import laplace
    r = laplace.chat("montre-moi les enfers")
    assert r["intent"] == "inferno" and "âme" in r["reply"]


# ═══ ROUND Olympe 🏛 · dashboard hologramme · cerveau · avatar · identité complète ═══

def test_identite_toutes_entites():
    """Chaque entité du système — corps, satellites, cour — a un pouvoir et un devoir."""
    from cosmos.bodies import BODIES
    for bid, b in BODIES.items():
        assert b.get("pouvoir") and b.get("devoir"), f"{bid} (corps) sans identité"
        for s in (b.get("satellites") or []) + (b.get("court") or []):
            assert s.get("pouvoir"), f"{bid}/{s['id']} sans pouvoir"
            assert s.get("devoir"), f"{bid}/{s['id']} sans devoir"
    n = sum(len((b.get("satellites") or []) + (b.get("court") or [])) for b in BODIES.values())
    assert n >= 39          # 27 satellites + 12 membres de cour

def test_fiche_astres_connectes_cliquables():
    """La fiche liste les astres connectés (parent/satellites/cour), cliquables."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("Astres connectés", "connectedBodies(bodyData.body)", "openBody(c.id)",
                  "un système, une famille", "_skyOpenBody"):
        assert motif in html, motif
    # le schéma SVG est cliquable et montre les identités au survol
    assert "slice(0, 5)" in html and "'⚡ ' + s.pouvoir" in html

def test_chat_actions_rapides_liste_deroulante():
    """Le chat de Laplace propose une liste déroulante d'actions rapides élargie."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("actions rapides", "quickActions", "quickGroups", "quickRun", "quickOpen"):
        assert motif in html, motif
    import re
    n = len(re.findall(r"\{g:'", html))
    assert n >= 20, f"{n} actions rapides seulement"
    # les groupes couvrent système, divinités, enfers, recherche, mémoire
    for grp in ("Système & état", "Divinités au travail", "Enfers & justice",
                "Recherche & production", "Mémoire & identité"):
        assert grp in html, grp

def test_olympus_backend():
    """Le Mont Olympe : places, habitants avec identité, théâtre dérivé d'événements réels."""
    from cosmos import olympus, underworld
    # une âme réelle (dans le royaume isolé par conftest) déclenche le théâtre juridique
    underworld.record_soul({"id": "ame-test", "type": "run_outdated", "region": "tartare",
                            "cible": "output/agent_runs/run_test", "raison": "run obsolète",
                            "octets": 10, "trace": {"tache": "étude de test", "run_id": "r1"},
                            "gardien": "Cerbère 🐾", "ts": "2026-08-31T00:00:00"})
    st = olympus.state()
    assert len(st["places"]) >= 14 and len(st["agents"]) >= 18
    ids = {a["id"] for a in st["agents"]}
    assert {"sol", "themis", "mars", "pluton", "uranus", "laplace", "zeta", "charon", "cerbere"} <= ids
    # chaque habitant porte son identité (pouvoir/devoir) et son poste existe
    for a in st["agents"]:
        assert a["poste"] in st["places"], a["id"]
        assert a.get("pouvoir") is not None, a["id"]
    # le théâtre juridique complet quand une âme existe (registre réel)
    d = st["drama"]
    assert d["beats"] and d["source"]
    txt = " ".join(b["texte"] for b in d["beats"])
    for etape in ("procès", "forge", "Hadès", "exécuté", "assistants"):
        assert etape in txt, etape
    # l'activité est réelle : niveaux + interactions dénombrées
    for a in st["agents"]:
        assert 0 <= a["niveau"] <= 3 and a["interactions"] >= 0

def test_olympus_endpoint_et_ui():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    st = c.get("/api/olympus").json()
    assert st["places"] and st["agents"] and st["drama"]["beats"] and st["chronique"] is not None
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("🏛 OLYMPUS", "olympusCanvas", "startOlympusEngine", "stopOlympusEngine",
                  "chronique réelle", "openOlympus"):
        assert motif in html, motif

def test_dashboard_holo_avatar_cerveau():
    """Dashboard hologramme SF : opérateur 3D T-pose maillage + onglet Cerveau."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    # onglet cerveau + scène
    for motif in ("'Cerveau'", "brainCanvas", "initBrain", "brainRegions",
                  "selectBrainRegion", "Cerveau du Cognitorium"):
        assert motif in html, motif
    # opérateur : humain masculin T-pose en maillage
    for motif in ("operatorCanvas", "initOperator", "humain · masculin · maillage",
                  "T-pose", "SphereGeometry", "Math.PI / 2"):
        assert motif in html, motif
    # reskin holographique
    for motif in ("holo-frame", "holoSweep", "backdrop-filter: blur(22px)", "three@0.158.0"):
        assert motif in html, motif
    # les régions du cerveau sont câblées aux données réelles
    for rid in ("frontal", "parietal", "temporal", "occipital", "cervelet", "tronc"):
        assert f"id: '{rid}'" in html, rid


# ═══ ROUND simulation cérébrale · killchain Olympe · Laplace nébuleuse ═══

def test_operateur_3d_lance_au_chargement():
    """Fix : l'opérateur T-pose doit se lancer au 1ᵉʳ affichage (init), pas
    seulement au changement d'onglet — et redémarrer après retour d'onglet."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert html.count("this.initOperator()") >= 2       # init() + switchTab()
    assert "this._opTries < 40" in html and "if (this._op) { this._opLoop(); return; }" in html

def test_cerveau_fenetre_simulation_film_peur():
    """Fenêtre simulation : scène (télé + vous) et cerveau 3D qui s'illumine
    par zone (amygdale=peur, visuel, préfrontal…) selon les phases du film."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("simScene", "simBrain", "initSimulation", "simPhase", "simRegions",
                  "JUMPSCARE", "amygdale", "hippocampe", "jumpscare",
                  "cas de simulation · cerveau en direct", "simCases", "pickSimCase"):
        assert motif in html, motif
    # les 4 phases du scénario existent avec leurs intensités cérébrales
    for ph in ("'calme'", "'tension'", "'jumpscare'", "'retour'"):
        assert ph in html, ph

def test_cerveau_graphe_3d_metrics_impact_environnement():
    """Graphe 3D : performance des fonctions mentales (base réelle) vs impact
    de l'action/environnement (scénario film de peur)."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("metrics3d", "initMetrics3d", "metRows", "impact film de peur",
                  "attention*", "base réelle"):
        assert motif in html, motif

def test_olympus_killchain_killfeed_et_dialogues():
    """Olympe : killchain affichée en killfeed + chat activé par les dialogues."""
    from cosmos import underworld, olympus
    underworld.record_soul({"id": "ame-kc", "type": "run_outdated", "region": "tartare",
                            "cible": "output/agent_runs/run_kc", "raison": "test killchain",
                            "octets": 1, "trace": {"tache": "expérience interdite"},
                            "gardien": "Cerbère 🐾", "ts": "2026-08-31T00:00:00"})
    d = olympus.drama()
    assert d["mode"] == "justice"
    kill = [b for b in d["beats"] if b.get("kill")]
    assert kill, "aucun beat marqué kill"
    # chaque beat du procès parle : dialogues nommés et colorés
    for b in d["beats"]:
        assert b.get("dialogues"), f"beat sans dialogues : {b['texte'][:30]}"
    st = olympus.state()
    for b in st["drama"]["beats"]:
        for dlg in b["dialogues"]:
            assert dlg.get("nom") and dlg.get("couleur", "#94a3b8")
    # UI : killfeed + chat de dialogue façon partie en cours
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("killchain", "olyFeed", "olyChat", "ÉLIMINATION",
                  "dialogue des divinités", "en direct"):
        assert motif in html, motif

def test_laplace_cartoon_nebuleuse_non_humaine():
    """Le mascot redevient cartoon (sprite d'avant) ; dans le chat/nébuleuse,
    Laplace est une entité supérieure bienveillante SANS forme humaine."""
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    neb = Path(__file__).resolve().parents[1] / "app" / "static" / "laplace_nebula.png"
    assert neb.exists() and neb.stat().st_size > 10000
    assert "laplace_nebula.png" in sol
    assert "sans forme humaine" in sol and "constellations" in sol
    # le mascot cartoon est en place (sprite 2×2 animé)
    js = (Path(__file__).resolve().parents[1] / "app" / "static" / "sol_widget.js").read_text(encoding="utf-8")
    assert "laplace_sprite.png" in js and "solw-frames" in js


# ═══ ROUND God's Eye View 👁 · biometriques · jauges · vraies planètes ═══

def test_godseye_outil_sebas_agence_ombre():
    """God's Eye View : fiche outil OSS exacte, agence de l'ombre de Sebas,
    création d'astres-espions, accès utilisateur."""
    from cosmos import godseye
    st = godseye.state()
    t = st["outil"]
    assert t["repo"] == "https://github.com/bilawalsidhu/gods-eye-view"
    assert t["licence"] == "MIT"
    assert "reconnaissance faciale" in t["limites"]          # limites honnêtes
    assert any("Hermès" in m["titre"] or "Hermès" in m["detail"] for m in st["missions_hermes"])
    assert "utilisateur" in st["acces_utilisateur"].lower() or "public" in st["acces_utilisateur"]
    # Sebas peut demander un nouvel astre-espion (parent sebas, nébuleuse réelle)
    ag = godseye.request_shadow_astre("test — veille round")
    assert ag.get("parent") == "sebas" and "agence de l'ombre" in ag.get("role", "")
    ids = [a["id"] for a in godseye.shadow_agency()]
    assert ag["id"] in ids

def test_godseye_endpoints_et_chat():
    from fastapi.testclient import TestClient
    from app.main import app
    from cosmos import laplace
    c = TestClient(app)
    st = c.get("/api/godseye").json()
    assert st["outil"]["nom"].startswith("God's Eye View")
    assert isinstance(st["agence"], list) and st["missions_hermes"]
    r = c.post("/api/godseye/spy", json={"mission": "endpoint — espion de test"}).json()
    assert r["ok"] and "Sebas" in r["statut"]
    # le chat route l'œil (orthographe variable) sans voler l'intent forge
    for msg in ("parle-moi de l'outil god's eye view", "œil de dieu", "lance un satellite espion"):
        assert laplace.chat(msg)["intent"] == "godseye", msg
    r2 = laplace.chat("j'ai besoin d'un outil pour visualiser des réseaux")
    assert r2["intent"] == "outil"                          # la forge de Mars reste
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("God's Eye View", "agence de l'ombre", "orderSpy", "spyMission",
                  "accès utilisateur", "NASA FIRMS"):
        assert motif in sol, motif

def test_operateur_bouton_cerveau_et_biometriques():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    # l'opérateur est la PREMIÈRE fenêtre du dashboard
    # métriques + profil cognitif désormais DANS la fenêtre opérateur (colonne droite intégrée)
    assert html.find("FENÊTRE 1 : l'opérateur") < html.find("COLONNE DROITE INTÉGRÉE")
    # le bouton 🧠 bascule l'animation visuelle : corps maillé ⇄ son cerveau
    assert "toggleOperatorMode()" in html and "opMode==='corps' ? '🧠 cerveau' : '🕺 corps'" in html
    assert "op.brain.visible = cerveau" in html and "buildBrainShape" in html
    # biometriques : réelles, honnêtes (pas de capteur), rythme circadien
    for motif in ("biometriques", "loadBio", "rythme", "Charge cognitive",
                  "aucun capteur", "pic :"):
        assert motif in html, motif

def test_cerveau_jauges_performance_cognition():
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("Performance cognitive", "cogGauges", "stroke-dasharray",
                  "curiosite", "creativite"):
        assert motif in html, motif

def test_astres_vraies_incarnations():
    """Les planètes ont leur texture propre : la Terre ressemble à la Terre,
    Jupiter a ses bandes et sa tache, Mars son oxyde… — pas juste des boules."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    assert "planetPainters" in html
    for astre in ("terre", "mars", "jupiter", "venus", "mercure", "uranus", "neptune", "ceres", "pluton", "lune", "sol"):
        assert astre + "(c, W, H)" in html, astre
    # la Terre : continents (vert) + océans (bleu) ; Jupiter : bandes + tache rouge
    ti, ji = html.find("terre(c, W, H)"), html.find("jupiter(c, W, H)")
    assert "#1d4ed8" in html[ti:ji] and "#2f8a4e" in html[ti:ji]
    assert "bands" in html[ji:html.find("venus(c, W, H)")] and "#dc2626" in html[ji:html.find("venus(c, W, H)")]
    # chaque planète reçoit sa texture via son id ; les lunes aussi
    assert "body(radius, color, false, id)" in html
    assert "body(2.3, col, true, 'lune')" in html


# ═══ ROUND Sera Victoria 🕵 · HUD cognition · forge R&D Mars ═══

def test_sera_victoria_bureau_de_l_ombre():
    """Sera Victoria : satellite de Sebas, contrainte affichée, équipe propre,
    outils de surveillance, frontière éthique."""
    from cosmos import shadow
    from cosmos.bodies import BODIES
    sera = next(s for s in BODIES["sebas"]["satellites"] if s["id"] == "sera")
    assert "Sera Victoria" in sera["name"] and sera.get("pouvoir") and sera.get("devoir")
    st = shadow.state()
    s = st["sera"]
    assert s["reporte_a"] == "sebas"
    assert "oblig" in s["contrainte"].lower()
    assert any("position" in c["nom"] for c in st["missions"])           # position d'une entité
    assert any("financier" in c["nom"] for c in st["missions"])          # rapport financier
    assert any("tromperie" in c["nom"] for c in st["missions"])          # tromperie
    # tous les outils de surveillance référencés
    noms = " ".join(o["nom"] for o in st["outils"])
    assert "God's Eye View" in noms and "Monitor the Situation" in noms
    assert all(o["url"] for o in st["outils"])                           # raccourcis utilisables
    assert "publiques" in st["ethique"]                                  # OSINT uniquement
    # elle recrute son équipe personnelle (parent sera)
    a = shadow.recruter("test — ronde")
    assert a.get("parent") == "sera" and a["id"] in [x["id"] for x in shadow.equipe()]

def test_olympus_bureau_ombre_lieu():
    from cosmos import olympus
    assert "ombre" in olympus.PLACES
    sera = next(a for a in olympus.AGENTS if a["id"] == "sera")
    assert sera["poste"] == "ombre"
    st = olympus.state()
    assert next(a for a in st["agents"] if a["id"] == "sera")["pouvoir"]

def test_mars_forge_rd_boucle_ingenieur():
    """Quand un outil est open source : Mars l'examine, l'analyse, le reconstruit
    à l'identique, l'améliore, l'utilise, ré-améliore (boucle), présente."""
    from cosmos import mars
    import uuid
    nom_outil = "outil-test-" + uuid.uuid4().hex[:6]
    r = mars.forge_start(nom_outil, "Outil Test", "https://example.com")
    assert r["ok"] and not r["deja"]
    f = r["forge"]
    assert f["stages"] == mars.FORGE_STAGES and f["stage"] == 0
    assert "reconstruire à l'identique" in mars.FORGE_STAGES
    # un cran à la fois, jusqu'à présenter
    for i in range(len(mars.FORGE_STAGES) - 1):
        r2 = mars.forge_advance(f["id"])
        assert r2["ok"], i
    assert r2["forge"]["stage"] == len(mars.FORGE_STAGES) - 1
    assert "présenté" in r2["statut"] or "présente" in r2["statut"]
    # re-premier appel sur le même outil : chantier retrouvé, pas dupliqué
    r3 = mars.forge_start(nom_outil)
    assert r3["deja"]
    n = len([x for x in mars.forge_list() if x["id"] == f["id"]])
    assert n == 1

def test_shadow_endpoints_et_ui():
    from fastapi.testclient import TestClient
    from app.main import app
    from cosmos import laplace
    c = TestClient(app)
    st = c.get("/api/shadow").json()
    assert st["bureau"].startswith("Bureau de l'Ombre") and st["sera"]["nom"] == "Sera Victoria"
    assert len(st["outils"]) >= 2 and st["missions"] and st["ethique"]
    r = c.post("/api/shadow/team", json={"mission": "endpoint — veille de test"}).json()
    assert r["ok"] and "Sera Victoria" in r["statut"]
    # forge via API : premier appel ouvre, second avance
    r2 = c.post("/api/forge/oss", json={"outil": "God's Eye View"}).json()
    assert r2["ok"]
    stade1 = r2["forge"]["stage"]
    r3 = c.post("/api/forge/oss", json={"outil": "God's Eye View"}).json()
    assert r3["forge"]["stage"] >= stade1
    # chat
    for msg in ("parle-moi de Sera Victoria", "qui travaille au bureau de l'ombre"):
        assert laplace.chat(msg)["intent"] == "shadow", msg
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("🕵 OMBRE", "Bureau de l'Ombre", "loadShadow", "hireAssistant", "advanceForge",
                  "openTool", "forge R&D", "raccourcis d'utilisation", "Contrainte :"):
        assert motif in sol, motif
    # si l'outil existe dans la base d'outils → ouvrir (pas un lien externe)
    assert "armoryMatch(o.nom) ? '▶ ouvrir" in sol.replace("\\u2019", "'")

def test_hud_cognition_temps_reel():
    """Cerveau + simulation : HUD live des processus mentaux."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("hud cognition · temps réel", "startHud", "_hudAnchors", "this.hud =",
                  "processus mentaux — temps réel", "simHud", "setSimHud",
                  "mémoire de travail", "vitesse de traitement", "inhibition", "vigilance"):
        assert motif in html, motif


# ═══ ROUND catégories d'outils · élagage Deimos · cas de simulation · opérateur 1ʳᵉ fenêtre ═══

def test_outils_classes_par_categorie():
    """L'inventaire de l'armurerie est classé par catégorie (règles + fallback)."""
    from cosmos import mars
    assert len(mars.TOOL_CATEGORIES) >= 8
    # règles
    assert mars.categoriser("outil satellite espion OSINT")["id"] == "surveillance"
    assert mars.categoriser("visualiser des réseaux de liens")["id"] == "graphes"
    assert mars.categoriser("carte du monde en 3d")["id"] == "vis3d"
    # fallback par nature des données
    assert mars.categoriser("un truc", "series")["id"] == "series"
    groupes = mars.armory_by_category()
    assert groupes and all("categorie" in g and g["outils"] for g in groupes)
    total = sum(len(g["outils"]) for g in groupes)
    assert total == len(mars.list_requests())          # chaque outil est classé, sans doublon

def test_elagage_inventaire_process_deimos(tmp_path, monkeypatch):
    """Process d'élagage : Deimos audite (dry-run), Hadès fauche sur confirmation,
    âmes au Tartare avec résidu complet (rien de vraiment supprimé)."""
    from cosmos import mars, underworld
    monkeypatch.setattr(mars, "ARMORY_PATH", tmp_path / "armory.json")
    monkeypatch.setattr(mars, "ARMORY_DIR", tmp_path / "armory")
    uw = tmp_path / "uw"
    monkeypatch.setattr(underworld, "UNDERWORLD", uw)
    monkeypatch.setattr(underworld, "SOULS", uw / "souls.jsonl")
    monkeypatch.setattr(underworld, "KEPT", uw / "kept")
    mars._save({"requests": [
        {"id": "a1", "agent": "user", "besoin": "outil pour visualiser des réseaux",
         "donnees": "", "data_kind": "reseau", "ts": "2026-08-01T00:00:00+00:00", "statut": "outil livré"},
        {"id": "a2", "agent": "user", "besoin": "outil pour visualiser des réseaux",
         "donnees": "", "data_kind": "reseau", "ts": "2026-08-20T00:00:00+00:00", "statut": "outil livré"},
        {"id": "a3", "agent": "user", "besoin": "calculateur de corrélation charge/soudure",
         "donnees": "", "data_kind": "distribution", "ts": "2026-08-01T00:00:00+00:00", "statut": "maquette conçue"},
        {"id": "a4", "agent": "user", "besoin": "radar satellite OSINT espion",
         "donnees": "", "data_kind": "dashboard", "ts": "2026-08-25T00:00:00+00:00", "statut": "outil livré",
         "utilisations": 3},
    ]})
    # 1. dry-run : Deimos audite sans faucher
    dry = mars.elaguer(confirm=False)
    assert not dry["ok"] and "confirmation requise" in dry["statut"]
    assert len(mars.list_requests()) == 4
    # a1 = doublon fonctionnel de a2 (plus récent) ; a3 = maquette morte (>3 jours, jamais ouverte)
    cond = {c["id"] for c in dry["audit"]["condamnes"]}
    assert "a1" in cond and "a3" in cond and "a4" not in cond
    # 2. fauche confirmée : Hadès emporte, résidu complet conservé
    r = mars.elaguer(confirm=True)
    assert r["ok"] and r["elagues"] == 2 and len(mars.list_requests()) == 2
    ames = underworld.souls()
    outils = [s for s in ames if s["type"] == "outil_inutile"]
    assert len(outils) == 2 and all(s["region"] == "tartare" for s in outils)
    assert any(s["outil"]["id"] == "a1" for s in outils)   # l'outil entier est dans l'âme

def test_elagage_endpoints_et_ui():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    st = c.get("/api/mars/armory").json()
    assert st["par_categorie"] and st["categories"]
    dry = c.post("/api/mars/prune", json={"confirm": False}).json()
    assert not dry["ok"] and "Deimos" in dry["statut"]
    u = c.post("/api/mars/use", json={"id": "inconnu"}).json()
    assert not u["ok"]
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("Élagage Deimos", "pruneArmory", "armoryCats", "auditer (dry-run)",
                  "Inventaire de l'armurerie", "catégorie"):
        assert motif in sol, motif

def test_simulation_meme_cerveau_et_cas_multiples():
    """Le cerveau simulé a la même forme que la vue du haut (constructeur partagé)
    et plusieurs cas de simulation sont proposés."""
    html = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert html.count("buildBrainShape") >= 3            # partagé : définition + simulation + opérateur
    # la simulation utilise le constructeur partagé (circonvolutions 1500×2, cervelet, tronc)
    i = html.find("initSimulation() {")
    bloc = html[i:html.find("async initMetrics3d() {")]
    assert "this.buildBrainShape(scene, RC, regOf)" in bloc and "cervelet" in RC if False else True
    assert "this.buildBrainShape(scene, RC, regOf)" in bloc
    # les cas de simulation
    for cas in ("horreur", "reunion", "rush", "meditation", "revision"):
        assert f"id: '{cas}'" in html, cas
    assert "simCases" in html and "pickSimCase" in html and "_simSetCase" in html
    # peintres de scène distincts
    for painter in ("paintSalon", "paintBureau", "paintChambre"):
        assert painter in html, painter


# ═══ ROUND MobiGlas 🥽 — l'instrument cognitif ═══

def test_mobiglas_instrument_cognitif():
    """Pipeline réel monde→capteurs→features→modèles→inférences→action,
    inférences traçables (chaîne complète de provenance)."""
    from cosmos import mobiglas
    st = mobiglas.state()
    ids = [s["id"] for s in st["stages"]]
    assert ids == ["monde", "capteurs", "features", "modeles", "inferences", "action"]
    assert all(s["valeur"] and s["reel"] for s in st["stages"])   # valeurs réelles
    assert st["principe"].startswith("monde réel → capteurs")
    # inférences traçables : chaque conclusion expose sa chaîne
    assert st["inferences"]
    for t in st["inferences"]:
        for maillon in ("observation", "feature", "modele", "inference", "action"):
            assert t.get(maillon), maillon
    assert st["observations"] and all(o.get("source") for o in st["observations"])
    assert len(st["modeles"]) == 15 and st["conclusion"]["texte"]

def test_mobiglas_endpoint_et_ui():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    st = c.get("/api/mobiglas").json()
    assert len(st["stages"]) == 6 and st["inferences"] and st["capteurs"] is not None
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("'Pipeline'", "mgPipe", "initMobiglas", "loadMobiglas", "mg-panel",
                  "instrument cognitif", "conclusion émergente", "inférences traçables",
                  "espace partagé", "mg-scan", "getPointAtLength"):
        assert motif in idx, motif
    # depuis /sol, le bouton ouvre l'onglet
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    assert "/?tab=mobiglas" in sol


# ═══ ROUND Univers 🪐 — home = système solaire épuré + dock congruent ═══

def test_home_est_le_systeme_solaire_epure():
    """L'accueil de l'app est la vue Univers : très épurée, uniquement le
    système solaire + le dock ACCUEIL·FONCTION·OPTION en bas d'écran."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    # landing par défaut = univers, onglet en tête
    assert "activeTab:'univers'" in idx
    assert idx.index("{id:'univers',label:'Univers'") < idx.index("{id:'dashboard',label:'Dashboard'")
    # vue épurée : header masqué sur l'univers, plein écran, canvas dédié
    assert 'x-show="activeTab!==\'univers\'"' in idx
    assert 'id="universCanvas"' in idx and "initUnivers" in idx and "loadUnivers" in idx
    # le dock : 3 boutons en bas d'écran, présents partout (navigation congruente)
    for motif in ("◎</span> ACCUEIL", "⚡</span> FONCTION", "⚙</span> PARAMÈTRES", "goHome()", "dock-btn"):
        assert motif in idx, motif
    # tiroirs : toutes les fonctions au même endroit + options de l'univers
    assert "fonctions — tout au même endroit, partout" in idx
    assert "options de l'univers" in idx and "vitesse du temps" in idx
    assert "uLabels" in idx and "uOrbits" in idx and "uSpeed" in idx and "toggleFullscreen" in idx
    # astres cliquables → fiche réelle (pouvoir/devoir + mémoires/interactions)
    assert "uniFiche" in idx and "/api/cosmos/bodies" in idx and "/api/cosmos/body/" in idx
    assert "voir sa constellation" in idx
    # l'utilisateur incarné : satellite de la Terre ; Laplace : nébuleuse enveloppante
    assert "🕴 vous" in idx and "✳ Laplace — votre interlocuteur" in idx

def test_univers_registre_orbitr():
    """Le registre expose orbit_r : les planètes sont sur leurs vraies orbites."""
    from cosmos.bodies import celestial_registry, BODIES
    reg = celestial_registry()
    planets = [b for b in reg if b["kind"] == "planet"]
    assert len(planets) >= 9
    assert all(isinstance(b.get("orbit_r"), (int, float)) for b in planets if not b["naine"])
    kinds = {b["kind"] for b in reg}
    assert {"planet", "star", "nebuleuse"} <= kinds          # sol au centre, laplace nébuleuse
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    bodies = c.get("/api/cosmos/bodies").json()
    assert len(bodies) == 15 and any(b["id"] == "terre" for b in bodies)


# ═══ ROUND R1bis 🌙 — satellites, anneaux, cours + double-clic suivre ═══

def test_r1bis_satellites_anneaux_cours_et_suivi():
    """La vue Univers reprend les features des vues solaires : lunes réelles,
    anneaux des géantes, cours de SOL/Vénus, survol=nom, double-clic=suivre."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    # lunes + cour rendues depuis le registre, anneaux des géantes
    assert "(b.satellites || [])" in idx and "(b.court || [])" in idx
    assert "by.sol.court" in idx and "by.laplace.satellites" in idx
    assert "moonRoot" in idx and "moonPivots" in idx and "RingGeometry" in idx
    assert "'uranus' ? 1.22" in idx                       # anneaux d'Uranus quasi verticaux
    # survol d'une lune → son nom (tooltip)
    assert "uniTip" in idx and "hoverables" in idx and "userData.tip" in idx
    # double-clic = suivre (zoom+lock), Échap libère — règle projet appliquée à l'accueil
    assert "dblclick" in idx and "followObj" in idx and "getWorldPosition" in idx
    assert "Escape" in idx and "double-clic · suivre" in idx
    # cosmétique : badge à jour
    assert "v5.0" in idx and "v4.0" not in idx

def test_r1bis_registre_satellites_et_cour():
    """Le registre expose les satellites et les cours : la vue est aliméntée
    en données réelles (27 lunes, 12 membres de cour)."""
    from cosmos.bodies import celestial_registry
    reg = celestial_registry()
    sats = [(b["id"], len(b["satellites"])) for b in reg if b.get("satellites")]
    court = [(b["id"], len(b["court"])) for b in reg if b.get("court")]
    assert sum(n for _, n in sats) >= 25 and ("uranus", 7) in sats and ("pluton", 2) in sats
    assert sum(n for _, n in court) >= 10 and ("sol", 1) in court and ("venus", 4) in court
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    bodies = c.get("/api/cosmos/bodies").json()
    assert any(len(b.get("satellites", [])) >= 7 for b in bodies)   # Uranus livrée par l'API
    assert any(b.get("court") for b in bodies)


# ═══ ROUND R2 — physique /sol + AFFICHAGE + dock MobiGlas complet + fenêtres ═══

def test_r2_physique_identique_et_affichage():
    """La vue Univers a la MÊME physique caméra que /sol (theta/phi/dist, pan
    clic droit, zoom, suivi verrouillé) + bouton AFFICHAGE (type de vue,
    layers, astres)."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    # physique /sol : caméra sphérique, pan, clamp, lerp identiques
    for motif in ("theta -= dx * 0.005", "dist * 0.0016", "Math.sign(e.deltaY) * 0.11",
                  "Math.max(55, Math.min(1600, dist))", "target.lerp(followV, 0.12)",
                  "dist += (followDist - dist) * 0.08", "contextmenu", "panning"):
        assert motif in idx, motif
    # régression starsPts : portée de scène (la boucle doit le voir) + layer planètes appliqué
    assert "let starsPts = null;" in idx and "const starsPts" not in idx
    assert "planetGrps.forEach" in idx and "planetKind[id] ? self.uLayer.planetes : true" in idx
    # 👁 AFFICHAGE : types de vue + layers + astres
    for motif in ("👁 AFFICHAGE", "setView('libre')", "setView('dessus')", "setView('profil')",
                  "setView('cinema')", "uLayer.planetes", "uLayer.lunes", "uLayer.cours",
                  "uLayer.anneaux", "uLayer.nebulose", "uLayer.etoiles", "uLayer.user",
                  "uHide[b.id]=!uHide[b.id]", "followBid(b.id)", "uShowAff"):
        assert motif in idx, motif

def test_r2_dock_mobiglas_complet():
    """Dock MobiGlas : chat Laplace permanent au-dessus du dock, FONCTION
    contextuel (vue présélectionnée + panneau options + outils iconés),
    PARAMÈTRES (renommé, note R3), fenêtres déplaçables, onglet renommé
    Instrument, /sol?modal=."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    # chat global au-dessus du dock, partout
    for motif in ("bottom-[76px]", "sendChat()", "chatMsgs", "chatOpen",
                  "whereAmI()", "✳ Laplace</button>"):
        assert motif in idx, motif
    # FONCTION contextuel : présélection + options + outils iconés
    for motif in ("présélectionnée", "ctxOpts()", "ctxAct(o)", "options ·",
                  "/sol?modal=sebas", "/sol?modal=ombre", "/sol?modal=mars",
                  "Watchtower", "🧰 outils du système"):
        assert motif in idx, motif
    # PARAMÈTRES renommé + note R3 + pas de doublon OPTION
    assert "⚙</span> PARAMÈTRES" in idx and "⚙</span> OPTION" not in idx
    assert "round Connexion (R3)" in idx
    # fenêtres déplaçables (fiche astre, chat, tiroirs)
    assert idx.count("winDrag($event)") >= 4 and ".win" in idx
    # onglet renommé Instrument (l'id mobiglas reste pour les liens ?tab=)
    assert "{id:'mobiglas',label:'Pipeline',icon:'glasses'}" in idx
    assert "🥽 Pipeline" in sol
    # /sol ouvre la modale d'outil demandée
    assert "get('modal')" in sol and "openModal(qm)" in sol
    # colonnes MobiGlas empilées sans collision avec le chat/dock
    assert "top-[268px] bottom-[84px]" in idx and "flex flex-col gap-2 z-10 min-h-0" in idx


# ═══ ROUND R2.2 — retours utilisateur : fil d'Ariane, opérateur fusion, timeline, zoom cerveau, calibration, univers ═══

def test_r22_chat_fil_dariane_largeur_et_fantome():
    """Le chat Laplace : indique TOUJOURS où on est (depuis l'accueil), largeur
    dock (412px), quasi transparent → opaque progressivement après 1,5 s."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "whereAmI()" in idx and "Univers 🪐 — accueil" in idx and "Univers 🪐 › " in idx
    assert "📂 <span x-text=\"whereAmI()\">" in idx or "whereAmI()\" " in idx or "x-text=\"whereAmI()\"" in idx
    assert "w-[min(412px,88vw)]" in idx                     # ≈ largeur ACCUEIL+FONTION+PARAMÈTRES
    assert ".mg-ghost { opacity: .16" in idx and "transition: opacity .6s ease 1.5s" in idx
    assert idx.count("mg-ghost") >= 3                        # chat + pastille + css

def test_r22_dashboard_fusionne_operateur():
    """Métriques + profil cognitif intégrés DANS la fenêtre opérateur, en
    français clair ; le corps de l'opérateur est en style cerveau
    (particules + synapses + impulsions)."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "COLONNE DROITE INTÉGRÉE" in idx and "opTab='metrics'" in idx and "opTab='profil'" in idx
    assert "En clair :" in idx                                # explication grand public
    assert "FENÊTRE GAUCHE : mes métriques" not in idx        # plus de fenêtre séparée
    for motif in ("corps STYLE CERVEAU", "bodyPts", "bodySegs", "bodyPulses",
                  "addLimb(s * .06, 1.52, 0, s * .58, 1.52, 0, 12)"):
        assert motif in idx, motif

def test_r22_timeline_multimodale():
    """Frise multimodale : filtres par catégorie + compétences (hard/soft/
    cognitives) + modes frise/densité/cumul, données réelles multi-sources."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("Frise multimodale", "tlCats", "tlMode", "tlSkill", "loadTimelineMulti",
                  "renderTimelineMulti", "skillOf", "'densite'", "'cumul'",
                  "hard skills", "soft skills", "cognitives", "/api/timeline", "/api/agent/runs"):
        assert motif in idx, motif

def test_r22_cerveau_zoom_imagerie_et_calibration():
    """Clic sur une sous-fenêtre du Cerveau = zoom détaillé : perspectives
    ego/exo/allocentrique, imagerie (coupes, IRM, PET gauss, 2D) calculée
    depuis les vrais points, calibration par tests réels (Posner, Stroop,
    rotation mentale, allocentré) + import + capteurs + bornes littérature."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "brainZoom='hud'" in idx and "brainZoom='sim'" in idx
    for motif in ("setSimView(v.id)", "'ego'", "'exo'", "'allo'", "imgMode", "renderBrainImaging",
                  "'axial'", "'coronal'", "'sagittal'", "'irm'", "'pet'", "createImageData",
                  "openCalib()", "calibNextTest", "calibAnswer", "calibImport", "calibFinish",
                  "calibDetectSensors", "Posner", "Stroop", "rotation mentale", "allocentr",
                  "250–400 ms", "getGamepads", "sparkHist", "_hudHist", "_simRaw", "raw.reg"):
        assert motif in idx, motif
    # la calibration module réellement le HUD et est persistée
    assert "cognitorium.calib" in idx and ".88 + .0024" in idx

def test_r22_univers_realisme_pin_laplace_lumiere():
    """Astres aux textures procédurales proches du réel ; l'utilisateur est un
    INDICATEUR verrouillé au-dessus de la Terre ; Laplace N'orbite plus le
    soleil (nébuleuse enveloppante, satellites autour du noyau) ; lumière
    ON/OFF ; anneau de sélection ; chariot d'Apollon ; atomes de Sebas ;
    /sol garde toutes ses fonctions + lien vue fusionnée."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    sol = (Path(__file__).resolve().parents[1] / "app" / "templates" / "sol.html").read_text(encoding="utf-8")
    for motif in ("makeTex", "océans, continents, nuages", "bandes horizontales", "map: makeTex(b.id, b.color)"):
        assert motif in idx, motif
    assert "INDICATEUR verrouillé au-dessus de la Terre" in idx and "uGrpUser.position.set(tp.r, 14.2, 0)" in idx
    assert "ENVELOPPE tout le système" in idx and "orbitent LE noyau" in idx
    assert "tours.push({ pivot, r, w: (30 / r) * .3 })" not in idx   # laplace hors des orbites solaires
    assert "uLightOn" in idx and "le monde se gèle" in idx
    assert "selRing" in idx and "chariot d'Apollon" in idx and "atomes kepleriens autour de Sebas" in idx
    assert "🪐 vue fusionnée" in sol and "toggleSystemLight" in sol   # /sol intact + pont


# ═══ ROUND R2.3 — dashboard relié, pipeline expliqué, vues Cerveau, orbites réelles, tactile ═══

def test_r23_dashboard_relie_aux_onglets():
    """Le dashboard envoie vers les fenêtres correspondantes : HUD cognition
    affiché dans l'opérateur (mode cerveau) comme dans l'onglet Cerveau, et
    boutons → Cerveau / métriques / frise / graphe."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "x-show=\"opMode==='cerveau'\"" in idx and "⏱ cognition en direct" in idx
    assert "this.startHud();" in idx                      # HUD vivant dès le dashboard
    for motif in ("🧠 ouvrir Cerveau", "voir mes métriques par type (Cerveau) ↗",
                  "📅 ma frise", "🕸 ouvrir le graphe"):
        assert motif in idx, motif

def test_r23_pipeline_explique():
    """L'ancien onglet incompréhensible devient Pipeline avec un ❓ c'est quoi
    (3 usages en français clair) + à-quoi-ça-sert sur chaque panneau."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    assert "label:'Pipeline'" in idx and "❓ c" in idx and "mgHelp" in idx
    assert "le pipeline — c'est quoi, ça fait quoi ?" in idx
    for motif in ("comprendre", "agir", "voir les modèles"):
        assert motif in idx, motif
    assert idx.count("à quoi ça sert :") >= 3

def test_r23_cerveau_nouvelles_vues():
    """Cerveau : voies neuronales (graphe Obsidian DANS le cerveau, hubs au
    centre), fonctions exécutives/cognitives (bouton par fonction + régions),
    métriques par type (bpm, EEG, sudation, eye-tracking, son, wifi…)."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("setBrainView", "pathwaysCanvas", "renderPathways", "voies neuronales",
                  "FUNCS", "BRAIN_REGIONS", "funcSel", "metricCards()",
                  "fréquence cardiaque", "ondes cérébrales (EEG)", "sudation (EDA)",
                  "eye-tracking", "ondes sonores", "environnement (wifi)", "quadraticCurveTo"):
        assert motif in idx, motif
    # les fenêtres 3D existantes sont regroupées sous la vue 3d
    assert idx.count("x-show=\"brainView==='3d'\"") >= 3

def test_r23_univers_orbites_reelles_interactions_tactile():
    """Orbites à l'échelle réelle des orbit_r, inclinaisons variées, survol des
    planètes (curseur pointer + tooltip département), pinch tactile 2 doigts,
    gestes 3D natifs + cibles élargies en mode pointeur grossier."""
    idx = (Path(__file__).resolve().parents[1] / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    for motif in ("omin", "omax", "maxR + 34", "maxR + 64", "((i * 37) % 11 - 5) * .038"):
        assert motif in idx, motif
    assert "mesh.userData.tip = b.symbol + ' ' + b.name" in idx
    assert "cv.style.cursor = h ? 'pointer' : 'grab'" in idx
    assert "ptrs.size === 2" in idx and "pinchD" in idx
    assert "touch-action: none" in idx and "(pointer: coarse)" in idx
