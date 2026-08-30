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
