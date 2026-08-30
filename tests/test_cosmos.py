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
    assert len(planets()) == 8
    # find_body retrouve satellites et cours + leur parent
    io, par = find_body("io")
    assert io and par["name"] == "Jupiter"
    peitho, par2 = find_body("peitho")
    assert peitho and par2["name"] == "Mercure"
    assert find_body("pluton") == (None, None)
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
    assert c.get("/api/cosmos/body/pluton").status_code == 404
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
