# Guide de Remplissage pour IA - Base de Données État de l'Art Psychologie

**Version:** 2.0 - Méthodologique (2026-05-13)  
**Auteur:** IA Anara + Sathancabrol  
**Objectif:** Permettre à une IA (ou humain) de remplir automatiquement la base `nodes_etat_art_psychologie.csv` à partir d'un PDF, DOI ou page web, avec 42 champs normalisés, triangulation et Trust Factor.

---

## 1. Vue d'ensemble 42 champs

### Répartition

| Catégorie | Nombre | Obligatoires | Description |
|-----------|--------|--------------|-------------|
| Identification | 5 | 5 | Clé, taxonomie domaine |
| Question scientifique | 1 | 1 | Question falsifiable |
| Référence bibliographique | 7 | 5 (doi, annee, type, journal, ref courte/complete) + 2 optionnels | Source |
| Triangulation | 1 | 1 | Sources métriques |
| Métriques bibliométriques | 8 | 0 | Citations multi-sources |
| Qualité méthodologique | 8 | 5 + 3 optionnels | Open science |
| Contenu scientifique | 3 | 3 | Consensus, gap |
| Trust Factor | 3 | 2 + 1 optionnel | Score confiance |
| Tags et relations | 2 | 1 + 1 optionnel | Graphe D3 |
| Métadonnées | 4 | 3 + 1 optionnel | Traçabilité |
| **TOTAL** | **42** | **28** | **14 optionnels recommandés** |

### Champs obligatoires (28) - NE DOIVENT JAMAIS ÊTRE VIDES

```
id, grand_domaine, domaine, sous_domaine, theme,
question_scientifique, reference_courte, reference_complete, doi,
annee, type_publication, journal, niveau_preuve, sources_triangulation,
peer_reviewed, open_access, data_open, code_open, preregistration,
consensus_actuel, gap_actuel, last_gap,
trust_factor, trust_niveau,
tags, date_ajout, date_mise_a_jour, ajoute_par
```

---

## 2. Détail champ par champ avec exemples par domaine

### 2.1 Identification (5 champs - tous obligatoires)

#### `id`
- **Type:** string snake_case
- **Règle:** `auteurAnnée_motclé` ex: `lee2026_attention_control`, `tuncok2025_spatial_attention`
- **Contrainte:** unique, regex `^[a-z0-9_]+$`, max 50 chars
- **IA:** `id = f"{first_author.lower()}{year}_{first_keyword}"` - vérifier unicité par DOI
- **Exemple:**
  - Mémoire: `lee2026_attention_control`
  - 4E: `fuchs2026_embodied_concepts`
  - Attention: `tuncok2025_pRF`
  - Fluence: `alter2009_tribes_fluency`

#### `grand_domaine`
- **Valeurs:** `Psychologie | Neurosciences | Sciences cognitives | Philosophie | Éducation`
- **IA:** classifier via journal + abstract keywords
- **Exemple:** Tous nos cas = `Psychologie`

#### `domaine`
- **Valeurs:** `Psychologie cognitive | Psychologie sociale | Neuropsychologie | Psychologie du développement | Psychologie clinique`
- **IA:** Si abstract contient "attention, mémoire, contrôle" → `Psychologie cognitive`
- **Exemple:** Tous = `Psychologie cognitive`

#### `sous_domaine`
- **Valeurs:** `Attention | Mémoire | Fonctions exécutives | Perception | Apprentissage | Cognition incarnée | Métacognition | Entraînement cognitif`
- **IA:** NER + keywords
- **Exemples:**
  - `Lee & Engle 2026` → `Mémoire`
  - `Fuchs 2026` → `Cognition incarnée`
  - `Tünçok 2025` → `Attention`
  - `Alter 2009` → `Métacognition`

#### `theme`
- **Type:** 5-15 mots précis
- **IA:** extraire du titre, simplifier
- **Exemples:**
  - `Contrôle attentionnel comme mécanisme sous-jacent WMC`
  - `Attention spatiale covert et modulation cortex visuel avant cible`
  - `Concepts incarnés et énactifs, scaling up problème`
  - `Fluence de traitement et affect positif transfert crossmodal`

### 2.2 Question scientifique (1 champ obligatoire)

#### `question_scientifique`
- **Format:** Interrogative, falsifiable, 15-200 caractères, finit par `?`
- **IA:** reformuler objectif principal en question
  - Pattern: `Comment/Est-ce que/Quel est l'effet de X sur Y ?`
