# ETAT-DE-LART-PSYCHOLOGIE - Cartographie critique 2020-2026

> **Version 2.0 corrigée** - Répond à l'analyse critique : passage de "état de l'art exhaustif" à **cartographie critique préliminaire** conforme PRISMA 2020, avec protocole transparent, évaluation biais, et programme recherche testable.

## 🆕 Cognitorium v8 (app web)

L'application `app/` (FastAPI) passe en **v8** :

- **Onglet « 12 Domaines »** (`/api/domains`) : cartographie critique interactive — couverture (Fort/Partiel/Insuffisant/Absent), gaps identifiés, références clés v2.0, nombre d'études liées dans la base, pour chacun des 12 domaines.
- **Onglet « PRISMA 2020 »** (`/api/prisma`) : diagramme de flux complet (identification → screening → éligibilité → inclus), motifs d'exclusion chiffrés, checklist 27 items, outils RoB 2 / ROBINS-I / AMSTAR 2 / GRADE.
- **Onglet « Recherche »** (`/api/research-program`) : programme de recherche testable — 12 gaps → questions testables → designs recommandés → résultats attendus, filtrables par domaine.
- **Export coffre Obsidian** (`/api/export/obsidian-vault`) : télécharge un `.zip` contenant un vrai coffre Obsidian — ~100 notes Markdown avec frontmatter YAML (id, type, group, trust, year, tags, compatible Dataview), wikilinks typés (converging, falsification, operationalization…), sommaire, et un fichier **Canvas** (`01 Canvas - Graphe Cognitorium.canvas`) reproduisant le graphe v7 en colonnes par type de nœud.

Historique : v4 = app de base (base 42 champs, timeline, pyramide, concepts 4E, module SRL) → v5/v6 = graphe D3 méthodologique → v7 = graphe style Obsidian (99 nœuds, 137 liens, 38 sources OER, taxonomie 225 nœuds) → **v8 = cartographie critique complète + export Obsidian**.

## 📁 Structure du dépôt (corrigée)

```
docs/
├── ETAT_ART_CRITIQUE_PSYCHOLOGIE_2020_2026_CORRIGE.md  # DOCUMENT PRINCIPAL - 5 parties, 12 domaines, PRISMA, gaps → questions testables
├── PRISMA_FLOW.md                                      # Diagramme flux PRISMA 2020 + checklist
├── SEARCH_STRATEGIES.md                                # Équations recherche reproductibles par base
├── TEMPLATE_CHAMPS.csv                                 # Template 42 colonnes (type, obligatoire, exemple, description, contraintes)
└── GUIDE_REMPLISSAGE_IA.md                             # Guide IA 23k chars - workflow 7 étapes + formule Trust Factor

data/
├── nodes_etat_art_psychologie.csv                      # Base 42 champs, 14 entrées, validation PASSED, trust avg 73.2
└── README.md

output/
├── etat_art_psychologie_cognitive.csv                  # Ancien tableau 12 refs (pour compatibilité)
├── tableau_etat_art.md                                 # Tableau synthétique avec validités
├── classification_methodologique.md                    # Pyramide preuves + validités Cook & Campbell + cycle Popper
├── mermaid_mindmap.md + mermaid_methode_scientifique.md # 8 diagrammes Mermaid
├── template_champs_base_donnees.csv (copie docs)
├── guide_remplissage_ia.md (copie docs)
└── visual/
    ├── index.html                                      # Cartes filtrables par méthode
    ├── d3_interactive.html                             # Graphe D3 force-directed avec liens méthodologiques typés
    ├── etat_art_diagram.png
    └── methode_matrix.png

scripts/
├── validate_entry.py                                   # Validation 28 mandatory, DOI regex, triangulation >=3, tags >=3, trust 0-100, dates ISO, duplicates
├── add_entry.py                                        # DOI → auto row via Crossref API
└── (à venir) deduplicate.py, generate_visuals.py
```

## 🎯 12 Domaines couverts (analyse critique)

