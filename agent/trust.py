"""Trust Factor — implémentation DÉTERMINISTE de la formule du dépôt.

Source : docs/GUIDE_REMPLISSAGE_IA.md §2.8 et §7
    trust = M(0-30) + R(0-20) + O(0-20) + C(0-15) + T(0-15) - P(0-50), borné [0, 100]
    trust_niveau : 0-29 faible | 30-59 modere | 60-84 eleve | 85-100 tres_eleve

Principe d'or : le LLM fournit les jugements (design, validité, cohérence),
le code calcule le score → deux exécutions donnent le même résultat.
"""
from __future__ import annotations

# Journaux considérés Q1 (match par sous-chaîne, minuscules) — liste extensible.
Q1_JOURNALS = (
    "psychological bulletin", "psychological science", "perspectives on psychological science",
    "nature", "science", "lancet", "jama", "bmj", "pnas", "new england",
    "teaching and teacher education", "british journal of educational psychology",
    "learning and instruction", "journal of educational psychology",
    "educational psychology review", "educational technology research and development",
    "teaching and learning in medicine", "medical education", "medical teacher",
    "cognition", "trends in cognitive sciences", "journal of memory and language",
    "journal of experimental psychology", "psychonomic", "frontiers in human neuroscience",
    "neuroimage", "journal of applied psychology", "personality and social psychology",
)

DESIGN_POINTS = {
    "experimental_controle": 10,
    "meta_analytique": 10,
    "quasi_experimental": 8,
    "revue_systematique": 8,
    "correlationnel": 5,
    "qualitatif": 4,
    "theorique": 3,
}
VALIDITE_POINTS = {"eleve": 10, "modere": 6, "faible": 3}
COHERENCE_POINTS = {"coherent": 15, "partiel": 8, "contradictoire": 3}
CONVERGENCE_POINTS = {"meta_analyse": 10, "revue_systematique": 10, "article_empirique": 4,
                      "perspective": 4, "theorique": 4, "preprint": 2}


def is_q1_journal(journal: str) -> bool:
    j = (journal or "").lower()
    return any(q in j for q in Q1_JOURNALS)


def trust_niveau_of(score: int) -> str:
    if score >= 85:
        return "tres_eleve"
    if score >= 60:
        return "eleve"
    if score >= 30:
        return "modere"
    return "faible"


def niveau_preuve_of(type_publication: str, study_design: str) -> str:
    """Niveau de preuve (champ CSV) — pyramide classique."""
    if type_publication == "meta_analyse":
        return "tres_eleve"
    if type_publication == "revue_systematique":
        return "eleve"
    if type_publication == "preprint":
        return "faible"
    if type_publication in ("theorique", "perspective", "chapitre"):
        return "theorique"
    return {
        "experimental_controle": "eleve",
        "quasi_experimental": "modere_eleve",
        "correlationnel": "modere",
        "qualitatif": "faible_modere",
    }.get(study_design, "modere")


def score_trust(a: dict) -> dict:
    """Calcule M+R+O+C+T-P sur le dict d'analyse d'un article.

    Clés attendues (produites par agent/analysis.py) :
        type_publication, study_design, sample_size (int|None), citations (int|None),
        is_oa (bool), data_open, code_open, preregistration ("TRUE"|"FALSE"|"PARTIAL"),
        validite ("eleve"|"modere"|"faible"), coherence ("coherent"|"partiel"|"contradictoire"),
        journal (str), has_doi (bool), has_url (bool), flags_penalites (list[str])
    """
    tpub = a.get("type_publication", "article_empirique")
    design = a.get("study_design", "correlationnel")
    n = a.get("sample_size")
    cites = a.get("citations")
    flags = list(a.get("flags_penalites", []))

    # ---- M : Méthodologie (0-30) ----
    d_design = DESIGN_POINTS.get(design, 5)
    if tpub in ("meta_analyse", "revue_systematique") and n is None:
        d_sample, note_sample = 8, "revue (NA)"
    elif n is None:
        d_sample, note_sample = 7, "N non déterminé (hyp. 30-100)"
    elif n > 100:
        d_sample, note_sample = 10, "N>100"
    elif n >= 30:
        d_sample, note_sample = 7, "30≤N≤100"
    else:
        d_sample, note_sample = 4, "N<30"
    d_valid = VALIDITE_POINTS.get(a.get("validite", "modere"), 6)
    M = d_design + d_sample + d_valid

    # ---- R : Réplication (0-20) ----
    if cites is None:
        d_cit, note_cit = 2, "citations inconnues"
    elif cites > 100:
        d_cit, note_cit = 10, f"citations {cites}>100"
    elif cites >= 50:
        d_cit, note_cit = 7, f"citations {cites} (50-100)"
    elif cites >= 10:
        d_cit, note_cit = 4, f"citations {cites} (10-50)"
    else:
        d_cit, note_cit = 2, f"citations {cites}<10"
    d_conv = CONVERGENCE_POINTS.get(tpub, 4)
    R = d_cit + d_conv

    # ---- O : Open Science (0-20) ----
    O = 5 if a.get("is_oa") else 0
    O += {"TRUE": 5, "PARTIAL": 3}.get(a.get("data_open", "FALSE"), 0)
    O += {"TRUE": 5, "PARTIAL": 3}.get(a.get("code_open", "FALSE"), 0)
    O += 5 if a.get("preregistration") == "TRUE" else 0
    O = min(O, 20)

    # ---- C : Cohérence (0-15) ----
    C = COHERENCE_POINTS.get(a.get("coherence", "partiel"), 8)

    # ---- T : Transparence (0-15) ----
    has_doi, has_url = bool(a.get("has_doi")), bool(a.get("has_url"))
    if not has_doi:
        T, note_t = 0, "sans DOI"
    elif tpub == "preprint":
        T, note_t = 5, "préprint"
    else:
        q1 = is_q1_journal(a.get("journal", ""))
        if q1:
            T, note_t = (15, "Q1 + DOI + url") if has_url else (10, "Q1 + DOI")
        else:
            T, note_t = 10, "Q2 + DOI"

    # ---- P : Pénalités (0-50, soustrait) ----
    P_list: list[tuple[int, str]] = []
    if n is not None and n < 20 and tpub == "article_empirique":
        P_list.append((10, f"petit échantillon N={n}"))
    if tpub == "preprint":
        P_list.append((5, "préprint non relu"))
    for f in flags:
        P_list.append((10, f))
    P = min(sum(p for p, _ in P_list), 50)

    raw = M + R + O + C + T
    trust = max(0, min(100, raw - P))

    justification = (
        f"M={M}/30 (design {design}={d_design}, {note_sample}={d_sample}, "
        f"validité {a.get('validite', 'modere')}={d_valid}); "
        f"R={R}/20 ({note_cit}={d_cit}, convergence {tpub}={d_conv}); "
        f"O={O}/20 (OA={'5' if a.get('is_oa') else '0'}, data={a.get('data_open', 'FALSE')}, "
        f"code={a.get('code_open', 'FALSE')}, prereg={a.get('preregistration', 'FALSE')}); "
        f"C={C}/15 ({a.get('coherence', 'partiel')}); T={T}/15 ({note_t}); "
        f"P=-{P} ({', '.join(n for _, n in P_list) if P_list else 'aucune'}); "
        f"brut {raw} → trust {trust}"
    )

    return {
        "M": M, "R": R, "O": O, "C": C, "T": T, "P": P, "raw": raw,
        "trust_factor": trust,
        "trust_niveau": trust_niveau_of(trust),
        "trust_justification": justification,
    }
