# Analyse critique des concepts 4E / Énactivisme pour Cognitorium
# Sources, gaps et opérationnalisation

**Version:** 1.0 - Analyse concepts docs  
**Date:** 25 août 2026  
**Statut:** Document de travail - Transposition théorie → design opérationnel falsifiable  
**Base:** Analyse paste.txt + docs existants + revues 2024-2026  
**Objectif:** Transformer cadre philosophique riche (4E, énactivisme, ACT-IN, affordance) en principes mesurables pour Cognitorium

---

## 1. Méthode d'analyse

### Corpus analysé
- `docs/ETAT_ART_CRITIQUE_PSYCHOLOGIE_2020_2026_CORRIGE.md` (12 domaines)
- `output/classification_methodologique.md` (pyramide preuves, validités)
- `data/nodes_etat_art_psychologie.csv` (42 champs, 14 entrées)
- `output/visual/d3_interactive.html` (graphe liens méthodologiques)
- Document interne Epsylon / Thomas Camus thèse Montpellier 3 (action-perception intégration)

### Recherche sources (2024-2026)
- Bases: PsycINFO, PubMed, Scopus, OpenAlex, Crossref
- Requêtes: `embodied cognition meta-analysis`, `affordance ecological-enactive 2024`, `ACT-IN Versace`, `cognitive load Tricot Sweller`, `sense of agency scale validation`, `4E cognition heterogeneity Carney`
- Critère: revues intégratives, méta-analyses, validations psychométriques, thèses Epsylon

### Grille d'analyse par concept
Pour chaque concept: définition docs, définition scientifique, intérêt Cognitorium, solidité (échelle 1-5), sources récentes avec DOI, gaps, chaîne opérationnalisation `concept → mécanisme → comportement observable → fonctionnalité → métrique → hypothèse testable`.

---

## 2. Synthèse concepts (tableau)

| Concept | Définition docs | Intérêt Cognitorium | Solidité (1-5) | Risque principal |
|---------|-----------------|---------------------|----------------|------------------|
| Cognition incarnée | Cognition dépend corps, perceptions, actions | Activités manipulables, multimodales, contextualisées | 4/5 - bien documenté mais dépend domaine | Confondre incarnation décorative vs fonctionnelle |
| Cognition située / embedded | Cognition dépend contexte matériel, social, culturel | Relier compétences à situations professionnelles réelles | 4/5 - solide approches situées/écologiques | Réduire contexte à décor |
| Énactivisme | Sens émerge interaction dynamique apprenant-environnement | Boucles perception-action-feedback | 3/5 - théoriquement influent, difficile à tester directement | Amalgamer 4E et énactivisme radical |
| Cognition étendue | Outils/artefacts participent système cognitif | Portfolio, graphes, IA comme supports cognitifs | 3/5 - fécond mais frontière outil-système débattue | Anthropomorphisme IA agent cognitif |
| Affordance | Possibilité action offerte par situation à individu donné | Adapter actions proposées capacités/intentions/contexte | 5/5 - très utile UX si pas réduit à bouton | Réduire affordance à fonctionnalité visible |
| ACT-IN | Expérience cognitive émerge activation/intégration traces sensorimotrices | Exploiter trajectoires, hésitations, stratégies récurrentes | 3/5 - pertinent modèle traces, nécessite validation | Inférer trace cognitive depuis clics |
| Charge cognitive | Difficulté dépend tâche, support, connaissances | Éviter interface/IA ajoute complexité inutile | 5/5 - très bien documenté empiriquement | Vouloir réduire systématiquement toute charge |
| Agence | Sentiment auteur décisions/actions | Maintenir contrôle humain face IA, éviter automatisation excessive | 4/5 - important, doit être mesuré instruments validés | Mesure auto-rapportée biaisée |
| Émotion/régulation | États affectifs influencent engagement/action | Détecter décrochage, proposer changement rythme/modalité | 3/5 - pertinent mais inférences abusives | Surinterprétation émotionnelle intrusive |
| Échec couplage | Rupture intention-perception-décision-action-feedback | Détecter surcharge, désorientation, abandon, dépendance IA | 2/5 - très prometteur mais axe recherche à construire | Définir qualité couplage sans mesure validée |