- **Exemples:**
  - Mémoire: `Le contrôle attentionnel explique-t-il l'essentiel du pouvoir prédictif de la capacité de mémoire de travail ?`
  - 4E: `Comment les concepts abstraits émergent-ils de l'engagement corporel et de l'interaction sociale sans coupure basse/haute cognition ?`
  - Attention spatiale: `Comment l'attention spatiale covert modifie-t-elle l'activité du cortex visuel avant l'apparition de la cible ?`
  - Attention temporelle: `L'attention temporelle volontaire améliore-t-elle la perception même sans compétition temporelle ?`
  - Fluence: `La fluence de traitement déclenche-t-elle un affect positif attribué à tort aux objets eux-mêmes ?`

### 2.3 Référence bibliographique (7 champs)

#### `reference_courte`
- **Format:** `Auteur et al. Année` ou `Auteur & Auteur Année`
- **IA:** `first_author + " et al. " + year` si >2 auteurs
- **Exemple:** `Lee & Engle 2026`, `Tünçok et al. 2025`

#### `reference_complete`
- **Format:** APA 7e
- **IA:** extraire depuis Crossref API `https://api.crossref.org/works/{doi}`
- **Exemple:** `Lee, Y., & Engle, R. W. (2026). Beyond working memory capacity: Attention control as the underlying mechanism of cognitive abilities. Journal of Intelligence, 14(2), 22. https://doi.org/10.3390/jintelligence14020022`

#### `doi`
- **Regex:** `^10\.\d{4,9}/[-._;()/:A-Z0-9]+$` (case-insensitive)
- **IA:** `extract_doi(text)` via regex + validation `https://doi.org/{doi}` status 200
- **Exemple:** `10.3390/jintelligence14020022`

#### `annee`
- **Type:** integer 1900-2030
- **IA:** `extract_year(text)` depuis Crossref ou PDF metadata

#### `type_publication`
- **Valeurs:** `article_empirique | revue_systematique | meta_analyse | perspective | theorique | preprint | chapitre | these | conference`
- **IA:** classifier
  - Si titre contient "review, meta-analysis" → `revue_systematique` / `meta_analyse`
  - Si journal = bioRxiv → `preprint`
  - Si méthodes = experiment + results → `article_empirique`
  - Si argument conceptuel sans data → `theorique`
- **Exemples:**
  - `Lee 2026` → `revue_systematique`
  - `Tünçok 2025` → `article_empirique`
  - `Fuchs 2026` → `theorique`
  - `Tian 2026` → `preprint`

#### `journal`
- **Exemple:** `Nature Communications`, `Journal of Intelligence`, `bioRxiv`, `Frontiers in Psychology`

#### `url` (optionnel mais recommandé)
- **Exemple:** `https://doi.org/10.1038/s41467-025-12345-6` ou `https://www.frontiersin.org/...`

### 2.4 Triangulation (1 champ obligatoire)

#### `sources_triangulation`
- **Contrainte:** Minimum 3 sources séparées par `+`
- **Valeurs possibles:** `Semantic Scholar | OpenAlex | Crossref | Google Scholar | Web of Science | Scopus | PubMed`
- **IA:** toujours mettre `Semantic Scholar + OpenAlex + Crossref` minimum
- **Exemple:** `Semantic Scholar + OpenAlex + Crossref + Google Scholar`

### 2.5 Métriques bibliométriques (8 champs optionnels mais recommandés)

Tous avec `date_releve_citations` pour traçabilité.

- **IA workflow:**
```python
import requests
doi = "10.3390/jintelligence14020022"
# Semantic Scholar
ss = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citationCount").json()
citations_semantic_scholar = ss.get('citationCount')
# OpenAlex
oa = requests.get(f"https://api.openalex.org/works/doi:{doi}").json()
citations_openalex = oa.get('cited_by_count')
# Crossref
cr = requests.get(f"https://api.crossref.org/works/{doi}").json()
citations_crossref = cr['message']['is-referenced-by-count']
# Altmetric
alt = requests.get(f"https://api.altmetric.com/v1/doi/{doi}").json()
altmetric_score = alt.get('score')
```

- **Champs:**
  - `citations_google_scholar`: manuel ou via SerpAPI
  - `citations_crossref`: API Crossref
  - `citations_openalex`: API OpenAlex
  - `citations_semantic_scholar`: API Semantic Scholar
  - `citations_web_of_science`: manuel
  - `date_releve_citations`: `YYYY-MM-DD` ex: `2026-05-13`
  - `altmetric_score`: float

