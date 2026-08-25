# Index complet du projet ETAT-DE-LART-PSYCHOLOGIE

## 🎯 Objectif
État de l'art de la psychologie (2020-2026) + transposition 4E/énactivisme dans Cognitorium, avec méthode scientifique transparente, base de données 42 champs, visualisations D3.

## 📁 Arborescence complète

```
ETAT-DE-LART-PSYCHOLOGIE/
├── README.md                                           # Vue d'ensemble + structure + 12 domaines + méthode corrigée
├── docs/
│   ├── INDEX_PROJET.md                                 # Ce fichier
│   ├── ETAT_ART_CRITIQUE_PSYCHOLOGIE_2020_2026_CORRIGE.md # DOCUMENT PRINCIPAL - Version 2.0 corrigée PRISMA 2020 (5 parties, 12 domaines)
│   ├── ANALYSE_CONCEPTS_COGNITORIUM_4E.md              # Analyse 10 concepts 4E avec sources, gaps, opérationnalisation, modèle 6 couches, MVP
│   ├── SOURCE_PASTE_ANALYSE_4E_ORIGINAL.md             # Source originale paste.txt fournie
│   ├── PRISMA_FLOW.md                                  # Diagramme flux PRISMA 2020 + checklist
│   ├── SEARCH_STRATEGIES.md                            # Équations recherche reproductibles
│   ├── TEMPLATE_CHAMPS.csv                             # Template 42 colonnes (champ, type, obligatoire, exemple, description, contraintes)
│   └── GUIDE_REMPLISSAGE_IA.md                         # Guide IA 23k chars, workflow 7 étapes, formule Trust Factor
├── data/
│   ├── nodes_etat_art_psychologie.csv                  # Base 42 champs, 14 entrées, validation PASSED, trust avg 73.2
│   └── README.md                                       # Doc base
├── output/
│   ├── classification_methodologique.md                # Pyramide preuves + validités + cycle Popper + matrice Méthode x Domaine
│   ├── tableau_etat_art.md                             # Tableau synthétique avec validités
│   ├── etat_art_psychologie_cognitive.csv              # Ancien tableau 12 refs (compatibilité)
│   ├── mermaid_mindmap.md                              # 4 diagrammes Mermaid (mindmap, flowchart, quadrant, graph)
│   ├── mermaid_methode_scientifique.md                 # 4 diagrammes supplémentaires (Sankey, timeline, arbre décision, radar)
│   ├── template_champs_base_donnees.csv                # Copie TEMPLATE_CHAMPS.csv
│   ├── guide_remplissage_ia.md                         # Copie GUIDE_REMPLISSAGE_IA.md
│   └── visual/
│       ├── index.html                                  # Visualisation cartes filtrables par méthode
│       ├── d3_interactive.html                         # Graphe D3 force-directed avec liens méthodologiques typés (operationalization, converging, synthesis, falsification, revision)
│       ├── etat_art_diagram.png                        # Infographie mindmap générée
│       └── methode_matrix.png                          # Matrice Méthode x Domaine générée
└── scripts/
    ├── validate_entry.py                               # Validation 28 mandatory, DOI regex, triangulation >=3, tags >=3, trust 0-100, dates ISO, duplicates
    └── add_entry.py                                    # DOI -> auto row via Crossref API
```

## 🔬 Méthode scientifique

- Question opérationnalisée + 7 sous-questions par domaine
- Protocole préenregistré OSF, versionné CHANGELOG
- Bases: PsycINFO, PubMed, Scopus, WoS, ERIC, OSF/ClinicalTrials/PROSPERO, Crossref/OpenAlex, Google Scholar complémentaire seulement
- Stratégies recherche reproductibles (SEARCH_STRATEGIES.md)
- Processus sélection PRISMA 2020 (PRISMA_FLOW.md)
- Extraction 42 champs (TEMPLATE_CHAMPS.csv) + validation script
- Évaluation risque biais RoB2, ROBINS-I, AMSTAR2, GRADE
- Synthèse narrative + transversale + programme recherche testable

## 🧠 Concepts 4E analysés (10)

Cognition incarnée, située/embedded, énactivisme, étendue, affordance, ACT-IN, charge cognitive, agence, émotion/régulation, échec couplage.
Pour chaque: définition docs, définition scientifique, intérêt Cognitorium, solidité 1-5, sources 2024-2026, gaps, chaîne opérationnalisation concept->mécanisme->comportement->fonctionnalité->métrique->hypothèse testable.

## 📊 Visualisations

- `output/visual/index.html`: cartes filtrables
- `output/visual/d3_interactive.html`: graphe D3 force-directed
  - Nœuds: domaines + méthodes hubs + références
  - Liens typés: operationalization, converging, synthesis, falsification, revision
  - Modes: force, pyramide (niveau preuve), timeline (2009-2026)
  - Drag, zoom, click focus, filtres, export SVG

## 🗄️ Base 42 champs

28 obligatoires + 14 optionnels. Trust Factor M+R+O+C+T-P 0-100.

Validation:
```bash
python scripts/validate_entry.py --file data/nodes_etat_art_psychologie.csv
# PASSED - 14 rows, trust avg 73.2
```

## 🚀 Prochaines étapes

1. Finaliser requêtes (SEARCH_STRATEGIES.md)
2. Préenregistrer OSF
3. Recherche systématique 26-30 août 2026
4. Dédupliquer, screener, extraire 120-250 refs
5. Évaluer biais, synthèses, publier OSF/GitHub/Zenodo

## 📚 Sources clés

- Singh et al. 2025 DOI:10.1136/bjsports-2024-108589 N=258k SMD 0.42
- Paolini et al. 2024 DOI:10.1037/bul0000439 N=152k
- Cuijpers et al. 2024 DOI:10.1002/wps.21203 N=33k NNT 2.4-5.0
- Benge & Scullin 2025 DOI:10.1038/s41562-025-02159-9 OR=0.42 N=411k
- Sandoval-Lentisco 2025 DOI:10.1177/25152459241300113 27% prereg
- Frontiers Edu 2026 DOI:10.3389/feduc.2026.1811569 SMD 0.448
- Liu et al. 2025 meta g=0.406 DOI:10.3389/fpsyg.2025.1658797
- etc. (voir docs/ETAT_ART_CRITIQUE...)

## 📝 Licence

CC-BY 4.0 - Version 2.0 corrigée 25 août 2026
