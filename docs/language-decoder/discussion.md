# Language Decoder — Discussion, principes et conseils appliqués

> Dossier créé le 30 août 2026. Archive de la discussion sur **le langage de
> l'humain et son interface**, et mise en application de chaque conseil dans
> Cognitorium (voir « Où chaque conseil est appliqué » en fin de document).

---

## 1. Idée centrale

La science permet de mieux comprendre un objet dans son environnement. Lorsque
l'objet étudié est l'humain, il faut identifier ses différents **langages** :
parole, gestes, comportements, signaux physiologiques (ECG, variabilité
cardiaque, conductance cutanée, respiration) et signaux neurophysiologiques
(EEG, BCI).

Un signal ne possède pas une signification unique. Il doit être interprété
**avec le contexte, la ligne de base individuelle et son évolution dans le
temps**. Le système ne « lit » pas directement une émotion : il produit une
**hypothèse probabiliste sur un état latent** (charge cognitive, activation,
fatigue, engagement, stress possible), avec un niveau de confiance.

## 2. La chaîne de raisonnement (8 étapes)

1. **Observer** l'humain dans un contexte.
2. **Identifier ses langages** observables (parole, écriture, gestes, signaux).
3. **Acquérir les signaux** : fréquence cardiaque, variabilité, respiration,
   conductance cutanée, EEG/BCI, actions numériques.
4. **Extraire des caractéristiques** : rythme, amplitude, variation,
   synchronisation, durée.
5. **Relier au contexte** et à une période T1, T2, T3…
6. **Estimer un état latent** (hypothèse probabiliste, jamais une lecture directe).
7. **Afficher une confiance** et les données utilisées.
8. **Adapter l'interface** sans retirer le contrôle à l'utilisateur.

## 3. La métaphore de la langue (et sa limite)

| Langue humaine | Système de compréhension |
|---|---|
| Signes ou sons | Signaux corporels, cérébraux, comportementaux |
| Grammaire | Relations entre les signaux et le contexte |
| Sens | État ou intention **estimée** |
| Dialogue | Interaction humain ↔ interface |
| Réponse adaptée | Feedback ou action du système |

Limite scientifique : les biomarqueurs ne constituent **pas** une langue au
sens strict. Un mot a une signification conventionnelle ; un signal
physiologique est **ambigu, continu et dépendant du contexte**. On parle donc
de *langage multimodal de l'humain* ou de *système de signes incarnés*.

**Exemple (cœur)** : une fréquence élevée peut correspondre à un effort, une
excitation, une peur, une douleur ou un stress. Croiser plusieurs signaux + le
contexte avant toute interprétation. Formulation rigoureuse :
« à partir de plusieurs signaux et du contexte, le système **estime la
probabilité** de certains états » — et non « le système **déduit** l'émotion ».

## 4. Représentation d'une observation (modèle de données)

```json
{
  "temps": "T2",
  "contexte": "résolution d'un problème",
  "signaux": {
    "frequence_cardiaque": "élevée",
    "variabilite_cardiaque": "diminuée",
    "temps_sur_tache": "long"
  },
  "hypotheses": [
    {"etat": "charge cognitive élevée", "confiance": 0.68},
    {"etat": "frustration possible", "confiance": 0.42}
  ],
  "action_interface": "proposer une aide progressive"
}
```

Cette représentation **distingue les données, les hypothèses et les décisions
de l'interface** — jamais présentées comme des vérités absolues.

## 5. Interface adaptative (principes)

Ralentir le rythme si surcharge probable · proposer une explication différente
après plusieurs erreurs · fractionner une tâche complexe · ajuster la
difficulté · demander confirmation · **afficher pourquoi une adaptation a été
déclenchée**. L'humain est un système intégré : cerveau, corps, action et
environnement participent ensemble à l'interaction (cognition incarnée).

## 6. Les 5 couches du modèle d'orientation (notes manuscrites)

| Couche | Question centrale |
|---|---|
| Individu | Qui est la personne ? |
| Cognition | Comment apprend-elle, raisonne-t-elle, agit-elle ? |
| Compétences | Que sait-elle déjà faire ? |
| Monde professionnel | Quelles activités et métiers existent ? |
| Parcours | Comment passer d'une situation à une autre ? |

Idée forte : un système de **navigation** entre personne, cognition,
compétences, activités, métiers et parcours — des **compatibilités**, pas un
classement (« tu es fait pour… »). Distinguer ce qui relève de la mesure
psychologique, de l'auto-évaluation, des données objectives sur les métiers et
de la recommandation algorithmique.

## 7. Principes de conception (garde-fous)

- Distinguer **mesure / interprétation / action**.
- Afficher **l'incertitude** plutôt qu'une certitude artificielle.
- Utiliser une **ligne de base propre à chaque personne**.
- Conserver l'**historique temporel et le contexte**.
- Permettre à l'utilisateur de **corriger l'interprétation**.
- **Minimiser** les données collectées ; documented : sécurité, profils,
  durée de conservation, droits (CNIL).
- Jamais une estimation émotionnelle comme diagnostic médical.
- Jamais de décision à fort impact déclenchée automatiquement.

## 8. Formulation synthétique

