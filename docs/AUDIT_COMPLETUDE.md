# 🔍 Audit de complétude — fonctionnalités, affichages, exigences

*Vérification du 02/09 : rien d'oublié ? Inventaire réel du code croisé avec
TOUTES les exigences accumulées (contraintes des rounds précédents + briefs
MobiGlas/vision/mémoire + retours du jour). Aucune implémentation.*

---

## 1. État réel inventorié (ce qui existe dans le code)

- **3 pages** : `/` (Cognitorium), `/sol` (SOL + cosmos 3D + 13 modales),
  `/agent` (Uranus chercheur) ;
- **10 onglets** sur `/` : Univers 🪐 (accueil), Dashboard, MobiGlas
  (instrument), Cerveau, Graphe Obsidian, Taxonomie, Base de données,
  Concepts, Timeline, Module SRL ;
- **~90 endpoints API** (corps, constellations, mémoires, mars/forge, ombre,
  godseye, olymuse, underworld/restore, hades/scan, themis, metatron, sebas,
  apollon, profil cognitif + traits, agent, mobiglas…) ;
- **Verrouillé par 151 tests** ; doc `COSMOS.md` tenue à chaque round.

**Vérifications ponctuelles passées** : drill-down des chiffres ✓
(`metricDetail` + jauge + explications), fiches F/P/D ✓, clic=dbl-clic sur
/sol ✓ (rotation/zoom/pan/focus), light ON/OFF ✓ (`toggleSystemLight` /sol),
chat flottant Laplace ✓ (/sol, bouton ✳), élagage+catégories ✓, 5 simulations
+ HUD ✓, opérateur 1ʳᵉ fenêtre + toggle cerveau ✓, INFERNO + résidu
restaurable ✓, OLYMPUS temps réel ✓, God's Eye ✓, Sera/ombre ✓, forge OSS ✓.

## 2. Exigences déjà couvertes ou planifiées (rien à faire d'autre que la roadmap)

Parcours complet de la vision = chantiers **R1bis** (satellites/anneaux/cours
— données déjà présentes : 56 noms), **R2** (fenêtres déplaçables + dock
MobiGlas complet : chat permanent, FONCTION contextuel, PARAMÈTRES),
**R3** (connexion, mode libre, guide), **R4-R7** (Chronos, incarnation-tuto,
tuyauterie, genèse), **M1-M6** (import, extraction, recherche, prompt-pack,
window manager, watchtower), **IA1** (canaux gratuits légitimes). Détail dans
`UIUX_ROADMAP.md` §14 et `MEMOIRE_MULTI_IA_ET_ORCHESTRATION.md` §7.

## 3. ❌ OUBLIS DÉTECTÉS (aucun chantier ne les couvre aujourd'hui)

| # | Oubli | Détecté comment | Insertion proposée |
|---|---|---|---|
| 1 | **Double-clic = suivre (zoom+lock) absent de la vue Univers** — la règle projet n'est appliquée que sur /sol ; sur l'accueil, clic = fiche mais pas de suivi d'astre | grep `dblclick` : 0 dans index.html, présent dans sol.html | **R1bis** (avec les satellites) |
| 2 | **Collisions potentielles du dock** : bas-centre (dock) vs bas-gauche (panneau « espace partagé » de l'onglet MobiGlas) vs chat — la règle « aucune collision » du projet n'a pas été re-vérifiée après l'ajout du dock global | positions `bottom-3/bottom-4` superposées | audit z-index + ancrages dans **R2** |
| 3 | **Calculette & mail creator** cités comme outils du menu FONCTIONS → **inexistants** dans l'armurerie (élaguée : 4 outils) | inventaire armory | à **forger via Mars** (forge OSS) ou mapper sur existant — chantier outils |
| 4 | **« Zodiac »** cité dans les options du graphe → aucun concept zodiac dans le système | grep : néant | à **clarifier** (constellations existantes ? nouveau référentiel ?) |
| 5 | **Export des données** (PARAMÈTRES → compte : « données, export » promis) : aucun endpoint d'export | grep export : néant | **R3** (session/compte) |
| 6 | **Aperçu de partage Discord** : le lien n'a ni Open Graph ni titre/image → l'ami voit une URL nue, pas une carte | pattern FuturAI (OG/sitemap/PWA) dont je m'étais inspiré pour l'onboarding seulement | micro-chantier **R3** (image OG du système solaire) |
| 7 | **Mode « lumière off » de la connexion** : le composant existe (`toggleSystemLight`) mais la roadmap ne relie pas explicitement l'animation d'illumination de Laplace à la page de connexion | grep light : /sol seulement | note explicite dans **R3** |
| 8 | **Layout 3 volets style Arena** (volet options/prompts + chat + fenêtre d'objet) : cité dans la vision, relégué à une ligne de tableau du doc mémoire — pas un chantier officiel | doc §2 | officialiser dans **R2** |
| 9 | **Cognition incarnée & flow** (concepts du brief MobiGlas d'origine) : couverts implicitement (opérateur incarné, cas rush/flow des simulations) mais **jamais affichés ni reliés** dans l'onglet MobiGlas | lecture onglet | micro-chantier MobiGlas (lien concept→preuve) |
| 10 | **Profil « parcours pro/scolaire/perso »** : le cas d'emploi métier l'exige, ces données n'existent pas (seul le profil cognitif + traits est réel) | endpoints profil | dépendance explicite **R5 → M4/M5** |
| 11 | **Ambiguïté de nommage** : l'onglet s'appelle « MobiGlas » mais MobiGlas = désormais le style de menus du dock ; le bouton /sol « 🥽 MobiGlas » pointe vers l'onglet | renommage prévu §10 sans nouvelle destination | décider le nouveau nom de l'onglet (ex. « Instrument » / « Cogniscan ») en **R2** |
| 12 | **Cosmétique** : badge « v4.0 » du header obsolète ; l'aide de la vue Univers ne mentionne pas le double-clic (cf. #1) | grep v4.0 | R1bis/R2 |

## 4. Chantiers dormants (pas oubliés, à ne pas perdre)

- **Monitor the Situation** : forge stage 1 « analyser » — interrompu au
  profit des rounds UI ; à reprendre dans la boucle R&D Mars ;
- **En attente utilisateur** : repo Language Decoder (403), incarnation
  conceptuelle, overhaul HD (photos refs — uploads KO dans la sandbox).

## 5. Recommandations (ordre)

1. **R1bis élargi** : satellites + anneaux + cours **+ double-clic suivre +
   badge version + aide à jour** (un seul round, tout le §3-1/12) ;
2. **R2 consolidé** : fenêtres déplaçables + dock complet + **audit collisions
   (#2)** + **layout 3 volets officiel (#8)** + **renommage onglet (#11)** ;
3. **R3 élargi** : connexion + guide + **export données (#5)** + **carte OG
   Discord (#6)** + **lumière off liée (#7)** ;
4. décisions à prendre au fil de l'eau : **zodiac (#4)**, **calculette/mail
   creator (#3)** — forger ou mapper, **cognition incarnée/flow (#9)** en
   micro-chantier MobiGlas.

*Conclusion : le socle est complet et sain (151 tests, doc tenue) ; 12 oublis
détectés, tous absorbables par les chantiers existants à condition de les
écrire noir sur blanc — c'est fait ci-dessus.*
