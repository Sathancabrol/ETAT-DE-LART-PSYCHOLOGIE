# Uranus ♅ — Agent Chercheur du Cognitorium

> **Uranus** (Ouranos, Οὐρανός) : divinité primordiale du ciel chez les Grecs, « celui qui couvre le ciel » — la planète ♅ porte son nom. L'agent Uranus cartographie le ciel de la connaissance : agent scientifique hybride qui planifie et exécute des tâches de recherche via **11 compétences** — recherche documentaire multi-bases, enrichment DOI, métriques de citations, déduplication, validation 42 champs, Trust Factor, dépistage de biais, flux PRISMA, synthèse par domaine, visualisation, veille scientifique.

*Identité centralisée dans `agent/core/context.py` (`AGENT_NAME`, `AGENT_SYMBOL`, `AGENT_TAGLINE`) : un seul endroit à changer pour renommer l'agent partout — page web, CLI, rapports, API.*

## 🧠 Architecture

```
Tâche (langage naturel, FR)
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│ PLANIFICATEUR (cerveau)                                  │
│  • Règles déterministes (défaut, sans clé API)           │
│    - déclencheurs regex par compétence                   │
│    - extraction de paramètres (DOI, années, fenêtre…)    │
│    - composition de pipelines (« recherche systématique » │
│      → recherche → dédup → PRISMA → synthèse)            │
│  • LLM optionnel (OPENAI_API_KEY / ANTHROPIC_API_KEY)    │
│    - affine le plan à partir du catalogue des compétences│
│    - repli automatique sur les règles en cas d'erreur    │
└──────────────────────────────────────────────────────────┘
   │  Plan = liste ordonnée d'étapes (skill + params)
   ▼
┌──────────────────────────────────────────────────────────┐
│ ORCHESTRATEUR (agent/core/agent.py)                      │
│  • exécution séquentielle, état partagé entre étapes     │
│  • chaque étape : durée, statut, artefacts, traçabilité  │
│  • une étape qui échoue n'interrompt pas le run          │
└──────────────────────────────────────────────────────────┘
   │
   ▼
output/agent_runs/<run_id>/
   ├── trace.json      # trace machine complète (plan + steps + résultats)
   ├── report.md       # rapport lisible
   └── …               # artefacts des compétences (csv, md, html, json)
```

## 📚 Les 11 compétences

| # | Compétence | Catégorie | Rôle |
|---|-----------|-----------|------|
| 1 | `search_literature` | 🔎 recherche | Recherche Crossref + OpenAlex + PubMed, filtre années, résultats normalisés → CSV/JSON |
| 2 | `enrich_doi` | 🔎 recherche | DOI → ébauche de ligne 42 champs (Crossref + OpenAlex), ajout optionnel à la base |
| 3 | `citation_metrics` | 🗃️ données | Met à jour citations_openalex / open_access / date_releve pour toute la base |
| 4 | `deduplicate` | 🗃️ données | DOI exact + titres similaires (ratio ≥ 0.93) sur résultats de recherche ou base |
| 5 | `validate_entries` | 🛡️ qualité | Réutilise `scripts/validate_entry.py` : 28 champs obligatoires, DOI, triangulation ≥3, dates ISO |
| 6 | `trust_scoring` | 🛡️ qualité | Audit + re-calcul heuristique M+R+O+C+T-P avec justification et détection d'incohérences |
| 7 | `bias_assessment` | 🛡️ qualité | AMSTAR2-lite (revues/métas) et RoB2-lite (empiriques) : dépistage sur métadonnées |
| 8 | `prisma_flow` | 📝 synthèse | Compteurs PRISMA 2020 persistants (`output/prisma_state.json`) + diagramme Mermaid |
| 9 | `synthesize` | 📝 synthèse | Groupement par domaine, stats, gaps agrégés → questions de recherche émergentes |
| 10 | `visualize` | 📝 synthèse | Page HTML autonome (SVG inline, zéro dépendance réseau) |
| 11 | `monitor_watch` | 🔔 veille | Nouveautés OpenAlex depuis N jours sur les domaines du projet |

Chaque compétence se déclare au registre via le décorateur `@skill(...)` avec : description, catégorie, **déclencheurs** regex, exemples, paramètres documentés. Le registre alimente le planificateur, la CLI, l'API et l'interface web.

## 🖥️ Utilisation

### CLI

