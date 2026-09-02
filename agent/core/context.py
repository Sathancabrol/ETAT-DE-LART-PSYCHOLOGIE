"""
Contexte d'exécution partagé par les compétences pendant un run.

- Résout les chemins du dépôt (racine, data/, docs/, output/).
- Fournit un état partagé (dict) pour transmettre les résultats d'une
  compétence à la suivante (ex: résultats de recherche → déduplication).
- Fournit un client HTTP robuste : timeout court, 1 retry, et repli
  automatique sur des fixtures locales (mode dégradé clairement signalé)
  quand le réseau est indisponible.
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

ROOT = Path(__file__).resolve().parents[2]   # racine du dépôt
FIXTURES_DIR = ROOT / "agent" / "fixtures"
RUNS_DIR = ROOT / "output" / "agent_runs"
DATA_CSV = ROOT / "data" / "nodes_etat_art_psychologie.csv"

# ── Identité de l'agent (source de vérité unique) ─────────────────────────
# Uranus (Ouranos) : divinité primordiale du ciel chez les Grecs — « celui qui
# couvre le ciel » —, père des Titans. La planète ♅ porte son nom : l'agent
# cartographie le ciel de la connaissance.
AGENT_NAME = "Uranus"
AGENT_SYMBOL = "♅"          # symbole astronomique/astrologique d'Uranus
AGENT_TAGLINE = "Agent chercheur scientifique — cartographe du ciel de la connaissance"

MAILTO = os.environ.get("AGENT_CROSSREF_MAILTO", "cognitorium-agent@example.org")

# AGENT_OFFLINE=1 force le mode dégradé (fixtures) sans tenter le réseau
FORCE_OFFLINE = os.environ.get("AGENT_OFFLINE", "").strip() in {"1", "true", "TRUE", "yes"}


class AgentContext:
    """Contexte d'un run : identité, état partagé, espace d'artefacts, HTTP."""

    def __init__(self, run_id: Optional[str] = None, max_results: int = 10,
                 timeout: int = 15):
        self.run_id = run_id or (datetime.now(timezone.utc).strftime("run_%Y%m%d_%H%M%S")
                                 + "_" + uuid.uuid4().hex[:4])
        self.run_dir = RUNS_DIR / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.max_results = max_results
        self.timeout = timeout
        self.state: Dict[str, Any] = {}      # état partagé entre compétences
        self.offline_hits: int = 0           # nb de replis sur fixtures pendant le run
        self.started_at = time.time()

    # ── Artefacts ──────────────────────────────────────────────────────────

    def artifact_path(self, filename: str) -> Path:
        return self.run_dir / filename

    def save_json(self, filename: str, payload: Any) -> str:
        p = self.artifact_path(filename)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(p.relative_to(ROOT))

    def save_md(self, filename: str, text: str) -> str:
        p = self.artifact_path(filename)
        p.write_text(text, encoding="utf-8")
        return str(p.relative_to(ROOT))

    # ── Accès base 42 champs ───────────────────────────────────────────────

    def read_data_rows(self, csv_path: Optional[str] = None) -> List[Dict[str, str]]:
        path = Path(csv_path) if csv_path else DATA_CSV
        if not path.exists():
            return []
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def data_headers(self, csv_path: Optional[str] = None) -> List[str]:
        path = Path(csv_path) if csv_path else DATA_CSV
        if not path.exists():
            return []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            return next(reader, [])

    # ── HTTP robuste + repli fixtures ──────────────────────────────────────

    def http_get(self, url: str, params: Optional[Dict[str, Any]] = None,
                 fixture: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """GET JSON. En cas d'échec réseau : repli sur fixture locale si fournie.

        Retourne {"ok": bool, "json": ..., "offline": bool, "error": str|None}
        """
        if not FORCE_OFFLINE:
            last_err = None
            for attempt in (1, 2):
                try:
                    r = requests.get(url, params=params, timeout=self.timeout,
                                     headers={"User-Agent": f"CognitoriumAgent/1.0 (mailto:{MAILTO})",
                                              **(headers or {})})
                    r.raise_for_status()
                    return {"ok": True, "json": r.json(), "offline": False, "error": None}
                except Exception as e:  # réseau, DNS, 5xx, timeout…
                    last_err = str(e)
                    time.sleep(0.6)
        else:
            last_err = "mode hors-ligne forcé (AGENT_OFFLINE=1)"

        # Repli fixtures
        if fixture:
            fp = FIXTURES_DIR / fixture
            if fp.exists():
                self.offline_hits += 1
                return {"ok": True, "json": json.loads(fp.read_text(encoding="utf-8")),
                        "offline": True,
                        "error": f"réseau indisponible ({last_err}) — fixtures de démonstration utilisées"}
        return {"ok": False, "json": None, "offline": True, "error": last_err}


# ── Extraction de paramètres depuis le texte de la tâche ──────────────────

DOI_RE = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)')
YEARS_RANGE_RE = re.compile(r'\b(20\d{2})\s*(?:[-–—à/]|jusqu.[?\s]*\à|\bto\b)\s*(20\d{2})\b', re.I)
SINGLE_YEAR_RE = re.compile(r'\b(20\d{2})\b')
SINCE_RE = re.compile(r'\bdepuis\s+(\d+)\s*(jours?|j|semaines?|sem?\.?|mois)\b', re.I)

DOMAIN_LEXICON: Dict[str, str] = {
    "attention": "attention",
    "mémoire": "memory working memory",
    "memoire": "memory working memory",
    "fonctions exécutives": "executive function",
    "executives": "executive function",
    "métacognition": "metacognition",
    "metacognition": "metacognition",
    "cognition incarnée": "embodied cognition",
    "incarnee": "embodied cognition",
    "4e": "embodied enacted extended cognition",
    "émotion": "emotion cognition",
    "emotion": "emotion cognition",
    "psychothérapie": "psychotherapy",
    "psychotherapie": "psychotherapy",
    "dépression": "depression treatment",
    "exercice": "exercise cognition",
    "vieillissement": "aging cognition",
    "éducation": "education learning",
    "education": "education learning",
    "motivation": "motivation self-determination",
    "attachement": "attachment",
    "personnalité": "personality traits",
    "personnalite": "personality traits",
    "sommeil": "sleep cognition",
    "douleur": "chronic pain psychology",
    "stress": "stress occupational",
    "télétravail": "remote work",
    "teletravail": "remote work",
    "désinformation": "misinformation",
    "desinformation": "misinformation",
    "biais": "cognitive bias",
    "méta-analyse": "meta-analysis psychology",
    "meta-analyse": "meta-analysis psychology",
    "préenregistrement": "preregistration",
    "reenregistrement": "preregistration",
    "btp": "construction automation robotics AI",
    "construction": "construction automation robotics AI",
    "travaux publics": "civil engineering construction automation",
    "chantier": "construction site automation robotics",
    "robotique": "construction robotics automation",
    "visière": "augmented reality head-mounted display construction",
    "visiere": "augmented reality head-mounted display construction",
    "hud": "head-up display augmented reality",
    "exosquelette": "exoskeleton construction worker",
    "drone": "drone construction site monitoring",
    "infrastructure": "infrastructure construction technology",
    "jumeau numérique": "digital twin construction",
}


def extract_dois(task: str) -> List[str]:
    return [m.group(1).rstrip(".,;)") for m in DOI_RE.finditer(task)]


def extract_years(task: str) -> Optional[Dict[str, int]]:
    m = YEARS_RANGE_RE.search(task)
    if m:
        return {"from": int(m.group(1)), "to": int(m.group(2))}
    ys = [int(y) for y in SINGLE_YEAR_RE.findall(task)]
    if ys:
        y = max(ys)
        return {"from": y, "to": y}
    return None


def extract_since_days(task: str, default: int = 30) -> int:
    m = SINCE_RE.search(task)
    if not m:
        return default
    n = int(m.group(1))
    unit = m.group(2).lower()
    if unit.startswith("sem"):
        return n * 7
    if unit.startswith("mois") or unit == "m":
        return n * 30
    return n


def extract_query(task: str) -> str:
    """Transforme la tâche en requête de recherche exploitable."""
    t = task.lower()
    terms: List[str] = []
    for key, query in DOMAIN_LEXICON.items():
        if key in t and query not in terms:
            terms.append(query)
    if "méta-analyse" in t or "meta-analyse" in t or "meta-analysis" in t:
        q = "meta-analysis psychology"
        if q not in terms:
            terms.append(q)
    if not terms:
        # fallback : mots significatifs de la tâche
        stop = {"les", "des", "une", "sur", "pour", "dans", "avec", "que", "qui", "est",
                "rechercher", "recherche", "cherche", "trouve", "Trouver", "articles",
                "article", "publications", "publication", "littérature", "litterature",
                "sur", "de", "du", "la", "le", "et", "à", "a"}
        words = [w for w in re.findall(r"[a-zà-ÿ-]{3,}", t) if w not in stop]
        terms.append(" ".join(dict.fromkeys(words)) if words else "psychology")
    return " ".join(dict.fromkeys(terms))[:200]
