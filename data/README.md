# Data - Nodes État de l'Art Psychologie

Fichier principal: `nodes_etat_art_psychologie.csv`

- 42 colonnes (28 obligatoires + 14 optionnelles)
- 14 entrées peuplées (12 refs + 2 domaines hubs)
- Validation: `python scripts/validate_entry.py --file data/nodes_etat_art_psychologie.csv`
- Template champs: `docs/TEMPLATE_CHAMPS.csv`
- Guide IA: `docs/GUIDE_REMPLISSAGE_IA.md`

Colonnes: voir docs/TEMPLATE_CHAMPS.csv pour type, obligatoire, exemple, description, valeurs possibles.

Utilisation:
- Importer dans Notion / Airtable / Obsidian Dataview / D3 graph
- Relations: champ `relations` format `id:TYPE->id;` pour graphe D3 interactif
- Trust factor: 0-100 calculé M+R+O+C+T-P
