# Rapport d'exécution — ♅ Uranus

- **Tâche** : 
- **Statut** : ✅ succès
- **Cerveau** : regles — déterministe
- **Durée** : 0.0 s
- **Run** : `run_20260831_182951_f162`
- **⚠️ Mode dégradé** : une ou plusieurs compétences ont utilisé des fixtures de démonstration (réseau indisponible). Les données correspondantes ne sont PAS réelles.

## Plan exécuté

1. ✅ **search_literature** — 5 références uniques trouvées (OpenAlex:3 + Crossref:3) [MODE DÉGRADÉ hors-ligne : fixtures démo] (0.0 s)
2. ✅ **synthesize** — Synthèse générée : 5 références groupées (source : recherche du run) (0.0 s)

## Détail par compétence

### 1. search_literature

*Recherche documentaire multi-bases (Crossref, OpenAlex, PubMed) avec filtre d'années, résultats normalisés et export CSV/JSON.*

→ 5 références uniques trouvées (OpenAlex:3 + Crossref:3) [MODE DÉGRADÉ hors-ligne : fixtures démo]

- Requête : « psychology » | Période 2020–2026 | Limites : 10/base
- OpenAlex : 3 résultats
- Crossref : 3 résultats
- • Relative effects of psychotherapies for mental disorders: systematic review and meta-analy (2024) [OpenAlex]
- • Negative intergroup contact: influences, consequences, and moderators of contact effects (2024) [OpenAlex]
- • Effectiveness of physical activity interventions for improving cognitive function in child (2025) [OpenAlex]

**Artefacts :**
- `output/agent_runs/run_20260831_182951_f162/recherche_resultats.csv`

### 2. synthesize

*Synthétise les références par domaine : effectifs, trust moyen, niveaux de preuve, gaps agrégés → rapport markdown avec questions de recherche émergentes.*

→ Synthèse générée : 5 références groupées (source : recherche du run)

- 5 références, 538 citations cumulées

**Artefacts :**
- `output/agent_runs/run_20260831_182951_f162/synthese.md`
- `output/agent_runs/run_20260831_182951_f162/synthese.json`

---
*Généré automatiquement par Uranus (♅), agent chercheur du Cognitorium — traçabilité complète dans `trace.json`.*