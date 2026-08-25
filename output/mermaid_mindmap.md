# Mindmap - État de l'Art Psychologie Cognitive (2025-2026) - Classé par Méthode Scientifique

## Version 1: Mindmap Domaines + Méthodes

```mermaid
mindmap
  root((Psychologie Cognitive<br/>État de l'Art 2025-26))
    Mémoire & Contrôle Attentionnel
      Contrôle Attentionnel [Revue Systématique]
        Lee & Engle 2026
        Mécanismes: maintien but, suppression interférence, désengagement
        Méthode: variables latentes, 6 domaines
        Preuve: Élevée
      Cognition Distribuée [Perspective]
        Rosen & Freedman 2025
        Méthode: neurophysiologie + fMRI
        Validité: interne modérée, externe élevée
      Tâche n-back [Critique de paradigme]
        Huang et al. 2025
        Méthode: analyse validité construit
        Résultat: validité faible, stratégies confondues
    Entraînement & Plasticité
      Transfert [Revue + modèles animaux]
        Chen & Yan 2025
        Méthode: intégration inter-espèces
        Preuve: Modérée, hétérogène
        Médiateur: schémas neuronaux abstraits
    Cognition 4E
      Incarnée / Énactive [Théorique]
        Fuchs 2026
        Méthode: phénoménologie + argument conceptuel
        Thèse: concepts = engagement corps-monde
        Validité écologique: Élevée
      4E STEM [Revue + Méta-analyse]
        Frontiers Edu 2026
        Méthode: revue de revues + méta SMD=0.448
        Mécanismes: geste, structuration spatiale, offloading, interaction sociale
        Modérateurs: âge, domaine, alignement fonctionnel
      Statut Énactivisme [Philosophique]
        Exceptionality 2026
        Méthode: analyse épistémologique
        Thèse: seul autopoïétique rompt vraiment
    Attention Spatiale
      Covert + Cortex Visuel [Expérimental + Neuroimagerie]
        Tünçok, Carrasco & Winawer 2025
        Méthode: psychophysique + fMRI 7T + pRF
        Mécanismes: baseline shift + shift pRF
        Validité interne: Élevée
      Décodage Temps Réel [Revue neuro]
        Ben Hamed 2025 Annual Rev Vision Sci
        Méthode: décodage préfrontal temps réel
        Résultat: attention décodable, rythmique, suppression proactive/réactive
      Routines Spatio-temporelles [Perspective]
        Pascucci & Kristjánsson 2026 Nat Rev Psychol
        Méthode: intégration vision/attention/mémoire/décision
        Thèse: contexte spatio-temporel au coeur
    Attention Temporelle
      Volontaire [Préprint Expérimental]
        Tian, Motzer & Denison 2026 bioRxiv
        Méthode: psychophysique compétition vs non
        Résultat: facilitation pré-compétitive
        Preuve: Faible-Modérée (préprint)
      Structures Temporelles [Revue fondatrice]
        Nobre & Denison 2017-2024
        Méthode: revue + modèles computationnels
        Types: cues, hazard rates, rythmes, séquences
    Fluence
      Tribes of Fluency [Revue fondatrice]
        Alter & Oppenheimer 2009
        Méthode: revue systématique multi-paradigmes
        Thèse: fluence = indice métacognitif ubiquitaire
        Validité: Élevée (multi-manipulations)
      Fluence Crossmodal [Expérimental]
        Knight et al. 2025
        Méthode: audio-visuel crossmodal + décalage temporel
        Résultat: transfert affectif crossmodal, intégration
```

## Version 2: Flowchart Méthode Scientifique

```mermaid
flowchart TD
    A[Théorie] --> B[Hypothèse Falsifiable]
    B --> C[Opérationnalisation]
    C --> D[Design Expérimental]
    D --> E[Collecte Données]
    E --> F[Analyse]
    F --> G[Falsification / Corroboration]
    G --> H[Révision Théorique]
    H --> A

    A1[Fuchs 2026<br/>Enactivisme<br/>Exceptionality 2026] --> A
    B1[Lee & Engle 2026<br/>Si AC mécanisme, alors médiation WMC-gF] --> B
    C1[Antisaccade, Stroop<br/>vs Span complexe] --> C
    D1[Tünçok 2025<br/>Cueing covert + baseline pre-target] --> D
    E1[Ben Hamed 2025<br/>Enregistrement préfrontal temps réel] --> E
    F1[Modélisation pRF<br/>MVPA<br/>Variables latentes] --> F
    G1[Huang 2025 falsifie n-back<br/>Chen & Yan 2025 pas consensus transfert] --> G
    H1[Renommer WMC->AC<br/>4E inclusive] --> H

    style A1 fill:#f9f,stroke:#333
    style D1 fill:#bbf,stroke:#333
    style E1 fill:#bfb,stroke:#333
    style G1 fill:#fbb,stroke:#333
```

## Version 3: Matrice Méthode x Validité

```mermaid
quadrantChart
    title Pyramide Preuves vs Validité Écologique
    x-axis Faible Validité Écologique --> Forte Validité Écologique
    y-axis Faible Niveau Preuve --> Fort Niveau Preuve
    quadrant-1 Innovations théoriques
    quadrant-2 Gold standard transférable
    quadrant-3 Émergent à confirmer
    quadrant-4 Labo robuste mais artificiel
    "Fuchs 2026 Théorique": [0.85, 0.25]
    "Exceptionality 2026": [0.75, 0.2]
    "Tian 2026 Préprint": [0.3, 0.35]
    "Knight 2025 Expé": [0.35, 0.65]
    "Tünçok 2025 fMRI": [0.25, 0.85]
    "Ben Hamed 2025 Neuro": [0.3, 0.8]
    "Rosen 2025 Perspective": [0.6, 0.7]
    "Lee & Engle 2026 Revue syst": [0.55, 0.9]
    "Frontiers Edu 2026 Méta": [0.7, 0.85]
    "Alter 2009 Revue fondatrice": [0.65, 0.9]
    "Pascucci 2026 Routines": [0.9, 0.65]
```

## Version 4: Graphique Domaine -> Méthode -> Implication Design

```mermaid
graph LR
    subgraph Domaines
        A1[Mémoire & AC]
        A2[4E Incarnée]
        A3[Attention Spatiale]
        A4[Attention Temporelle]
        A5[Fluence]
    end

    subgraph Méthodes
        M1[Théorique]
        M2[Expérimental Contrôlé]
        M3[Neuroimagerie 7T/EEG]
        M4[Revue Systématique]
        M5[Méta-analyse]
    end

    subgraph Implications Cognitorium
        I1[Mesurer AC pas stockage]
        I2[Design geste-contenu aligné]
        I3[Pré-cues spatiaux]
        I4[Ryhtmes & hazard rates]
        I5[Parcours fluide + disfluence utile]
    end

    A1 --> M4 --> I1
    A1 --> M2 --> I1
    A2 --> M1 --> I2
    A2 --> M5 --> I2
    A3 --> M3 --> I3
    A3 --> M2 --> I3
    A4 --> M2 --> I4
    A4 --> M4 --> I4
    A5 --> M4 --> I5
    A5 --> M2 --> I5

    style M4 fill:#ffd700,stroke:#333
    style M5 fill:#ffd700,stroke:#333
    style M2 fill:#87ceeb,stroke:#333
    style M3 fill:#98fb98,stroke:#333
```
