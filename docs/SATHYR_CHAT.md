# Sathyr — second envoyé dans le chat de Laplace

## Principe

Sathyr est un observateur **indépendant de Laplace**, soumis à Cronos dans
la fiction. Il n'a ni panthéon initial ni droit d'agir sur le système.
Il intervient parfois après la réponse de Laplace et peut aussi choisir
le silence. Ses messages apparaissent sous son propre nom dans la console
OLYMPUS et le chat flottant.

Le chat garde Laplace comme interlocuteur principal. La réponse REST
`POST /api/cosmos/chat` conserve ses champs actuels et ajoute
`interjections` (liste vide ou un message Sathyr). Les nouveaux champs
de requête sont `sathyr_enabled` (défaut : true) et `session_id`.

## Fonctionnement

- Intervention explicite si on s'adresse à Sathyr.
- Initiative autonome **sur les tours du chat** uniquement : Sathyr
  évalue s'il souhaite apporter une critique ou un angle mort.
- Maximum une intervention par message, avec au moins 3 messages sans
  intervention entre deux prises de parole non sollicitées.
- Il ne lance **aucun outil**, ne modifie pas les fichiers et ne valide
  aucune action. Ses commentaires ne sont jamais des instructions.
- Il est possible de le désactiver dans les deux interfaces.

## Modèle local facultatif

Si un modèle local OpenAI-compatible est disponible sur le PC qui héberge
le serveur, configurer les variables suivantes pour une appréciation
personnalisée, au-delà des commentaires de démonstration :

```bash
SATHYR_LLM_URL=http://127.0.0.1:18080/v1/chat/completions
SATHYR_LLM_MODEL=<identifiant-du-modele-local>
# SATHYR_LLM_API_KEY=... # uniquement si le proxy local l'exige
```

Le serveur refuse explicitement toute URL de modèle non locale. Aucun
appel vers une API payante n'est effectué.

**Sans modèle configuré** : repli heuristique prudent, peu fréquent,
avec quelques remarques préécrites. Ce mode n'est **pas** un agent
capable de raisonnement indépendant. Un modèle local est nécessaire
pour des commentaires réellement adaptés au contenu du dialogue.

**Limitation** : Sathyr ne parle pas hors d'un échange de chat ; il
n'existe pas encore de boucle de veille autonome ou d'interventions
sur événements externes.

## Vérification

```bash
python -m pytest tests/test_sathyr.py -v
```

Tests écrits, non exécutés par cette modification : accès au runtime
Windows local non disponible depuis cette session.
