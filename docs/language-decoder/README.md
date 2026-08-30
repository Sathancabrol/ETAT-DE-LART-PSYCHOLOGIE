# Language Decoder

Prototype statique de dashboard de **compréhension multimodale de l'humain** —
probabiliste, explicable et contrôlée. Dossier rattaché au projet
ETAT-DE-LART-PSYCHOLOGIE (Cognitorium).

## Contenu

- `discussion.md` — la discussion archivée (chaîne de raisonnement en 8 étapes,
  métaphore de la langue, modèle de données JSON, interface adaptative, 5
  couches du modèle d'orientation) **+ les réponses aux 3 questions**
  (format HTML, indicateurs d'incertitude, minimisation des données)
  **+ le tableau « où chaque conseil est appliqué dans Cognitorium »**.
- `index.html` — prototype autonome, sans dépendance, données simulées.

## Utilisation

Ouvrir `index.html` dans un navigateur. GitHub Pages : Settings → Pages →
branche principale → `/root`.

## Principes affichés dans le prototype

1. **Mesuré / interprété / action** jamais confondus (3 sections distinctes,
   hachures pour l'estimé, barres pleines pour le mesuré).
2. **Incertitude visible** : intervalles `±`, dégradés qui s'estompent,
   badge d'échantillon `n =`, confiance globale avec niveau.
3. **Pourquoi cette adaptation** : l'action affiche les signaux concordants
   qui l'ont déclenchée ; réversible, contrôlée par l'utilisateur.

## Limites

Un signal physiologique isolé ne permet pas d'identifier une émotion. Toute
interprétation reste contextuelle, probabiliste, explicable et corrigeable.
Données biométriques réelles : uniquement avec consentement explicite,
minimisation, sécurité, durée de conservation et droits outillés (CNIL).
