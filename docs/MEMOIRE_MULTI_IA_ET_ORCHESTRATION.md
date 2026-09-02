# 🧠 Mémoire multi-IA & Orchestration — analyse, comparaison, proposition

*Note de réflexion (rien n'est implémenté). Source : réflexions utilisateur +
discussion externe sur la « Personal AI Memory » (PAM) et la boucle
Chronos → Laplace → SOL → fenêtres adaptatives.*

---

## 1. Les deux apports à analyser

**A — La mémoire multi-IA (PAM).** Centraliser les conversations éparpillées
(GPT, Claude, Kimi, Arena, Anara…) dans **une** mémoire où chaque chat devient
un *objet de première classe* : brute conservée à jamais (conversation =
journal), connaissance extraite à côté (mémoire = synthèse exploitable),
**provenance** sur tout (quelle IA, quelle date, quelle conversation),
**versions** des idées qui évoluent, recherche globale, et le killer feature :
**« continuer avec une IA »** — générer le contexte (projet, décisions
existantes, questions ouvertes, sources, dernière conversation) à copier dans
n'importe quelle IA.

**B — La boucle d'orchestration.** `utilisateur → Chronos (entrée) → demande à
Laplace → SOL dispatch → corps → Chronos répond **en changeant l'affichage**` :
la réponse n'est pas un texte, c'est une **scénographie de fenêtres** qui
s'ouvrent/déplacent (dans et en dehors de l'espace) selon la demande. Cas
d'emploi : « je cherche du travail, c'est quoi le boulot qui me convient le
mieux (flow state) » → cerveau temps réel + vue de l'humain + stats + fenêtre
de recherche métier (la recherche de l'IA visible) + constellation
métier dans le graphe Obsidian (correspondance profil incarné ↔ existant) +
vue **watchtower** focalisée sur les métiers identifiés et leurs
localisations (bulles sur la Terre 3D) + fenêtre des localisations.

## 2. Comparaison : PAM ↔ ce qui existe DÉJÀ dans le Cognitorium

| Concept PAM / orchestration | État réel dans le repo |
|---|---|
| Mémoire centrale persistante | ✅ **3 831 mémoires** (`cosmos/memory.py`) avec `source` (user/génération/mars/laplace…), `corps`, `type`, `tags`, `ts` — la provenance existe déjà |
| Conversation ≠ mémoire | ◐ le bus d'interactions journalise (600 dernières) ; les conversations ne sont pas des objets consolidés |
| Provenance de chaque connaissance | ✅ source + corps sur chaque item ; inférences traçables du MobiGlas (chaîne observation→feature→modèle→inférence→action) |
| Knowledge graph + constellations | ✅ graphe Obsidian (concepts/études/sources/méthodes/théoriciens), constellations par corps, liens « pourquoi » |
| Versions, historique | ◐ mémoires évolutives par round ; pas de v1/v2/v3 explicites d'une idée |
| Import GPT/Claude/Kimi | ❌ inexistant — c'est le vrai trou |
| Extraction idées/décisions/questions | ❌ pas d'extraction structurée des conversations |
| Recherche globale (sémantique) | ◐ recherche lexicale par fiche/graphe ; pas de recherche « partout » |
| « Continuer avec une IA » (prompt-pack) | ❌ inexistant — mais toutes les données nécessaires sont là |
| Watchtower / vue Terre géo | ✅ **God's Eye View** intégré (outil de Sebas : globe 3D données réelles) ; ❌ pas encore de bulles métiers/localisations sur la Terre |
| Orchestrateur qui ouvre des fenêtres | ❌ inexistant — le MobiGlas est un onglet fixe, pas des fenêtres adressables |
| Cerveau temps réel / humain / stats | ✅ existants (HUD cognition, opérateur, biometriques) — mais pas adressables comme fenêtres |

**Constat central : le Cognitorium EST déjà une External Cognitive Memory.**
Il ne manque pas un nouveau système à côté — il manque **trois couches**
dessus : ingestion, recherche, orchestration des fenêtres.

## 3. La proposition : architecture unifiée

```
        Chronos 🌌 (LESPACETEMPS — l'entrée et la scène)
              │  « je cherche du travail »
              ▼
        Laplace ✳ (dialogue + intents rules-first — existe)
              ▼
        SOL ☉ (dispatch vers les corps — existe)
              ▼
   ┌──────────┴────────────┬─────────────────┬──────────────┐
   ♅ Uranus (recherche)   ♂ Mars (outils)   ♇/⚖ (audit)   ☿ Mercure (comms)
              └──────────── MISSION ────────┘
                             ▼
        WINDOW MANAGER (nouveau) — Chronos « répond » en scène :
        fenêtres MobiGlas adressables (ouvrir/déplacer/fermer/épingler)
                             ▼
        MÉMOIRE CENTRALE (existe : 3 831 items + provenance + graphe)
        + conversations importées (GPT/Claude/Kimi = sources comme les autres)
```

Principes posés :
1. **Les IA externes sont des *sources***, exactement comme les corps du
   système : une conversation Claude importée = items de mémoire avec
   `source: claude`, provenance, date, lien vers l'original conservé brut.
   Les IA deviennent des interfaces différentes vers la même mémoire.
2. **Conversation brute ≠ extraits.** L'import conserve le fichier original
   intégral (résidu inviolable, comme le Tartare) ; l'extraction produit des
   items typés (décision / idée / question ouverte / hypothèse / source /
   concept) qui pointent vers l'original.
3. **Extraction rules-first, 0-token, honnête.** Pas de LLM qui « résume » :
   des patterns déterministes (lignes « décision : », « idée : », « Q: », « à
   faire », headers markdown…) + **édition assistée par l'utilisateur** (Chronos
   propose, l'humain valide — aucune donnée fabriquée).
4. **Le prompt-pack « continuer avec une IA »** est purement déterministe :
   assembler depuis la mémoire (projet + décisions + questions ouvertes +
   sources + derniers extraits) un bloc à copier. Zéro token, toute IA le lit.
5. **Chronos répond en scène.** Une intention ne renvoie pas seulement un
   texte : elle déclenche un *layout* — l'orchestrateur de fenêtres dispose
   des vues existantes (cerveau, opérateur, stats, graphe, recherche, fiche,
   doc, watchtower) comme de fenêtres flottantes. L'utilisateur garde toujours
   la main (déplacer, épingler, fermer) — la scène est une proposition.

## 4. Le gestionnaire de fenêtres (le cœur de la boucle B)

Grammaire minimale proposée :
- **types de fenêtres** : `chat` (Laplace), `brain` (HUD temps réel),
  `human` (opérateur + biometriques), `search` (recherche en cours, étapes
  visibles), `graph` (constellation Obsidian, ancrée sur un nœud),
  `watchtower` (Terre 3D + godseye + bulles localisées), `doc` (fiche F/P/D,
  conversation brute, source), `mobiglas` (pipeline/inférences) ;
- **événements** : `open(type, {anchor})`, `close`, `focus`, `pin`,
  `move` — chaque événement journalisé dans le bus (traçable) ;
- **layouts** : des scénographies nommées (« veille », « recherche emploi »,
  « écriture ») = listes ordonnées d'ouvertures ; une intention peut appeler
  un layout ou composer fenêtre par fenêtre ;
- **dans et en dehors de l'espace** : les fenêtres vivent par-dessus le zoom
  (Chronos → système solaire → Terre) — une fenêtre peut être « rattachée » à
  un astre (elle suit son orbite) ou flottante libre.

## 5. Cas d'emploi « recherche d'emploi / flow » — walkthrough proposé

1. **Demande** à Chronos → Laplace → intent `emploi` → SOL dispatch ;
2. **Fenêtre human** : opérateur + profil incarné (compétences, expériences —
   aucune donnée fabriquée : ce que l'utilisateur a déclaré/importé) ;
3. **Fenêtre brain** : HUD cognition temps réel pendant la réflexion (les
   mêmes processus que la simulation — attention, vigilance…) ;
4. **Fenêtre search** : la recherche **visible** d'Uranus (étapes : référentiel
   métiers → critères flow (compétence↑/défi, feedback clair, but clair —
   concepts déjà présents dans la base psychologie) → correspondances) ;
5. **Fenêtre graph** : constellation « métiers » ancrée sur le profil — les
   meilleurs appariements profil ↔ métier s'affichent comme des liens dans le
   graphe Obsidian (chaque lien = pourquoi, score, provenance) ;
6. **Fenêtre watchtower** : Terre 3D + bulles sur les localisations des métiers
   identifiés (données réelles via godseye si dispo, sinon bulle « localisation
   inconnue » honnête) + fenêtre liste des localisations ;
7. **Prompt-pack** : « continuer avec GPT/Claude » généré depuis la mémoire de
   la session.

**Écart de données honnête** : le repo n'a **aucun référentiel métiers** (pas
de ROME). Option réelle à étudier : l'**opendata ROME de France Travail**
(licence ouverte, ~13 000 appellations + compétences associées) — import local
une fois, ensuite tout marche rules-first. À valider avec l'utilisateur.

