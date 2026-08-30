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
