"""Isolation globale : les tests n'écrivent JAMAIS dans le vrai royaume d'Hadès.

L'underworld (registre des âmes + fractions conservées) est redirigé vers un
répertoire temporaire pour chaque test, y compris via les reap indirects
(hades.reap, themis.appliquer, endpoints API…). Le registre réel
output/underworld ne doit contenir que les âmes des vraies fauches.
"""

import pytest


@pytest.fixture(autouse=True)
def _underworld_isole(tmp_path, monkeypatch):
    from cosmos import underworld
    uw = tmp_path / "_uw"
    monkeypatch.setattr(underworld, "UNDERWORLD", uw)
    monkeypatch.setattr(underworld, "SOULS", uw / "souls.jsonl")
    monkeypatch.setattr(underworld, "KEPT", uw / "kept")
    yield
