"""Configuration de l'agent — variables d'environnement + fichier .env (racine du dépôt).

Priorité : variable d'environnement > fichier .env > défaut.

Variables reconnues :
    AGENT_PROVIDER   : none | openai | ollama   (défaut: none → mode heuristique, sans LLM)
    AGENT_MODEL      : nom du modèle            (défaut: gpt-4o-mini)
    AGENT_BASE_URL   : endpoint compatible OpenAI (défaut: https://api.openai.com/v1)
    AGENT_API_KEY    : clé API (jamais committée ; fallback OPENAI_API_KEY)
    AGENT_EMAIL      : email pour le "polite pool" OpenAlex/Crossref (recommandé)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> dict:
    """Mini-parseur .env (sans dépendance externe)."""
    env = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip('"').strip("'")
    return env


@dataclass
class AgentConfig:
    provider: str = "none"          # none | openai | ollama
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    email: str = "agent-demo@example.org"
    timeout: int = 30
    ollama_url: str = "http://localhost:11434"
    extra: dict = field(default_factory=dict)

    @property
    def llm_requested(self) -> bool:
        return self.provider in ("openai", "ollama")

    @classmethod
    def from_env(cls, dotenv_path: Path | None = None) -> "AgentConfig":
        dotenv = _load_dotenv(dotenv_path or REPO_ROOT / ".env")
        def get(name: str, default: str = "") -> str:
            return os.environ.get(name) or dotenv.get(name) or default

        provider = get("AGENT_PROVIDER", "none").lower()
        if provider in ("", "auto"):
            # auto-détection : clé dispo → openai, sinon heuristique
            provider = "openai" if get("AGENT_API_KEY", get("OPENAI_API_KEY")) else "none"
        return cls(
            provider=provider,
            model=get("AGENT_MODEL", "gpt-4o-mini"),
            base_url=get("AGENT_BASE_URL", "https://api.openai.com/v1"),
            api_key=get("AGENT_API_KEY", get("OPENAI_API_KEY", "")),
            email=get("AGENT_EMAIL", "agent-demo@example.org"),
            ollama_url=get("AGENT_OLLAMA_URL", "http://localhost:11434"),
        )
