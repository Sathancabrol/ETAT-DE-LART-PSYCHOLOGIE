# Classification par Méthode Scientifique - État de l'Art Psychologie Cognitive

## 1. Taxonomie de la Méthode Scientifique appliquée

Ce document organise l'état de l'art non seulement par **domaine** (mémoire, attention, 4E, fluence) mais par **niveau de méthode scientifique**, pour évaluer la robustesse et la transférabilité.

### A. Pyramide des preuves (adaptée de la médecine à la psychologie cognitive)

```
Niveau 1 - Théorique / Philosophique
  └─ Argument conceptuel, cohérence interne, critique épistémologique
  └─ Ex: Exceptionality of enactivism (2026), Fuchs (2026)

Niveau 2 - Observationnel / Corrélationnel
  └─ Corrélations individuelles, différences interindividuelles
  └─ Ex: Études WMC-gF corrélées

Niveau 3 - Expérimental contrôlé (Labo)
  └─ Randomisation, contrôle, manipulation causale, psychophysique
  └─ Ex: Tünçok et al. 2025 (pRF + cueing), Knight et al. 2025 (crossmodal fluency)

Niveau 4 - Neuroimagerie / Physiologie
  └─ fMRI, EEG, single-unit, décodage
  └─ Ex: Ben Hamed 2025 (décodage préfrontal temps réel)

Niveau 5 - Revue narrative / Perspective
  └─ Synthèse qualitative, intégration multi-études, cadre théorique
  └─ Ex: Rosen & Freedman 2025, Pascucci & Kristjánsson 2026

Niveau 6 - Revue systématique / Méta-analyse
  └─ Procédure systématique, évaluation biais, effet quantifié
  └─ Ex: Lee & Engle 2026 (6 domaines), Frontiers in Education 2026 (SMD=0.448)

Niveau 7 - Pré-enregistrement / Réplication / Open Science
  └─ Protocole pré-enregistré, données ouvertes, réplication multi-labos
  └─ Standard émergent, peu présent dans corpus actuel
```

### B. Dimensions de Validité (Cook & Campbell)

| Type de Validité | Question | Exemple dans corpus |
|------------------|----------|---------------------|
| **Interne** | L'effet est-il causal ? Contrôles suffisants ? | Tünçok 2025: baseline shift contrôlé, randomisation cue |
| **De Construit** | Mesure-t-on bien ce qu'on prétend ? | Huang 2025 critique n-back: validité faible, stratégies confondues |
| **Externe** | Généralisable à d'autres populations/tâches ? | 4E STEM review: hétérogénéité, modérateurs âge/domaine |
| **Écologique** | Transférable au monde réel ? | Fuchs 2026 + Pascucci 2026: plaident pour contextes riches, pas stimuli isolés |
| **Statistique** | Puissance, p-hacking, robustesse ? | Lee & Engle 2026: modélisation latente réduit erreur mesure |

### C. Cycle Hypothético-Déductif (Popper) appliqué

```
1. Théorie → 2. Hypothèse falsifiable → 3. Opérationnalisation → 4. Design → 5. Collecte → 6. Analyse → 7. Falsification/Corroboration → 8. Révision théorie

Placement des références:

[1 Théorie]: Fuchs 2026 (énactive), Exceptionality of enactivism 2026
[2 Hypothèse]: "Si AC est mécanisme sous-jacent, alors AC médie WMC-gF" (Lee & Engle 2026)
[3 Opérationnalisation]: Tâches AC pures (antisaccade, Stroop, flanker) vs span complexes
[4 Design]: Tünçok 2025: design cueing spatial covert avec baseline pre-target
[5 Collecte]: Ben Hamed 2025: enregistrement préfrontal singe/humain temps réel
[6 Analyse]: Modélisation pRF, décodage MVPA, modèles variables latentes
[7 Falsification]: Huang 2025: falsifie validité n-back; Chen & Yan 2025: pas de consensus transfert lointain → falsifie entraînement naïf
[8 Révision]: Lee & Engle proposent de renommer "WMC" en "AC" pour cohérence; 4E inclusive propose révision cadre
```

### D. Matrice Méthode x Domaine

| Domaine | Théorique | Corrélationnel | Expérimental | Neuroimagerie | Revue systématique | Méta-analyse |
|---------|-----------|----------------|--------------|---------------|-------------------|--------------|
| Mémoire & AC | | X (WMC-gF) | X (Draheim) | | X (Lee & Engle) | X (latente) |
| Cognition distribuée | | | | X (Rosen) | X (Perspective) | |
| n-back | X | | X | | X (Huang) | |
| Entraînement | | | X (mixte) | X (animal) | X (Chen & Yan) | |
| 4E incarnée | X (Fuchs) | | X (STEM) | | X (Frontiers Edu) | X (SMD .448) |
| Attention spatiale | | | X (Tünçok) | X (7T fMRI) | | |
| Attention spatiale décodage | | | X | X (prefrontal) | X (Ben Hamed) | |
| Attention temporelle | X (Nobre) | | X (Tian) | X (EEG alpha) | X (Denison 2024) | |
| Fluence | X (Alter) | | X (Knight) | | X (Alter 2009) | |

### E. Critères Open Science (évaluation)

- **Pré-enregistrement**: Aucune des références 2025-2026 ne mentionne explicitement pré-reg (limite). Tian et al. 2026 bioRxiv: non.
- **Open Access**: Toutes sélectionnées OA (critère inclusion)
- **Open Data/Code**: Tünçok et al. 2025 (Nature Comms) → données pRF partagées; Ben Hamed 2025 → méthodes décodage partagées
- **Réplication**: Lee & Engle synthétise réplications multi-labos; fluence: effet répliqué multi-manipulations (Alter 2009)
- **Hétérogénéité**: Frontiers Edu 2026 insiste: effets modérés mais hétérogènes → besoin modérateurs

## 2. Implications pour Cognitorium

**Si tu veux robustesse scientifique maximale** → privilégie:
- Lee & Engle 2026 (revue systématique 6 domaines, modélisation latente)
- Tünçok et al. 2025 (expé + neuroimagerie contrôlée)
- Frontiers Edu 2026 (revue intégrative + méta-analyse)

**Si tu veux innovation théorique radicale** → privilégie:
- Fuchs 2026 + Exceptionality of enactivism 2026 (rupture épistémologique)
- Pascucci & Kristjánsson 2026 (changement paradigme vers routines spatio-temporelles)

**Si tu veux transférabilité design UX**:
- Attention spatiale: utiliser pré-cues, baseline shift = montrer repères avant contenu
- Attention temporelle: rythmes, hazard rates, séquences prédictibles
- Fluence: parcours fluide = jugement positif, mais introduire disfluence volontaire pour pensée analytique
- 4E: alignement fonctionnel geste-contenu, offloading cognitif via outils

## 3. Prochaine étape méthodologique recommandée

1. Pré-enregistrer une expérience combinant: manipulation attention spatiale (Tünçok) + temporelle (Tian) + mesure fluence (Knight) sur tâche orientation Cognitorium
2. Mesures: comportement (RT, précision) + subjectif (fluence perçue) + oculométrie (décodage attention Ben Hamed)
3. Analyse: modèle latent AC (Lee & Engle) pour dissocier stockage vs contrôle
4. Open: données + code pRF + pré-reg OSF
