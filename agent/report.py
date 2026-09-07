"""Génération des livrables : rapport.md, bibliographie.md, bibliographie.bib."""
from __future__ import annotations

from pathlib import Path

from .models import Paper
from .schema import apa_ref, bibtex_ref


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.0f} %" if d else "n/a"


def build_report(topic: str, sub_questions: list[str], mode: str, prisma: dict,
                 entries: list[dict], synthese: list[str], limits: list[str]) -> str:
    now_date = entries[0]["date_ajout"] if entries else "—"
    trust_avg = round(sum(e["trust_factor"] for e in entries) / len(entries)) if entries else 0
    n_oa = sum(1 for e in entries if e["open_access"] == "TRUE")

    lines = [
        f"# Rapport d'exploration littéraire — « {topic} »",
        "",
        f"*Généré par l'agent de recherche littéraire v1 — {now_date} — "
        f"mode d'analyse : **{mode}***",
        "",
    ]
    if mode.startswith("heuristique"):
        lines.append(
            "> ⚠️ **Mode heuristique** (aucun LLM configuré) : les jugements méthodologiques "
            "sont produits par extracteurs automatiques — à considérer comme préliminaire. "
            "Configurez `AGENT_PROVIDER` + `AGENT_API_KEY` (ou Ollama) dans `.env` pour l'analyse LLM complète.\n")

    lines += [
        "## 1. Question et plan de recherche",
        "",
        f"**Question principale :** {topic}",
        "",
        "Sous-questions opérationnalisées :",
    ]
    lines += [f"{i}. {q}" for i, q in enumerate(sub_questions, 1)]

    lines += [
        "",
        "## 2. Méthode de recherche (esprit PRISMA)",
        "",
        "| Étape | N |",
        "|---|---|",
        f"| Notices identifiées (toutes sources) | {prisma.get('identifiees', 0)} |",
        f"| Doublons retirés | {prisma.get('doublons', 0)} |",
        f"| Exclus (sans abstract / hors critères) | {prisma.get('exclus', 0)} |",
        f"| **Retenus pour analyse** | **{prisma.get('retenus', 0)}** |",
        "",
        "Sources interrogées : " + ", ".join(prisma.get("sources", [])) + ".",
        "",
        "## 3. Tableau comparatif — benchmark Trust Factor (décroissant)",
        "",
        "| Rang | id | Réf. courte | Année | Type | Design | N | Cit. | OA | Trust | Niveau |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(entries, 1):
        lines.append(
            f"| {i} | `{e['id']}` | {e['reference_courte']} | {e['annee']} | "
            f"{e['type_publication']} | {e['study_design']} | {e['sample_size'] or 'n/a'} | "
            f"{e['citations_openalex'] or e['citations_crossref'] or 'n/a'} | "
            f"{e['open_access']} | **{e['trust_factor']}** | {e['trust_niveau']} |"
        )

    lines += [
        "",
        f"**Trust moyen : {trust_avg}/100** — OA : {n_oa}/{len(entries)} ({_pct(n_oa, len(entries))}).",
        "",
        "## 4. Fiches détaillées",
    ]
    for e in entries:
        app = e.get("_application", {})
        lines += [
            "",
            f"### {e['reference_courte']} — `{e['id']}` (Trust {e['trust_factor']}, {e['trust_niveau']})",
            "",
            f"- **Question scientifique :** {e['question_scientifique']}",
            f"- **Thème :** {e['theme']}",
            f"- **Type / design :** {e['type_publication']} / {e['study_design']}"
            + (f" — N = {e['sample_size']}" if e['sample_size'] != "" else ""),
            f"- **Consensus actuel :** {e['consensus_actuel']}",
            f"- **Gap actuel :** {e['gap_actuel']}",
            f"- **Open science :** OA={e['open_access']}, data={e['data_open']}, code={e['code_open']}, "
            f"prereg={e['preregistration']}",
            f"- **Sources (triangulation) :** {e['sources_triangulation']}",
            f"- **Justification Trust Factor :** {e['trust_justification']}",
            f"- **Tags :** {e['tags']}",
            "",
            "**Application monde réel**",
            f"- Terrain : {app.get('terrain', 'n/a')}",
            f"- Usage concret : {app.get('usage', 'n/a')}",
            f"- Conditions : {app.get('conditions', 'n/a')}",
            f"- Maturité : **{app.get('maturite', 'n/a')}**",
            f"- Référence : {e['reference_complete']}",
        ]

    lines += ["", "## 5. Synthèse comparative", ""]
    lines += [f"- {s}" for s in synthese]

    lines += ["", "## 6. Limites de ce rapport", ""]
    lines += [f"- {l}" for l in limits]

    lines += ["", "## 7. Bibliographie (APA 7)", ""]
    lines += [f"- {apa_ref(e['_paper'])}" for e in entries]

    return "\n".join(lines) + "\n"


def write_bibliography(out_dir: Path, entries: list[dict]) -> tuple[Path, Path]:
    md_path = out_dir / "bibliographie.md"
    bib_path = out_dir / "bibliographie.bib"
    md = ["# Bibliographie", "", "## APA 7", ""]
    md += [f"- {apa_ref(e['_paper'])}" for e in entries]
    md += ["", "## BibTeX", "", "```bibtex"]
    md += [bibtex_ref(e["id"], e["_paper"]) for e in entries]
    md += ["```", ""]
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md), encoding="utf-8")
    bib_path.write_text(
        "\n\n".join(bibtex_ref(e["id"], e["_paper"]) for e in entries) + "\n", encoding="utf-8")
    return md_path, bib_path
