"""
Cosmos — le système solaire du Cognitorium.

SOL ☉ orchestre les planètes (Uranus ♅ recherche, Vénus ♀ finances),
approuve leurs interactions, juge l'intégrité et sert d'interface.
"""

from cosmos import bodies, ledger, venus, sol, bus  # noqa: F401


def get_system():
    from cosmos.system import get_system as _gs
    return _gs()