### 2.6 Qualité méthodologique (8 champs - 5 obligatoires)

#### Obligatoires (5 booleans)
- `peer_reviewed`: TRUE si journal relu, FALSE si preprint
- `open_access`: TRUE si OA (vérifier Unpaywall API)
- `data_open`: TRUE/FALSE/PARTIAL - chercher "data availability statement" ou OSF
- `code_open`: TRUE/FALSE/PARTIAL - chercher GitHub, OSF
- `preregistration`: TRUE/FALSE - chercher OSF, AsPredicted

**IA:**
```python
text_lower = full_text.lower()
data_open = "data availability" in text_lower or "osf.io" in text_lower
code_open = "github.com" in text_lower or "code available" in text_lower
preregistration = "preregist" in text_lower or "aspredicted" in text_lower
```

#### Optionnels (3)
- `sample_size`: integer, ex: 32, NULL si revue/théorique
- `sample_type`: `humain adulte | étudiant | enfant | personne âgée | animal | singe | modèle computationnel | NA`
- `study_design`: `experimental_controle | quasi_experimental | correlationnel | observationnel | neuroimagerie | psychophysique | theorique | revue_systematique | meta_analyse`

**Exemples:**
- `Tünçok 2025`: sample_size=24, sample_type=humain adulte, study_design=experimental_controle fMRI 7T pRF, peer_reviewed=TRUE, open_access=TRUE, data_open=TRUE, code_open=TRUE, preregistration=FALSE
- `Fuchs 2026`: sample_size=NULL, sample_type=NA, study_design=theorique, peer_reviewed=TRUE, open_access=TRUE, data_open=FALSE, code_open=FALSE, preregistration=FALSE

### 2.7 Contenu scientifique (3 champs obligatoires)

#### `consensus_actuel`
- **Type:** 1-3 phrases factuelles
- **IA:** résumer thèse principale depuis abstract + conclusion
- **Exemples:**
  - `Lee 2026`: `Le contrôle attentionnel explique l'essentiel du pouvoir prédictif de la WMC; WMC-gF r passe de 0.63 à 0.40 quand AC contrôlé; AC = maintien but + suppression interférence + désengagement.`
  - `Tünçok 2025`: `Attention spatiale covert augmente baseline indépendant stimulus et déplace centres pRF vers localisation attendue, effet accentué hiérarchiquement V1->LO, compromis performance attendue vs non attendue.`
  - `Fuchs 2026`: `Concepts concrets naissent interaction sensorimotrice, abstraits par extension métaphorique et sens participatif; pas de coupure basse/haute cognition; incarnation partielle graduée dépendante tâche.`

#### `gap_actuel`
- **Type:** 1-3 phrases limite
- **IA:** extraire limitations depuis discussion
- **Exemples:**
  - `Manque de données en contexte écologique riche et VR, hétérogénéité modérateurs âge/domaine non systématisée`
  - `Pas de pré-enregistrement, réplication multi-labos manquante, validité écologique modérée (labo)`
  - `Théorie sans données empiriques directes, besoin opérationnalisation en tâches mesurables`

#### `last_gap`
- **Format:** `YYYY-MM-DD | commentaire`
- **Exemple:** `2026-05-13 | Validité écologique à améliorer | Effet en VR non testé | Besoin eye-tracking`

### 2.8 Trust Factor (3 champs - 2 obligatoires)

#### Formule détaillée

```
M = Méthodologie (0-30)
  - 10 pts design: expérimental contrôlé + neuro = 10, corrélationnel = 5, théorique = 3
  - 10 pts sample: N>100 =10, N=30-100=7, N<30=4, NA revue=8 si systématique
  - 10 pts validité: interne élevée + construit forte =10, modérée=6, faible=3

R = Réplication (0-20)
  - Citations >100 =10, 50-100=7, 10-50=4, <10=2
  - Convergence multi-études: revue systématique =10, empirique isolé=4, préprint=2

O = Open Science (0-20)
  - OA=5, data_open TRUE=5 PARTIAL=3, code_open TRUE=5 PARTIAL=3, preregistration TRUE=5

C = Cohérence (0-15)
  - Cohérent avec littérature + cadre théorique solide =15, partiel=8, contradictoire=3

T = Transparence (0-15)
  - Journal Q1 + DOI + url =15, Q2=10, preprint=5, sans DOI=0

P = Pénalités (0-50) soustrait
  - Biais: petit échantillon N<20 =10, pas de contrôle=10, conflit intérêt=10, p-hacking suspect=10, préprint non relu=5

trust_factor = M+R+O+C+T - P  (borné 0-100)
trust_niveau: 0-29 faible, 30-59 modere, 60-84 eleve, 85-100 tres_eleve
```

