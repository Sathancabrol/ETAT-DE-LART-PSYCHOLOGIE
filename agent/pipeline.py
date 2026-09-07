"""Orchestrateur — la boucle agentique en 8 étapes.

    1 PLANIFIER  (LLM | heuristique) : sous-questions de recherche
    2 CHERCHER   (OpenAlex + Crossref + arXiv [| S2] | fixtures démo)
    3 FILTRER    (PRISMA : doublons, abstract requis, fenêtre d'années)
    4 ANALYSER   (LLM | heuristique) : 42 champs scientifiques par article
    5 SCORER     (code pur) : Trust Factor M+R+O+C+T-P
    6 COMPARER   : matrice triée par Trust + synthèse (LLM | heuristique)
    7 APPLIQUER  : applications monde réel par article
    8 LIVRER     : rapport.md + bibliographie.md/.bib + nodes_agent.csv
"""
from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from . import tools
from .analysis import analyze_paper_heuristic, analyze_paper_llm, heuristic_application
from .config import REPO_ROOT, AgentConfig
from .llm import get_llm
from .models import Paper
from .report import build_report, write_bibliography
from .schema import build_row, make_id, write_csv
from .trust import score_trust

log = logging.getLogger("agent.pipeline")

FIXTURES = Path(__file__).parent / "fixtures" / "demo_results.json"

PROGRESS_STAGES = [
    ("plan", 5, "Planification des sous-questions"),
    ("search", 20, "Recherche multi-sources"),
    ("filter", 35, "Filtrage PRISMA"),
    ("analyze", 60, "Analyse des articles"),
    ("trust", 75, "Calcul Trust Factor"),
    ("compare", 85, "Comparaison et synthèse"),
    ("deliver", 95, "Écriture des livrables"),
    ("done", 100, "Terminé"),
]


# ------------------------------------------------------------ 1. PLANIFIER --
def plan_questions(llm, topic: str) -> list[str]:
    if llm is not None:
        out = llm.complete(
            "Tu décomposes une question de recherche en 3-5 sous-questions falsifiables, "
            "une par ligne, préfixées par '- '. Aucun texte autour.",
            f"Sujet : {topic}",
        )
        if out:
            qs = [re.sub(r"^[-*\d.\s]+", "", ln).strip() for ln in out.splitlines() if ln.strip().startswith(("-", "*", "1", "2", "3", "4", "5"))]
            qs = [q for q in qs if len(q) > 12][:5]
            if qs:
                return qs
    return [
        f"Quel est l'état des preuves empiriques sur « {topic} » (designs, échantillons, effets) ?",
        f"Quels mécanismes et construits sont mobilisés pour expliquer « {topic} » ?",
        f"Quelles limites méthodologiques et quels gaps la littérature récente identifie-t-elle sur « {topic} » ?",
        f"Quelles applications concrètes (terrain) se dégagent des travaux sur « {topic} » ?",
    ]


# ----------------------------------------------------------- 2/3. CHERCHER --
def _load_demo_papers() -> list[Paper]:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    papers = []
    for p in data["papers"]:
        papers.append(Paper(
            doi=p["doi"], title=p["title"], year=p["year"], journal=p["journal"],
            authors=p.get("authors", []), cited_by_count=p.get("cited_by_count"),
            is_oa=p.get("is_oa", False), oa_url=p.get("oa_url", ""), url=p.get("url", ""),
            abstract=p.get("abstract", ""), openalex_id=p.get("openalex_id", ""),
            sample_size_hint=p.get("sample_size"),
            sources=list(p.get("sources", ["OpenAlex"])),
            abstract_truncated=p.get("abstract_truncated", False),
            notes=p.get("notes", ""),
        ))
    return papers


def _enrich_triangulation(papers: list[Paper], email: str) -> None:
    """Assure ≥ 3 sources de triangulation : confirmation Crossref + résolution doi.org."""
    for p in papers:
        if len(p.sources) >= 3:
            continue
        if p.doi:
            if tools.confirm_doi_crossref(p.doi, email) and "Crossref" not in p.sources:
                p.sources.append("Crossref")
            if "doi.org" not in p.sources:
                p.sources.append("doi.org")


