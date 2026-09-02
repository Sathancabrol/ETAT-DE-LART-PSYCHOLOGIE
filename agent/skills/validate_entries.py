"""
Compétence : validation de la base 42 champs.

Réutilise la logique de scripts/validate_entry.py (import dynamique pour
ne pas dupliquer les règles) : 28 champs obligatoires, regex DOI,
triangulation ≥3, tags ≥3, trust 0-100, dates ISO, doublons, cohérence.
"""

from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
from typing import List

from agent.core.registry import skill, SkillResult
from agent.core.context import ROOT, DATA_CSV

_VALIDATE_MOD = None


def _load_validator():
    """Charge scripts/validate_entry.py comme module (source de vérité unique)."""
    global _VALIDATE_MOD
    if _VALIDATE_MOD is None:
        path = ROOT / "scripts" / "validate_entry.py"
        spec = importlib.util.spec_from_file_location("validate_entry", path)
        _VALIDATE_MOD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_VALIDATE_MOD)
    return _VALIDATE_MOD


@skill(
    name="validate_entries",
    description="Valide la base 42 champs : 28 champs obligatoires, regex DOI, triangulation ≥3, tags ≥3, trust 0-100, dates ISO, doublons, cohérences.",
    category="qualite",
    triggers=[r"valid", r"v[ée]rifie?r?\s+(la\s+)?(base|donn)", r"contr[ôo]le", r"check"],
    examples=[
        "valider la base de données",
        "vérifier les entrées du CSV",
    ],
    params={"file": "chemin du CSV à valider (défaut : data/nodes_etat_art_psychologie.csv)"},
    defaults={},
    order=40,
)
def validate_entries(ctx, file: str = "", **_) -> SkillResult:
    path = Path(file) if file else DATA_CSV
    if not path.exists():
        return SkillResult(ok=False, summary=f"Fichier introuvable : {path}")

    v = _load_validator()
    errors_all, warnings_all = [], []
    seen_dois, seen_ids = set(), set()
    rows = []
    import csv as _csv
    with open(path, newline="", encoding="utf-8") as f:
        reader = _csv.DictReader(f)
        n_cols = len(reader.fieldnames or [])
        for idx, row in enumerate(reader, start=2):
            rows.append(row)
            e, w = v.validate_row(row, idx, seen_dois, seen_ids)
            errors_all.extend(e)
            warnings_all.extend(w)

    trust_vals = [int(r["trust_factor"]) for r in rows if (r.get("trust_factor") or "").isdigit()]
    stats = {
        "lignes": len(rows),
        "colonnes": n_cols,
        "erreurs": len(errors_all),
        "avertissements": len(warnings_all),
        "trust_moyen": round(sum(trust_vals) / len(trust_vals), 1) if trust_vals else None,
        "par_niveau_preuve": dict(Counter(r.get("niveau_preuve") for r in rows if r.get("niveau_preuve"))),
        "par_type": dict(Counter(r.get("type_publication") for r in rows if r.get("type_publication"))),
    }
    ctx.state["validation"] = stats

    details = [f"{stats['lignes']} lignes × {stats['colonnes']} colonnes (attendu 42)",
               f"Erreurs : {stats['erreurs']} | Avertissements : {stats['avertissements']}",
               f"Trust moyen : {stats['trust_moyen']}"]
    details += errors_all[:10]
    if len(errors_all) > 10:
        details.append(f"… et {len(errors_all) - 10} autres erreurs")
    details += warnings_all[:5]

    artifacts = [ctx.save_json("validation_rapport.json",
                               {"stats": stats, "erreurs": errors_all, "avertissements": warnings_all})]
    status = "PASSED" if not errors_all else "FAILED"
    summary = f"Validation {status} : {stats['erreurs']} erreur(s), {stats['avertissements']} avertissement(s) sur {stats['lignes']} lignes"
    return SkillResult(ok=not errors_all, summary=summary, artifacts=artifacts,
                       details=details, data=stats)
