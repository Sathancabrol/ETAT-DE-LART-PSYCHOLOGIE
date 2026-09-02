# 🧭 Note de réflexion UI/UX — vers le MobiGlas complet

*Analyse de la vision finale (partage Discord → connexion → Chronos → Laplace →
système solaire → MobiGlas) et recommandations, round après round.*

---

## 1. La vision, reformulée

Un ami reçoit un lien Discord → l'app s'ouvre comme Arena Agent Mode : un
**volet d'options/prompts**, un **chat**, une **fenêtre d'objet** (preview,
documentation). Le parcours :

1. **Connexion** — page de chargement/synchronisation ; mode libre (pseudo
   seul), connexion, ou création de compte (en français).
2. **Chronos** — LESPACETEMPS incarné : un réceptacle-aquarium (globe
   irrégulier) rempli d'un fluide univers modelé par l'entropie, avec bulles
   d'air. Il se présente et invite à se présenter.
3. **Création d'incarnation = tuto** — un humain en points/particules à côté
   d'une fenêtre ; chaque info (nom, prénom, naissance, questions
   intra/interpersonnelles) transforme l'avatar en temps réel (homme/femme,
   forme). L'inscription **enseigne l'interface en même temps** que l'utilisateur
   rentre ses données.
4. **Tuyauterie spatio-temporelle** — décrire son parcours simplement (import
   CV/PDF/image/texte) ; si bloqué, Chronos pose des questions/réponses pour
   construire le graphe : connaissances, compétences, expériences pro &
   perso, contacts, productions, interactions avec le monde. Au moins 1 item
   par catégorie.
5. **Zoom dans Chronos → Laplace** — on plonge dans le fluide, une nébuleuse
   apparaît : Laplace, l'interlocuteur. Clic → chat (en bas à droite,
   déplaçable). Laplace se présente et présente les **constellations** de
   l'utilisateur (compétences, connaissances, ressources…). Un volant se
   déroule à gauche : le menu utilisateur.
6. **Enaction** — Laplace annonce que l'incarnation est prête ; animation de
   genèse du système solaire ; zoom lent sur la Terre ; Laplace explique
   qu'il a créé un système solaire pour gérer autonomement chaque élément qui
   définit l'utilisateur (Uranus = connaissance du monde, Mars = outils…).
7. **MobiGlas** — une fenêtre style MobiGlas s'ouvre par-dessus la vue
   Terre : l'interface principale (dashboard, paramètres, parcours…).

## 2. Ce qui existe déjà ↔ ce qui manque

| Concept de la vision | État dans le Cognitorium |
|---|---|
| Lien partagé → app web | ✅ l'app est déjà une page web publique (preview) |
| Système solaire = accueil épuré | ✅ **livré ce round** (vue Univers + dock) |
| Laplace nébuleuse interlocuteur | ✅ nébuleuse violette sur l'orbite externe + chat flottant ; ❌ pas encore le zoom depuis Chronos |
| MobiGlas | ✅ onglet instrument cognitif (pipeline + inférences traçables) ; ❌ pas encore fenêtre déplaçable par-dessus la Terre |
| Constellations de connaissances | ✅ graphe Obsidian (concepts/études/sources) ; ❌ pas encore « les constellations DE l'utilisateur » |
| Humain incarné (SF, points) | ✅ opérateur T-pose du dashboard ; ❌ pas encore l'avatar-particules morphing |
| Chaque planète gère un élément | ✅ 15 corps avec départements/pouvoirs réels, fiches clicables |
| Chronos (LESPACETEMPS, aquarium-entropie) | ❌ à créer — l'entité d'accueil n'existe pas encore |
| Connexion / mode libre / comptes | ❌ à créer |
| Création de compte = tuto | ❌ à créer (l'avatar qui se transforme selon les réponses) |
| Import CV → graphe de connaissances | ❌ à créer ( parsing local, rules-first, aucune donnée fabriquée) |
| Genèse animée du système solaire + zoom Terre | ❌ à créer |
| Volet options/prompts + fenêtre d'objet | ✅ partiel : chat flottant + fiches ; ❌ disposition 3 volets à la Arena |

## 3. Principes de congruence (le cœur de la demande)

**Le problème actuel** : 9 onglets plats dans une barre en haut + des modales
côté /sol → l'utilisateur doit *apprendre* la carte de l'app.

**Recommandation fondatrice — un seul modèle mental : le ZOOM.** Toute
l'app vit dans **un seul espace continu** à niveaux d'échelle :

```
Chronos (l'univers-aquarium)  →  Laplace (la nébuleuse)  →  le système solaire
→  la Terre  →  le MobiGlas (les fenêtres projetées)
```

Naviguer = zoomer/dézoomer, jamais « changer de page ». Les fenêtres
(MobiGlas, chat, fiches) flottent **par-dessus** cet espace, se déplaçent,
et se rappellent d'où elles viennent (fil d'Ariane existant).

