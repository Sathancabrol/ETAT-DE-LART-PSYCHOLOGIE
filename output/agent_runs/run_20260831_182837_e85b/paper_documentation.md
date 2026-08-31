# Documentation — comment lire ce papier généré

## Statut épistémique
Synthèse **documentaire** : agrégation et hiérarchisation de références réelles.
Elle ne remplace ni une revue systématique préenregistrée (2 évaluateurs, Kappa),
ni une méta-analyse originale (extraction d'effets, hétérogénéité I², biais de publication).

## Comment évaluer chaque référence
1. **Trust factor** (0-100) : méthodo + réplication + open science + cohérence + transparence ;
2. **Niveau de preuve** : méta-analyse > revue systématique > expérimental > corrélationnel > théorique ;
3. **Recoupement** : `sources_triangulation ≥ 3` exigé dans la base 42 champs.

## Données et reproductibilité
- Run complet : `output/agent_runs/run_20260831_182837_e85b/trace.json` ;
- Résultats bruts : `recherche_resultats.csv` / `.json` dans le même dossier ;
- Base 42 champs : `data/nodes_etat_art_psychologie.csv`.

## Prolonger le travail
- Demander l'enrichissement des DOI retenus (`enrich_doi`) ;
- Lancer l'audit trust + biais (`trust_scoring`, `bias_assessment`) ;
- Programmer une veille sur le sujet (`monitor_watch`).