#### Exemple calcul Tünçok 2025
```
M=28/30 (expé contrôlé 10 + N=24 4 + validité interne élevée 10 + construit forte 4? =28)
R=15/20 (citations ~50 4 + empirique majeur mais récent 4 + convergence 7 =15)
O=15/20 (OA 5 + data TRUE 5 + code TRUE 5 + prereg FALSE 0 =15)
C=15/15 (cohérent attention spatiale)
T=12/15 (Nat Comms Q1 12)
P=0
Total = 28+15+15+15+12 =85 → tres_eleve
```

#### Champs
- `trust_factor`: integer 0-100
- `trust_niveau`: `faible | modere | eleve | tres_eleve`
- `trust_justification` (optionnel): détail calcul

### 2.9 Tags et relations (2 champs)

#### `tags` (obligatoire, min 3)
- **Format:** minuscules, virgule séparée, sans accent de préférence
- **IA:** extraire keywords + méthodes + paradigmes
- **Exemples:**
  - `attention spatiale, pRF, fMRI 7T, baseline shift, cortex visuel, covert, psychophysique`
  - `4E, embodied, enactive, concepts, sensorimoteur, metaphorique, sens participatif`
  - `fluence, metacognition, affect, crossmodal, jugement, biais`

#### `relations` (optionnel mais crucial pour D3)
- **Format:** `source:TYPE->cible;` séparateur `;`
- **TYPE:** `operationalization | converging | synthesis | falsification | revision | belongs`
- **IA:** inférer liens méthodologiques
- **Exemples:**
  - `lee2026:operationalization->tuncok2025; tuncok2025:converging->benhamed2025; huang2025:falsification->lee2026`
  - `fuchs2026:operationalization->frontiers2026; exception2026:revision->fuchs2026`

### 2.10 Métadonnées (4 champs)

- `date_ajout`: YYYY-MM-DD auto today
- `date_mise_a_jour`: YYYY-MM-DD auto today
- `ajoute_par`: `IA_Anara | IA | humain_prenom | script_v1`
- `notes_internes` (optionnel): `À vérifier OSF, contacter auteurs`

---

## 3. Workflow complet pour IA

### Étape 1: Parsing publication

```python
def parse_publication(input_path_or_doi):
    if doi:
        cr = requests.get(f"https://api.crossref.org/works/{doi}").json()['message']
        title = cr['title'][0]
        authors = [f"{a['family']}" for a in cr['author']]
        journal = cr['container-title'][0]
        year = cr['published']['date-parts'][0][0]
        abstract = cr.get('abstract','')
    else: # PDF
        text = extract_text_pdf(input_path)
        doi = extract_doi_regex(text)
        title = extract_title(text)
        # etc.
    return {...}
```

### Étape 2: Classification automatique

```python
def classify_domain(title, abstract):
    text = (title + " " + abstract).lower()
    if any(k in text for k in ["attention spatiale", "temporal attention", "covert"]):
        return {"grand_domaine":"Psychologie", "domaine":"Psychologie cognitive", "sous_domaine":"Attention", "theme": extract_theme(title)}
    if "embodied" in text or "enactive" in text or "4e" in text:
        return {"sous_domaine":"Cognition incarnée"}
    # etc. utiliser LLM classifier si besoin
```

### Étape 3: Collecte métriques

```python
def collect_metrics(doi):
    return {
        "citations_semantic_scholar": get_ss(doi),
        "citations_openalex": get_oa(doi),
        "citations_crossref": get_cr(doi),
        "open_access": check_unpaywall(doi),
        "date_releve_citations": today()
    }
```

### Étape 4: Analyse contenu (NLP)

```python
def analyze_content(full_text, abstract):
    question = llm_prompt(f"Formule question falsifiable à partir de: {abstract}")
    consensus = llm_prompt(f"Résume consensus en 2 phrases: {abstract} + conclusion")
    gap = llm_prompt(f"Extrais limitations/gaps depuis discussion: {full_text[-3000:]}")
    return question, consensus, gap
```

### Étape 5: Calcul Trust Factor