**Référence Epsylon:** Thèse Thomas Camus (Brunel & Brouillet, Montpellier 3) montre action ne constitue pas seulement conséquence cognition : elle participe construction représentation cohérente interaction environnement [11](https://www.researchgate.net/publication/306026175_Assessing_the_Functional_Role_of_Motor_Response_During_the_Integration_Process).

---

## 3. Analyse détaillée par concept avec sources

### 3.1. Cognition incarnée

**Définition scientifique:** Cognition façonnée par structures corporelles et processus sensorimoteurs, pas seulement computation neurale. Quatre traditions partiellement recouvrantes : grounded/simulation-based, enactive/ecological, extended/embedded, pluralist [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full).

**Mécanismes (revue intégrative 2026):** 4 clusters [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full):
1. Représentation gestuelle (gesture-based representation)
2. Structuration perceptivo-spatiale
3. Offloading cognitif (décharge cognitive via outils)
4. Interaction sociale médiée

**Effets:** Méta-analyses récentes [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full)[2](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1658797/full):
- Liu et al. 2025, 46 études 66 effets, g=0.406 [0.264-0.548], p<0.001, hétérogénéité forte [2](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1658797/full)
- Frontiers Edu 2026, SMD=0.448 cognitif, 0.285 non-cognitif (attitudes/motivation) [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full)
- Effets plus grands : humanités > sciences, lycée > université, groupe petit > individuel, haut niveau incarnation > bas niveau, actif > passif, 1 trimestre > autres durées, N>50 [2](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1658797/full)

**Boundary conditions (crucial pour Cognitorium):** Bénéfices quand [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full):
- Alignement fonctionnel : activité corporelle alignée avec demande représentationnelle tâche
- Supplante plutôt que compose charge cognitive
- Clarté représentationnelle

Effets diminuent/inversent quand mal aligné ou complexité excessive.

**Solidité:** 4/5 - relativement bien documenté mais dépend fortement domaine.

**Gap:** Confusion incarnation décorative vs fonctionnelle. Une animation n'est pas automatiquement incarnée.

**Opérationnalisation:**
```
Concept: cognition incarnée
Mécanisme supposé: représentation gestuelle + structuration perceptivo-spatiale
Comportement observable: gestes qui externalisent pensée, révèlent stratégies implicites, restructurent raisonnement
Fonctionnalité Cognitorium: micro-situations où manipulation remplace difficulté abstraite (ex: réorganiser tâches sous contrainte temporelle pour priorisation)
Métrique: taux utilisation geste pertinent, rétention, transfert, charge perçue
Hypothèse testable: "Si manipulation fonctionnellement alignée avec concept (vs contrôle sans manipulation), alors rétention +20% et transfert +15% avec charge extrinsèque réduite (NASA-TLX)"
```

### 3.2. Cognition située / embedded

**Définition:** Cognition dépendante environnement, dépend de l'entourage. Savoir inséparable de faire, lié à activité située dans contextes sociaux/culturels/physiques [3](https://en.wikipedia.org/wiki/Situated_cognition).

**Intérêt Cognitorium:** Relier compétences à situations professionnelles réelles, pas objets statiques. Portfolio comme support.

**Solidité:** 4/5 - solide dans approches situées et écologiques.

**Gap:** Réduire contexte à décor.

**Opérationnalisation:**
```
Concept: situated/embedded
Mécanisme: attunement aux affordances pertinentes via éducation de l'attention
Comportement: sélection informations pertinentes selon intention
Fonctionnalité: projets réels, études de cas professionnelles, interactions sociales
Métrique: performance situation nouvelle vs labo, validité écologique
Hypothèse: "Si compétence enseignée en situation professionnelle réelle vs abstraite, alors transfert +25%"
```

### 3.3. Énactivisme

**Définition:** Sens émerge interaction dynamique organisme-environnement, cognition comme activité. Autopoïèse, couplage structurel.

**Exceptionnalité dans 4E:** Seul énactivisme autopoïétique rompt vraiment avec cognitivisme classique (représentationnalisme, computationnalisme, fonctionnalisme, internalisme, réalisme). Autres E compatibles cognitivisme amendé [14](https://link.springer.com/article/10.1007/s11097-025-10131-1). 4E reste hétérogène théoriquement, ne doit pas être amalgamé [15](https://www.researchgate.net/publication/341092559_Thinking_avant_la_lettre_A_Review_of_4E_Cognition)[13](https://www.researchgate.net/publication/399859423_Critical_4E_Cognitive_Science).

**Intérêt:** Organiser apprentissage autour boucles perception-action-feedback.

**Solidité:** 3/5 - théoriquement influent, difficile à tester directement.

**Gap 1 - Confusion incarnation/énactivisme (majeur):** Docs utilisent parfois "incarnée", "située", "4E", "énactivisme" comme synonymes. Or hiérarchie nécessaire:
- 4E: famille générale
- embodied: rôle corps
- embedded: rôle contexte
- enactive: cognition comme activité et émergence sens
- extended: participation artefacts

Carney souligne 4E reste hétérogène et composantes ne doivent pas être amalgamées [15](https://www.researchgate.net/publication/341092559_Thinking_avant_la_lettre_A_Review_of_4E_Cognition).

**À corriger Cognitorium:** Associer chaque fonctionnalité à mécanisme précis:
- simulation interactive: embodiment + enaction
- projet réel: embedded
- portfolio: externalisation ou extension
- IA accompagnement: support distribué, pas nécessairement cognition étendue

**Opérationnalisation:**
```
Concept: énactivisme
Mécanisme: couplage dynamique agent-environnement, émergence sens via interaction
Comportement: boucles perception-action-feedback avec ajustement
Fonctionnalité: situation → intention → action → conséquence → interprétation → nouvelle action (pas contenu→mémorisation→évaluation)
Métrique: qualité couplage C=f(I,P,A,F,R) (voir gap 4)
Hypothèse: "Si boucle action-conséquence-feedback immédiat vs explication préalable, alors engagement + transfert supérieurs"
```

### 3.4. Cognition étendue

**Définition:** Outils/artefacts participent système cognitif, pas seulement support causal (Clark & Chalmers parity principle). Débat frontière outil-système.

**Intérêt:** Portfolio, graphes, IA, documents comme supports cognitifs.

**Solidité:** 3/5 - conceptuellement fécond mais frontière débattue.

**Gap:** Risque anthropomorphisme "IA est agent cognitif". Reformuler "IA peut participer à système d'activité cognitive distribué".

**Opérationnalisation:**
```
Concept: extended
Mécanisme: offloading cognitif, externalisation
Comportement: utilisation artefact pour réduire charge, restructurer raisonnement
Fonctionnalité: portfolio contextuel longitudinal, graphes compétences contextualisés
Métrique: réduction charge perçue, rétention avec vs sans artefact
Hypothèse: "Si graphe compétences contextualisé vs liste niveaux, alors identification affordances +30%"
```

### 3.5. Affordance

**Définition Gibson:** Possibilités action offertes par environnement à organisme donné, dépend propriétés environnement + capacités utilisateur + intention + histoire + situation actuelle. Perception directe, pas médiatisée représentation [3](https://en.wikipedia.org/wiki/Situated_cognition). Concept développé vers socio-culturel, pratiques habiles [4](https://www.tandfonline.com/doi/full/10.1080/19415257.2024.2374340). Émergent dans relation agent-environnement orienté but, expertise liée à buts in-the-moment et environnements socio-culturels construits, noticing situé et embedded [4](https://www.tandfonline.com/doi/full/10.1080/19415257.2024.2374340). Éducation attention via comportement exploratoire, feedback, direction attention [4](https://www.tandfonline.com/doi/full/10.1080/19415257.2024.2374340).

**Intérêt:** Adapter actions proposées capacités/intentions/contexte apprenant. Très utile UX si pas réduit à simple bouton.

**Solidité:** 5/5.

**Gap:** Réduire affordance à fonctionnalité visible. Compétence ne doit pas être objet statique mais reliée à situations où devient actionnable.

**Exemple opérationnel:**
| Compétence abstraite | Affordance proposée | Situation apprentissage |
|----------------------|---------------------|-------------------------|
| Prioriser | Réorganiser tâches sous contrainte | Projet délai réduit |
| Déléguer | Choisir qui reçoit responsabilité | Équipe profils différents |
| Analyser | Identifier variables pertinentes | Étude cas professionnelle |
| Argumenter | Défendre décision face objections | Simulation entretien/réunion |

**Opérationnalisation:**
```
Concept: affordance
Mécanisme: perception possibilité action actualisée dans couplage dynamique agent-environnement
Comportement: identification et utilisation affordance pertinente
Fonctionnalité: actions disponibles selon contexte, pas toutes options tout le temps
Métrique: taux identification et utilisation, temps décision
Hypothèse: "Si affordances filtrées par intention déclarée vs toutes options visibles, alors temps tâche -20% et erreurs -15%"
```

### 3.6. ACT-IN (Versace, Brouillet, Brunel - Epsylon)

**Définition:** Expérience cognitive émerge activation et intégration traces sensorimotrices. Traces mnésiques se forment automatiquement via dynamique activations/intégrations différentes dimensions expérience, particulièrement sensorimotrices [9](https://www.researchgate.net/publication/352288191_When_the_Action_to_Be_Performed_at_the_Stage_of_Retrieval_Enacts_Memory_of_Action_Verbs)[10](https://www.researchgate.net/publication/343981301_Eye_movements_of_recent_and_remote_autobiographical_memories_fewer_and_longer_lasting_fixations_during_the_retrieval_of_childhood_memories). Lors seconde expérience, situation réactive en cascade traces antérieures, provoquant intégration dimensions situation présente et antérieures. Modèle sans représentations inspiré MINERVA2 mais prenant en compte apports ACT-IN, traces dans état réorganisation constante via activité et contraintes environnementales, modèle fractal garde trace processus antérieurs émergence connaissance [travaux Epsylon].

**Thèse Camus:** Action ne constitue pas seulement conséquence cognition : elle participe construction représentation cohérente interaction environnement. Intégration multimodale, anticipation conséquences désirées selon intentions, expérience action-effet contingencies établit durable event files intégrant représentations [11](https://www.researchgate.net/publication/306026175_Assessing_the_Functional_Role_of_Motor_Response_During_the_Integration_Process).

**Intérêt:** Exploiter trajectoires apprentissage, hésitations, retours, rythmes, stratégies récurrentes. Pertinent pour modèle traces.

**Solidité:** 3/5 - nécessite validation spécifique.

**Gap 3 - Modèle ACT-IN insuffisamment opérationnalisé:** Docs proposent capturer séquences actions, hésitations, retours, rythmes, stratégies. Mais distinguer:
- trace comportementale (clics, temps réponse)
- trace cognitive interprétée
- trace sensorimotrice sens fort (nécessite données corporelles/gestuelles)

Clics et temps réponse = comportement numérique, pas inférence directe expérience incarnée ou schème cognitif.

**Recommandation MVP:** Parler "traces d'activité" puis réserver "traces sensorimotrices" aux situations où données corporelles/gestuelles effectivement recueillies. Inspirer système réactivation sous forme hypothèse: "Lors activité comparable, vous aviez utilisé cette stratégie. Voulez-vous l'examiner ?" Éviter déterministe "Vous êtes profil visuel" / "Vous apprenez mieux par mouvement" (trop fort).

**Opérationnalisation:**
```
Concept: ACT-IN
Mécanisme: activation-intégration traces multimodales, réorganisation constante
Comportement: séquences actions, hésitations, retours arrière, rythmes, stratégies récurrentes
Fonctionnalité: graphe trajectoires, rappel stratégie antérieure comme hypothèse
Métrique: similarité trajectoires, stabilité stratégie, transfert
Hypothèse: "Si rappel stratégie antérieure proposée comme hypothèse vs imposée, alors agence préservée et transfert +15%"
```

### 3.7. Charge cognitive (Tricot, Sweller)

**Définition:** Difficulté dépend tâche, support, connaissances apprenant. Distinction classique [5](https://www.researchgate.net/publication/331280470_The_Evolution_of_Cognitive_Load_Theory_and_the_Measurement_of_Its_Intrinsic_Extraneous_and_Germane_Loads_A_Review):
- intrinsèque: complexité contenu
- extrinsèque: mauvaise conception tâche/support
- essentielle/germane: construction/transformation connaissances (redistributive, pas load additionnel) [5](https://www.researchgate.net/publication/331280470_The_Evolution_of_Cognitive_Load_Theory_and_the_Measurement_of_Its_Intrinsic_Extraneous_and_Germane_Loads_A_Review)

Tricot souligne interface/document mal conçu impose efforts inutiles (intégrer infos dispersées/redondantes).

**Mesure différenciée:** Questionnaire différenciant ICL, ECL, GCL validité pronostique bonne [6](https://link.springer.com/article/10.1007/s11251-020-09502-9). Unidimensionnel effort mental Paas valide si ICL constant [5](https://www.researchgate.net/publication/331280470_The_Evolution_of_Cognitive_Load_Theory_and_the_Measurement_of_Its_Intrinsic_Extraneous_and_Germane_Loads_A_Review).

**Intérêt:** Éviter interface/IA ajoute complexité inutile. Très bien documenté empiriquement.

**Solidité:** 5/5.

**Gap - Correction formulation importante:** Objectif n'est pas réduire systématiquement charge cognitive. Il faut réduire charge extrinsèque inutile tout en maintenant charge nécessaire apprentissage.

**Pour Cognitorium:**
- Ne pas multiplier animations simplement parce qu'elles sont "incarnées"
- Éviter interfaces trop riches graphes/couleurs/panneaux
- Ne pas demander manipuler objet lorsque manipulation n'aide pas réellement concept
- Adapter guidage à expertise
- Distinguer exploration, entraînement, évaluation

Activité corporelle pertinente si remplace difficulté abstraite par expérience fonctionnelle, pas si ajoute tâche motrice supplémentaire. Renforcé par revue intégrative récente: approches incarnées effets plutôt positifs mais hétérogènes, bénéfices diminuent quand activité corporelle mal alignée ou augmente complexité [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full).

**Opérationnalisation:**
```
Concept: charge cognitive
Mécanisme: ICL (complexité contenu + expertise), ECL (design), GCL (ressources allouées ICL)
Comportement: temps tâche, erreurs, charge perçue (NASA-TLX ou Leppink)
Fonctionnalité: réduction éléments superflus, segmentation, scaffolding, exemples travaillés
Métrique: ECL perçu (questionnaire différencié), performance, satisfaction
Hypothèse: "Si interface épurée (ECL bas) vs riche (ECL haut) pour même contenu, alors performance +20% et satisfaction +15%, sans réduire GCL"
```

### 3.8. Agence

**Définition:** Sentiment apprenant est auteur décisions/actions, initiateur actions et influence environnement. Aspect fondamental monitoring action, reconnaissance soi, distinction actions propres vs événements externes.

**Mesure validée:** Sense of Agency Scale (SoAS) 2 facteurs: SoPA (positive agency) et SoNA (negative) [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539649/)[8](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1696418/full). Validations allemande, turque, italienne, japonaise avec CFA, excellents fit indices. Corrélations: locus contrôle interne r=0.44 SoPA, -0.32 SoNA; self-efficacy r=0.32/-0.32; free will r=0.31/-0.42 [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539649/).

**Intérêt:** Maintenir contrôle humain face IA, éviter automatisation excessive.

**Solidité:** 4/5 - important mais doit être mesuré instruments validés.

**Gap:** Mesure auto-rapportée biaisée, besoin triangulation comportementale.

**Opérationnalisation:**
```
Concept: agence
Mécanisme: attribution action à soi, contrôle perçu
Comportement: choix explicite intention, confirmation, contrôle humain
Fonctionnalité: IA ne supprime pas alternatives, rend visibles options et conséquences, confirmation choix
Métrique: SoAS (SoPA/SoNA), taux choix autonome vs suggestion IA, temps correction
Hypothèse: "Si choix intention explicite avant action vs IA impose action, alors SoPA +0.5 SD et rétention +15%"
```

### 3.9. Émotion et régulation

**Définition:** États affectifs influencent engagement/action, mais émotion déclarée ≠ cause échec, baisse interaction ≠ désengagement, adaptation algo peut renforcer biais, analyse émotionnelle intrusive, inférences physiologiques nécessitent consentement explicite.

**Intérêt:** Détecter décrochage, proposer changement rythme/modalité.

**Solidité:** 3/5 - pertinent mais attention inférences abusives.

**Gap 5 - Risque surinterprétation émotionnelle:**
- Émotion déclarée pas nécessairement cause échec
- Baisse interaction pas forcément désengagement
- Adaptation algo renforce biais
- Analyse émotionnelle intrusive
- Inférences physiologiques consentement explicite

**MVP recommandation:** Privilégier auto-évaluation volontaire, question courte après activité, possibilité corriger interprétation système, aucune décision importante fondée sur inférence émotionnelle seule.

**Opérationnalisation:**
```
Concept: émotion/régulation
Mécanisme: valence, activation influencent engagement
Comportement: auto-évaluation volontaire, signaux compatibles difficulté/baisse engagement
Fonctionnalité: question courte après activité "Comment vous sentez-vous ?", proposition changement rythme
Métrique: valence auto-rapportée, taux acceptation changement, pas inférence automatique
Hypothèse: "Si proposition changement rythme basée sur auto-évaluation vs inférence automatique, alors acceptation +30% et pas de sentiment intrusion"
```

### 3.10. Échec du couplage

**Définition:** Rupture intention-perception-décision-action-feedback. Très prometteur mais axe recherche à construire.

**Gap 4 - Mesure couplage vague:** Proposé mesurer "qualité couplage" mais doit être défini. Modélisation possible comme coordination entre:
- intention déclarée
- perception infos pertinentes
- sélection action
- exécution
- interprétation feedback
- capacité ajuster action suivante

Indicateur composite exploratoire:
```
C = f(I,P,A,F,R)
I = clarté intention
P = pertinence perception
A = adéquation action
F = compréhension feedback
R = récupération après erreur
```

Pas mesure psychologique validée, instrument prototype à comparer à mesures existantes: performance, charge perçue, engagement, sentiment agence, transfert.

**Opérationnalisation:**
```
Concept: échec couplage
Mécanisme: rupture boucle
Comportement: erreurs répétées, abandons, surcharge apparente, dépendance excessive IA
Fonctionnalité: détection simple ruptures, feedback explicatif lié décision
Métrique: temps correction, erreurs répétées, taux abandon, C composite
Hypothèse: "Si feedback immédiat lié action vs différé générique, alors temps correction -30% et R (récupération) +20%"
```

---

## 4. Gaps transversaux identifiés

### Gap 1 - Confusion incarnation/énactivisme (déjà détaillé 3.3)
**Source:** Carney review [15](https://www.researchgate.net/publication/341092559_Thinking_avant_la_lettre_A_Review_of_4E_Cognition) + Exceptionality enactivism [14](https://link.springer.com/article/10.1007/s11097-025-10131-1) + Critical 4E [13](https://www.researchgate.net/publication/399859423_Critical_4E_Cognitive_Science)

**Correction:** Hiérarchie 4E famille générale, associer chaque fonctionnalité à mécanisme précis.

### Gap 2 - Passage trop rapide théorie → design
Docs passent directement de concepts "autonomie, couplage, re-enactment" à fonctionnalités animations, feedback haptique, graphes, adaptation algo, capture émotionnelle. Interface animée ≠ automatiquement énactive. Trace utilisation ≠ trace sensorimotrice. Graphe compétences ≠ automatiquement extension cognitive.

**Correction:** Documenter chaîne transformation:
```
concept théorique → mécanisme cognitif → comportement observable → fonctionnalité → métrique → hypothèse testable
```
Exemple tableau déjà en 3.5.

### Gap 3 - ACT-IN insuffisamment opérationnalisé (3.6)

### Gap 4 - Mesure couplage vague (3.10)

### Gap 5 - Risque surinterprétation émotionnelle (3.9)

### Gaps supplémentaires transversaux (issus cartographie 12 domaines)

- **Faible représentation pays non occidentaux, diversité linguistique/culturelle**
- **Sous-représentation adultes âgés**
- **Peu recherches longitudinales, peu large échantillon**
- **Faible articulation comportemental-cognitif-neuronal**
- **Peu mesures écologiques contexte réel, forte dépendance auto-questionnaires**
- **Manque réplications directes, faible comparaison interventions actives**
- **Intégration limitée IA, données passives, environnements numériques**
- **Distinction corrélationnel/causal/prédictif/applicable non faite** - association trait cognitif-réussite scolaire ne justifie pas recommandation individuelle

---

## 5. Ce qu'il faut retirer ou reformuler

| Formulation actuelle | Problème | Reformulation recommandée |
|----------------------|----------|---------------------------|
| "L'énactivisme est un pilier central du paradigme dominant" | Trop fort | "L'énactivisme est une tradition importante du débat 4E" [14](https://link.springer.com/article/10.1007/s11097-025-10131-1) |
| "La cognition n'est pas une représentation interne" | Valable certaines versions radicales, pas toutes | "Certaines versions de l'énactivisme critiquent fortement le rôle central des représentations internes" [14](https://link.springer.com/article/10.1007/s11097-025-10131-1) |
| "Le feedback haptique soutient l'énactivisme" | Lien pas automatique | "Un feedback sensorimoteur peut soutenir une boucle perception-action lorsqu'il est fonctionnellement pertinent" [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full) |
| "L'émotion organise la neuroplasticité" | Général et insuffisamment étayé | "Les états affectifs peuvent influencer l'engagement, l'apprentissage et la régulation" |
| "L'IA est un agent cognitif" | Anthropomorphisme | "L'IA peut participer à un système d'activité cognitive distribué" |
| "Détecter la fatigue" | Inférence non valide | "Repérer des signaux compatibles avec une difficulté ou une baisse d'engagement" |
| "Les compétences émergent des traces" | Traces = indices, pas compétence elle-même | "Les traces peuvent contribuer à documenter la construction et la mobilisation des compétences" [9](https://www.researchgate.net/publication/352288191_When_the_Action_to_Be_Performed_at_the_Stage_of_Retrieval_Enacts_Memory_of_Action_Verbs) |
| "Le système construit le monde de sens de l'apprenant" | Constructivisme excessif | "Le système soutient l'exploration et l'interprétation personnelle de situations significatives" |

---

## 6. Modèle cible pour Cognitorium (6 couches)

Recommandation structurer Cognitorium autour modèle 6 couches (issu paste.txt, enrichi sources):

### Couche 1 - Situation
Contexte: projet, problème, interaction sociale, simulation professionnelle, orientation, tâche métier/compétence.
**Source:** Situated cognition [3](https://en.wikipedia.org/wiki/Situated_cognition), affordance [4](https://www.tandfonline.com/doi/full/10.1080/19415257.2024.2374340), routines spatio-temporelles Pascucci 2026.

### Couche 2 - Intention
Apprenant indique ce qu'il cherche à faire: comprendre, explorer, décider, s'entraîner, produire, vérifier, transférer. Important pour agence.
**Source:** SoAS validation [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539649/), attention intention [3](https://en.wikipedia.org/wiki/Situated_cognition).

### Couche 3 - Affordances
Système propose plusieurs possibilités action: consulter ressource, modifier hypothèse, comparer stratégies, demander aide, agir directement, observer exemple, collaborer. IA ne doit pas supprimer alternatives: rendre visibles options et conséquences possibles.
**Source:** Affordance Gibson, effectivities [3](https://en.wikipedia.org/wiki/Situated_cognition), perception affordances ecological-enactive [4](https://www.tandfonline.com/doi/full/10.1080/19415257.2024.2374340).

### Couche 4 - Action
Micro-tâche observable: classer, argumenter, planifier, diagnostiquer, simuler, concevoir, expliquer, choisir compromis.
**Source:** Camus et al. 2016-2017 rôle fonctionnel action [11](https://www.researchgate.net/publication/306026175_Assessing_the_Functional_Role_of_Motor_Response_During_the_Integration_Process), ACT-IN [9](https://www.researchgate.net/publication/352288191_When_the_Action_to_Be_Performed_at_the_Stage_of_Retrieval_Enacts_Memory_of_Action_Verbs).

### Couche 5 - Feedback
Retour doit être: immédiat si correction rapide nécessaire, différé si réflexion, explicatif plutôt que simplement évaluatif, relié décision prise, proportionné niveau expertise.
**Source:** Charge cognitive feedback [5](https://www.researchgate.net/publication/331280470_The_Evolution_of_Cognitive_Load_Theory_and_the_Measurement_of_Its_Intrinsic_Extraneous_and_Germane_Loads_A_Review), couplage [11](https://www.researchgate.net/publication/306026175_Assessing_the_Functional_Role_of_Motor_Response_During_the_Integration_Process).

### Couche 6 - Réflexivité et transfert
Apprenant examine: ce qu'il a fait, pourquoi, ce qui a fonctionné/échoué, ce qu'il changerait, dans quelle autre situation réutiliser stratégie. Articulation énactivisme et métacognition sans confondre.
**Source:** Embodied mechanisms [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full), fluence métacognitive.

**Architecture fonctionnelle proposée:** Graphe compétences doit être contextuel et longitudinal. Pas "maîtrise gestion projet: niveau 3" mais "mobilise priorisation dans situation projet simulée, avec contrainte temporelle, en autonomie partielle". Distinguer connaissance déclarative, stratégie, performance, niveau aide, contexte, transfert.

---

## 7. Priorités MVP

| Priorité | Fonctionnalité | Justification | Source |
|----------|----------------|---------------|--------|
| 1 | Modules fondés micro-situations | Teste apprentissage par action | Situated cognition [3](https://en.wikipedia.org/wiki/Situated_cognition), Pascucci routines |
| 2 | Choix explicite intention | Soutient agence et personnalisation | SoAS [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539649/) |
| 3 | Boucle action-feedback | Cœur opérationnel modèle | Camus et al. [11](https://www.researchgate.net/publication/306026175_Assessing_the_Functional_Role_of_Motor_Response_During_the_Integration_Process), ACT-IN [9](https://www.researchgate.net/publication/352288191_When_the_Action_to_Be_Performed_at_the_Stage_of_Retrieval_Enacts_Memory_of_Action_Verbs) |
| 4 | Traces d'activité interprétables | Documente stratégies sans surinterprétation | ACT-IN, gap 3 |
| 5 | Réflexion métacognitive courte | Relie expérience, apprentissage, orientation | Fluence, métacognition |
| 6 | Transfert plusieurs contextes | Teste si compétence dépasse situation initiale | Embodied boundary conditions [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full) |
| 7 | IA comme aide optionnelle | Évite dépendance et préserve contrôle humain | Extended cognition critique [14](https://link.springer.com/article/10.1007/s11097-025-10131-1) |
| 8 | Détection simple ruptures | Identifie erreurs répétées, abandons, surcharge apparente | Échec couplage C=f(I,P,A,F,R) |

**À repousser après validation modèle base:** Fonctions haptiques, physiologiques, émotionnelles, immersives. Coûteuses et risquent incarnation décorative sans bénéfice pédagogique démontré [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full).

---

## 8. Conclusion scientifique + Gap stratégique

Le potentiel Cognitorium ne réside pas dans ajout gestes, animations ou IA conversationnelle. Il réside dans conception système où:

- compétences liées à situations
- apprenant agit avant recevoir explication complète
- actions ont conséquences perceptibles
- feedback modifie situation suivante
- traces décrivent trajectoires plutôt que scores isolés
- IA soutient réflexion sans confisquer décision
- réussite évaluée par transfert pas seule interaction interface

**Gap le plus stratégique à traiter:**

> Comment transformer notions d'affordance, de couplage, d'agence et d'émergence en indicateurs observables permettant de démontrer qu'un dispositif énactif améliore réellement l'apprentissage, le transfert et l'orientation professionnelle ?

Littérature actuelle confirme pertinence générale approches incarnées (g=0.406 [2](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1658797/full), SMD 0.448 [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full)) mais souligne aussi hétérogénéité et nécessité préciser quel mécanisme agit, pour quel apprenant, dans quel contexte et avec quelle charge cognitive [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full). Pour Cognitorium, cette exigence doit devenir principe directeur architecture scientifique et produit.

---

## 9. Références (pour ce document)

- Kougioumtzis K (2026). Embodied cognition in STEM learning: integrative review. Front Educ. [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full) - 4 traditions, 4 mécanismes, SMD 0.448, alignement fonctionnel, supplanter pas composer charge
- Liu et al. (2025). Effect of embodied learning on performance: meta-analysis g=0.406. Front Psychol. [2](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1658797/full) - 46 études, modérateurs discipline, niveau, période, N, approche, niveau incarnation, type
- Situated cognition - Wikipedia - affordance, effectivities, attunement, community practice [3](https://en.wikipedia.org/wiki/Situated_cognition)
- Ecological-enactive model teacher noticing - affordance perception 2024 [4](https://www.tandfonline.com/doi/full/10.1080/19415257.2024.2374340) - affordance relationnelle, éducation attention
- Sweller et al. Evolution Cognitive Load Theory [5](https://www.researchgate.net/publication/331280470_The_Evolution_of_Cognitive_Load_Theory_and_the_Measurement_of_Its_Intrinsic_Extraneous_and_Germane_Loads_A_Review) - ICL, ECL, GCL redistributive
- Differentiated measurement cognitive load - Klepsch et al. 2020 [6](https://link.springer.com/article/10.1007/s11251-020-09502-9) - validité pronostique questionnaire ICL/ECL/GCL
- Sense of Agency Scale validation German [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539649/) - SoPA/SoNA, locus contrôle, self-efficacy, free will
- Sense of Agency Turkish validation [8](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1696418/full) - 2 facteurs, CFA excellent fit
- ACT-IN - Brouillet et al. action enacts memory action verbs [9](https://www.researchgate.net/publication/352288191_When_the_Action_to_Be_Performed_at_the_Stage_of_Retrieval_Enacts_Memory_of_Action_Verbs) - traces multisensorielles distribuées, couplage sensorimoteur présent-passé
- Eye movements autobiographical memories - ACT-IN traces [10](https://www.researchgate.net/publication/343981301_Eye_movements_of_recent_and_remote_autobiographical_memories_fewer_and_longer_lasting_fixations_during_the_retrieval_of_childhood_memories) - traces overlap, discrimination
- Camus, Brouillet, Brunel (2016). Functional role motor response integration [11](https://www.researchgate.net/publication/306026175_Assessing_the_Functional_Role_of_Motor_Response_During_the_Integration_Process) - Epsylon Montpellier, 3 expériences, multimodal traces
- Thèse affordance schizophrénie - HAL tel-00981433 [12](https://theses.hal.science/tel-00981433v1/document) - SRC paradigm, compatibilité sensorimotrice, enrichissement situation
- Critical 4E Cognitive Science 2026 [13](https://www.researchgate.net/publication/399859423_Critical_4E_Cognitive_Science) - family resemblance, historical influence, upside/downside agent-environment
- Exceptionality of enactivism within 4E - Springer 2026 [14](https://link.springer.com/article/10.1007/s11097-025-10131-1) - seul autopoïétique rompt vraiment avec cognitivisme classique
- Carney - Thinking avant la lettre: Review 4E Cognition 2020 [15](https://www.researchgate.net/publication/341092559_Thinking_avant_la_lettre_A_Review_of_4E_Cognition) - critique rigueur argumentative, 4E manque évaluation critique

---

## 10. Prochaines étapes

1. **Opérationnaliser** chaque concept en chaîne `concept → mécanisme → comportement → fonctionnalité → métrique → hypothèse` (table section 3)
2. **Implémenter MVP 8 priorités** (section 7) avec mesures charge différenciée [6](https://link.springer.com/article/10.1007/s11251-020-09502-9), SoAS [7](https://pmc.ncbi.nlm.nih.gov/articles/PMC10539649/), traces activité
3. **Préenregistrer** sur OSF protocole testant alignement fonctionnel [1](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2026.1811569/full): manipulation incarnée fonctionnelle vs décorative
4. **Éviter** formulations excessives (table section 5)
5. **Mesurer** C = f(I,P,A,F,R) comme instrument prototype, comparer à performance, charge perçue, engagement, agence, transfert

**Fin analyse concepts - 1.0**
