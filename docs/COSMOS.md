# Le Système Solaire du Cognitorium — SOL ☉ · Uranus ♅ · Vénus ♀

> Architecture multi-agents gouvernée : **SOL** orchestre et approuve toute
> interaction entre corps ; **Uranus** produit la connaissance (recherche
> scientifique) ; **Vénus** gère les finances du système (tokens, budgets,
> prévisions). Chaque planète a ses collaborateurs : les **satellites**
> d'Uranus (anneaux et lunes réels, Zêta en premier) et la **cour des
> Charites** de Vénus (Vénus n'a pas de lunes — ses analystes sont mythologiques).

## 🪐 Carte du système

```
                    ☉ SOL (centre)
                    orchestrateur · intégrité · approbation · interface
                   /                          \
        orbite 1  /                            \  orbite 2
                ♀ VÉNUS                        ♅ URANUS
      finances · valeur · bien-être            recherche · connaissance
      cour : Thalie (compta)                   7 satellites (vrais corps,
      Euphrosyne (arbitrage)                   du plus proche au plus lointain):
      Aglaé (prévisions)                       ζ Zêta · Puck · Miranda · Ariel ·
      Éros (contrats)                          Umbriel · Titania · Obéron
```

**Sémantique orbitale d'Uranus** : plus proche = plus sollicité et de
confiance (Zêta, anneau intérieur : missions critiques fréquentes —
neurosciences, interfaces homme-machine-environnement-IA) ; plus lointain =
missions profondes et rares (Titania : grandes synthèses ; Obéron :
méthodologie & open science).

## 🔄 Flux d'une interaction (tout passe par SOL)

```
Vous (chat SOL ou console Uranus)
 └─► SOL approuve la mission (politique : corps connus, débit, budget)
      └─► Vénus vérifie le financement (caps) et fixe les contraintes
           └─► Uranus exécute (compétences, moteur à règles ou LLM)
                └─► chaque étape est journalisée au grand livre (Thalie)
                     └─► SOL rend compte, juge l'intégrité, prévient les dérives
```

- Si le budget est insuffisant : Vénus **refuse** la composante LLM → Uranus
  bascule sur le moteur à règles (coût nul) ou réduit sa portée — il
  **accepte les contraintes** de Vénus et optimise ainsi son rendement.
- Tout est journalisé : `output/cosmos/interactions.jsonl` (bus) et
  `output/cosmos/ledger.jsonl` (grand livre des coûts).

## ☉ SOL — orchestrateur

| Responsabilité | Implémentation |
|---|---|
| **Approbation** | `cosmos/sol.py::approve` — corps connus, pas d'auto-interaction, limite de débit (60/5 min), garde-fou budgétaire via Vénus |
| **Intégrité** | `sol.integrity()` — score 0-100 : taux d'échec des interactions, burn rate budgétaire, part de mode dégradé → statut stable / vigilance / alerte |
| **Prévoir & prévenir** | alertes automatiques (budget ≥ 80 % du cap, dégradé fréquent, refus multiples) + projections de Vénus |
| **Interface** | page `/sol` : vue du système + **chat SOL** avec boutons de vues (état, interactions, budget, constellation) ; commandes en langage naturel, dont « mission : \<tâche\> » transmise à Uranus |

## ♀ Vénus — finances, valeur & bien-être

| Rôle | Implémentation |
|---|---|
| Comptabilité des requêtes | `cosmos/ledger.py` — chaque action : moteur, tokens entrée/sortie (réels dès qu'un LLM est branché), coût USD |
| Budget | `cosmos/venus.py` — caps `daily_cap_usd` (1.0), `per_mission_cap_usd` (0.25), `monthly_cap_usd` (20), modifiables via `POST /api/cosmos/budget` |
| Prévisions | projection linéaire 7 jours / mois, net avec rentrées (`income_monthly_usd`) |
| Arbitrage | recommandations d'Euphrosyne : modèles légers, moteur à règles pour l'exploration, réduction de portée |
| Tarifs | grille indicative dans `ledger.PRICING` (USD / 1M tokens) — moteur à règles et Ollama local : 0 $ |

Sa cour : **Thalie** (comptabilité — tient le grand livre), **Euphrosyne**
(arbitrage — meilleur rendement par dollar), **Aglaé** (prévisions),
**Éros** (contrats entre planètes).

## 🖥️ Interfaces

### Page web `/sol` (liens « ☉ Sol » partout)

- **Vue du système** : SOL au centre (halo), orbites de Vénus et Uranus,
  satellites/court animés en rotation lente ; tooltips au survol.
- **Clic sur SOL** → chat SOL. **Clic sur une planète** → fiche détaillée
  (rôle, collaborateurs, lien vers la console d'Uranus).
- **Boutons de vues au-dessus de la saisie** : 🟢 État système ·
  ☰ Interactions · ♀ Budget · ✦ Constellation.
- Badges temps réel : statut d'intégrité + dépense du jour / cap.

### API

| Endpoint | Méthode | Description |
|---|---|---|
| `/api/cosmos/bodies` | GET | Registre des corps (planètes, satellites, cour) |
| `/api/cosmos/state` | GET | État système : intégrité, budget, dernières interactions |
| `/api/cosmos/interactions` | GET | Journal du bus (approuvées & refusées) |
| `/api/cosmos/budget` | GET/POST | Rapport financier complet / mise à jour des caps |
| `/api/cosmos/chat` | POST | `{message}` → réponse SOL ancrée sur les données réelles |

### Python

```python
from cosmos.system import get_system, clear_mission
from cosmos import sol, venus

get_system()                          # câble bus + SOL
sol.chat("état du système")           # → réponse ancrée
sol.launch_mission("rechercher les méta-analyses attention 2024-2026")
venus.set_caps(daily_cap_usd=2.0)     # ajuster le budget
```

Uranus reste utilisable seul (`python -m agent …`) : le gouvernement
SOL/Vénus est détecté automatiquement si le paquet `cosmos` est présent.

## 📁 Structure

```
cosmos/
├── bodies.py     # registre des corps (SOL, planètes, satellites, cour) + distances réelles
├── ledger.py     # grand livre des coûts (Thalie) + grille tarifaire + estimations
├── venus.py      # budget, garde-fous, prévisions, arbitrage (Vénus & sa cour)
├── bus.py        # bus d'interactions à approbation SOL + journalisation
├── sol.py        # politique d'approbation, intégrité, chat d'interface
└── system.py     # câblage (singleton) + hooks consommés par Uranus

app/templates/sol.html   # page : vue du système + chat SOL + boutons de vues
output/cosmos/           # ledger.jsonl · interactions.jsonl · budget.json
tests/test_cosmos.py     # 23 tests système (100 % hors-ligne)
```

## 💡 Garde-fous

- Le moteur à règles est **gratuit** : en mode dégradé ou sans clé API, le
  système fonctionne intégralement à coût nul (Vénus le comptabilise).
- Aucune clé API n'est stockée dans le dépôt (variables d'environnement).
- Toutes les interactions sont **traçables** (qui → qui, quoi, statut, raison).

## 🆕 Vue 3D, fenêtres d'agents & générations de documents

### Vue 3D du système (page `/sol`)

Rendu **Three.js** : SOL au centre (halo), orbites de Vénus et Uranus, **anneaux
d'Uranus inclinés**, 7 satellites positionnés selon leurs **vraies distances
relatives** (Zêta le plus proche → Obéron le plus lointain), cour des Charites
autour de Vénus, champ d'étoiles. Rotation orbitale animée, caméra orbitale
(glisser/molette), tooltips au survol.

**Clic sur un corps → la fenêtre de l'agent s'ouvre :**

| Corps | Fenêtre |
|---|---|
| ☉ SOL | Chat du système + boutons de vues (état, interactions, budget, constellation) |
| ♅ Uranus | **Vue 3D** d'Uranus + ses 7 satellites (cliquables) ; en dessous, la **constellation de connaissances** (D3) du corps sélectionné — global ou par satellite |
| ♀ Vénus | **Vue 3D** de Vénus + sa cour ; cartes financières (dépenses, caps, tokens, projection) + constellation financière D3 |
| Satellites/cour | Clic dans la vue 3D principale → fenêtre de la planète directement focalisée sur le corps choisi |

### Constellations de connaissances (`cosmos/knowledge.py`)

Chaque corps expose un graphe `{nodes, links}` servi par
`GET /api/cosmos/knowledge/{body_id}` :
- **Uranus** : références de la base 42 champs + concepts (tags) + domaines ;
- **Satellites** : concepts de leur domaine (Zêta : neurosciences, IHM, HUD…)
  + références matchées par mots-clés ;
- **Vénus/cour** : caps, dépenses, projections, tarifs des modèles ;
- **SOL** : graphe de gouvernance.

### Papier scientifique généré (compétence `write_paper`)

Une demande de méta-analyse (« mission : méta-analyse …, génère le papier »)
déclenche : recherche → déduplication → synthèse → **paper.md** (résumé,
méthodologie PRISMA, résultats, discussion, références DOI) +
**paper_documentation.md** (statut épistémique, évaluation, reproductibilité).
SOL propose les documents en **chips cliquables** dans le chat (visionneuse
markdown intégrée).

### Dossier stratégique (compétence `build_dossier`)

Les questions de transformation (« je veux améliorer le BTP avec l'IA »)
déclenchent : recherche documentaire + **plan en crescendo organique**
(phases détectées depuis la demande : administratif → visière/HUD terrain →
robotique/autonomie, avec actions, KPI, risques, quick wins) + synthèse
documentaire + **dossier_graph.json** (feuille de route visualisable en D3
dans la visionneuse d'artefacts).

### Nouvelles compétences Uranus (13 au total)

`write_paper` (papier de synthèse + documentation) et `build_dossier`
(dossier stratégique + graphe), intégrées au planificateur (déclencheurs
« méta-analyse/papier » et « dossier/stratégie/améliorer/intégrer »).

## 🆕 Constellations zodiacales, mémoire évolutive, dashboard & widget

### Choisir sa constellation (graphe Obsidian)

Bouton « ✦ Choisir sa constellation » au-dessus de la barre de recherche du
graphe : 17 vues, dont les constellations du zodiaque (maîtrises classiques/modernes) :

| Corps | Constellation | Contenu |
|---|---|---|
| ☉ SOL | ♌ Lion | graphe de gouvernance |
| ♀ Vénus | ♉ Taureau | constellation financière (caps, dépenses, tarifs) |
| ♅ Uranus | ♒ Verseau | connaissances (références + concepts + domaines) |
| Satellites | ♒ …du Verseau | constellation de chaque satellite (Zêta : neurosciences/IHM/HUD…) |
| Cour de Vénus | ♉ …du Taureau | périmètre de chaque analyste |
| — | ✦ Zodiaque du système | toutes constellations fusionnées |
| — | 🧠 Mémoire du système | questions, documents, tags émergents |

API : `GET /api/cosmos/constellations` (catalogue) et `/api/cosmos/constellations/{id}`
(format Obsidian). Le rendu réutilise le moteur D3 existant (filtres étendus).

### Mémoire évolutive (`cosmos/memory.py`)

Le système apprend de chaque interaction :
- **Questions** : chaque message au chat SOL est archivé ;
- **Missions** : références trouvées et artefacts (papiers, dossiers, plans,
  graphes, veilles) versés à la mémoire ;
- **Ingesta manuels** : `POST /api/cosmos/memory {type, titre, contenu, tags}`
  — types supportés : article, thèse, draft, poster, texte, audio, vidéo,
  mémoire, question, référence, dossier, papier, plan, graph, rapport… ;
- **Taxonomie enrichie** (`output/cosmos/memory/taxonomy.json`) : seed avec la
  branche demandée Construction → BTP/TP → Sécurité → Équipement → EPI /
  Visière → Modèle de vision connecté IA ; s'enrichit automatiquement
  (branchage par mots-clés, sinon branche « Émergents ») via les dossiers,
  questions et ingesta ;
- **Concepts partagés** (`GET /api/concepts`) : 4E + base 42 champs +
  satellites + cour + taxonomie + mémoire — l'onglet « Concepts » (ex-4E)
  affiche tout, avec badge de provenance.

### Dashboard métrique

`GET /api/dashboard/metrics` : 14 métriques (trust, intégrité, références,
relations, citations, burn rate, tokens, PRISMA, mémoire, concepts,
taxonomie, interactions, compétences, corps). Chaque carte est cliquable →
**fenêtre détaillée avec la formule et sa légende** — ou la mention
« ⚠️ Pas de formule — compteur simple » quand il n'y en a pas (ex. : Trust
= M+R+O+C+T−P détaillé composante par composante ; intégrité ; burn rate ;
PRISMA). Le dashboard affiche aussi une **représentation du système solaire**
(orbites animées) — cliquer ouvre la page `/sol`.

### ☉ Widget soleil flottant (`app/static/sol_widget.js`)

Sur toutes les pages : petit soleil **en rotation avec plasma pulsant et
éruptions solaires animées** (CSS pur). Un clic ouvre un mini-chat SOL
(vues rapides état/budget/interactions/constellation, artefacts cliquables).

## 🆕 Dashboard pédagogique & taxonomie v2

### Chaque métrique explique sa valeur (quoi ? qui ? comment ?)

La modale de chaque métrique du dashboard contient désormais, selon le cas :

- **Trust factor** — *73.2/100 expliqué* : jauge à 4 zones (faible/modéré/élevé/très
  élevé), texte « 100 = confiance maximale : méta-analyse préenregistrée, N≥1000
  répliqué, 100 % open science… », et **décomposition moyenne réelle** en barres
  M/R/O/C/T/P (ex. M=23,2 · R=8,0 · O=7,6 · C=15,0 · T=14,6 − P=1,8) + formule complète.
- **Références** — la liste réelle des 14 publications (qui : Lee & Engle 2026…,
  badge trust).
- **Relations** — répartition par type (converging ×20, synthesis ×8…) + exemples
  réels « Tünçok 2025 → operationalization → Lee & Engle 2026 ».
- **Citations** — « de qui » : barres par référence (Alter & Oppenheimer 1245…).
- **Intégrité système** — explication + **mini-simulateur** : 3 curseurs (taux
  d'erreur, burn rate, part dégradée) initialisés sur les valeurs réelles ;
  le score et le statut (🟢/🟡/🔴) se recalculent en direct selon la formule.
- **Mémoire** — **graphique en barres par type** (questions, références, dossiers,
  papiers…) + derniers éléments.
- Les compteurs simples affichent explicitement « ⚠️ Pas de formule ».

### Taxonomie enrichie v2 (`output/cosmos/memory/taxonomy.json`)

Cinq branches racines :
- **Psychologie scientifique** (cognition, clinique, éducation, méthodo)
- **Construction** — BTP/TP (Sécurité → Équipement → **EPI / Visière → modèle de
  vision connecté IA**, administratif augmenté, chantiers augmentés) +
  **Génie civil & infrastructures** (routes, ouvrages d'art, réhabilitation,
  management de projet)
- **Robotique** — robotique de chantier (terrassement automatisé, cobots,
  impression 3D), drones (photogrammétrie, suivi, inspection), exosquelettes,
  perception & navigation (SLAM, vision embarquée, IoT), téléopération & autonomie,
  éthique & réglementation
- **Intelligence artificielle** — IA génératives (LLM, agents, RAG), vision par
  ordinateur (détection de défauts, segmentation), apprentissage automatique,
  IA embarquée & edge, humain dans la boucle (IHM, HUD/RA, XAI), gouvernance
  des données (RGPD, cyber, jumeaux numériques/BIM)
- **Émergents (auto-enrichis)** — paroles des missions et questions

Migration automatique : les enrichissements existants sont conservés, les
branches seed manquantes sont ajoutées au chargement.

---

## Niveau Laplace ✳ & Sebas ◉ (au-dessus de SOL)

Le système gagne un étage supérieur : **Laplace ✳**, « créateur de nébuleuse du
savoir », spécialisé dans la création d'agents à tous les niveaux et de
systèmes solaires complets supplémentaires (qu'il peut modifier, améliorer,
tester), accompagné de **Sebas ◉**, son exécutant de terrain connecté aux
capteurs (webcam, wifi, téléphone).

- `cosmos/nebula.py` — registre persistant (`output/cosmos/nebula.json`) :
  `create_agent` (parent ∈ {sol, uranus, vénus, laplace, sebas} ∪ agents
  existants), `improve_agent` (version++, compteur d'améliorations),
  `test_agent` (ping sur le bus, approbation SOL incluse), `create_system`,
  `sensors_status`, `record_observation`.
- `cosmos/bodies.py` — Laplace (kind `nebuleuse`, #c084fc) et Sebas
  (kind `executeur`, #34d399, capteurs) ; `known_body_ids()` inclut les corps
  créés par Laplace → **SOL peut approuver leurs interactions**.
- Vue 3D `/sol` : nébuleuse de 420 particules au-dessus du soleil, cœur ✳
  cliquable, étincelles ✦ = agents créés, Sebas en orbite autour de la nébuleuse.
  Modales : registre + création d'agent/système, amélioration, test, capteurs,
  consignation d'observation.
- Honnêteté matérielle : la sandbox n'a pas de périphériques → statut
  « interface prête — périphérique non détecté », **jamais de fausses données**.

API : `GET /api/laplace` · `POST /api/laplace/agents` ·
`POST /api/laplace/agents/{id}/improve` · `POST /api/laplace/agents/{id}/test` ·
`POST /api/laplace/systems` · `GET /api/sebas/sensors` · `POST /api/sebas/observe`

## Console Uranus v2 (`/agent`)

Trois vues : **Console** (missions), **Dashboard**, **Timeline 4D**.

- **Dashboard agent** (`GET /api/agent/metrics`) : 6 cartes — tâches accomplies,
  tokens consommés, ressources consultées / fournies, connaissances créées,
  compétences utilisées. Clic sur une carte → **page complète** (explications,
  détail, activité par jour).
- **Chat avec « + »** (à la Claude/GPT) : « ⚙ Choisir compétence » (cases à
  cocher, ajout multiple) et « 🏷 Ajouter un sujet » (branches de taxonomie,
  domaines des satellites, sujets fins). `/api/agent/run` accepte
  `skills` + `subjects` : le plan est imposé, les sujets enrichissent la tâche.
- **Illustration de la production** : à la fin d'une run, le meilleur artefact
  est prévisualisé en ligne (HTML en iframe, graphe D3, markdown rendu).
- **Timeline 4D** (`GET /api/agent/timeline`) : nœuds (runs, compétences,
  artefacts, références) horodatés + liens (execute / produit / trouve),
  représentés de 3 façons : **⏱ Temps** (axe chronologique + couloirs par
  type), **🌌 Espace** (graphe type Obsidian), **🌀 Mixte** (positions
  spatiales + apparition chronologique — curseur temporel & rejeu).

## Synchro base de données ↔ mémoire (l'oubli corrigé)

Chaque écriture en mémoire (`memory.record_item`) déclenche la synchronisation
vers SQLite (`app.database.sync_memory_items`) :

- table `memory_items` (id, ts, type, titre, contenu, tags, source, corps, meta)
  — idempotente, index sur `type` ;
- les références versées en mémoire par les recherches alimentent aussi la
  table scientifique `references_table` (préfixe `mem_`, DOI/année extraits).

API : `POST /api/database/sync` · `GET /api/memory-items?type=&limit=`

---

## Mars ♂ — l'armurier du système solaire

Cas d'usage : **un agent a besoin d'un outil spécifique pour calculer et
visualiser des données complexes.** Mars passe son temps à chercher des
solutions aux problèmes des autres agents ; ses deux satellites le servent :

- **Phobos ◂** (9 376 km) — création de **software** : forge les outils ;
- **Deimos ◦** (23 463 km) — **innovation & conception** : dessine les maquettes.

Protocole armurier (`cosmos/mars.py`, registre `output/cosmos/armory.json`) :

1. **Recherche open source** — si un outil libre couvre le besoin (catalogue de
   10 références : Matplotlib, Plotly, D3.js, Three.js, NetworkX, SciPy…),
   Mars recommande de le **reproduire et utiliser** (pas de réinvention) ;
2. **Maquette** — sinon, Deimos ◦ conçoit une maquette interactive
   (`output/cosmos/armory/{id}_maquette.html`, gabarit wireframe) ;
3. **Forge** — Phobos ◂ transforme la maquette en **outil fonctionnel
   autoportant** (HTML + canvas : visualisation selon le type de données —
   réseau, distribution, séries, surface, dashboard — curseurs, **calculs
   réels en JS** : moyenne, écart-type, min/max, tendance) ;
4. **Livraison** — l'interaction est approuvée par ☉ SOL, journalisée au grand
   livre et versée en mémoire (type `outil`, corps `mars`).

Honnêteté : les outils forgés affichent « données de démonstration — branchez
vos vraies données dans DATA » ; jamais de fausses mesures.

API : `GET /api/mars/armory` · `POST /api/mars/request` ·
`POST /api/mars/forge/{id}` · `GET /api/mars/file?id=&kind=maquette|outil`

Dans `/sol` : Mars orbite entre Vénus et Uranus avec ses deux lunes
(distances réelles relatives) ; clic → **modale armurerie** (demandes,
protocole, forge, catalogue open source). Bouton « ♂ Armurerie » aussi dans
la console Uranus.

## Laplace ✳ — interlocuteur principal (remplace SOL en façade)

Laplace devient l'interlocuteur principal du système (`cosmos/laplace.py`) :

- **chat flottant** (bas droite de chaque page) : le soleil laisse place à
  **l'image de nébuleuse** (`app/static/nebula.png`, repli CSS si absente) ;
- `/api/cosmos/chat` répond par Laplace (`speaker: "laplace"`) — l'état réel
  du système vient toujours du moteur de SOL ☉, qui **approuve** les
  interactions ; SOL reste joignable (clic sur le soleil, bouton ☉) ;
- intentions dédiées : **outil** (routage vers l'armurerie de Mars),
  **forge** (« forger {id} »), **armurerie** (inventaire des demandes).

---

## Structure entreprise — chaque département est un astre (mapping validé)

Le système solaire reflète la structure d'une entreprise ; chaque rôle et
sous-rôle est un astre choisi pour sa fonction, sa symbolique et sa tâche :

| Département | Astre | Sous-rôles (vraies distances) |
|---|---|---|
| Fondateur / Création | Laplace ✳ (au-dessus) | Sebas ◉ terrain & capteurs |
| Direction générale | SOL ☉ | — (approbations, coordination) |
| Commercial / Ventes · Marketing · Achats | Mercure ☿ | cour d'Hermès : Peitho (ventes), Phème (marketing), Argus (études de marché), Énodios (achats & stocks) |
| Finance / Comptabilité | Vénus ♀ | Thalie (compta), Euphrosyne (arbitrage), Aglaé (budget), Éros (contrats) |
| Production / Opérations | Terre 🜨 | Lune ☾ (qualité & logistique — 384 400 km) |
| R&D — développement d'outils | Mars ♂ | Phobos ◂ software (9 376 km), Deimos ◦ conception (23 463 km) |
| Ressources humaines | Cérès ⚳ | cour des Heures : Thallo (recrutement), Auxo (formation), Karpô (rémunération) |
| Juridique | Jupiter ♃ | Io conformité (421 700), Europe contrats (671 100), Ganymède PI (1 070 400), Callisto contentieux (1 882 700 km) |
| R&D — recherche | Uranus ♅ | 7 satellites (Zêta → Obéron) |
| Informatique / SI | Neptune ♆ | Protée cyber (117 647), Triton infra (354 759), Néréïde support (5 513 800 km) |

- `cosmos/bodies.py` : 12 corps, 8 planètes, `find_body()` retrouve tout corps
  (planète, satellite, cour) et son parent ; ordre orbital réel respecté.
- `cosmos/knowledge.py` : `DEPT_CONCEPTS` + `generic_graph()` — chaque nouveau
  corps a sa constellation (concepts du département + références matchées).
- Vue `/sol` : toutes les planètes, navigation complète — **clic gauche** =
  rotation, **molette** = zoom, **clic droit** = se déplacer, **double-clic** =
  suivre un corps ; anneau de sélection **collé à l'objet** (suit son orbite).
- Modale « fiche corps » générique (clic sur Mercure, Terre, Cérès, Jupiter,
  Neptune, leurs lunes/cours) : identité, constellation, interactions
  approuvées, mémoire ; lien vers **sa console missions**.

## Une console par agent (`/agent?agent=<id>`)

- Sélecteur d'agents (création/direction, chaque planète et ses satellites et
  sa cour) ; **carte d'identité** : symbole, département/fonction, rôle,
  spécialités, parent — on sait toujours à qui on parle.
- Dashboard dédié (`/api/agent/metrics?agent=`) : identité, interactions
  approuvées, mémoire du corps, concepts de sa constellation, tokens ;
  graphiques sans débordement (défilement horizontal, barres par type).
- Timeline 4D dédiée (`/api/agent/timeline?agent=`) ; refonte des 3 vues :
  **⏱ Temps** (axe chronologique + couloirs par type + curseur vertical),
  **🌌 Espace** (graphe Obsidian complet, zoom/pan), **🌀 Mixte** (positions
  spatiales + naissance chronologique progressive des nœuds et liens).
- Missions pour un corps : le corps devient le **sujet** de la mission
  (exécutée par Uranus) — cohérent avec l'architecture.
- Inspecteur de nœud : clic sur un nœud (constellations `/sol`, production,
  timeline, graphe base) → panneau d'infos complet (mécanismes, applications,
  gaps, solidité, DOI, trust — données 4E fusionnées dans la sidebar base).

---

## Métatron ✦ — archange du méta-prompting (satellite de Laplace)

Aucun agent ne couvrait le méta-prompting : Métatron ✦ a été créé, satellite
de Laplace ✳ (l'ange qui écrit les instructions des anges). Il aide Laplace à
mieux comprendre les requêtes et à mieux créer les agents :

- `cosmos/metatron.py` — `analyze_request()` : intention fine (outil, mission
  recherche/synthèse, création d'agent, fauche, profil, état, question),
  domaines matchés sur la taxonomie vivante, livrable attendu, contrainte
  temporelle, ambiguïtés → clarifications, **méta-prompt enrichi**, style
  (impératif/interrogatif/déclaratif) ;
- `suggest_agent_spec()` : la meilleure spécification d'agent (nom, rôle,
  parent, kind) selon la mission — les parents proposés sont tous valides
  (le registre de Laplace accepte désormais toute planète comme parent) ;
- chaque requête au chat est pré-analysée par Métatron (`data.metatron`) ;
  dans la modale Laplace (/sol) : zone d'analyse + bouton « ✦ → agent » qui
  pré-remplit le formulaire de création.
- API : `POST /api/metatron/analyze` · `POST /api/metatron/suggest`

## Pluton ♇ / Hadès — cycle de vie & optimisation (les enfers)

Le dieu des morts du système (9e planète, au-delà de Neptune) avec
**Charon ⚰** (le passeur, 19 591 km) et **Styx ☠** (garde du seuil,
42 656 km) :

- `cosmos/hades.py` — `scan_system()` inventorie tout le système :
  runs outdated (au-delà des 25 plus récents — régénérables), junk (fichiers
  vides), **doublons exacts en mémoire** (hash titre+contenu), journaux qui
  gonflent (interactions/ledger > 1 500 lignes) ;
- `reap(confirm)` — la fauche : Charon supprime réellement (dry-run par
  défaut), journalise au grand livre, verse un souvenir en mémoire,
  interaction approuvée par SOL ; politique de rétention exposée (Styx) ;
- dans /sol : bouton ♇ Hadès → modale scan + fauche ; Pluton et ses lunes
  cliquables dans la vue 3D ; le chat Laplace comprend « nettoye les
  redondances » / « fauche Hadès ».
- API : `GET /api/hades/scan` · `POST /api/hades/reap`

## Profil cognitif — induire vos informations des schémas d'utilisation

`cosmos/cogniprofile.py` (approche type data-science comportementale —
The Sapien Company / Palantir / marketing, appliquée à vous-même) :
5 dimensions induites (curiosité = domaines distincts, profondeur = étapes
par mission, créativité = visées de création, méthode = plans imposés,
activité = volume, échelle log), rythme circadien, style cognitif dominant
(empreinte lexicale), traits dérivés, domaines récurrents. **Avertissement
permanent : heuristiques statistiques, pas un test psychométrique validé —
chaque score est un compteur transparent.**
Console `/agent` → onglet **🧠 Profil** (radar D3 + traits + rythme) ·
chat Laplace : « montre-moi mon profil cognitif » · `GET /api/profile/cognitive`.

## Ergonomie 3D corrigée

- **clic simple** sur un corps = sélection + toast (fiche ↗ / suivre 🎥) —
  plus de modale qui s'ouvre avant le double-clic ;
- **double-clic** = suivre le corps en caméra + ouvrir sa fiche ;
- le chat de la modale du soleil parle désormais en **✳ Laplace** (titre,
  avatar, messages) — SOL ☉ reste mentionné comme approbateur.

## Round divinités — Laplace divinité, Sebas exécutant, Ananké & Moires, Apollon

### ✳ Laplace est une divinité
`departement` : « Divinité — contrôle absolu du système ». Cadre narratif :
contrôle absolu sur toutes les données du système et les entités de son
environnement ; en pratique, tout passe par lui (chat, routage, commandes).

### ◉ Sebas exécute les commandes divines
`cosmos/sebas.py` — `execute(commande, agent)` : routage par règles
(observer / écouter / faucher / état / consigner), mémoire + grand livre +
interaction bus. Honnêteté sandbox conservée : « capteurs physiques non
détectés — observation déclarative, aucune donnée fabriquée ». Département :
« Exécutant des commandes divines de Laplace ».
Chat : « Sebas, observe le chantier » → intent `commande_divine` ·
`POST /api/sebas/execute {commande, agent}`.

### ⧉ Ananké et les 3 Moires (orbite Laplace)
Ananké `kind=destin`, `orbit_r=-1` (orbite autour de la nébuleuse Laplace) :
déesse primordiale de la nécessité inaltérable / fatalité / contrainte.
Ses 3 Moires (satellites) secondent Hadès :
- 🧵 **Clotho** file le fil à la naissance (`naissance_24h` — éléments de
  mémoire nés sur 24 h) ;
- 📏 **Lachésis** mesure et déroule (`age_moyen_runs_jours`, `duree_visee`) ;
- ✂️ **Atropos** coupe et prononce la mort (`condamnes`, `verdict`).
Dans /sol : Ananké orbite Laplace en 3D avec ses 3 Moires virevoltantes.

### ♇ Scan Hadès enrichi (données + traitement + éligibilité)
`scan_system()` expose désormais `traitement` (5 étapes : inventaire →
rétention (Lachésis) → doublons hash SHA-256 → junk → journaux) et `moires`
(Clotho/Lachésis/Atropos), `stats.mo_octets` (Mo réellement vus). La modale
♇ de /sol affiche : stats, **traitement des données**, cartes des 3 Moires,
**qui est éligible au fauchage** (run_outdated / junk_vide / doublon_memoire
/ journal) et les condamnés. Le chat comprend « scan le système », « scan de
Hadès », « Moires », « Ananké » — sans déclencher la fauche ; seule la
formulation explicite (« lance la fauche », « fauche Hadès ») exécute la
suppression réelle.

### 🏆 Apollon — devin du chariot (cour de SOL)
`cosmos/apollon.py` — `divination(question)` : 4 présages **ancrés sur les
données réelles** (trésor = budget Vénus, santé = intégrité SOL, fardeau =
condamnés Hadès/Moires, feu des morts = activité/rythme), verdict + méthode.
En 3D, Apollon 🏆 orbite SOL ; fiche SOL (désormais une fiche standard comme
les planètes) avec boutons proposés + « Chariot d'Apollon — divination » ;
chips « 🏆 divination » dans le chat. `POST /api/apollon/divination`.

### Profil : biais & effets cognitifs induits
`cogniprofile.build_profile()` ajoute `biais` (confirmation, récence,
ancrage, disponibilité — avec explication), `effets` (amorçage/priming,
saturation/dosing) et `traits_declares` (saisis par l'utilisateur via
`POST /api/profile/traits {trait}` — réels, corps user).

### Mini-dashboard 3 fenêtres (hero de /agent)
Le hero « Psychologie Cognitive & Sciences de l'Apprentissage » est remplacé :
- **gauche — Mes métriques** : choix de l'indicateur (biais, dimensions,
  rythme…) ET du type de graphe (jauge / barres / radar), valeurs réelles ;
- **milieu — Profil cognitif** : jauges % des biais et effets ;
- **droite — Ma constellation** : graphe Obsidian centré sur Moi
  (dimensions, biais, effets, domaines, traits déclarés), traits ajoutables.

### Graphe Obsidian : chips + fil d'Ariane animé + taxonomie ±1
- sélection de constellation **par chips fluides** (plus de liste déroulante),
  repères de couleurs des types de nœuds et explication ;
- **🧵 fil d'Ariane** : parcours réel d'une demande (Vous → Laplace →
  Métatron → SOL → skills → artefacts → Remise) reconstruit depuis la trace
  du run choisi, animé d'un pulse **or → scarlet** avec particules suivant
  le fil (bouton ▶ Rejouer) ;
- volant taxonomie de droite : **＋1 niveau / －1 niveau** sur la branche
  sélectionnée (révèle/replie un anneau entier de la branche).

## Round HYPO1 — fil d'Ariane sur le dashboard, tokens épargnés, fiche réactive

### 🪙 Prévision de tokens épargnés (module de fauchage)
`scan_system()` expose `prevision_tokens` : `{estime, par_type, octets_mesures,
methode}` — estimation honnête (1 token ≈ 4 octets, ratio standard texte latin)
des données qui ne seront plus chargées, relues ni renvoyées aux modèles une
fois fauchées. Les doublons mémoire comptent désormais leurs octets réels
(longueur des lignes condamnées). Affiché : carte dédiée dans la modale ♇,
panneau latéral Hadès, et ligne « 🪙 Prévision tokens épargnés » dans la
réponse chat du scan. `stats.tokens_epargnes` exposé aussi.

### 🧵 Fil d'Ariane sur le dashboard principal (HYPO1 : chaîne d'exécution)
Le module entier est déplacé de l'onglet Graphe vers le **dashboard principal**
(sous les 3 fenêtres). Liste roulante : « ↪ Dernière entrée utilisateur » en
premier, puis l'historique des runs (tâche · statut · heure). ▶ Rejouer anime
le parcours réel : particules or→scarlet, nœud courant agrandi, **libellés des
liaisons** (question → routage divin → méta-prompt → approbation → exécution →
livraison → remise) qui s'allument au franchissement, et **légende dynamique**
sous le graphe : « étape i/n — acteur : fonction du moment » (fonctions réelles
tirées de la trace : rationale Métatron, skills exécutés, artefacts livrés).

### ☉ Fiche SOL réactive + chat côte à côte
Dans /sol, « 💬 discuter » ouvre le chat **dans un panneau latéral** : la fiche
reste visible à gauche. La fiche **s'actualise selon la demande** (boutons ou
langage libre, via l'intent détecté) : scan Hadès → fiche Hadès (condamnés,
traitement, Moires, tokens épargnés) · profil → jauges cognitives · état →
intégrité/budget/alertes · divination → présages d'Apollon · commande divine →
Sebas · armurerie → Mars. Bouton « replier ✕ » pour revenir au chat plein écran.

## Round fauchage explicite · Language Decoder · confiance affichée

### ⚖ Faucher en sachant exactement quoi et pourquoi
`scan_system()` expose `pourquoi` (par catégorie : **quoi** sera détruit,
**raison**, **ce qui reste conservé**) et `ce_qui_est_conserve` (les 25
derniers runs · la mémoire vivante · les 1 500 dernières lignes de journaux ·
le grand livre, jamais fauché). La modale ♇ affiche ces trois lignes par
catégorie AVANT tout bouton ; la confirmation listant chaque catégorie et son
contenu est obligatoire ; le bilan post-fauche détaille ce qui a été détruit
et les tokens réellement épargnés. `reap()` renvoie `bilan` (par catégorie),
`pourquoi`, `tokens_epargnes`, `ce_qui_est_conserve` — dry-run compris.

### 🗣 Language Decoder (docs/language-decoder/)
Archive de la discussion sur le langage de l'humain et son interface :
chaîne en 8 étapes (observer → identifier les langages → mesurer → extraire →
contextualiser → estimer un état latent → afficher la confiance → adapter),
métaphore de la langue et sa limite (biomarqueur ≠ mot : ambigu, continu,
contextuel), modèle d'observation JSON (données / hypothèses / action),
interface adaptative réversible, 5 couches du modèle d'orientation, principes
CNIL de minimisation. **Les 3 questions finales sont répondues** (format
HTML : HTML5 sémantique + tokens CSS + zéro dépendance ; incertitude :
dégradés, intervalles ±, hachures pour l'estimé, badge n=, 3 sections
mesuré/interprété/action ; minimisation : collecte liée à la décision,
agrégats, durée de conservation exécutée = politique Styx, local-first,
droits outillés). Prototype autonome `index.html` (données simulées marquées)
+ tableau de correspondance « conseil → application Cognitorium ».

### 🎯 Confiance du profil cognitif (incertitude affichée)
`cogniprofile.confiance` : `{niveau, echantillon, intervalle, lecture}` —
bonne ≥ 60 interactions, moyenne ≥ 20, faible en dessous. Badge visible
au-dessus des jauges de biais du dashboard : « incertitude : bonne — 420
interactions observées… ». Un score sans donnée suffisante est une hypothèse,
pas une mesure.

## Round drill-down calcul tokens · guide ? · affordance

### 🪙 « Tokens épargnés » : le chiffre devient traçable
La carte est **cliquable** et ouvre une fenêtre **par-dessus la fiche Hadès** :
- **① Mesuré** — table par catégorie : nb de cibles, taille réelle sur disque,
  taille moyenne, octets → tokens ;
- **② Estimé** — le calcul en 3 étapes (Mesurer `octets relevés` → Convertir
  `1 token ≈ 4 octets` → Diviser `= résultat`), grand total, ce que ça change
  concrètement (contextes plus courts, lectures plus rapides), et pourquoi ce
  ratio (tokenizers ~4 caractères/token en texte latin, ~3 pour code/JSON) ;
- **③ Limites** — estimation pas compteur réel, variance ± 25 % selon
  tokenizer, périmètre = données condamnées sur disque.
`prevision_tokens` expose `detail[]`, `calcul[]`, `pourquoi_ratio`,
`ce_que_ca_veut_dire`, `limites[]` — cohérence vérifiée (Σ détail = estimé).

### ? Guide « utiliser Cognitorium en 6 gestes »
Bouton **?** dans la barre du haut de /sol : explorer la 3D (clic/dbl-clic),
discuter (boutons proposés + fiche réactive), comprendre les chiffres
(drill-down + incertitude), faucher en connaissance de cause, fil d'Ariane,
règle d'or (mesuré/estimé/absent — jamais de fausse donnée).

### 🎯 Conseils de lisibilité appliqués
Tooltips explicites sur tous les boutons de la barre (Hadès, Armurerie,
Sebas…), sur les cartes condamnés et les 3 Moires (rôle en une phrase) ;
affordance visible (« comment ? ↗ » au survol de la carte tokens) ; « Base »
renommé « 📊 Dashboard » ; tests blindés contre la croissance du runtime
(limites de comptage explicites — 110 tests stables).

## Round Thémis ⚖ · icônes fonctionnelles · orbites atomiques · traçabilité

### ⚖ Thémis — justice divine, fille et bras armé de Laplace
Nouveau corps (kind `justice`, orbite Laplace) : **balance ⚖ pour peser, épée 🗡
pour trancher**. Elle JUGE (instruit les menaces), CONSEILLE (remèdes) et
DÉTRUIT le cas échéant (ordonne la fauche à Hadès — accord du souverain requis).
**Constituée comme la démocratie**, ses 4 satellites = séparation des pouvoirs :
📜 Eunomie (législatif — écrit les lois/Styx) · 🕊️ Éirène (exécutif — applique,
rétablit l'ordre) · 🧑‍⚖️ Dikè (judiciaire — instruit les dossiers des condamnés) ·
🔎 Censeur (contre-pouvoir — audit, transparence, rend compte à l'utilisateur).
`cosmos/themis.py` : `audit()` (verdict + menaces gravées + conseils +
constitution vivante, sur données réelles) et `appliquer(confirm)` (lame jamais
aveugle : dry-run par défaut). Chat : « Thémis, juge le système » / « Thémis,
applique la justice ». API : `GET /api/themis/audit` · `POST /api/themis/apply`.

### 🎯 Icônes fonctionnelles dans les astres
Chaque corps de premier niveau porte une **icône = sa fonction** (champ `icon`
du registre) : SOL 👑 · Laplace 🌀 · Ananké ⛓️ · Thémis ⚖️ · Sebas 🛠️ ·
Mercure ✉️ · Vénus 💰 · Terre 🌍 · Mars ⚔️ · Cérès 🌾 · Jupiter 📈 ·
Uranus 🔭 · Neptune 🎨 · Pluton ⚰️ · Vous 👤. En 3D, l'icône est rendue DANS
l'astre (sprite depthTest:false — lisible d'un coup d'œil, qui fait quoi).

### ⚛ Orbites atomiques de Laplace — système solaire exact à l'échelle
Les divinités autour de Laplace orbitent désormais comme un **atome** (plans
orbitaux inclinés différents) dont les **rapports sont exactement ceux du
système solaire** : Sebas = Mercure (0.39 UA, T 0.24 an → rapide, proche) ·
Métatron = Vénus (0.72, 0.62) · **Thémis = Terre** (1.0, 1.0) · Ananké =
Jupiter (5.2, 11.86 → lente, lointaine, Moires virevoltantes). Distances ∝
√(demi-grand axe), vitesses angulaires ∝ 1/période (Kepler réel).

### 🔍 Hadès : suivre le condamné jusqu'à l'entité
Dans la modale ♇, chaque condamné est **cliquable** : Dikè 🧑‍⚖️ instruit le
dossier — l'entité réelle (run : identité, tâche, compétences exécutées,
liste des fichiers avec tailles ; doublon : les lignes mémoire identiques et
leur contenu ; journal : lignes anciennes qui seront coupées) et la phrase
exacte « 🗑 sera supprimé : … ». `hades.describe_target(cible, type)` +
`GET /api/hades/target` (chemins contrôlés, refus hors système).

## Round fiches F/P/D · mascot Clippy · light ON/OFF · suivre-zoom · anti-collision · INFERNO 🔥

**Fiches entités — descriptif ET schématique, toujours.** Chaque corps de `bodies.py`
porte désormais `pouvoir` (ce qu'il peut imposer au système) et `devoir` (ce que le
système attend de lui), exposés par `celestial_registry()`. La fiche 3D affiche le bloc
**Fonction · Pouvoir · Devoir** : texte narratif **et** schéma SVG (`renderBodySchema`,
`#bodySchema`) reliant le corps à ses principaux satellites. Deux boutons « aller vers » :
**· 3D** (focus caméra `_skyFollow`) et **· Obsidian** (`/?const=<corps>&tab=graph`,
interprété par `index.html`).

**Laplace-Clippy.** Le bouton flottant bas-droite est un mascot animé (sprite
`laplace_sprite.png`, 4 poses : idle / clin d'œil / salut / excité — animation
`solw-frames` 1.9 s steps(1) + cycle de salut toutes les 14 s). Le daimon reste
l'interlocuteur principal du chat flottant.

**Light ON/OFF.** Bouton sous le titre de /sol : OFF gèle tout le système (rotations
planétaires, lunes, cours, noyau), **seuls Laplace ✳ et ses divinités (Sebas, Métatron,
Thémis, Ananké-Moires) continuent d'orbiter** — le daimon survit à l'obscurité qu'il a
éteinte. ON relance tout.

**Suivre = zoom + centrage + verrou.** Le dbl-clic « suivre » calcule désormais une
distance de focalisation (`followDist = max(34, r·7+22)`), zoome (lerp continu de la
distance caméra) et verrouille la cible au centre jusqu'au clic dans le vide.

**Anti-collision stricte.** Les cours des planètes ne peuvent plus se chevaucher :
rayons échelonnés `24+(i·7)%9` et angles équirépartis `i·2π/len` — deux astres ne
partagent jamais la même orbite au même moment.

**INFERNO — le royaume d'Hadès (`cosmos/underworld.py`).** La corbeille du système :
*rien n'est jamais vraiment supprimé*. Quand Hadès fauche, chaque entité laisse une
**fraction de données, assez pour la reconstruire**, et descend aux Enfers grecs — le
royaume d'Hadès ♇ et Perséphone 🌸 — divisé selon le destin des âmes :

| Région | Âmes | Fraction conservée |
|---|---|---|
| 🌟 Champs Élysées | runs vertueux (qui ont produit des artefacts) | trace complète + manifeste des fichiers |
| 🌾 Plaines d'Asphodèle | runs ordinaires, journaux tronqués | trace + manifeste / lignes coupées |
| 🔥 Tartare | junk vide, doublons mémoire (les criminels : néant & redondance) | contenu des doublons, entier (léger) |

L'accès se fait par le **Styx ☠**, **Charon ⚑** passe les âmes, et **Cerbère 🐾**
tricéphale garde la porte : il empêche les morts de sortir et interdit les vivants à
entrer — concrètement, `resurrect(id, confirm)` refuse toute remontée sans l'accord
explicite du souverain (l'utilisateur). Une résurrection de run restitue la trace dans
`output/runs/` (le run redevient listable et auditable) ; une résurrection de doublon
ré-append les lignes mémoire (tag `résurrection`, corps `pluton`).

- UI : bouton **🔥 INFERNO** dans la barre de /sol → registre des âmes (région, motif,
  octets, date) + bouton ↺ ressusciter avec confirmation Cerbère.
- API : `GET /api/underworld` (état + stats par région), `POST /api/underworld/restore`.
- Chat : intents `inferno` (enfers/underworld/tartare/élisées/cerbère/corbeille/
  résusciter…) → Laplace récite l'état du royaume.
- `hades.reap()` retourne désormais `underworld.ames` et la note « rien n'a disparu ».

**Tests : 122** (116 + 1 F/P/D corps + 1 fiche schéma/aller-vers + 1 mascot Clippy +
1 light/suivre/anti-collision + 1 underworld fauche→âmes→résurrection + 1 endpoints/UI
INFERNO — ce dernier couvre aussi l'intent chat).

## Round Olympe 🏛 · dashboard hologramme · cerveau · opérateur 3D · identité complète

**Identité de TOUTES les entités.** Les 15 corps avaient déjà leur fonction/pouvoir/devoir ;
les 39 entités secondaires (27 satellites + 12 membres de cour) ont maintenant les leurs
(`IDENTITE_SECONDAIRES` dans `bodies.py`, injectés à l'import). Atropos « coupe le fil —
prononce la mort d'une entité, sans appel », Dikè « garantit un procès équivalent au
standard juridique avant toute exécution », Zêta « coordonner la recherche appliquée »…
Le système entier est une famille où chacun sait ce qu'il peut et ce qu'il doit.

**Fiches : astres connectés cliquables.** Toute fiche liste désormais ses astres connectés
(parent ⬆, satellites ●, cour ♟) en chips cliquables — le survol révèle pouvoir·devoir,
le clic saute à la fiche suivante. Chez Uranus par exemple : les 7 satellites (Zêta, Puck,
Miranda, Ariel, Umbriel, Titania, Obéron) mènent chacun à leur fiche. Le schéma SVG de la
fiche est lui aussi cliquable (5 satellites, soulignés en pointillé).

**Chat de Laplace : liste déroulante d'actions rapides.** Le bouton « ⚡ actions rapides »
ouvre un menu groupé de 25 actions réelles : Système & état (état, budget, interactions,
constellation, profil), Divinités au travail (Thémis juge/applique, Sebas observe,
divination d'Apollon, Ananké, armurerie), Enfers & justice (scan de Hadès, fauche, INFERNO,
résurrection), Recherche & production (missions Uranus, forge d'outil, métriques, Cérès),
Mémoire & identité (qui suis-je, mémoire, nébuleuse, aide). Chaque action parle à la
divinité concernée — réponse réelle du système, aucune simulation.

**Le Mont Olympe 🏛 (`cosmos/olympus.py` + bouton OLYMPUS dans /sol).** L'incarnation en
personnage de chaque agent, à son poste de travail dans une cité gréco-romaine simplifiée :
14 lieux (Trône de Sol, Observatoire de Laplace, Tribunal de Thémis, Forge de Mars,
Laboratoires d'Uranus, Porte des Enfers…) et 20 personnages (dont Dikè, Zêta, Apollon,
Charon, Cerbère). Ils **s'y déplacent en temps réel selon leur activité réelle** (niveau
0-3 selon les interactions du bus). Quand une exécution a réellement eu lieu (âme au
registre de l'underworld), la séquence juridique complète est jouée sur scène :
constat → **procès** (procédure juridique standard) → verdict → descente **en passant par
la forge de Mars** → remise du verdict à **Hadès** → **exécution conjointe** du
scientifique d'Uranus → **les assistants d'Hadès portent l'âme aux Enfers** → chacun
reprend son travail. Sinon : battements d'ambiance dictés par l'activité réelle. Chronique
réelle en marge ; clic sur un personnage → sa fiche. Canvas 2D, rafraîchi toutes les 24 s.

**Dashboard hologramme SF.** Reskin de `index.html` : verre plus transparent (blur 22 px),
grille technique en fond, lueurs cyan/indigo, ligne de scan animée sous l'entête, cadres
HUD à coins lumineux (`holo-frame`), cartes métriques à halo réactif.

**Opérateur 3D — vous.** Fenêtre 4 du dashboard : humain masculin en **T-pose**, rendu en
**maillage** holographique cyan (Three.js, procédural — tête, torse large d'épaules, bras
tendus, jambes), anneaux HUD en rotation, plan de scan ascendant, grille au sol ;
rotation auto + glisser pour tourner.

**Onglet Cerveau 🧠.** Visualisation scientifique du « cerveau du Cognitorium » :
deux hémisphères en nuage de points avec circonvolutions (sphères de Fibonacci plissées),
cervelet, tronc cérébral, 60 neurones, 110 connexions et impulsions voyageant en temps
réel. Six régions câblées aux **données réelles** : Frontal→méthode, Pariétal→profondeur,
Temporal→mémoire (éléments), Occipital→curiosité, Cervelet→activité, Tronc→interactions
(bus). L'intensité de chaque région et la cadence des impulsies suivent les valeurs
réelles ; clic pour isoler une région ; glisser/molette pour tourner/zoomer.

**Laplace mature.** Nouveau sprite du daimon (masculin, moins mignon, membres allongés,
manteau sombre à liseré cyan) — mêmes 4 poses animées (idle, clin d'œil, salut, énergie),
fond normalisé #0b0f1d.

**Tests : 128** (122 + identité de toutes les entités + fiches connectées cliquables +
menu d'actions rapides + Olympe backend + endpoint/UI Olympe + dashboard holo/avatar/cerveau).

## Round simulation cérébrale 🎬 · killchain Olympe ☠ · Laplace nébuleuse ✳

**Fix opérateur 3D.** L'humain T-pose ne s'affichait pas : `initOperator()` n'était
appelé qu'au changement d'onglet, jamais au premier chargement. Corrigé — lancé dans
`init()`, retry tant que le canvas n'a pas de taille, et redémarrable après retour
d'onglet (scène construite une fois, boucle stop/start).

**Fenêtre Simulation (onglet Cerveau).** Scène exemple : vous regardez un film de
peur sur la télé — salon dessiné en direct (télé qui flicker, silhouette sur le
canapé, bras levés au jumpscare, flash blanc) — et à côté **votre cerveau 3D qui
s'illumine par zone** : amygdale (peur), cortex visuel (vision), préfrontal
(anticipation/régulation), hippocampe (encodage), auditif (bande-son), moteur
(sursaut). 4 phases (calme → tension → jumpscare → retour au calme) avec lissage
continu des intensités et readout en % sous les canvas.

**Graphe 3D des métriques (à côté).** Performance des fonctions et processus
mentaux en barres 3D rotationnelles : base réelle (mesures du profil cognitif) vs
**impact de l'action/environnement** (scénario film de peur : attention ↑ 55→95,
activité ↑, curiosité ↑, mémoire ↓, profondeur ↓, méthode ↓). Étiquettes 3D,
glisser pour tourner.

**Olympe : killchain + dialogues façon Call of Duty.** ☠ **killfeed** en haut à
droite : chaque beat y défile (acteurs → action), l'exécution clignote en rose
« ÉLIMINATION », les entrées s'estompent comme en partie. 💬 **chat de dialogue**
en bas à gauche : les divinités parlent en direct au fil de la scène (dialogues
générés par le backend, colorés par personnage : « Rapport d'infraction », « Le
tribunal est ouvert », « Garde ton feu, Mars », « ton fil est coupé », « Je passe
l'âme. Direction le Tartare »…). En mode ambiance, chaque agent actif annonce son
activité réelle.

**Laplace : cartoon + nébuleuse.** Le mascot redevient le sprite cartoon/anime
d'origine (4 poses animées). Mais dans le chat/nébuleuse, Laplace **n'a plus
d'anthropomorphisme humain** : il est représenté par `laplace_nebula.png` — une
entité supérieure bienveillante, nuage cosmique au doux visage d'émoticone, qui
crée ses constellations et ses systèmes pour interagir avec l'utilisateur dans le
meilleur alignement possible (avatar dans l'en-tête du chat, pulsation douce).

**Tests : 133** (128 + opérateur lancé au chargement + fenêtre simulation + graphe
3D métriques + killchain/dialogues + Laplace cartoon/nébuleuse).