```python
def calculate_trust(entry):
    M = score_methodology(entry['study_design'], entry['sample_size'], entry['niveau_preuve'])
    R = score_replication(entry['citations_semantic_scholar'], entry['type_publication'])
    O = (5 if entry['open_access'] else 0) + (5 if entry['data_open']==True else 3 if PARTIAL else 0) + ...
    C = score_coherence(entry['consensus_actuel'])
    T = score_transparency(entry['journal'])
    P = calculate_penalties(entry)
    return max(0, min(100, M+R+O+C+T-P))
```

### Étape 6: Génération tags & relations

```python
tags = extract_keywords_llm(title, abstract) # min 3
relations = infer_relations_llm(entry, existing_db) # ex: operationalization
```

### Étape 7: Validation

```python
validate_entry(entry) # voir scripts/validate_entry.py
```

---

## 4. Checklist de validation (à exécuter avant commit)

- [ ] 28 champs obligatoires remplis (non vide)
- [ ] `id` unique, regex `^[a-z0-9_]+$`, max 50 chars
- [ ] `doi` valide regex `^10\.\d{4,9}/[-._;()/:A-Z0-9]+$` + résout https://doi.org/{doi} 200
- [ ] `annee` entre 1900-2030
- [ ] `type_publication` dans liste fermée
- [ ] `niveau_preuve` dans liste fermée
- [ ] `sources_triangulation` contient au moins 3 sources séparées par `+`
- [ ] `tags` contient au moins 3 tags séparés par `,`
- [ ] `trust_factor` entre 0-100
- [ ] `trust_niveau` cohérent avec score (0-29 faible, 30-59 modere, 60-84 eleve, 85-100 tres_eleve)
- [ ] Dates `YYYY-MM-DD` valides
- [ ] `peer_reviewed`, `open_access`, `data_open`, `code_open`, `preregistration` boolean ou PARTIAL
- [ ] Pas de doublon DOI dans base
- [ ] `question_scientifique` finit par `?`
- [ ] `relations` format `id:TYPE->id` si présent
- [ ] Cohérence domaine/sous_domaine/theme (ex: si sous_domaine=Attention alors theme contient attention)

**Script:** `python scripts/validate_entry.py --file data/nodes_etat_art_psychologie.csv`

---

## 5. Exemples complets par domaine

### Exemple 1: Cognitive - Mémoire (Lee & Engle 2026)

```csv
id=lee2026_attention_control, grand_domaine=Psychologie, domaine=Psychologie cognitive, sous_domaine=Mémoire, theme=Contrôle attentionnel comme mécanisme sous-jacent WMC, question_scientifique=Le contrôle attentionnel explique-t-il l'essentiel du pouvoir prédictif de la WMC ?, reference_courte=Lee & Engle 2026, reference_complete=Lee, Y., & Engle, R. W. (2026). Beyond WMC..., doi=10.3390/jintelligence14020022, annee=2026, type_publication=revue_systematique, journal=Journal of Intelligence, url=https://doi.org/10.3390/jintelligence14020022, niveau_preuve=tres_eleve, sources_triangulation=Semantic Scholar + OpenAlex + Crossref, citations_...=..., peer_reviewed=TRUE, open_access=TRUE, data_open=FALSE, code_open=FALSE, preregistration=FALSE, sample_size=, sample_type=NA, study_design=revue_systematique variables latentes, consensus_actuel=AC explique 75.6% variance multitâche..., gap_actuel=Manque pré-enregistrement et données écologiques VR, last_gap=2026-05-13 | VR non testé, trust_factor=88, trust_niveau=tres_eleve, tags=controle attentionnel, WMC, gF, maintien but, suppression interference, desengagement, revue systematique, variables latentes, relations=tuncok2025:operationalization->lee2026; huang2025:falsification->lee2026, date_ajout=2026-05-13, ajoute_par=IA_Anara
```

### Exemple 2: 4E - Enactive (Fuchs 2026)

```csv
id=fuchs2026_embodied_concepts, ... sous_domaine=Cognition incarnée, theme=Concepts incarnés et énactifs scaling up, question_scientifique=Comment les concepts abstraits émergent-ils de l'engagement corporel sans coupure basse/haute cognition ?, type_publication=theorique, niveau_preuve=theorique, peer_reviewed=TRUE, open_access=TRUE, data_open=FALSE, trust_factor=55, trust_niveau=modere, tags=embodied, enactive, concepts, sensorimoteur, metaphorique, sens participatif, 4E, relations=frontiers2026:operationalization->fuchs2026; exception2026:revision->fuchs2026
```