> Observer les signes, comprendre le contexte, représenter les états,
> anticiper les besoins et adapter l'interface — de manière explicable,
> probabiliste et contrôlée.

---

## 9. Réponses aux trois questions finales

### 9.1 Quel format de code HTML recommander pour le dashboard ?

**HTML5 sémantique + CSS moderne, zéro dépendance** :

- une seule page `index.html` autonome (fonctionne hors-ligne, ouvrable
  directement, publiable sur GitHub Pages) ;
- **variables CSS** (`--bg`, `--ink`, `--line`…) comme design tokens →
  thème cohérent et adaptable sans framework ;
- **CSS Grid + `grid-column: span`** pour le responsive (une seule media
  query pour tout replier en une colonne) ;
- balises sémantiques (`<header> <main> <section> <article> <footer>`) pour
  l'accessibilité et la lisibilité du code ;
- données **séparées du rendu** : un objet JSON en tête de script génère les
  cartes → remplacer les données simulées ne touche pas la mise en page ;
- pour un système vivant (comme Cognitorium) : garder ce socle statique comme
  maquette, puis le brancher sur l'API — éviter d'embarquer un framework
  lourd tant que le besoin n'existe pas.

### 9.2 Quels indicateurs visuels pour montrer l'incertitude ?

1. **Barres dégradées** : la part certaine en couleur pleine, la zone
   incertaine en dégradé qui s'estompe (jamais une barre pleine qui « sonne »
   précis).
2. **Intervalles affichés** (`±`, `68 % [55–78]`) plutôt qu'un chiffre seul ;
   arrondir pour ne pas fabriquer de fausse précision.
3. **Hachures / opacité réduite** pour tout ce qui est *estimé* ou
   *hypothétique*, couleur pleine pour ce qui est *mesuré*.
4. **Badge d'échantillon** : `n = 420 interactions` à côté du score — un score
   sans donnée suffisante est une hypothèse.
5. **Trois sections visuellement distinctes** : Mesuré / Interprété (avec
   confiance) / Action proposée (réversible) — le regard comprend immédiatement
   ce qui est fait vs déduit.
6. **Légende explicite** : « un signal isolé ne prouve rien ; plusieurs
   signaux + contexte = hypothèse probabiliste ».

### 9.3 Comment appliquer la minimisation des données ici ?

- **Ne collecter que ce qui sert la décision** : pour chaque indicateur,
  demander « quelle décision cette donnée améliore-t-elle ? » — sans réponse,
  pas de collecte.
- **Agrégats d'abord, brut ensuite** : stocker des comptages et des scores
  plutôt que des signaux bruts ; le brut n'est conservé que le temps d'en
  extraire des caractéristiques.
- **Durée de conservation définie** (politique de rétention documentée et
  exécutée automatiquement — dans Cognitorium : Styx/Hadès, fenêtre de 25 runs,
  journaux tronqués à 1 500 lignes, purge réelle et journalisée).
- **Local-first** : le prototype ne rien envoyer nulle part ; tout reste dans
  le navigateur / la machine.
- **Consentement explicite avant tout capteur réel** ; les données simulées
  sont marquées comme telles partout.
- **Droits outillés** : consulter (tout est visible), corriger (traits
  déclarés modifiables), supprimer (la fauche détruit réellement).
- **Jamais de biométrie déguisée** : aucune « donnée cardiaque » invented —
  en sandbox, les interfaces capteurs affichent « non détecté, aucune donnée
  fabriquée ».

---

## 10. Où chaque conseil est appliqué dans Cognitorium

| Conseil | Application |
|---|---|
| Mesure / interprétation / action distinctes | Modale Hadès : *données mesurées* (Mo, compteurs) → *interprétation* (politique Styx, Moires) → *action* (fauche, confirmation obligatoire) |
| Afficher l'incertitude | `cogniprofile.confiance` (niveau + échantillon + intervalle) affiché au-dessus des jauges de biais ; tokens épargnés marqués « estimation » ; divination : présages + méthode |
| Ligne de base individuelle | Profil cognitif induit des interactions de **cet** utilisateur (pas de norme absolue) |
| Historique temporel | Fil d'Ariane (parcours réel T1→remise), rythme d'activité horaire |
| Correction par l'utilisateur | Traits déclarés (ajoutables), observations déclaratives de Sebas |
| Minimisation + durée de conservation | Politique Styx exécutée par Hadès : 25 runs, journaux 1 500 lignes, doublons purgés — suppression réelle, journalisée |
| Expliquer pourquoi une action | Fauche : « quoi / pourquoi / ce qui reste conservé » par catégorie + bilan post-fauche ; alertes SOL préventives motivées |
| Pas de fausse donnée capteur | Sebas : « capteurs non détectés en sandbox — observation déclarative, aucune donnée fabriquée » |
| Probabiliste, jamais « lecture directe » | Formulations « état estimé », « hypothèse », avertissement permanent : heuristiques, pas un test psychométrique validé |
| Interface adaptative réversible | Boutons proposés (jamais exécutés seuls), panneaux repliables, confirmation avant toute destruction |

**Prototype** : ouvrir `index.html` (autonome, données simulées marquées).
