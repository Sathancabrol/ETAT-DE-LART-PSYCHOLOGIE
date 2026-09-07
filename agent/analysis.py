"""Analyse d'un article : remplir les champs scientifiques de la base 42 champs.

Deux modes :
    - LLM  : un appel JSON par article (jugement méthodologique argumenté)
    - Heuristique : extracteurs par expressions régulières sur titre+abstract
      (fonctionne sans aucune clé API — moins fin, mais déterministe et gratuit)
"""
from __future__ import annotations

import re

from .llm import BaseLLM, extract_json
from .models import Paper
from .trust import niveau_preuve_of

SYSTEM_PROMPT = """Tu es évaluateur méthodologique pour une base de recherche en psychologie/sciences de l'éducation.
Tu analyses UN article à partir de son titre, abstract et métadonnées. Tu réponds STRICTEMENT en JSON valide, sans texte autour.
Champs attendus :
{
 "type_publication": "article_empirique|revue_systematique|meta_analyse|perspective|theorique|preprint",
 "study_design": "experimental_controle|quasi_experimental|correlationnel|qualitatif|meta_analytique|theorique",
 "sample_size": entier ou null (taille d'échantillon; null pour revues),
 "validite": "eleve|modere|faible" (validité interne+de construit),
 "coherence": "coherent|partiel|contradictoire" (cohérence avec la littérature),
 "question_scientifique": "question falsifiable que l'article adresse, finissant par ?",
 "theme": "5-12 mots décrivant le thème précis",
 "consensus_actuel": "1-2 phrases sur ce que l'étude établit",
 "gap_actuel": "1-2 phrases : limite ou question restée ouverte",
 "data_open": "TRUE|FALSE|PARTIAL", "code_open": "TRUE|FALSE|PARTIAL", "preregistration": "TRUE|FALSE|PARTIAL",
 "tags": ["5-7 tags minuscules, méthodes + paradigmes + construct"],
 "application_reelle": {"terrain": "où cela s'applique", "usage": "comment l'utiliser concrètement",
                        "conditions": "conditions/limites de transfert", "maturite": "labo|prometteur|terrain"}
}"""

_STOPWORDS = set("""a an and are as at be by for from has have in is it its of on or that the to was were which with
un une des le la les de du et ou dans pour sur par avec est sont cette ce aux au en que qui quoi dont lors plus moins
cette leur nos nous vous ils elles été être this study results article paper research using used between among""".split())


def analyze_paper_llm(llm: BaseLLM, paper: Paper, topic: str) -> dict | None:
    user = (
        f"SUJET DE LA REVUE : {topic}\n\n"
        f"TITRE : {paper.title}\n"
        f"AUTEURS : {', '.join(paper.authors[:8]) or 'n.c.'}\n"
        f"ANNÉE : {paper.year} | JOURNAL : {paper.journal} | CITATIONS : {paper.cited_by_count}\n"
        f"ABSTRACT : {paper.abstract[:2500] or '(non disponible)'}\n\n"
        "Réponds uniquement avec le JSON."
    )
    data = extract_json(llm.complete(SYSTEM_PROMPT, user))
    if not isinstance(data, dict) or "type_publication" not in data:
        return None
    data.setdefault("tags", [])
    data.setdefault("application_reelle", {})
    data.setdefault("flags_penalites", [])
    return data


# --------------------------------------------------------------- heuristique --
def _guess_type(text: str, paper: Paper) -> str:
    t = text.lower()
    if paper.type_hint == "preprint" or re.search(r"preprint|arxiv|biorxiv|ssrn", t):
        return "preprint"
    if re.search(r"meta-?analy", t):
        return "meta_analyse"
    if re.search(r"systematic review|revue syst", t):
        return "revue_systematique"
    if re.search(r"we (propose|argue|discuss)|perspective|commentary|conceptual framework", t):
        return "theorique"
    return "article_empirique"


def _guess_design(text: str, tpub: str) -> str:
    t = text.lower()
    if tpub == "meta_analyse":
        return "meta_analytique"
    if tpub == "revue_systematique":
        return "revue_systematique"
    if tpub == "theorique":
        return "theorique"
    if re.search(r"random(ly|ized|ised|isation|ization)|controlled trial|\brct\b", t):
        return "experimental_controle"
    if re.search(r"quasi-?experiment|pre-?test/?post-?test|pretest.?posttest", t):
        return "quasi_experimental"
    if re.search(r"interview(s)?|qualitative|thematic|think-?aloud|focus group", t):
        return "qualitatif"
    if re.search(r"survey|questionnaire|cross-?sectional|regression|relationship|correlat|self-?report", t):
        return "correlationnel"
    return "correlationnel"


_NUMWORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    "thousand": 1000,
}


def _words_to_number(fragment: str) -> int | None:
    """'one hundred and eighty-five' -> 185 (parseur minimal anglais/franglais)."""
    fragment = fragment.replace("-", " ").lower()
    total, current = 0, 0
    found = False
    for tok in re.findall(r"[a-z]+", fragment):
        val = _NUMWORDS.get(tok)
        if val is None:
            if found:
                break
            continue
        found = True
        if val == 100:
            current = max(current, 1) * 100
        elif val == 1000:
            current = max(current, 1) * 1000
        elif val >= 20:
            total += current + val
            current = 0
        else:
            current += val
    return (total + current) if found else None


