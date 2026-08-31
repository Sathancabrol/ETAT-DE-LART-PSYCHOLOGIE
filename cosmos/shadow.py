"""
🕵 Le Bureau de l'Ombre — Sera Victoria, agent de terrain de Sebas.

Inspirée de Seras Victoria (Hellsing) : une agente de terrain redoutable,
au service direct de Sebas 🛠 (l'exécutant divin). Elle travaille seule ou
avec son **équipe personnelle d'assistants**, depuis le **bureau de l'ombre**.

**Contrainte** (ce n'est pas une option) : Sera Victoria est *tenue* de
chercher des informations utiles du monde réel pour aider la chaîne
hiérarchique (Sebas → Mercure/Hermès → SOL → l'utilisateur) :

  • position d'une entité publique (vols ADS-B, navires AIS, satellites) ;
  • rapports financiers et marchés (données publiques) ;
  • détection de tromperie (recoupement multi-sources, signaux faibles).

Ses outils : **tout ce qui existe** — God's Eye View 👁 (OSS MIT),
Monitor the Situation 📡 (carte mondiale de crises + OSINT), les autres
open source, et les outils **fabriqués maison par Mars** (armurerie).

⚠ Frontière éthique du système (affichée partout) : données **publiques**
uniquement (OSINT). Pas de reconnaissance faciale, pas de suivi de
personnes privées, pas de données personnelles — God's Eye View lui-même
le refuse, et le Cognitorium suit la même ligne.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]

SERA: Dict[str, Any] = {
    "id": "sera",
    "nom": "Sera Victoria",
    "titre": "agent de terrain du Bureau de l'Ombre",
    "reporte_a": "sebas",
    "style": "opératrice de nuit — œil rouge, gants de cuir, sang-froid",
    "contrainte": "OBLIGÉE de chercher des informations utiles du monde réel "
                  "(position d'une entité publique, rapport financier, tromperie) "
                  "pour aider la chaîne hiérarchique",
    "pouvoir": "utiliser tous les outils de surveillance (God's Eye View, Monitor the "
               "Situation, OSS, forge de Mars) et commander son équipe d'assistants",
    "devoir": "ne remonter que des informations vérifiables et publiques — jamais "
              "de données personnelles privées, jamais de suivi de personnes",
    "travail": "seule ou avec son équipe personnelle d'assistants, dans le bureau de l'ombre",
}

OUTILS: List[Dict[str, Any]] = [
    {"id": "godseye", "nom": "God's Eye View 👁", "type": "OSS",
     "url": "https://github.com/bilawalsidhu/gods-eye-view",
     "raccourci": "globe 3D photoréaliste — aviation, navires, satellites, séismes, "
                  "incendies FIRMS, caméras publiques, câbles sous-marins",
     "usage": "position d'une entité publique · contexte terrain avant une négociation"},
    {"id": "mts", "nom": "Monitor the Situation 📡", "type": "web",
     "url": "https://monitor-the-situation.com/",
     "raccourci": "carte mondiale de crises en direct — conflits, vols militaires ADS-B, "
                  "navires AIS, marchés, séismes, pannes internet, 50+ flux d'info",
     "usage": "pouls du monde en temps réel · détection d'anomalie · tromperie par recoupement"},
]

CATEGORIES_MISSION = [
    {"id": "position", "nom": "position d'une entité publique", "exemples": [
        "un vol (ADS-B)", "un navire (AIS)", "un satellite", "une infrastructure (datacentre, barrage)"]},
    {"id": "finance", "nom": "rapport financier", "exemples": [
        "marchés et matières premières en direct", "indice de confiance", "exposition d'un secteur"]},
    {"id": "tromperie", "nom": "détection de tromperie", "exemples": [
        "recoupement multi-sources d'une nouvelle", "incohérence entre flux",
        "signal faible contredisant le narratif dominant"]},
]

ETHIQUE = ("Données publiques uniquement (OSINT) : aucune reconnaissance faciale, "
           "aucun suivi de personnes privées, aucune donnée personnelle — la ligne "
           "de God's Eye View est la nôtre.")


def equipe() -> List[Dict[str, Any]]:
    """L'équipe personnelle d'assistants de Sera (astres en orbite autour d'elle)."""
    try:
        from cosmos.nebula import list_agents
        return [a for a in list_agents() if a.get("parent") == "sera"]
    except Exception:
        return []


def recruter(mission: str) -> Dict[str, Any]:
    """Sera recrute un assistant dans son équipe (nébuleuse, validation ☉ SOL)."""
    from cosmos.nebula import create_agent
    mission = (mission or "").strip()[:120] or "assister Sera Victoria sur le terrain"
    nom = "Ombre-" + datetime.now(timezone.utc).strftime("%H%M%S")
    return create_agent(name=nom,
                        role=f"assistant de Sera Victoria (bureau de l'ombre) — {mission}",
                        parent="sera", kind="agent")


def outils_mars() -> List[Dict[str, Any]]:
    """Les outils fabriqués maison par Mars, utilisables par Sera."""
    try:
        from cosmos.mars import list_requests
        return list_requests()[-12:]
    except Exception:
        return []


def state() -> Dict[str, Any]:
    from cosmos import godseye
    from cosmos.mars import forge_list
    return {
        "bureau": "Bureau de l'Ombre — l'agence de terrain de Sebas",
        "sera": SERA,
        "equipe": equipe(),
        "outils": OUTILS,
        "outils_mars": outils_mars(),
        "agence_sebas": godseye.shadow_agency(),
        "missions": CATEGORIES_MISSION,
        "ethique": ETHIQUE,
        "forge": forge_list(),
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
