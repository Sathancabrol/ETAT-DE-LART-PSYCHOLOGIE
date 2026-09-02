"""
Compétence : flux PRISMA 2020.

Agrège les compteurs du run (identifiés → dédupliqués → screening →
inclus) et des exécutions précédentes, met à jour l'état PRISMA persistant
(output/prisma_state.json) et régénère le diagramme Mermaid.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Dict

from agent.core.registry import skill, SkillResult
from agent.core.context import ROOT

STATE_PATH = ROOT / "output" / "prisma_state.json"


def _load_state() -> Dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"historique": []}


@skill(
    name="prisma_flow",
    description="Met à jour et restitue le flux PRISMA 2020 (identifiés, dédupliqués, screenés, inclus) avec diagramme Mermaid régénéré.",
    category="synthese",
    triggers=[r"prisma", r"flux", r"flow", r"diagramme\s+de\s+flux"],
    examples=[
        "mettre à jour le flux PRISMA",
        "générer le diagramme PRISMA après déduplication",
    ],
    params={},
    defaults={},
    order=60,
)
def prisma_flow(ctx, **_) -> SkillResult:
    p: Dict[str, Any] = ctx.state.get("prisma") or {}
    identified = p.get("identifies")
    dedup = p.get("apres_deduplication")

    # Sans compteurs de run, on restitue l'état persistant
    state = _load_state()
    if identified is None:
        if not state.get("historique"):
            return SkillResult(ok=False, summary="Aucun compteur PRISMA disponible : lancez d'abord une recherche + déduplication.")
        last = state["historique"][-1]
        identified, dedup = last["identifies"], last["apres_deduplication"]
    else:
        state["historique"].append({"date": date.today().isoformat(),
                                    "run": ctx.run_id,
                                    "identifies": identified,
                                    "apres_deduplication": dedup})
        state["dernier"] = {"date": date.today().isoformat(), "run": ctx.run_id,
                            "identifies": identified, "apres_deduplication": dedup}
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    n = ctx.state.get("prisma_screenes") or dedup or 0
    mermaid = f"""```mermaid
flowchart TD
    A[Identifiés via bases de données<br/>{identified} registres] --> B[Après déduplication<br/>{dedup}]
    B --> C[Screening titre/résumé<br/>{n}]
    C --> D[Exclus : {max(0, (dedup or 0) - (n or 0))}]
    C --> E[Évalués plein texte<br/>{n}]
    E --> F[Inclus dans la synthèse<br/>{len(ctx.state.get('search_results_dedup') or [])}]
```"""
    lines = ["# Flux PRISMA 2020 — état", "",
             f"- Identifiés : **{identified}**",
             f"- Après déduplication : **{dedup}**",
             f"- Screenés (estimation) : **{n}**",
             f"- Historique : {len(state.get('historique', []))} mise(s) à jour", "",
             "## Diagramme", "", mermaid]
    artifacts = [ctx.save_md("prisma_flux.md", "\n".join(lines)),
                 str(STATE_PATH.relative_to(ROOT))]
    return SkillResult(ok=True,
                       summary=f"PRISMA : {identified} identifiés → {dedup} après déduplication ({len(state.get('historique', []))} mises à jour cumulées)",
                       artifacts=artifacts,
                       details=[f"Identifiés : {identified}", f"Après déduplication : {dedup}"],
                       data={"identifies": identified, "apres_deduplication": dedup})