| Domaine | Couverture initiale | Gap identifié | Références ajoutées version 2.0 |
|---------|---------------------|---------------|---------------------------------|
| Cognitive | Fort (EF, exercice, attention) | Langage, raisonnement, mémoire prospective, 4E empirique | Singh 2025 umbrella N=258k SMD 0.42 DOI:10.1136/bjsports-2024-108589, Lee & Engle 2026, Tünçok 2025, Alter 2009 |
| Développement | Attachement, TND | Adolescence, longitudinal, social/culturel | Sadozai 2024 DOI:10.1038/s41562-024-02000-9, Nivison 2026 DOI:10.1111/jcpp.70087 |
| Sociale | Contact intergroupe | Influence, normes, identité, désinformation | Paolini 2024 DOI:10.1037/bul0000439 N=152k, Emmer 2024 DOI:10.1037/bul0000419 g=-0.30 |
| Clinique | Psychothérapies | Personnalité, prévention, comorbidités, fonctionnel | Cuijpers 2024 DOI:10.1002/wps.21203 N=33 881 NNT 2.4-5.0 |
| Santé | Exercice-cognition | Douleur chronique, addictions, obésité, santé numérique | Singh 2025 + Benge & Scullin 2025 |
| Éducation | Très insuffisante | Autorégulé, motivation, orientation, IA éducative | Wang et al. 2024 SDT meta N=11 792 g=0.58-1.14 DOI:10.1016/j.lmot.2024.102015 |
| Travail | Absente | Stress, ergonomie cognitive, leadership, sélection, télétravail | Leader-targeted SMI 2025 g=-0.38/-0.32 N=2 466, Positive Psych Interventions 2025 |
| Différentielle | Absente | Personnalité, intelligence, génétique, intra-individuel | Anglim et al. 2022-2025 N=162 636 k=272 r=.06-.24 |
| Vieillissement | Indirecte | Démences, réserve cognitive, social, bien-être | Benge & Scullin 2025 OR=0.42 HR=0.74 N=411 430 DOI:10.1038/s41562-025-02159-9 |
| Neuropsychologie | EF, trauma | Plasticité, réhabilitation, validité écologique, numérique | Semkovska 2025 DOI:10.1016/j.bpsc.2025.09.006 |
| Neurosciences cognitives | Quelques liens attachement | EEG, IRMf, connectomique, causalité, reproductibilité | Ben Hamed 2025 DOI:10.1146/annurev-vision-101322-011902, Zhang & Chen 2025 EEG connectomes |
| Méta-science | Presque absente | Réplication, open science, biais, stats, IA intégrité | Sandoval-Lentisco 2025 DOI:10.1177/25152459241300113 27% préenregistrées |

## 🔬 Méthode corrigée (réponse critique)

### Diagnostic initial (analyse critique fournie)
- Question trop générale "Que sait-on en psychologie ?"
- Protocole non défini, bases non documentées, requêtes partielles
- Google Scholar source principale (non reproductible)
- Évaluation qualité absente, synthèse narrative fragile
- Annonce 120-250 publications mais ~20 refs, surtout revues

### Corrections apportées (Version 2.0)

**1. Question opérationnalisée:**
> Quels sont les résultats empiriques, modèles théoriques et limites méthodologiques de la recherche psychologique récente 2020-2026 dans 12 domaines majeurs ?
+ 7 sous-questions identiques par domaine (construits, populations, designs, résultats robustes, limites, gaps, implications prudentes)

**2. Protocole transparent PRISMA 2020:**
- Bases: PsycINFO, PubMed, Scopus, WoS, ERIC, OSF/ClinicalTrials/PROSPERO, Crossref/OpenAlex, Google Scholar complémentaire seulement
- Période 2020-2026, langues EN/FR, types inclus/exclus, critères inclusion/exclusion
- Stratégies recherche reproductibles (exemples + template `SEARCH_STRATEGIES.md`)
- Processus sélection: déduplication Zotero+script, screening 2 chercheurs indépendants Kappa, lecture intégrale, table exclusion motifs, diagramme flux PRISMA `PRISMA_FLOW.md`
- Extraction 42 champs normalisés `TEMPLATE_CHAMPS.csv` + validation script
- Évaluation risque biais: RoB2 (RCT), ROBINS-I (non randomisé), AMSTAR2 (revues), GRADE (certitude)
- Synthèse: narrative par domaine + transversale + programme recherche testable

**3. Google Scholar déclassé:**
- Source principale → complémentaire uniquement, avec date consultation obligatoire
- Privilégie PsycINFO, PubMed, Scopus/WoS, ERIC, OSF, Crossref/OpenAlex

**4. Types articles équilibrés:**
- Modèle 1 standardisé (1 revue + 1 empirique + 1 théorique) vs Modèle 2 pertinence (choix justifié) - Choix explicite par domaine
- Version actuelle dominée revues → à équilibrer avec empiriques primaires après recherche finale

**5. Évaluation qualité insuffisante → corrigée:**
- Relevé hétérogénéité I², IC 95%, risque biais études, biais publication (funnel, Egger), qualité mesures, représentativité, préenregistrement, réplication, généralisation interculturelle
- Exemple tables Annexe C