Règles dérivées, appliquées dès maintenant :
1. **Un seul dock, toujours au même endroit** (ACCUEIL · FONCTION · OPTION,
   bas d'écran) — livré ce round, présent sur tous les onglets.
2. **L'accueil est un lieu, pas un menu** — la vue Univers épurée, sans
   header : on *est* quelque part, on ne clique pas dans une liste.
3. **Clic = sélection/fiche, double-clic = suivre** — déjà la règle, à
   conserver partout (planètes, nœuds du graphe, outils).
4. **Toute action est réversible et traçable** — résidus au Tartare, bus
   d'interactions, inférences traçables du MobiGlas.
5. **Aucun anthropomorphisme humain dans le chat** — Laplace mascot/cartoon
   et Chronos = entités distinguables (bulles/fluide), jamais d'humain autre
   que l'avatar de l'utilisateur.
6. **Le 1ʳᵉ lancement est un scénario, pas un formulaire** — la création de
   compte EST le tuto (voir R4).

## 4. Feuille de route recommandée

- **R1 ✅ (ce round)** — Accueil = système solaire épuré + dock congruent
  ACCUEIL·FONCTION·OPTION (tiroirs fonctions/options : étiquettes, orbites,
  vitesse du temps, plein écran) ; astres clicables → fiches réelles
  (pouvoir/devoir/mémoires/interactions) ; l'utilisateur 🕴 satellite de la
  Terre ; Laplace ✳ nébuleuse enveloppante.
- **R2 — Fenêtres déplaçables** : MobiGlas, chat et fiches deviennent des
  fenêtres flottantes drag-resize par-dessus l'espace (le chat l'est déjà en
  partie) ; disposition mémorisée. *Prérequis technique pour la vue « Arena
  à 3 volets ».*
- **R3 — Connexion & mode libre** : page de synchronisation, pseudo →
  compte libre (aucune info perso), session locale ; le lien Discord ouvre
  directement ici.
- **R4 — Chronos & l'incarnation-tuto** : l'aquarium-entropie (globe
  irrégulier, fluide, bulles — particules + shader), l'humain en points qui
  **se transforme en temps réel** selon les réponses ; chaque écran de
  données = un geste de l'interface appris (c'est le tuto).
- **R5 — Tuyauterie spatio-temporelle** : import CV/texte (parsing local),
  questions/réponses guidées par Chronos, ≥ 1 item par catégorie →
  constellations de l'utilisateur dans le graphe.
- **R6 — Le zoom fondateur** : plongée Chronos → nébuleuse Laplace (transition
  continue), présentation des constellations, volant menu utilisateur à
  gauche, chat en bas à droite.
- **R7 — Genèse & MobiGlas** : animation de création du système solaire,
  zoom lent sur la Terre, discours de Laplace (les planètes gèrent
  l'utilisateur), puis fenêtre MobiGlas par-dessus la Terre = hub principal.

**Ordre délibéré** : fenêtres (R2) avant connexion (R3) car R6/R7 dépendent
des fenêtres flottantes ; Chronos (R4) après la connexion (R3) car le tuto
presuppose une session ; la genèse (R7) en dernier car c'est la récompense.

## 5. Recommandations transverses

- **Performance** : une seule scène 3D vivante à la fois (déjà le cas) ;
  transitions par fondu/caméra, jamais de rechargement de page.
- **Honnêteté des données** (règle du projet) : Chronos modélise l'entropie
  du *vrai* registre (mémoires, interactions), l'avatar ne devine rien —
  les questions de Chronos sont les seules sources.
- **Français partout**, boutons « ENTRER en mode libre / connexion / créer
  un compte » — déjà la langue de l'app.
- **Mobile** : le dock se réduit à 3 icônes ; les tiroirs passent en
  bottom-sheet plein largeur (déjà le cas en petite largeur).
- **Partage** : URL avec état (`/?tab=…&const=…` déjà fonctionnel) →
  ajouter plus tard le token de session dans le lien Discord.

---
*R1 livré : voir `docs/COSMOS.md` pour le détail du round.*
