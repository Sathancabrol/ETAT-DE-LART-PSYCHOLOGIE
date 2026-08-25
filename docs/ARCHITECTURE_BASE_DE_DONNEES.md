# 🗄️ Architecture de Base de Données pour le Cognitorium et le Graphe de Connaissances

> **Objectif :** Spécification technique et schémas de base de données relationnelle (PostgreSQL / SQLite) et NoSQL / Graph (Neo4j / JSON) pour alimenter l'application web de visualisation, d'exploration et de partage de l'état de l'art en psychologie et des briques du Cognitorium.

---

## 1. Vue d'ensemble de l'architecture des données

L'application web et le système de partage nécessitent un stockage capable de gérer à la fois :
1. **Les entités bibliographiques structurées** (modèle 42 champs validé par notre script).
2. **La taxonomie et l'arborescence taxonomique** (les 5 piliers de la psychologie, les sous-domaines et processus cognitifs).
3. **Le graphe de connaissances sémantique et épistémologique** (relations orientées : *operationalization, converging, synthesis, falsification, revision, belongs*).
4. **Les traces métacognitives et les profils utilisateurs** (pour le module d'auto-régulation et l'IA du Cognitorium).

---

## 2. Schéma Relationnel (PostgreSQL / SQLite)

Ce schéma normalisé s'appuie directement sur notre template de 42 champs et l'arborescence taxonomique.

### 2.1. Table `domains` (Taxonomie)
Stocke l'arborescence hiérarchique des piliers, domaines et sous-domaines.
```sql
CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    parent_id INT REFERENCES domains(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,       -- ex: 'cog_attention', 'bio_neuro'
    name VARCHAR(150) NOT NULL,             -- ex: 'Attention Spatiale'
    level INT NOT NULL,                     -- 1: Pilier, 2: Domaine, 3: Sous-domaine, 4: Processus
    description TEXT,
    cognitorium_implication TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2. Table `references` (La base de 42 champs)
Stocke chaque article, méta-analyse, revue ou théorie avec son score *Trust Factor*.
```sql
CREATE TABLE references (
    id VARCHAR(100) PRIMARY KEY,            -- ex: 'lee2026_attention_control'
    grand_domaine VARCHAR(100) NOT NULL,
    domaine VARCHAR(100) NOT NULL,
    sous_domaine VARCHAR(100) NOT NULL,
    theme VARCHAR(255) NOT NULL,
    question_scientifique TEXT NOT NULL,
    reference_courte VARCHAR(150) NOT NULL,
    reference_complete TEXT NOT NULL,
    doi VARCHAR(100) UNIQUE NOT NULL,
    annee INT NOT NULL CHECK (annee BETWEEN 1900 AND 2030),
    type_publication VARCHAR(50) NOT NULL,  -- revue_systematique, article_empirique, etc.
    journal VARCHAR(150) NOT NULL,
    url TEXT NOT NULL,
    niveau_preuve VARCHAR(50) NOT NULL,     -- tres_eleve, eleve, modere, etc.
    sources_triangulation TEXT NOT NULL,    -- ex: 'Semantic Scholar + OpenAlex + Crossref'
    
    -- Métriques de citations
    citations_google_scholar INT DEFAULT 0,
    citations_crossref INT DEFAULT 0,
    citations_openalex INT DEFAULT 0,
    citations_semantic_scholar INT DEFAULT 0,
    citations_web_of_science INT DEFAULT 0,
    date_releve_citations DATE,
    altmetric_score FLOAT DEFAULT 0.0,
    
    -- Statut Open Science
    peer_reviewed BOOLEAN DEFAULT TRUE,
    open_access BOOLEAN DEFAULT FALSE,
    data_open BOOLEAN DEFAULT FALSE,
    code_open BOOLEAN DEFAULT FALSE,
    preregistration BOOLEAN DEFAULT FALSE,
    
    -- Échantillon et Design
    sample_size INT,
    sample_type VARCHAR(150),
    study_design TEXT,
    
    -- Résultats et Gaps
    consensus_actuel TEXT NOT NULL,
    gap_actuel TEXT NOT NULL,
    last_gap TEXT,
    
    -- Trust Factor (0-100)
    trust_factor INT NOT NULL CHECK (trust_factor BETWEEN 0 AND 100),
    trust_niveau VARCHAR(50) NOT NULL,      -- faible, modere, eleve, tres_eleve
    trust_justification TEXT NOT NULL,
    
    -- Méta
    tags TEXT NOT NULL,                     -- séparés par des virgules
    date_ajout DATE NOT NULL,
    date_mise_a_jour DATE NOT NULL,
    ajoute_par VARCHAR(100) NOT NULL,
    notes_internes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3. Table `reference_relations` (Le Graphe Méthodologique)
Stocke les liens typés entre références (opérationnalisation, convergence, synthèse, falsification, révision).
```sql
CREATE TABLE reference_relations (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100) REFERENCES references(id) ON DELETE CASCADE,
    target_id VARCHAR(100) REFERENCES references(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,     -- 'operationalization', 'converging', 'synthesis', 'falsification', 'revision', 'belongs'
    label TEXT,                             -- Description textuelle du lien
    strength FLOAT DEFAULT 0.5,             -- Force du lien (0.0 à 1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_relation UNIQUE (source_id, target_id, relation_type)
);
```

### 2.4. Tables applicatives pour le Cognitorium (Métacognition & SRL)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE metacognitive_traces (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    phase VARCHAR(50) NOT NULL,             -- 'planification', 'monitoring', 'controle', 'evaluation'
    prompt_text TEXT,
    user_response TEXT,
    confidence_rating INT CHECK (confidence_rating BETWEEN 0 AND 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Schéma NoSQL / Graph (JSON / Neo4j)

Pour alimenter directement les visualisations D3.js (`d3_interactive.html` et `taxonomy_graph.html`), la base de données peut exporter ou stocker directement un format JSON hiérarchique et orienté graphe.

### Exemple de structure JSON pour le Graphe de Connaissances :
```json
{
  "nodes": [
    {
      "id": "lee2026_attention_control",
      "label": "Lee & Engle 2026",
      "type": "reference",
      "method": "revue",
      "domain": "d_memoire",
      "size": 14,
      "year": 2026,
      "preuve": "tres_eleve",
      "color": "#facc15",
      "thesis": "AC explique 75.6% variance multitâche, r WMC-gF 0.63→0.40",
      "mechanisms": "maintien but, suppression interférence, désengagement",
      "validite": "Construit forte",
      "trust_factor": 88
    }
  ],
  "links": [
    {
      "source": "tuncok2025_prf",
      "target": "lee2026_attention_control",
      "type": "operationalization",
      "label": "AC → baseline shift opérationnalisation"
    }
  ]
}
```

---

## 4. API & Stack Technique Recommandée pour l'App

Pour concrétiser l'application de visualisation et de partage :
* **Backend :** Python (FastAPI) ou Node.js (Express / NestJS) pour exposer les données CSV/PostgreSQL sous forme d'API REST / GraphQL.
* **Base de Données :** PostgreSQL (robuste, requêtes relationnelles et JSONB) ou SQLite (pour un MVP ultra-rapide sans serveur de base de données lourd, stocké directement dans le repo).
* **Frontend :** Next.js (React) ou Vue.js avec **D3.js** (pour réutiliser et enrichir nos graphes interactifs existants) + Tailwind CSS.
* **Hébergement :** Vercel / Netlify (Frontend) + Render / Supabase / Railway (Backend & PostgreSQL).

---
*Spécification de base de données générée pour le projet ETAT-DE-LART-PSYCHOLOGIE / Cognitorium.*