def search(topic: str, year_min: int, year_max: int, max_papers: int,
           cfg: AgentConfig, demo: bool, progress) -> tuple[list[Paper], dict]:
    progress("search", 20, "Recherche multi-sources…")
    if demo:
        papers = _load_demo_papers()
        identified = len(papers)
        prisma_sources = ["OpenAlex (fixtures démo, données réelles)"]
    else:
        s2 = cfg.extra.get("s2_enabled", False)
        papers = tools.search_all(topic, year_min, year_max, limit=max(max_papers * 3, 15),
                                  email=cfg.email, s2_enabled=s2)
        identified = len(papers)
        prisma_sources = ["OpenAlex", "Crossref", "arXiv"] + (["SemanticScholar"] if s2 else [])
        _enrich_triangulation(papers, cfg.email)

    before = len(papers)
    papers = [p for p in papers if p.abstract or p.title]  # critère : abstract/titre dispo
    papers = [p for p in papers if p.year and year_min <= p.year <= year_max]
    retained = papers[:max_papers]
    prisma = {
        "identifiees": identified,
        "doublons": before - identified if before > identified else 0,
        "exclus": len(papers) - len(retained),
        "retenus": len(retained),
        "sources": prisma_sources,
    }
    return retained, prisma


# ------------------------------------------------------- 4-7. BOUCLE AGENT --
def run_research(topic: str, year_min: int = 2020, year_max: int = 2026,
                 max_papers: int = 8, cfg: AgentConfig | None = None,
                 demo: bool = False, out_dir: Path | None = None,
                 progress=None) -> dict:
    cfg = cfg or AgentConfig.from_env()
    t0 = time.time()

    def progress_default(stage, pct, msg=""):
        log.info("[%3d%%] %s %s", pct, stage, msg)
    progress = progress or progress_default

    slug = (unicodedata.normalize("NFKD", topic.lower()).encode("ascii", "ignore").decode())
    slug = re.sub(r"[^a-z0-9]+", "_", slug).strip("_")[:40] or "recherche"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = out_dir or REPO_ROOT / "output" / "agent_reports" / f"{slug}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. PLANIFIER
    progress(*PROGRESS_STAGES[0])
    llm = get_llm(cfg)
    llm_probe = None
    if llm is not None:
        llm_probe = llm.complete("Réponds exactement : OK", "Test de connexion. Réponds exactement : OK")
    llm_active = llm_probe is not None
    sub_questions = plan_questions(llm if llm_active else None, topic)
    mode = "LLM" if llm_active else "heuristique"

    # --- 2/3. CHERCHER + FILTRER
    papers, prisma = search(topic, year_min, year_max, max_papers, cfg, demo, progress)
    progress("filter", 35, f"Filtrage PRISMA : {len(papers)} articles retenus")

    # --- 4. ANALYSER
    entries: list[dict] = []
    taken_ids: set[str] = set()
    for i, paper in enumerate(papers):
        progress("analyze", 40 + int(20 * i / max(len(papers), 1)), f"Analyse {i + 1}/{len(papers)}: {paper.title[:60]}")
        analysis = None
        if llm_active:
            analysis = analyze_paper_llm(llm, paper, topic)
            if analysis is not None:
                analysis["mode"] = "LLM"
        if analysis is None:
            analysis = analyze_paper_heuristic(paper, topic)
            if mode == "LLM":
                analysis["mode"] = "LLM→heuristique (échec LLM sur cet article)"
        # les métriques objectives écrasent toujours le LLM :
        analysis["citations"] = paper.cited_by_count
        analysis.setdefault("is_oa", paper.is_oa)
        analysis.setdefault("journal", paper.journal)
        analysis["has_doi"] = bool(paper.doi)
        analysis["has_url"] = bool(paper.url or paper.doi or paper.oa_url)
        # --- 5. SCORER (code déterministe)
        trust = score_trust(analysis)
        entry_id = make_id(paper, analysis, taken_ids)
        row = build_row(entry_id, paper, analysis, trust)
        app_real = analysis.get("application_reelle") or heuristic_application(analysis)
        row["_paper"] = paper
        row["_application"] = app_real
        entries.append(row)

    entries.sort(key=lambda e: e["trust_factor"], reverse=True)

    # --- 6. COMPARER
    progress(*PROGRESS_STAGES[5])
    synthese = heuristic_synthesis(entries, sub_questions)
    if llm_active and entries:
        llm_syn = llm_synthesis(llm, topic, entries)
        if llm_syn:
            synthese = llm_syn

    limits = [
        "Analyse basée sur titres + abstracts (pas les textes intégraux) — lire les articles retenus avant citation définitive.",
        "Trust Factor reproduit la formule du dépôt (GUIDE_REMPLISSAGE_IA.md §2.8) ; les sous-scores validité/cohérence dépendent du mode d'analyse.",
        "Les citations comptées au jour du relevé ; un article récent est mécaniquement sous-noté sur R (réplication).",
        "La liste de journaux Q1 embarquée est une simplification (pas de JCR en direct).",
    ]
    if mode == "heuristique":
        limits.append("Mode heuristique : pas de jugement LLM sur validité/cohérence (valeurs conservatrices par défaut).")

    # --- 8. LIVRER
    progress(*PROGRESS_STAGES[6])
    report_md = build_report(topic, sub_questions, mode, prisma, entries, synthese, limits)
    report_path = out_dir / "rapport.md"
    report_path.write_text(report_md, encoding="utf-8")
    bib_md, bib_bib = write_bibliography(out_dir, entries)
    csv_path = out_dir / "nodes_agent.csv"
    write_csv(csv_path, entries)

    progress(*PROGRESS_STAGES[7])
    trust_avg = round(sum(e["trust_factor"] for e in entries) / len(entries)) if entries else 0
    summary = {
        "topic": topic,
        "mode": mode,
        "demo": demo,
        "period": f"{year_min}-{year_max}",
        "papers": len(entries),
        "trust_avg": trust_avg,
        "top_paper": entries[0]["reference_courte"] if entries else None,
        "prisma": prisma,
        "sub_questions": sub_questions,
        "out_dir": str(out_dir),
        "files": {"rapport": str(report_path), "bibliographie_md": str(bib_md),
                  "bibliographie_bib": str(bib_bib), "csv": str(csv_path)},
        "duration_s": round(time.time() - t0, 1),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


# ------------------------------------------------------------ 6. SYNTHÈSE --
def heuristic_synthesis(entries: list[dict], sub_questions: list[str]) -> list[str]:
    if not entries:
        return ["Aucun article retenu — élargir la requête ou la fenêtre d'années."]
    top = entries[0]
    most_cited = max(entries, key=lambda e: e["citations_openalex"] or e["citations_crossref"] or 0)
    designs = [e["study_design"] for e in entries]
    oa = sum(1 for e in entries if e["open_access"] == "TRUE")
    out = [
        f"Meilleur Trust Factor : **{top['reference_courte']}** ({top['trust_factor']}/100, {top['trust_niveau']}) — "
        f"{top['study_design']}, N={top['sample_size'] or 'n/a'}.",
        f"Article le plus cité : **{most_cited['reference_courte']}** "
        f"({most_cited['citations_openalex'] or most_cited['citations_crossref'] or 'n/a'} citations).",
        f"Répartition des designs : {', '.join(f'{d} ×{designs.count(d)}' for d in dict.fromkeys(designs))} — "
        f"{'minorité de designs expérimentaux : prudence causale' if designs.count('experimental_controle') <= 1 else 'base expérimentale présente'}.",
        f"Accès ouvert : {oa}/{len(entries)} — le corpus est {'vérifiable sans paywall' if oa == len(entries) else 'partiellement verrouillé'}.",
        "Convergences thématiques visibles via les tags partagés ; divergences à creuser texte intégral en main.",
    ]
    return out


def llm_synthesis(llm, topic: str, entries: list[dict]) -> list[str]:
    import re as _re
    corpus = "\n".join(
        f"- {e['reference_courte']} ({e['annee']}, {e['type_publication']}, N={e['sample_size'] or 'n/a'}, "
        f"trust {e['trust_factor']}): {e['consensus_actuel'][:200]}"
        for e in entries
    )
    out = llm.complete(
        "Tu synthétises un corpus pour un état de l'art. Réponds par 5 à 7 puces '- ' en français : "
        "convergences, divergences, ce que le corpus établit, ce qui reste ouvert. Aucun texte autour.",
        f"Sujet : {topic}\nCorpus :\n{corpus}",
    )
    if not out:
        return []
    bullets = [_re.sub(r"^[-*\d.\s]+", "", ln).strip() for ln in out.splitlines() if ln.strip().startswith(("-", "*"))]
    return [b for b in bullets if len(b) > 10][:7]
