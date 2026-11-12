"""Tests du second envoyé Sathyr — aucune connexion réseau, aucun coût."""
from cosmos import sathyr
from cosmos.bodies import BODIES

def test_sathyr_is_a_separate_envoy():
    assert "sathyr" in BODIES
    assert BODIES["sathyr"]["kind"] == "envoye"
    assert "parallèle" in BODIES["sathyr"]["departement"]
    assert sathyr.IDENTITY["independent_of"] == "laplace"
    assert sathyr.IDENTITY["can_execute_actions"] is False

def test_sathyr_silent_when_disabled(monkeypatch):
    monkeypatch.delenv("SATHYR_LLM_URL", raising=False)
    monkeypatch.delenv("SATHYR_LLM_MODEL", raising=False)
    sathyr._SESSIONS.clear()
    assert sathyr.maybe_interject("Sathyr, que penses-tu des risques ?", enabled=False) is None

def test_sathyr_replies_when_addressed(monkeypatch):
    monkeypatch.delenv("SATHYR_LLM_URL", raising=False)
    monkeypatch.delenv("SATHYR_LLM_MODEL", raising=False)
    sathyr._SESSIONS.clear()
    note = sathyr.maybe_interject("Sathyr, la quête de l'immortalité vaut-elle le prix ?", session_id="direct")
    assert note is not None
    assert note["role"] == "sathyr"
    assert note["mode"] == "heuristique"
    assert note["initiative"] == "adresse"

def test_sathyr_does_not_interject_on_every_turn(monkeypatch):
    monkeypatch.delenv("SATHYR_LLM_URL", raising=False)
    monkeypatch.delenv("SATHYR_LLM_MODEL", raising=False)
    monkeypatch.setattr(sathyr.random, "random", lambda: 0.0)
    sathyr._SESSIONS.clear()
    message = "Je veux une preuve du pouvoir et des limites du système, quels risques existent ?"
    first = sathyr.maybe_interject(message, session_id="cooldown")
    second = sathyr.maybe_interject(message, session_id="cooldown")
    third = sathyr.maybe_interject(message, session_id="cooldown")
    assert first is not None and first["initiative"] == "spontanee"
    assert second is None and third is None

def test_local_model_may_choose_silence(monkeypatch):
    monkeypatch.setattr(sathyr, "_local_model_decision",
                        lambda *args: {"speak": False, "text": ""})
    sathyr._SESSIONS.clear()
    assert sathyr.maybe_interject("Question détaillée sur les risques et la preuve.",
                                 session_id="model") is None

def test_remote_model_url_rejected(monkeypatch):
    monkeypatch.setenv("SATHYR_LLM_URL", "https://api.example.com/v1/chat/completions")
    monkeypatch.setenv("SATHYR_LLM_MODEL", "not-used")
    assert sathyr._local_model_decision("salut", "bonjour") is None
