"""
Compétence : visualisation.

Génère une page HTML autonome (SVG inline, sans CDN ni réseau) avec :
  - barres : trust moyen par domaine ;
  - barres : répartition des types de publication ;
  - timeline : publications par année.
Sauvegardée comme artefact du run, ouvrable hors-ligne.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
from typing import Dict, List

from agent.core.registry import skill, SkillResult

PALETTE = ["#818cf8", "#22d3ee", "#34d399", "#fbbf24", "#fb7185", "#c084fc", "#38bdf8", "#a3e635"]


def _bars(title: str, data: Dict[str, float], unit: str = "") -> str:
    if not data:
        return f"<h3>{escape(title)}</h3><p class='muted'>aucune donnée</p>"
    maxv = max(data.values()) or 1
    rows = []
    for i, (k, v) in enumerate(sorted(data.items(), key=lambda kv: -kv[1])):
        w = max(2, int(v / maxv * 420))
        color = PALETTE[i % len(PALETTE)]
        rows.append(f"<div class='row'><span class='lbl'>{escape(str(k))[:44]}</span>"
                    f"<svg width='440' height='18'><rect x='0' y='3' width='{w}' height='12' rx='6' fill='{color}'/></svg>"
                    f"<span class='val'>{v}{unit}</span></div>")
    return f"<h3>{escape(title)}</h3>" + "".join(rows)


@skill(
    name="visualize",
    description="Génère une page HTML autonome (SVG inline, sans dépendance réseau) : trust par domaine, types de publication, timeline par année.",
    category="synthese",
    triggers=[r"visuali", r"graph", r"figure", r"diagramme", r"chart"],
    examples=[
        "visualiser le trust factor par domaine",
        "générer les graphiques de la base",
    ],
    params={},
    defaults={},
    order=80,
)
def visualize(ctx, **_) -> SkillResult:
    search_results: List[Dict] = ctx.state.get("search_results_dedup") or ctx.state.get("search_results") or []
    if search_results:
        by_year: Dict[str, float] = {str(y): n for y, n in sorted(Counter(
            str(r.get("annee")) for r in search_results if r.get("annee")).items())}
        by_base: Dict[str, float] = dict(Counter(r.get("base") for r in search_results))
        body = (_bars("Résultats par année", by_year) +
                _bars("Résultats par base", by_base))
        title = "Visualisation — résultats de recherche"
    else:
        rows = ctx.read_data_rows()
        if not rows:
            return SkillResult(ok=False, summary="Aucune donnée à visualiser (base vide, aucun résultat de recherche).")
        dom_trust: Dict[str, List[int]] = defaultdict(list)
        for r in rows:
            if (r.get("trust_factor") or "").isdigit():
                dom_trust[r.get("domaine") or "non classé"].append(int(r["trust_factor"]))
        body = (_bars("Trust factor moyen par domaine", {d: round(sum(v)/len(v), 1) for d, v in dom_trust.items()}) +
                _bars("Types de publication", dict(Counter(r.get("type_publication") for r in rows if r.get("type_publication")))) +
                _bars("Publications par année", {str(y): n for y, n in sorted(Counter(
                    r.get("annee") for r in rows if r.get("annee")).items())}))
        title = "Visualisation — base 42 champs"

    html = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<title>{escape(title)} — Agent Cognitorium</title><style>
body{{font-family:'Inter',system-ui,sans-serif;background:#070b14;color:#f1f5f9;margin:0;padding:32px}}
h1{{font-size:22px;margin:0 0 4px}} h3{{font-size:13px;color:#94a3b8;margin:24px 0 8px;text-transform:uppercase;letter-spacing:.08em}}
.row{{display:flex;align-items:center;gap:10px;margin:4px 0}}
.lbl{{width:230px;font-size:12px;color:#cbd5e1;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.val{{font-size:12px;color:#64748b;font-family:monospace}}
.muted{{color:#64748b;font-size:12px}} .sub{{color:#64748b;font-size:12px}}
</style></head><body><h1>{escape(title)}</h1>
<p class="sub">Run {escape(ctx.run_id)} — généré automatiquement, autonome (aucune dépendance réseau)</p>
{body}</body></html>"""
    artifacts = [ctx.save_md("visualisation.html", html)]
    return SkillResult(ok=True, summary="Page de visualisation autonome générée (SVG inline)",
                       artifacts=artifacts,
                       details=[f"Fichier : {artifacts[0]} — ouvrable directement dans un navigateur."])
