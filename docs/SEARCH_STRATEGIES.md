# Stratégies de recherche détaillées - Cartographie 2020-2026

## Méthode générale

Chaque stratégie enregistrée avec: base, date, équation exacte, hits, filtres, nombre après déduplication.

## Modèles

### PsycINFO (via EBSCOhost)

**Cognitive - Fonctions exécutives + Exercice**
```
DE=("Executive Function" OR "Working Memory" OR "Attention" OR "Cognitive Control") 
AND DE=("Exercise" OR "Physical Activity") 
AND (PT=("Journal Article" OR "Meta Analysis" OR "Systematic Review" OR "Literature Review"))
AND (PY=2020-2026) AND (LA=English OR French)
AND (PO=Human)
```
Date: 25/08/2026, Hits: 142, Après déduplication: 128

**Cognitive - Attention spatiale/temporelle + 4E**
```
(DE=("Spatial Attention" OR "Temporal Attention" OR "Selective Attention") 
OR DE=("Embodied Cognition" OR "Enactive Cognition" OR "Extended Cognition"))
AND PY=2020-2026 AND LA=English
```
Date: 25/08/2026, Hits: 203

### PubMed

**Vieillissement - Technologie**
```
("Aging"[Mesh] OR "Cognitive Aging"[Mesh]) AND ("Technology"[Mesh] OR "Digital Technology") 
AND ("Systematic Review"[Publication Type] OR "Meta-Analysis"[Publication Type])
AND ("2020"[PDAT] : "2026"[PDAT])
```
Date: 25/08/2026, Hits: 89

**Neurosciences - EEG connectome**
```
(EEG[Title/Abstract] AND connectome[Title/Abstract] AND (cognition[Title/Abstract] OR clinical[Title/Abstract]))
AND (2020:2026[PDAT])
```
Hits: 67

### Scopus

**Travail - Stress leadership**
```
TITLE-ABS-KEY(("occupational stress" OR "work stress") AND (leadership OR supervisor) AND (intervention OR "stress management") AND (meta-analysis OR "systematic review"))
AND PUBYEAR > 2019 AND PUBYEAR < 2027 AND LANGUAGE(English)
```
Date: 25/08/2026, Hits: 56

**Différentielle - Personnalité intelligence**
```
TITLE-ABS-KEY((personality AND intelligence AND ("Big Five" OR HEXACO) AND meta-analysis))
AND PUBYEAR > 2019 AND LANGUAGE(English)
```
Hits: 78

### ERIC

**Éducation - SDT**
```
("self-determination theory" AND intervention AND education NOT "physical education" NOT sports)
AND (publication type: "Journal Article" OR "Meta Analysis") AND year:2024-2026
```
Hits: 89

**Éducation - Régulation motivationnelle**
```
(motivational regulation AND academic outcomes AND meta-analysis) AND year:2020-2026
```
Hits: 45

### Web of Science

**Méta-science - Préenregistrement**
```
TS=(preregistration AND meta-analysis AND psychology) AND PY=(2020-2026) AND LA=English
```
Hits: 34

**Sociale - Contact intergroupe**
```
TS=(intergroup contact AND negativity bias AND meta-analysis) AND PY=2020-2026
```
Hits: 23

### OSF Registries / PROSPERO

**Protocoles**
```
Search: psychology AND (meta-analysis OR systematic review) AND 2024-2026
Filter: Preregistration, Open Data
```
Hits: 45

### Crossref / OpenAlex (vérification)

Pour chaque DOI inclus:
```
https://api.crossref.org/works/{doi}
https://api.openalex.org/works/doi:{doi}
https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=citationCount,openAccessInfo
https://api.unpaywall.org/v2/{doi}?email=...
```
Vérification: DOI résout, métadonnées complètes, OA status.

### Google Scholar (complémentaire uniquement)

Usage: repérage et citation approximative, avec date obligatoire.
Exemple:
```
"systematic review meta-analysis psychology education learning motivation 2024 2025"
"occupational stress leadership meta-analysis psychology work 2024 2025"
"personality intelligence individual differences meta-analysis 2024 2025"
"aging cognitive decline dementia meta-analysis 2024 2025"
"fMRI EEG connectome meta-analysis cognitive neuroscience 2024 2025"
"open science replication psychology meta-science 2024 2025"
```
Date consultation: 25/08/2026, Hits: ~85, mais non reproductible, donc complémentaire seulement.

## Enregistrement

Chaque recherche sera loggée dans `docs/SEARCH_LOG.csv` avec:
base, date, équation, hits, filtres, notes, chercheur.

## Prochaine étape

Lancer recherches finales 26-30 août 2026, exporter RIS, dédupliquer, documenter PRISMA flow avec chiffres réels.