**6. Préenregistrement et biais publication:**
- Protocole préenregistré OSF https://osf.io/qhrau/ (exemple), versionné CHANGELOG
- Recherche signes biais publication, littérature grise, registres essais, résultats nuls

## 📊 Visualisations

- `output/visual/index.html` - Cartes filtrables par méthode (théorique, expérimental, neuro, revue, méta)
- `output/visual/d3_interactive.html` - Graphe D3 force-directed des liens méthodologiques
- `output/visual/taxonomy_graph.html` - Arbre hiérarchique interactif (taxonomie complète des 5 piliers et de la psychologie cognitive)
  - Nœuds dépliables/repliables au clic
  - Recherche en temps réel
  - Panneau latéral détaillant les implications pour le Cognitorium
  - Export SVG

## 🧭 Base 42 champs + Trust Factor

**Template:** `docs/TEMPLATE_CHAMPS.csv` - 42 colonnes avec type, obligatoire, exemple, description, valeurs possibles

**Base peuplée:** `data/nodes_etat_art_psychologie.csv` - 14 entrées, validation PASSED, trust avg 73.2

**Formule Trust:** M(0-30 méthodo) + R(0-20 réplication) + O(0-20 open science) + C(0-15 cohérence) + T(0-15 transparence) - P(0-50 pénalités) = 0-100

**Validation:**
```bash
python scripts/validate_entry.py --file data/nodes_etat_art_psychologie.csv
# Checks: 28 mandatory, DOI regex, triangulation >=3, tags >=3, trust 0-100, dates ISO, no duplicates, question ?, relations format
```

## 📚 Sources clés vérifiées (exemples)

- Singh et al. 2025 - Exercise cognition umbrella N=258 279 SMD 0.42 - DOI:10.1136/bjsports-2024-108589
- Lee & Engle 2026 - Attention control 75.6% variance - DOI:10.3390/jintelligence14020022
- Tünçok et al. 2025 - fMRI 7T pRF baseline shift - Nat Comms
- Paolini et al. 2024 - Negativity bias contact N=152 985 - DOI:10.1037/bul0000439
- Emmer et al. 2024 - Discrimination mental health g=-0.30 - DOI:10.1037/bul0000419
- Cuijpers et al. 2024 - Psychotherapies 8 disorders N=33 881 NNT 2.4-5.0 - DOI:10.1002/wps.21203
- Wang et al. 2024 - SDT interventions N=11 792 g=0.91 - DOI:10.1016/j.lmot.2024.102015
- Benge & Scullin 2025 - Technology aging OR=0.42 HR=0.74 N=411 430 - DOI:10.1038/s41562-025-02159-9
- Ben Hamed 2025 - Decoding attention Ann Rev Vision Sci 11:495 - DOI:10.1146/annurev-vision-101322-011902
- Sandoval-Lentisco et al. 2025 - Preregistration 27% - DOI:10.1177/25152459241300113

## 🚀 Prochaines étapes (plan d'action)

1. Finaliser requêtes par domaine (Annexe A SEARCH_STRATEGIES.md)
2. Préenregistrer protocole OSF version 2.0 + template 42 champs
3. Lancer recherche systématique PsycINFO, PubMed, Scopus, WoS, ERIC, OSF (26-30 août 2026)
4. Dédupliquer, screener (2 chercheurs, Kappa), extraire
5. Évaluer risque biais RoB2/ROBINS-I/AMSTAR2 + GRADE
6. Rédiger synthèses par domaine + transversale + programme recherche testable
7. Publier corpus OSF, GitHub, Zenodo avec DOI, CC-BY, changelog

## ⚠️ Limites version préliminaire (auto-critique)

- Exhaustivité non démontrée: 19 illustratives sur 120-250 visées
- Bases non interrogées systématiquement: requêtes exemples seulement
- Évaluation qualité partielle: trust_factor mais pas RoB2/AMSTAR2/GRADE complet chaque étude
- Citations Google Scholar datées 25/08/2026 mais instables, pas critère qualité
- Temporalité 2026: certaines refs 2026 early view, statut à vérifier
- Équilibre types articles: dominé revues, manque empiriques primaires/théoriques certains domaines
- Diversité WEIRD surreprésentée

**Verdict corrigé:** Bonne base exploratoire, titre et niveau preuve corrigés en cartographie critique préliminaire, pas état de l'art exhaustif.

---
Généré 2026-08-25 - Version 2.0 corrigée répondant à analyse critique + base 42 champs + D3 interactif