## 6. Méthodes comparées (réponse à « les plus utilisées dans mon cas »)

| Méthode | Apport | Limite | Place ici |
|---|---|---|---|
| Second brain (PARA, Zettelkasten) | organisation simple, robuste | manuel, pas de recherche sémantique, pas de provenance multi-IA | couche présentation (projets/constellations) — déjà couvert |
| RAG vectoriel | retrouver des passages par le sens | embeddings à héberger/calculer ; noir/blanc sur la provenance | **V2 optionnelle** (embeddings locaux) — pas le socle |
| Mémoire structurée (items typés + provenance) | machine-readable, traçable, durable | extraction à faire | **le socle — existe déjà, à étendre** |
| Knowledge graph | relations entre idées, « pourquoi » | construction des liens | déjà là (Obsidian + constellations), à relier aux extraits |
| Conversation as first-class object | jamais perdre le contexte historique | volume | couche ingestion à construire |
| Orchestration agentique (Chronos répond en scène) | l'IA agit sur l'interface | complexité UI | le différentiateur — window manager à construire |

**Recommandation** : mémoire structurée + graphe (déjà en place) → ingestion
conversations → recherche **lexicale riche** V1 (scoring type BM25 maison +
synonymes via le registre de concepts, 0 dépendance, 0 token) → embeddings
**locaux** en V2 seulement si la V1 déçoit (coût sandbox, mais faisable
hors-ligne). Le RAG nu ne résout pas la provenance ; notre force c'est la
chaîne traçable.