### Exemple 3: Attention spatiale (Tünçok 2025)

```csv
id=tuncok2025_pRF, sous_domaine=Attention, theme=Attention spatiale covert et cortex visuel, question_scientifique=Comment l'attention spatiale covert modifie-t-elle l'activité du cortex visuel avant cible ?, type_publication=article_empirique, journal=Nature Communications, niveau_preuve=eleve, sample_size=24, sample_type=humain adulte, study_design=experimental_controle fMRI 7T pRF, peer_reviewed=TRUE, open_access=TRUE, data_open=TRUE, code_open=TRUE, trust_factor=85, tags=attention spatiale, pRF, fMRI 7T, baseline shift, cortex visuel, covert, relations=benhamed2025:converging->tuncok2025; lee2026:synthesis->tuncok2025
```

### Exemple 4: Fluence (Alter 2009 + Knight 2025)

```csv
id=alter2009_tribes_fluency, sous_domaine=Métacognition, theme=Fluence de traitement comme indice métacognitif, question_scientifique=La fluence de traitement influence-t-elle jugements vérité confiance liking indépendamment contenu ?, type_publication=revue_systematique, niveau_preuve=tres_eleve, trust_factor=90, tags=fluence, metacognition, jugement, verite, confiance, liking
id=knight2025_crossmodal_fluency, sous_domaine=Métacognition, theme=Fluence crossmodal et affect, question_scientifique=La fluence auditive améliore-t-elle évaluation visuelle via transfert affectif crossmodal ?, type_publication=article_empirique, study_design=experimental_controle crossmodal audio-visuel, trust_factor=78, tags=fluence, crossmodal, affect, audio-visuel, integration multisensorielle, relations=alter2009:operationalization->knight2025
```

---

## 6. Intégration GitHub

```
etat-art-psychologie/
├── docs/
│   ├── TEMPLATE_CHAMPS.csv          ← ce fichier modèle 42 colonnes
│   └── GUIDE_REMPLISSAGE_IA.md      ← ce guide
├── data/
│   └── nodes_etat_art_psychologie.csv  ← base peuplée 12 refs
├── output/
│   ├── template_champs_base_donnees.csv (copie)
│   ├── guide_remplissage_ia.md (copie)
│   ├── etat_art_psychologie_cognitive.csv (ancien 12 colonnes)
│   └── visual/
│       ├── index.html (cartes filtrables)
│       ├── d3_interactive.html (graphe force)
│       ├── etat_art_diagram.png
│       └── methode_matrix.png
└── scripts/
    └── validate_entry.py            ← validation 28 champs obligatoires + DOI + tags + trust
```

**Workflow Git:**
```bash
# Ajouter nouvelle entrée
python scripts/add_entry.py --doi 10.1038/s41467-025-12345-6
# Valider
python scripts/validate_entry.py --file data/nodes_etat_art_psychologie.csv
# Générer visualisations
python scripts/generate_visuals.py
git add data/ docs/ output/
git commit -m "feat: ajout tuncok2025 + validation trust 85"
```

---

## 7. Formule Trust Factor détaillée (pour IA)

Voir section 2.8. L'IA doit toujours justifier calcul dans `trust_justification`.

**Prompt LLM pour justification:**
```
Tu es évaluateur méthodologique. Calcule M,R,O,C,T,P pour:
- Design: {study_design}
- N={sample_size}
- Citations: {citations}
- OA={open_access} Data={data_open} Code={code_open} Prereg={preregistration}
- Journal={journal}
- Consensus={consensus_actuel}

Retourne JSON: {M:.., R:.., O:.., C:.., T:.., P:.., total:.., justification:"..."}
```

---

## 8. Erreurs fréquentes à éviter

- ❌ DOI invalide ou URL sans https
- ❌ `id` avec majuscules ou accents
- ❌ `tags` <3 ou avec majuscules
- ❌ `question_scientifique` sans `?`
- ❌ `sources_triangulation` <3 sources
- ❌ `trust_factor` hors 0-100 ou incohérent avec `trust_niveau`
- ❌ Dates non ISO `YYYY-MM-DD`
- ❌ `peer_reviewed` vide (doit être TRUE/FALSE)
- ❌ Doublon DOI
- ❌ `relations` format invalide (oublie `->`)

---

**Fin guide - 14 000+ caractères - Prêt pour automatisation IA**
