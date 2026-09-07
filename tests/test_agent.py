"""Tests de l'agent — exécuter avec: .venv/bin/python -m pytest tests/ -v

Tout est hors-ligne (mode démo + fixtures réelles embarquées).
"""
import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from agent.config import AgentConfig          # noqa: E402
from agent.models import Paper, deduplicate   # noqa: E402
from agent.pipeline import run_research       # noqa: E402
from agent.tools import reconstruct_abstract  # noqa: E402
from agent.trust import score_trust, trust_niveau_of  # noqa: E402


# ------------------------------------------------------------------ Trust --
class TestTrustFactor:
    def test_meta_analyse_citee_oa_tres_eleve(self):
        score = score_trust({
            "type_publication": "meta_analyse", "study_design": "meta_analytique",
            "sample_size": 5000, "citations": 350, "is_oa": True,
            "data_open": "TRUE", "code_open": "TRUE", "preregistration": "TRUE",
            "validite": "eleve", "coherence": "coherent",
            "journal": "Psychological Bulletin", "has_doi": True, "has_url": True,
        })
        # M=30 R=20 O=20 C=15 T=15 P=0 → 100
        assert score["trust_factor"] == 100
        assert score["trust_niveau"] == "tres_eleve"

    def test_preprint_faible(self):
        score = score_trust({
            "type_publication": "preprint", "study_design": "correlationnel",
            "sample_size": 15, "citations": 3, "is_oa": True,
            "validite": "faible", "coherence": "partiel",
            "journal": "arXiv", "has_doi": False, "has_url": True,
        })
        # M=5+4+3=12 R=2+2=4 O=5 C=8 T=0 P=10+5=15 → 34-15=14... vérif: M=12,R=4,O=5,C=8,T=0 raw=29, P=15 → 14
        assert score["trust_factor"] < 30
        assert score["trust_niveau"] == "faible"

    def test_niveaux_bornes(self):
        for s in (score_trust({"citations": None, "sample_size": None,
                               "coherence": "contradictoire", "has_doi": False,
                               "journal": ""})["trust_factor"],):
            assert 0 <= s <= 100
        assert trust_niveau_of(29) == "faible"
        assert trust_niveau_of(30) == "modere"
        assert trust_niveau_of(60) == "eleve"
        assert trust_niveau_of(85) == "tres_eleve"

    def test_determinisme(self):
        args = {"type_publication": "article_empirique", "study_design": "correlationnel",
                "sample_size": 185, "citations": 118, "is_oa": True,
                "validite": "modere", "coherence": "partiel",
                "journal": "Teaching and Teacher Education", "has_doi": True, "has_url": True}
        assert score_trust(args) == score_trust(dict(args))


# ----------------------------------------------------------------- Modèles --
class TestModels:
    def test_dedup_par_doi(self):
        a = Paper(doi="10.1038/x", title="Une étude", sources=["OpenAlex"])
        b = Paper(doi="https://doi.org/10.1038/X", title="Une étude", cited_by_count=7, sources=["Crossref"])
        merged = deduplicate([a, b])
        assert len(merged) == 1
        assert merged[0].cited_by_count == 7
        assert set(merged[0].sources) == {"OpenAlex", "Crossref"}

    def test_dedup_par_titre(self):
        a = Paper(title="Learning to Learn!", year=2021)
        b = Paper(title="learning   to learn", year=2021)
        assert len(deduplicate([a, b])) == 1

    def test_reconstruct_abstract(self):
        inv = {"Hello": [0], "world": [1], "beautiful": [2]}
        assert reconstruct_abstract(inv) == "Hello world beautiful"


# ---------------------------------------------------------------- Pipeline --
class TestPipelineDemo:
    def setup_method(self):
        self.out = REPO / "output" / "agent_reports" / "_test_run"
        self.summary = run_research(
            topic="métacognition et apprentissage autorégulé",
            year_min=2020, year_max=2026, max_papers=6,
            cfg=AgentConfig(provider="none"), demo=True, out_dir=self.out,
        )

    def test_sorties_generees(self):
        for key in ("rapport", "bibliographie_md", "bibliographie_bib", "csv"):
            assert Path(self.summary["files"][key]).exists(), key
        assert self.summary["papers"] == 4
        assert self.summary["mode"] == "heuristique"

    def test_trust_tri_decroissant(self):
        with open(self.summary["files"]["csv"], newline="", encoding="utf-8") as f:
            scores = [int(r["trust_factor"]) for r in csv.DictReader(f)]
        assert scores == sorted(scores, reverse=True)

    def test_journal_q1_reconnu_dans_le_score(self):
        """Le journal TATE est Q1 : la transparence doit valoir 15 (et non 10)."""
        with open(self.summary["files"]["csv"], newline="", encoding="utf-8") as f:
            rows = {r["id"]: r for r in csv.DictReader(f)}
        karlen = rows["karlen2023_teachers_as_learners_a"]
        assert karlen["trust_factor"] == "63", karlen["trust_justification"]
        assert "Q1" in karlen["trust_justification"]

    def test_csv_passe_le_validateur_officiel(self):
        """Le CSV de l'agent doit passer scripts/validate_entry.py sans erreur."""
        res = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "validate_entry.py"),
             "--file", self.summary["files"]["csv"]],
            capture_output=True, text=True, cwd=REPO,
        )
        assert "PASSED" in (res.stdout + res.stderr).upper() or res.returncode == 0, \
            f"validate_entry a rejeté le CSV:\n{res.stdout}\n{res.stderr}"

    def test_questions_scientifiques_point_interrogation(self):
        with open(self.summary["files"]["csv"], newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                assert r["question_scientifique"].endswith("?"), r["id"]
                assert len(r["tags"].split(",")) >= 3, r["id"]