def _guess_sample(text: str) -> int | None:
    m = (re.search(r"\(?\s*N\s*=\s*([\d\s,]+)\)?", text, re.I)
         or re.search(r"(\d[\d,]*)\s+participants", text, re.I)
         or re.search(r"participants?\s+(?:were\s+)?(\d[\d,]*)", text, re.I))
    if m:
        val = int(re.sub(r"[^\d]", "", m.group(1)) or 0)
        return val if 0 < val < 10_000_000 else None
    m = re.search(r"\b((?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
                  r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)"
                  r"(?:[\s\-a-z]{0,30}))\s*"
                  r"(participants|students|teachers|children|adults|medical students|school teachers|learners|university students)",
                  text, re.I)
    if m:
        val = _words_to_number(m.group(1))
        if val:
            return val
    return None


def _guess_tags(text: str, k: int = 6) -> list[str]:
    words = re.findall(r"[a-zà-ÿ][a-zà-ÿ\-]{3,}", text.lower())
    counts: dict[str, int] = {}
    for w in words:
        if w in _STOPWORDS:
            continue
        counts[w] = counts.get(w, 0) + 1
    tags = [w for w, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:k]]
    return tags if len(tags) >= 3 else (tags + ["recherche", "education", "apprentissage"])[:3]


def _sentence_with(pattern: str, text: str, default: str = "") -> str:
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if re.search(pattern, sent, re.I):
            return sent.strip()[:280]
    return default


def analyze_paper_heuristic(paper: Paper, topic: str) -> dict:
    text = f"{paper.title}. {paper.abstract}"
    tpub = _guess_type(text, paper)
    design = _guess_design(text, tpub)
    n = paper.sample_size_hint if paper.sample_size_hint else _guess_sample(text)
    prereg = "TRUE" if re.search(r"pre-?registr", text, re.I) else "FALSE"
    data_open = "TRUE" if re.search(r"data (are|is) (publicly |openly )?available|\bosf\b|open data", text, re.I) else "FALSE"
    code_open = "TRUE" if re.search(r"code (is )?available|github|open-?source", text, re.I) else "FALSE"
    consensus = (_sentence_with(r"results?|findings?|reveal|show|demonstrat|indicat", paper.abstract)
                 or paper.abstract[:220] or "À déterminer sur le texte intégral.")
    gap = (_sentence_with(r"future research|further research|remains|limitation|needed|unclear", paper.abstract)
           or "Gap non identifiable dans l'abstract — lecture du texte intégral requise (mode LLM recommandé).")

    if design in ("experimental_controle", "quasi_experimental"):
        validite = "modere"
    elif tpub in ("meta_analyse", "revue_systematique"):
        validite = "eleve"
    elif design == "qualitatif":
        validite = "faible"
    else:
        validite = "modere"

    short_title = re.sub(r"\s+", " ", paper.title).strip().rstrip(".")
    question = (f"Que montre « {short_title[:140]} » concernant « {topic} », "
                f"et quel est le niveau de confiance de cette contribution ?")

    return {
        "type_publication": tpub,
        "study_design": design,
        "sample_size": n,
        "validite": validite,
        "coherence": "partiel",  # neutre en mode heuristique (pas de lecture de la littérature)
        "is_oa": paper.is_oa,
        "question_scientifique": question,
        "theme": short_title[:120],
        "consensus_actuel": consensus,
        "gap_actuel": gap,
        "data_open": data_open,
        "code_open": code_open,
        "preregistration": prereg,
        "tags": _guess_tags(text),
        "flags_penalites": [],
        "mode": "heuristique",
    }


def heuristic_application(a: dict) -> dict:
    """Application monde réel par défaut (mode heuristique), calibrée par design d'étude."""
    design = a.get("study_design", "correlationnel")
    tpub = a.get("type_publication", "article_empirique")
    if tpub in ("meta_analyse", "revue_systematique"):
        return {"terrain": "Politiques éducatives, guides de bonnes pratiques, formation des formateurs",
                "usage": "S'appuyer sur la synthèse quantitative pour prioriser les interventions les mieux étayées",
                "conditions": "Vérifier l'hétérogénéité entre études avant tout transfert de terrain",
                "maturite": "terrain"}
    if design in ("experimental_controle", "quasi_experimental"):
        return {"terrain": "Conception d'interventions pédagogiques et d'outils numériques d'apprentissage",
                "usage": "Reproduire le protocole testé (ex. support métacognitif détaché, auto-explication) dans un contexte comparable",
                "conditions": "Population et durée comparables ; mesurer le transfert à moyen terme",
                "maturite": "prometteur"}
    if design == "qualitatif":
        return {"terrain": "Formation initiale des enseignants et des professionnels de santé",
                "usage": "Cibler explicitement les compétences métacognitives faibles (planification, évaluation) dans les maquettes de formation",
                "conditions": "Résultats exploratoires : valider par des études quantitatives avant généralisation",
                "maturite": "labo"}
    if tpub in ("theorique", "perspective"):
        return {"terrain": "Cadres de conception pour la recherche et l'ingénierie pédagogique",
                "usage": "Utiliser le cadre pour formuler des hypothèses testables et structurer les interventions",
                "conditions": "Cadre théorique : nécessite une validation empirique dédiée",
                "maturite": "labo"}
    return {"terrain": "Formation des enseignants et ingénierie pédagogique",
            "usage": "Identifier les leviers corrélés (connaissances, sentiment d'efficacité, intérêt) à renforcer dans les formations",
            "conditions": "Corrélationnel : ne pas inférer de causalité ; prudence sur le transfert",
            "maturite": "prometteur"}
