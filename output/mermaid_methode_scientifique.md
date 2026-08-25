# Diagrammes Méthode Scientifique - Supplément

## Diagramme 1: Classification par Type de Preuve + Domaine (Sankey-like via flowchart)

```mermaid
flowchart TD
    subgraph Preuves["Pyramide des Preuves"]
        P1[Théorique]
        P2[Corrélationnel]
        P3[Expérimental Contrôlé]
        P4[Neuroimagerie]
        P5[Revue Narrative/Perspective]
        P6[Revue Systématique]
        P7[Méta-analyse]
    end

    subgraph Domaines["Domaines Psychologie Cognitive"]
        D1[Mémoire & AC]
        D2[4E Enaction]
        D3[Attention Spatiale]
        D4[Attention Temporelle]
        D5[Fluence]
    end

    subgraph Validite["Validité Dominante"]
        V1[Écologique Élevée]
        V2[Interne Élevée]
        V3[Construit Forte]
        V4[Externe Modérée]
    end

    P1 --> D2
    P3 --> D3
    P3 --> D4
    P3 --> D5
    P4 --> D3
    P4 --> D1
    P5 --> D1
    P5 --> D3
    P6 --> D1
    P6 --> D2
    P6 --> D4
    P6 --> D5
    P7 --> D2
    P7 --> D1

    D2 --> V1
    D3 --> V2
    D1 --> V3
    D5 --> V2
    D4 --> V4

    style P6 fill:#ffd700,stroke:#333,stroke-width:2px
    style P7 fill:#ff8e8e,stroke:#333,stroke-width:2px
    style P3 fill:#8ec8ff,stroke:#333
    style P4 fill:#8eff9e,stroke:#333
```

## Diagramme 2: Timeline Méthodologique 2009-2026

```mermaid
timeline
    title Évolution Méthodologique État de l'Art
    2009 : Alter & Oppenheimer - Revue fondatrice fluence - Méthode: revue multi-manipulations - Preuve: Élevée
    2017 : Nobre & van Ede - Anticipated moments - Méthode: revue + modèles - Structures temporelles
    2024 : Denison - Visual temporal attention - Update computationnel
    2025 : Tünçok et al. - fMRI 7T pRF - Méthode: expé + neuro - Baseline shift + pRF shift
         : Ben Hamed - Decoding Attention - Méthode: décodage temps réel préfrontal
         : Knight et al. - Fluence crossmodal - Méthode: expé audio-visuel
         : Rosen & Freedman - Perspective - Cognition distribuée
         : Huang et al. - Critique n-back - Validité construit faible
         : Chen & Yan - Entraînement - Modèles animaux + humains
    2026 : Lee & Engle - AC comme mécanisme - Revue 6 domaines + variables latentes - 75.6% variance multitâche
         : Fuchs - Concepts incarnés - Théorique énactive
         : Frontiers Edu - 4E STEM - Méta SMD 0.448 - 4 mécanismes
         : Pascucci & Kristjánsson - Routines spatio-temporelles - Perspective intégrative
         : Tian et al. - Attention temporelle volontaire - Préprint facilitation pré-compétitive
         : Exceptionality of enactivism - Seul autopoïétique rompt vraiment
```

## Diagramme 3: Arbre de Décision Méthodologique pour Cognitorium

```mermaid
flowchart TD
    Start{Quelle question Cognitorium?} --> Q1{Veut-on mesurer<br/>capacité stable?}
    Q1 -->|Oui| M1[Utiliser tâches AC pures<br/>antisaccade, Stroop, flanker<br/>Lee & Engle 2026<br/>Validité construit forte]
    Q1 -->|Non, veut-on comprendre<br/>expérience située?| Q2{Contexte riche ou labo?}
    Q2 -->|Riche, écologique| M2[4E + Routines spatio-temporelles<br/>Fuchs 2026 + Pascucci 2026<br/>Gestes, offloading, contexte]
    Q2 -->|Contrôlé, causal| Q3{Quelle modalité attention?}
    Q3 -->|Spatiale| M3[Tünçok 2025<br/>Pré-cues + baseline shift<br/>pRF mapping]
    Q3 -->|Temporelle| M4[Nobre + Denison 2024 + Tian 2026<br/>Hazard rates, rythmes, séquences]
    Q3 -->|Jugement / UX| M5[Fluence<br/>Alter 2009 + Knight 2025<br/>Parcours fluide + disfluence utile]

    M1 --> Design1[Évaluation compétences = AC]
    M2 --> Design2[Compétences = patterns engagement]
    M3 --> Design3[Mise en page prédictive]
    M4 --> Design4[Timing structuré]
    M5 --> Design5[Cohérence crossmodale]

    style M1 fill:#ffd700
    style M3 fill:#87ceeb
    style M5 fill:#ffcc99
```

## Diagramme 4: Radar Validités par Méthode

```mermaid
radarBeta
    title Radar Validités par Type Méthode
    axis Interne, Construit, Externe, Écologique, Statistique
    curve Théorique 4E{"Interne": 20, "Construit": 40, "Externe": 50, "Écologique": 90, "Statistique": 10}
    curve Expérimental Labo{"Interne": 95, "Construit": 70, "Externe": 40, "Écologique": 30, "Statistique": 85}
    curve Neuroimagerie{"Interne": 80, "Construit": 75, "Externe": 60, "Écologique": 35, "Statistique": 80}
    curve Revue Systématique{"Interne": 70, "Construit": 85, "Externe": 85, "Écologique": 60, "Statistique": 90}
    curve Méta-analyse{"Interne": 75, "Construit": 80, "Externe": 90, "Écologique": 55, "Statistique": 95}
    max 100
    min 0
```

Ces diagrammes complètent la visualisation interactive et permettent de justifier le choix méthodologique pour chaque implication design Cognitorium.
