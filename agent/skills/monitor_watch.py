"""
Compétence : veille scientifique.

Interroge OpenAlex par défaut depuis N jours (défaut 30) sur les
domaines du projet (lexicon de SEARCH_STRATEGIES) ou sur un sujet
explicite, trie par citations décroissantes, et produit un rapport
markdown « nouveautés à surveiller ».
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from agent.core.registry import skill, SkillResult
from agent.core.context import extract_query, extract_since_days
from agent.skills.search_literature import _norm_openalex

VEILLE_DOMAINS = {
    "attention": "attention control",
    "mémoire / working memory": "working memory",
    "métacognition": "metacognition education",
    "cognition incarnée 4E": "embodied cognition",
    "exercice-cognition": "exercise cognition",
    "psychothérapies": "psychotherapy meta-analysis",
    "vieillissement": "cognitive aging",
    "open science / réplication": "replication crisis preregistration",
}


@skill(
    name="monitor_watch",
    description="Veille scientifique : nouveautés OpenAlex depuis N jours sur les domaines du projet (ou un sujet donné), triées par citations, avec rapport markdown.",
    category="veille",
    triggers=[r"veille", r"nouveaut[ée]s?", r"nouveaux?\s+(articles|papiers)", r"surveiller?", r"derni[èe]res?\s+pub", r"monitor"],
    examples=[
        "faire la veille sur la métacognition depuis 30 jours",
        "quelles nouveautés depuis 2 semaines ?",
        "surveiller les publications exercise cognition",
    ],
    params={"since_days": "fenêtre en jours (défaut 30)", "subject": "sujet spécifique (défaut : tous les domaines du projet)"},
    defaults={"since_days": 30},
    order=90,
)
def monitor_watch(ctx, since_days: int = 0, subject: str = "", **_) -> SkillResult:
    task = ctx.state.get("task", "")
    if not since_days:
        since_days = extract_since_days(task)
    if not subject:
        for key in VEILLE_DOMAINS:
            if key.split()[0].lower() in task.lower():
                subject = VEILLE_DOMAINS[key]
                break
    since = (date.today() - timedelta(days=since_days)).isoformat()

    queries: Dict[str, str] = ({subject: subject} if subject
                               else VEILLE_DOMAINS)
    all_new: List[Dict[str, Any]] = []
    offline = False
    errors: List[str] = []
    per_topic: Dict[str, int] = {}

    for label, q in list(queries.items())[:6]:
        res = ctx.http_get(
            "https://api.openalex.org/works",
            params={"search": q, "per-page": 5, "sort": "cited_by_count:desc",
                    "filter": f"from_publication_date:{since},type:article"},
            fixture="openalex_veille.json")
        if not res["ok"]:
            errors.append(f"{label} : {res['error']}")
            continue
        offline = offline or res["offline"]
        works = (res["json"] or {}).get("results", [])
        per_topic[label] = len(works)
        for w in works:
            n = _norm_openalex(w)
            n["sujet"] = label
            all_new.append(n)

    all_new.sort(key=lambda r: -(r.get("citations") or 0))
    ctx.state["search_results"] = ctx.state.get("search_results") or all_new

    lines = [f"# Veille scientifique — {since} → aujourd'hui", "",
             f"- Fenêtre : **{since_days} jours** | sujets : {len(queries)} | nouveautés : **{len(all_new)}**", ""]
    for label, q in queries.items():
        items = [r for r in all_new if r["sujet"] == label]
        if not items:
            continue
        lines += [f"## {label}", ""]
        for r in items[:5]:
            lines.append(f"- ({r['annee']}, {r['citations']} cit.) **{r['titre'][:100]}** — {r['auteurs'][:50]} · DOI: {r['doi']}")
        lines.append("")
    if errors:
        lines += ["## Erreurs", ""] + [f"- {e}" for e in errors[:4]]
    artifacts = [ctx.save_md("veille.md", "\n".join(lines)),
                 ctx.save_json("veille.json", all_new)]

    summary = (f"Veille : {len(all_new)} nouveautés sur {len(per_topic)} sujets (depuis {since_days} jours)"
               + (" [MODE DÉGRADÉ hors-ligne : fixtures démo]" if offline else ""))
    return SkillResult(ok=bool(all_new) or not queries, summary=summary, degraded=offline,
                       artifacts=artifacts,
                       details=[f"Depuis {since} : {per_topic}"] + errors[:3],
                       data={"resultats": all_new[:20], "per_topic": per_topic})
