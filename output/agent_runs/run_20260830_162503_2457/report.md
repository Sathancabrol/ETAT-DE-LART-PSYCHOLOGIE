# Rapport d'exécution — ♅ Uranus

- **Tâche** : méta-analyse sur l'attention 2024-2026, génère le papier scientifique
- **Statut** : ✅ succès
- **Cerveau** : regles — déterministe
- **Durée** : 0.01 s
- **Run** : `run_20260830_162503_2457`
- **⚠️ Mode dégradé** : une ou plusieurs compétences ont utilisé des fixtures de démonstration (réseau indisponible). Les données correspondantes ne sont PAS réelles.

## Plan exécuté

1. ✅ **search_literature** — 5 références uniques trouvées (OpenAlex:3 + Crossref:3) [MODE DÉGRADÉ hors-ligne : fixtures démo] (0.0 s)
2. ✅ **deduplicate** — 0 doublon(s) supprimé(s) sur 5 résultats → 5 conservés (0.0 s)
3. ✅ **synthesize** — Synthèse générée : 5 références groupées (source : recherche du run) (0.0 s)
4. ✅ **write_paper** — Papier de synthèse généré (5 réf., 3 méta-analyses, 538 citations) + documentation de lecture (0.0 s)

## Détail par compétence

### 1. search_literature

*Recherche documentaire multi-bases (Crossref, OpenAlex, PubMed) avec filtre d'années, résultats normalisés et export CSV/JSON.*

→ 5 références uniques trouvées (OpenAlex:3 + Crossref:3) [MODE DÉGRADÉ hors-ligne : fixtures démo]

- Requête : « attention meta-analysis psychology » | Période 2024–2026 | Limites : 10/base
- OpenAlex : 3 résultats
- Crossref : 3 résultats
- • Relative effects of psychotherapies for mental disorders: systematic review and meta-analy (2024) [OpenAlex]
- • Negative intergroup contact: influences, consequences, and moderators of contact effects (2024) [OpenAlex]
- • Effectiveness of physical activity interventions for improving cognitive function in child (2025) [OpenAlex]

**Artefacts :**
- `output/agent_runs/run_20260830_162503_2457/recherche_resultats.csv`

### 2. deduplicate

*Déduplique les résultats de recherche du run (DOI exact + titres similaires) ou la base 42 champs ; alimente les compteurs PRISMA.*

→ 0 doublon(s) supprimé(s) sur 5 résultats → 5 conservés

- Identifiés (toutes bases) : 5
- Supprimés : 0 (0 DOI identiques, 0 titres similaires)
- Conservés : 5

**Artefacts :**
- `output/agent_runs/run_20260830_162503_2457/deduplication_rapport.json`

### 3. synthesize

*Synthétise les références par domaine : effectifs, trust moyen, niveaux de preuve, gaps agrégés → rapport markdown avec questions de recherche émergentes.*

→ Synthèse générée : 5 références groupées (source : recherche du run)

- 5 références, 538 citations cumulées

**Artefacts :**
- `output/agent_runs/run_20260830_162503_2457/synthese.md`
- `output/agent_runs/run_20260830_162503_2457/synthese.json`

### 4. write_paper

*Génère un papier scientifique (synthèse structurée : résumé, méthode PRISMA, résultats, discussion, références DOI) + sa documentation de lecture, à partir des résultats du run ou de la base.*

→ Papier de synthèse généré (5 réf., 3 méta-analyses, 538 citations) + documentation de lecture

- paper.md : 59 sections (résumé, méthode, résultats, discussion, références)
- paper_documentation.md : statut épistémique, évaluation, reproductibilité

**Artefacts :**
- `output/agent_runs/run_20260830_162503_2457/paper.md`
- `output/agent_runs/run_20260830_162503_2457/paper_documentation.md`

---
*Généré automatiquement par Uranus (♅), agent chercheur du Cognitorium — traçabilité complète dans `trace.json`.*