"""Schéma CSV 42 champs du dépôt + construction des lignes et de la bibliographie."""
from __future__ import annotations

import csv
import re
import unicodedata
from datetime import date
from pathlib import Path

from .models import Paper
from .trust import niveau_preuve_of

# Ordre EXACT de data/nodes_etat_art_psychologie.csv
CSV_COLUMNS = [
    "id", "grand_domaine", "domaine", "sous_domaine", "theme",
    "question_scientifique", "reference_courte", "reference_complete", "doi",
    "annee", "type_publication", "journal", "url", "niveau_preuve", "sources_triangulation",
    "citations_google_scholar", "citations_crossref", "citations_openalex",
    "citations_semantic_scholar", "citations_web_of_science", "date_releve_citations",
    "altmetric_score", "peer_reviewed", "open_access", "data_open", "code_open",
    "preregistration", "sample_size", "sample_type", "study_design",
    "consensus_actuel", "gap_actuel", "last_gap",
    "trust_factor", "trust_niveau", "trust_justification",
    "tags", "relations", "date_ajout", "date_mise_a_jour", "ajoute_par", "notes_internes",
]

TODAY = date.today().isoformat()
AGENT_SIGNATURE = "agent_litteraire_v1"


def _slug(text: str, maxlen: int = 22) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:maxlen].strip("_")


def make_id(paper: Paper, analysis: dict, taken: set[str]) -> str:
    kw = _slug(_slug(analysis.get("theme", paper.title)).replace("_", " ")) or "etude"
    base = f"{paper.first_author}{paper.year or 0}_{kw}"
    base = re.sub(r"[^a-z0-9_]", "", base) or "etude"
    candidate, i = base, 1
    while candidate in taken:
        i += 1
        candidate = f"{base}_{i}"
    taken.add(candidate)
    return candidate


def short_ref(paper: Paper) -> str:
    fam = paper.authors[0].split(",")[-1].strip() if paper.authors else "Anonyme"
    fam = re.sub(r"[^A-Za-zÀ-ÿ'\- ]", "", fam)
    others = " et al." if len(paper.authors) > 2 else (f" & {paper.authors[1].split()[-1]}" if len(paper.authors) == 2 else "")
    year = paper.year or "s.d."
    return f"{fam}{others} {year}"


def full_ref(paper: Paper) -> str:
    authors = ", ".join(paper.authors) if paper.authors else "Anonyme"
    year = paper.year or "s.d."
    link = f"https://doi.org/{paper.doi}" if paper.doi else paper.url
    return f"{authors} ({year}). {paper.title}. {paper.journal}. {link}"


def apa_ref(paper: Paper) -> str:
    authors = paper.authors or ["Anonyme"]
    if len(authors) > 7:
        heads = ", ".join(authors[:6]) + f", ... {authors[-1]}"
    else:
        heads = ", ".join(a for a in authors)
        heads = re.sub(r",([^,]*)$", r", &\1", heads) if len(authors) > 1 else heads
    year = paper.year or "s.d."
    tail = f"https://doi.org/{paper.doi}" if paper.doi else paper.url
    return f"{heads} ({year}). {paper.title}. *{paper.journal or 'n.p.'}*. {tail}".replace("..", ".")


def bibtex_ref(entry_id: str, paper: Paper) -> str:
    authors = " and ".join(paper.authors) or "Anonyme"
    return (
        f"@article{{{entry_id},\n"
        f"  title = {{{paper.title}}},\n"
        f"  author = {{{authors}}},\n"
        f"  year = {{{paper.year or ''}}},\n"
        f"  journal = {{{paper.journal}}},\n"
        f"  doi = {{{paper.doi}}},\n"
        f"  url = {{{paper.url}}}\n"
        f"}}"
    )


def build_row(entry_id: str, paper: Paper, analysis: dict, trust: dict) -> dict:
    """Assemble une ligne CSV complète, compatible scripts/validate_entry.py."""
    tpub = analysis.get("type_publication", "article_empirique")
    design = analysis.get("study_design", "correlationnel")
    triangulation = "+".join(paper.sources)  # sources réellement interrogées (pipeline enrichit au besoin)
    tags = [t.strip().lower() for t in analysis.get("tags", []) if t and t.strip()]
    tags = list(dict.fromkeys(tags))[:7]
    row = {c: "" for c in CSV_COLUMNS}
    row.update({
        "id": entry_id,
        "grand_domaine": analysis.get("grand_domaine", "Psychologie"),
        "domaine": analysis.get("domaine", "Psychologie cognitive"),
        "sous_domaine": analysis.get("sous_domaine", "Métacognition"),
        "theme": analysis.get("theme", paper.title[:120]),
        "question_scientifique": analysis["question_scientifique"].rstrip() + "?"
            if not analysis["question_scientifique"].rstrip().endswith("?") else analysis["question_scientifique"],
        "reference_courte": short_ref(paper),
        "reference_complete": full_ref(paper),
        "doi": paper.doi.lower(),
        "annee": paper.year or "",
        "type_publication": tpub,
        "journal": paper.journal,
        "url": paper.url or (f"https://doi.org/{paper.doi}" if paper.doi else ""),
        "niveau_preuve": niveau_preuve_of(tpub, design),
        "sources_triangulation": triangulation,
        "citations_openalex": paper.cited_by_count if "OpenAlex" in paper.sources else "",
        "citations_crossref": paper.cited_by_count if "Crossref" in paper.sources and "OpenAlex" not in paper.sources else "",
        "citations_semantic_scholar": paper.cited_by_count if "SemanticScholar" in paper.sources else "",
        "date_releve_citations": TODAY,
        "peer_reviewed": "FALSE" if tpub == "preprint" else "TRUE",
        "open_access": "TRUE" if paper.is_oa else "FALSE",
        "data_open": analysis.get("data_open", "FALSE"),
        "code_open": analysis.get("code_open", "FALSE"),
        "preregistration": analysis.get("preregistration", "FALSE"),
        "sample_size": analysis.get("sample_size") if analysis.get("sample_size") is not None else "",
        "sample_type": analysis.get("sample_type", ""),
        "study_design": design,
        "consensus_actuel": analysis.get("consensus_actuel", ""),
        "gap_actuel": analysis.get("gap_actuel", ""),
        "last_gap": analysis.get("last_gap", "À confirmer sur texte intégral"),
        "trust_factor": trust["trust_factor"],
        "trust_niveau": trust["trust_niveau"],
        "trust_justification": trust["trust_justification"],
        "tags": ", ".join(tags),
        "relations": analysis.get("relations", ""),
        "date_ajout": TODAY,
        "date_mise_a_jour": TODAY,
        "ajoute_par": AGENT_SIGNATURE,
        "notes_internes": f"Mode analyse: {analysis.get('mode', 'heuristique')}; "
                          f"abstract_tronque: {'oui' if paper.abstract_truncated else 'non'}; "
                          f"maturite application: {analysis.get('application_reelle', {}).get('maturite', 'n/a')}",
    })
    return row


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in CSV_COLUMNS})