```bash
# avec le venv du projet
source .venv/bin/activate        # ou .venv\Scripts\activate sous Windows

python -m agent skills           # catalogue des compétences
python -m agent status           # cerveau LLM disponible ?
python -m agent run "recherche systématique des méta-analyses attention 2024-2026"
python -m agent run "valider la base et auditer le trust factor"
python -m agent run "veille scientifique sur la métacognition depuis 30 jours"
python -m agent run "enrichir le DOI 10.1037/bul0000439"
python -m agent run "…" --dry-run   # plan sans exécuter
python -m agent runs            # historique
```

### Python

```python
from agent import Agent
trace = Agent(use_llm=False).run("valider la base et évaluer le risque de biais")
print(trace["statut"], [s["skill"] for s in trace["steps"]])
```

### Interface web

```bash
uvicorn app.main:app --reload    # puis ouvrir http://localhost:8000/agent
```

La page **/agent** (lien « ♅ Uranus » dans l'en-tête du Cognitorium) permet de : saisir une tâche (exemples cliquables), suivre le plan exécuté étape par étape (statut, durée, détails), ouvrir les artefacts (rapports, visualisations), parcourir l'historique des runs et le catalogue des compétences.

### API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/agent/skills` | GET | Catalogue des compétences |
| `/api/agent/status` | GET | Disponibilité du cerveau LLM |
| `/api/agent/run` | POST | `{task, max_results, use_llm}` → trace complète |
| `/api/agent/runs` | GET | Historique (30 derniers) |
| `/api/agent/runs/{id}` | GET | Trace détaillée d'un run |
| `/api/agent/artifact?path=…` | GET | Contenu d'un artefact (chemins contrôlés sous `output/`) |

## ⚙️ Configuration

| Variable | Effet |
|----------|-------|
| `AGENT_OFFLINE=1` | Force le mode hors-ligne (fixtures de démonstration, jamais de requête réseau) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Active le cerveau LLM optionnel |
| `AGENT_USE_LLM=0` | Désactive le LLM même si une clé est présente |
| `AGENT_LLM_MODEL` | Modèle LLM (défaut : `claude-sonnet-4-20250514` ou `gpt-4o-mini`) |
| `AGENT_CROSSREF_MAILTO` | Email pour le politeness pool Crossref/OpenAlex |

## 🛡️ Garanties scientifiques

1. **Déterminisme par défaut** — sans clé API, l'agent est 100 % reproductible (mêmes règles, mêmes requêtes).
2. **Traçabilité intégrale** — chaque run produit `trace.json` (plan, params, durées, résultats, mode) + `report.md`.
3. **Mode dégradé explicite** — si le réseau échoue, les compétences basculent sur des *fixtures de démonstration* et le marquent `degraded` (badge « ⚠️ MODE DÉGRADÉ » dans les rapports et l'UI). Les données de fixtures ne sont **jamais présentées comme réelles*.
4. **Dépistage ≠ jugement** — les scores heuristiques (trust, RoB2-lite, AMSTAR2-lite) sont des *aides au tri* ; une évaluation complète exige RoB2/ROBINS-I/AMSTAR2 à deux évaluateurs + Kappa.
5. **La base reste sous contrôle humain** — `enrich_doi` n'ajoute que des ébauches marquées `à_compléter`, à valider ensuite via `validate_entries`.

## 🧪 Tests

```bash
python -m pytest tests/ -v     # 23 tests, 100 % hors-ligne
```

## 📁 Structure

```
agent/
├── __init__.py            # Agent, registre, import des skills
├── __main__.py            # python -m agent
├── cli.py                 # CLI (run, skills, runs, status)
├── core/
│   ├── registry.py        # @skill, SkillResult, registre global
│   ├── context.py         # AgentContext : chemins, état, HTTP robuste + fixtures
│   ├── planner.py         # planificateur à règles
│   ├── llm.py             # cerveau LLM optionnel (repli règles)
│   └── agent.py           # orchestrateur + rapports
├── skills/                # 11 compétences (1 fichier = 1 compétence)
└── fixtures/              # payloads de démo hors-ligne (API réelles simulées)
```

Ajouter une compétence = créer `agent/skills/ma_competence.py` avec le décorateur `@skill(...)` et l'importer dans `agent/skills/__init__.py` — elle devient immédiatement disponible en CLI, API, web et planification.
