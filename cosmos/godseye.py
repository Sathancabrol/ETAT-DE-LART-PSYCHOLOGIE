"""
👁 God's Eye View — l'outil de veille mondiale de Sebas, au service de Mercure/Hermès.

Outil open source (MIT) de Bilawal Sidhu : un simulateur de satellite-espion dans
le navigateur, **avec des données réelles** — aviation, navires, satellites,
séismes, trafic, incendies (NASA FIRMS), caméras publiques, barrages,
datacentres, câbles sous-marins — sur un globe 3D photoréaliste (CesiumJS),
pilotable à la voix. Le projet ne fait **aucune** reconnaissance faciale ni
suivi de personnes, et avertit que ses données peuvent être retardées,
incomplètes ou erronées.

Dans le Cognitorium :
  • Sebas 🛠 (outilleur divin) manie l'œil pour **aider Mercure/Hermès ✉** —
    trouver des datas réelles sur le monde, contextualiser une prospection,
    préparer le terrain d'Argus (études de marché), situer une infrastructure ;
  • si l'œil ne suffit pas, Sebas peut **demander la création de nouveaux
    astres** : son **agence de l'ombre** — des astres-espions en orbite autour
    de lui, chargés de récolter les informations utiles ;
  • l'**utilisateur accède aussi à l'outil** (lien public + fiche dans /sol).
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[1]

TOOL: Dict[str, Any] = {
    "id": "godseye",
    "nom": "God's Eye View 👁",
    "repo": "https://github.com/bilawalsidhu/gods-eye-view",
    "licence": "MIT",
    "auteur": "Bilawal Sidhu",
    "nature": "simulateur de satellite-espion dans le navigateur — données réelles",
    "donnees_reelles": ["aviation en direct", "navires", "satellites", "séismes",
                        "trafic", "incendies (NASA FIRMS)", "caméras publiques (~800)",
                        "barrages (704)", "datacentres (4 351)", "câbles sous-marins (712)"],
    "stack": "JavaScript (Vite) · CesiumJS · Google Photorealistic 3D Tiles · "
             "agent vocal temps réel (28 outils : caméra, annotation, analyse, console)",
    "limites": "aucune recherche de personnes nommées, aucune reconnaissance faciale, "
               "aucun suivi d'individus ; les données peuvent être retardées, "
               "incomplètes, modélisées ou erronées (avis officiel du projet).",
    "role_dans_le_systeme": "Sebas 🛠 manie l'œil pour aider Mercure/Hermès ✉ : "
                            "trouver des datas sur le monde et aider l'utilisateur "
                            "dans son interaction avec lui.",
}


def installed() -> bool:
    """L'outil est-il cloné localement (tools/gods-eye-view) ?"""
    return (REPO / "tools" / "gods-eye-view").exists()


def _agency_tag(agent: Dict[str, Any]) -> bool:
    role = (agent.get("role") or "").lower()
    return "agence de l'ombre" in role or "espion" in role


def shadow_agency() -> List[Dict[str, Any]]:
    """Les astres-espions de Sebas (sa cour de l'ombre, nébuleuse incluse)."""
    try:
        from cosmos.nebula import list_agents
        ags = [a for a in list_agents() if a.get("parent") == "sebas" and _agency_tag(a)]
    except Exception:
        ags = []
    return ags


def request_shadow_astre(mission: str) -> Dict[str, Any]:
    """Sebas demande un nouvel astre-espion : il entre en orbite autour de lui
    (validation ☉ SOL via le flux nébuleuse habituel)."""
    from cosmos.nebula import create_agent
    mission = (mission or "").strip()[:120] or "veille générale du monde extérieur"
    nom = "Œil-" + datetime.now(timezone.utc).strftime("%H%M%S")
    return create_agent(name=nom,
                        role=f"agence de l'ombre de Sebas — espion : {mission}",
                        parent="sebas", kind="satellite")


def missions_hermes() -> List[Dict[str, str]]:
    """Ce que l'œil apporte concrètement à Mercure/Hermès et à l'utilisateur."""
    return [
        {"titre": "prospection ancrée", "detail": "situer un client, un site, une "
         "infra avant un échange — Peitho (Mercure/Hermès) n'argument plus dans le vide"},
        {"titre": "études de marché vivantes", "detail": "Argus (cour de Mercure/Hermès) "
         "croise l'activité réelle (trafic, incendies, séismes, vols) avec ses signaux faibles"},
        {"titre": "veille infrastructure", "detail": "datacentres, câbles "
         "sous-marins, barrages — le terrain physique du système"},
        {"titre": "contexte négociation", "detail": "Éros connaît l'état du monde "
         "avant de conclure un accord entre planètes"},
    ]


def state() -> Dict[str, Any]:
    return {"outil": TOOL, "installe": installed(),
            "sebas": "Sebas 🛠 peut utiliser l'œil et demander de nouveaux astres-espions",
            "agence": shadow_agency(), "missions_hermes": missions_hermes(),
            "acces_utilisateur": "l'outil est public (MIT) — lien direct dans /sol, "
                                 "panneau Sebas 👁, et l'agence de l'ombre se commande "
                                 "depuis la fiche de Sebas",
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
