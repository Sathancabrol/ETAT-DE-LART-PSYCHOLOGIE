# Panorama GitHub — repos › branches › modules › fusion

Interface unifiée de visualisation des dépôts GitHub `Sathancabrol`
(page `/repos` de l'application FastAPI).

## Principe (hypothèses validées par défaut)

L'utilisateur n'ayant pas répondu au questionnaire de cadrage, les choix
**les moins risqués et non-destructifs** ont été appliqués :

| Question | Choix appliqué |
|---|---|
| Périmètre | 8 dépôts **publics** (aucun token requis en lecture) |
| Branches / commits | **Toutes les branches** (peu nombreuses) + 20 derniers commits de la branche par défaut |
| Définition d'un module | **Les deux** : dossier racine **et** dossier contenant un manifeste (`package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`…) + détection auto du langage |
| Interface | **Les deux** : page dédiée `/repos` **+** volet latéral (drawer) au clic |
| Vue | **Les trois** : cartes, arborescence, graphe de fusion |
| Fusion | **(a) agrégation visuelle + (c) cartographie logique** — aucun code copié, chaque repo reste autonome |
| Données | **Snapshot JSON** généré côté serveur (`data/github_inventory.json`), régénérable via `POST /api/github/refresh` |
| Token | Lu **côté serveur uniquement** (`GITHUB_TOKEN`/`GH_TOKEN`), jamais exposé au client |

> Pour passer au **monorepo réel (b)**, une validation explicite est requise
> (stratégie de conflits, versions de langages, CI/CD) — voir § 5 du cadrage.

## Fichiers

- `scripts/github_inventory.py` — inventaire via l'API REST GitHub (stdlib uniquement).
  `--owner`, `--repos a,b`, `--max-commits`, `--out`, `--no-blobs`,
  `--include-forks`, `--include-archived`.
- `data/github_inventory.json` — snapshot généré (régénérable, versionné).
- `app/main.py` § « PANORAMA GITHUB » — routes `/repos` + `/api/github/*`.
- `app/templates/repos.html` — page (cartes / arborescence / fusion + drawer).

## Lancement

```bash
pip install -r requirements.txt
# optionnel : token pour 5000 req/h et futurs dépôts privés
export GITHUB_TOKEN=ghp_...
python3 scripts/github_inventory.py --owner Sathancabrol
uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000/repos
```

## Endpoints

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/repos` | Page panorama + drawer + fusion |
| GET | `/api/github/snapshot` | Meta + résumé de chaque dépôt |
| GET | `/api/github/repos/{nom}` | Détail complet (README, commits, modules, dépendances) |
| GET | `/api/github/fusion` | Graphe repos↔modules↔dépendances + matrice |
| POST | `/api/github/refresh?owner=` | Régénère le snapshot côté serveur |

## Gestion des erreurs

- **Rate limit** : bandeau d'alerte + `kind: rate_limit` avec heure de reset.
- **Repo privé sans accès / 404** : carte « erreur » + hint (token scope `repo`).
- **Repo vide** : badge « vide », sections tolérantes (0 branche / 0 module / 0 commit).
- **Snapshot absent** : page d'aide + bouton de génération (`POST /api/github/refresh`).

## Résultat observé (snapshot initial)

8 dépôts, 39 modules, 17 dépendances partagées :
`animation-chronos` ↔ `proto-cognitorium` partagent tout le socle
React/Vite/Tailwind (`vite` aussi utilisé par `watchtower`) ;
`COGNITORIUM` → `watchtower` via le module `watchtower-mods`.
Familles : JS (`COGNITORIUM`, `watchtower`), TS (`animation-chronos`,
`proto-cognitorium`), Python (`HCSM`, `reaserch-engine`), HTML
(`ETAT-DE-LART-PSYCHOLOGIE`), quasi-vide (`Language-decoder`).
