"""Couche d'abstraction LLM : endpoints compatibles OpenAI + Ollama local.

Chaque provider expose complete(system, user) -> str | None.
None signifie "indisponible / échec" : le pipeline bascule alors en mode heuristique.
Aucune clé n'est jamais loggée ni committée.
"""
from __future__ import annotations

import json
import logging

import requests

from .config import AgentConfig

log = logging.getLogger("agent.llm")


class BaseLLM:
    name = "base"

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str | None:
        raise NotImplementedError


class OpenAICompatLLM(BaseLLM):
    """Tout endpoint compatible OpenAI : OpenAI, Mistral, Groq, vLLM, LM Studio…"""

    name = "openai-compatible"

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str | None:
        try:
            r = requests.post(
                f"{self.cfg.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.cfg.api_key}"},
                json={
                    "model": self.cfg.model,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=self.cfg.timeout,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM openai-compatible indisponible : %s", exc)
            return None


class OllamaLLM(BaseLLM):
    """Ollama en local (http://localhost:11434)."""

    name = "ollama"

    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg

    def complete(self, system: str, user: str, temperature: float = 0.2) -> str | None:
        try:
            r = requests.post(
                f"{self.cfg.ollama_url.rstrip('/')}/api/chat",
                json={
                    "model": self.cfg.model,
                    "stream": False,
                    "options": {"temperature": temperature},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=max(self.cfg.timeout, 120),
            )
            r.raise_for_status()
            return r.json()["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            log.warning("LLM ollama indisponible : %s", exc)
            return None


def get_llm(cfg: AgentConfig) -> BaseLLM | None:
    """Retourne le client LLM configuré, ou None (mode 100 % heuristique)."""
    if cfg.provider == "openai" and cfg.api_key:
        return OpenAICompatLLM(cfg)
    if cfg.provider == "ollama":
        return OllamaLLM(cfg)
    return None


def extract_json(text: str | None) -> dict | None:
    """Extrait le premier objet JSON valide d'une réponse LLM (tolère les clôtures markdown)."""
    if not text:
        return None
    text = text.strip()
    if "```" in text:  # retire les clôtures markdown
        for part in text.split("```"):
            part = part.strip()
            if part.startswith("json"):
                part = part[4:]
            if part.startswith("{"):
                text = part
                break
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None
