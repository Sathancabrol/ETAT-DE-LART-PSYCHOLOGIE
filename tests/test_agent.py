"""
Tests de l'agent chercheur — exécutables 100 % hors-ligne (AGENT_OFFLINE=1).

Lancement : python -m pytest tests/ -v
"""

import json
import os
import sys
from pathlib import Path

# Forcer le mode hors-ligne avant tout import de l'agent
os.environ["AGENT_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from agent import Agent, list_skills
from agent.core.context import (AgentContext, extract_dois, extract_years,
                                extract_since_days, extract_query)
from agent.core.planner import build_plan
from agent.core.registry import get_skill


# ── Registre ────────────────────────────────────────────────────────────────

def test_11_competences_enregistrees():
    names = {s.name for s in list_skills()}
    attendues = {"search_literature", "enrich_doi", "citation_metrics", "deduplicate",
                 "validate_entries", "trust_scoring", "bias_assessment",
                 "prisma_flow", "synthesize", "visualize", "monitor_watch"}
    assert attendues <= names, f"manquantes : {attendues - names}"


def test_unicite_et_catalogue():
    cats = [s.catalog() for s in list_skills()]
    assert all("name" in c and "description" in c and "examples" in c for c in cats)
    assert all(c["examples"] for c in cats), "chaque compétence doit avoir un exemple"


# ── Extraction de paramètres ───────────────────────────────────────────────

def test_extraction_doi():
    assert extract_dois("enrichir 10.1037/bul0000439 et 10.1002/wps.21203 svp") == \
        ["10.1037/bul0000439", "10.1002/wps.21203"]


def test_extraction_annees():
    assert extract_years("méta-analyses 2024-2026")["from"] == 2024
    assert extract_years("en 2025")["to"] == 2025
    assert extract_years("sans année précise") is None


def test_extraction_depuis():
    assert extract_since_days("veille depuis 2 semaines") == 14
    assert extract_since_days("veille depuis 3 mois") == 90
    assert extract_since_days("rien") == 30


def test_extraction_requete():
    assert "meta-analysis" in extract_query("rechercher les méta-analyses sur l'attention")
    assert "attention" in extract_query("articles attention")


# ── Planificateur à règles ──────────────────────────────────────────────────

def test_plan_pipeline_systematique():
    plan = build_plan("recherche systématique des méta-analyses attention 2024-2026")
    names = [s.skill for s in plan.steps]
    assert names[0] == "search_literature"
    assert {"deduplicate", "prisma_flow", "synthesize"} <= set(names)


def test_plan_validation():
    plan = build_plan("valider la base")
    assert [s.skill for s in plan.steps] == ["validate_entries"]


def test_plan_toujours_non_vide():
    plan = build_plan("n'importe quoi de vague")
    assert len(plan.steps) >= 1


def test_plan_doi():
    plan = build_plan("enrichir le DOI 10.1037/bul0000439")
    assert plan.steps[0].skill == "enrich_doi"
    assert plan.steps[0].params["dois"] == ["10.1037/bul0000439"]


# ── Compétences sur la vraie base ───────────────────────────────────────────

@pytest.fixture(scope="module")
def ctx():
    c = AgentContext(run_id="test_run")
    c.state["task"] = "test"
    return c


def test_validate_entries_base_reelle(ctx):
    res = get_skill("validate_entries").fn(ctx)
    assert res.ok
    assert res.data["lignes"] == 14
    assert res.data["colonnes"] == 42
    assert res.data["erreurs"] == 0


def test_trust_scoring(ctx):
    res = get_skill("trust_scoring").fn(ctx)
    assert res.ok
    assert res.data["moyennes"]["moyen_declare"] == 73.2


def test_bias_assessment(ctx):
    res = get_skill("bias_assessment").fn(ctx)
    assert res.ok
    assert sum(res.data["distribution"].values()) == 14


def test_deduplicate_base(ctx):
    res = get_skill("deduplicate").fn(ctx, source="base")
    assert res.ok


def test_synthesize_base(ctx):
    res = get_skill("synthesize").fn(ctx, source="base")
    assert res.ok
    assert res.data["domaines"]


def test_visualize_base(ctx):
    res = get_skill("visualize").fn(ctx)
    assert res.ok
    assert Path(ROOT / res.artifacts[0]).exists()


# ── Compétences réseau en mode dégradé (fixtures) ───────────────────────────

def test_search_literature_degrade(ctx):
    ctx.state["task"] = "rechercher les méta-analyses attention 2024-2026"
    res = get_skill("search_literature").fn(ctx)
    assert res.ok and res.degraded
    assert res.data["total"] >= 4
    assert all(r["titre"] for r in res.data["resultats"])


def test_deduplicate_resultats_recherche(ctx):
    ctx.state["task"] = "recherche attention"
    get_skill("search_literature").fn(ctx)  # peuple state["search_results"]
    res = get_skill("deduplicate").fn(ctx, source="search")
    assert res.ok
    assert ctx.state["prisma"]["identifies"] >= ctx.state["prisma"]["apres_deduplication"]


def test_prisma_flow_apres_recherche(ctx):
    res = get_skill("prisma_flow").fn(ctx)
    assert res.ok
    assert res.data["identifies"] > 0


def test_enrich_doi_degrade(ctx):
    ctx.state["task"] = "enrichir le DOI 10.1037/bul0000439"
    res = get_skill("enrich_doi").fn(ctx, dois=["10.1037/bul0000439"])
    assert res.ok and res.degraded
    draft = res.data["drafts"][0]
    assert draft["doi"] == "10.1037/bul0000439"
    assert draft["question_scientifique"].endswith("?")


def test_monitor_watch_degrade(ctx):
    ctx.state["task"] = "veille métacognition depuis 30 jours"
    res = get_skill("monitor_watch").fn(ctx)
    assert res.ok and res.degraded
    assert len(res.data["resultats"]) >= 3


# ── Agent bout-en-bout ──────────────────────────────────────────────────────

def test_agent_run_complet_hors_ligne():
    agent = Agent(use_llm=False)
    trace = agent.run("recherche systématique des méta-analyses attention 2024-2026")
    assert trace["statut"] in {"succès", "partiel"}
    assert trace["mode_degrade"]
    assert [s["skill"] for s in trace["steps"]][0] == "search_literature"
    run_dir = ROOT / "output" / "agent_runs" / trace["run_id"]
    assert (run_dir / "trace.json").exists()
    assert (run_dir / "report.md").exists()


def test_agent_dry_run():
    plan = Agent(use_llm=False).plan("valider la base")
    assert plan.brain == "regles"
    assert plan.steps[0].skill == "validate_entries"