## 7. Roadmap fusionnée (R = UI/UX existante, M = mémoire/orchestration)

| # | Chantier | Dépend de | Difficulté |
|---|---|---|---|
| R2/M4 | **Window manager** — fenêtres MobiGlas adressables (drag, épingler, layouts) | — | ⬛⬛⬛ |
| M1 | **Import conversations** (.md/.txt/.json, détection source IA, original conservé) | — | ⬛ |
| M2 | **Extraction structurée** rules-first + validation humaine (conversation = objet) | M1 | ⬛⬛ |
| M3 | **Recherche globale** lexicale riche (partout : mémoires, conversations, sources, fiches) | M1 | ⬛ |
| M6 | **Prompt-pack « continuer avec une IA »** | M2 | ⬛ |
| M5 | **Watchtower Terre 3D** — bulles localisations + godseye | R2/M4 | ⬛⬛ |
| R3–R7 | Connexion, Chronos, incarnation-tuto, genèse (inchangées) | R2 | ⬛⬛⬛ |

Deux tracks parallèles possibles : **Track scène** (R2 → M5 → intents qui
composent des layouts, dont le cas emploi avec données actuelles) et **Track
mémoire** (M1 → M2 → M3 → M6). Elles convergent dans l'intent `emploi` complet.

## 8. Décisions ouvertes (à trancher avant d'implémenter)

1. Priorité du prochain round : window manager, import mémoire, ou les deux en //
   ? 2. Référentiel métiers : importer l'opendata ROME (licence ouverte) ou
   partir des concepts psychology existants sans référentiel externe ? 3.
   Recherche : lexicale V1 seule, ou embeddings locaux dès le début ? 4. Les
   conversations importées restent-elles **strictement locales** (jamais dans
   output/ git poussé) — recommandé si données perso ?
