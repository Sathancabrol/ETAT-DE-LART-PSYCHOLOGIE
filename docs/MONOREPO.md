# Monorepo — tout le code en un seul projet + previews navigables

## Le dépôt

[`Sathancabrol/monorepo`](https://github.com/Sathancabrol/monorepo) (dépôt
**séparé**, à cloner à côté de celui-ci) contient les 8 projets importés
tels quels depuis leur branche `main` :

```
sathancabrol-monorepo/
├── README.md / MANIFEST.json   # index + provenance (URL, branche, SHA)
└── projects/
    ├── watchtower/             # vite+cesium (+ dist/ buildée)
    ├── COGNITORIUM/            # statique (learning/, watchtower-mods/)
    ├── animation-chronos/      # vite+react (+ dist/ buildée)
    ├── Language-decoder/       # 1 fichier
    ├── ETAT-DE-LART-PSYCHOLOGIE/  # snapshot de ce dépôt (sans monorepo/)
    ├── reaserch-engine/        # python
    ├── proto-cognitorium/      # vite+react (+ dist/ buildée)
    └── HCSM/                   # python
```

> Pourquoi séparé ? 129 Mo de code/assets : cela aurait dépassé les quotas
> d'artefacts de la branche et alourdi ce dépôt. Le monorepo est un vrai
> dépôt git local (`b8ee9e0` import, `e5a237c` builds) — voir son README
> pour le publier sur GitHub (`git remote add origin … && git push`).

## L'explorateur (`/monorepo`)

Page de l'app FastAPI : onglets projets → **explorateur de fichiers**
(fil d'Ariane, filtre, coloration syntaxique, rendu Markdown, images, PDF)
+ **preview web dans un iframe navigable** (boutons ←/→/accueil, barre
d'adresse synchronisée avec la navigation interne, sélecteur d'entrée,
ouverture nouvel onglet).

Endpoints : `GET /api/mono/projects`, `GET /api/mono/tree?project=&path=`,
`GET /api/mono/file?project=&path=`, fichiers bruts `GET /mono/<projet>/<chemin>`
(same-origin, protection anti-traversal).

## Previews disponibles

| Projet | Entrée par défaut | Nature |
|---|---|---|
| watchtower | `dist/index.html` | app buildée (`vite build --base=./`) |
| animation-chronos | `dist/index.html` | app buildée |
| proto-cognitorium | `dist/index.html` | app buildée (frontend seul, sans `server.ts`) |
| COGNITORIUM | `learning/index.html` (+ `watchtower-mods/`) | statique |
| ETAT-DE-LART-PSYCHOLOGIE | `output/visual/index.html` (+ d3, taxonomy) | statique |
| reaserch-engine / HCSM / Language-decoder | — | code seul (pas d'UI web) |

`--base=./` rend les assets relatifs : les builds fonctionnent sous
n'importe quel sous-chemin (`/mono/<projet>/dist/…`). Rebuild :

```bash
cd projects/<vite-projet> && npm install && npx vite build --base=./
# watchtower : export PUPPETEER_SKIP_DOWNLOAD=1 avant npm install
# (le téléchargement Chrome est bloqué dans le sandbox)
```

## Lancement

```bash
git clone https://github.com/Sathancabrol/monorepo.git ../monorepo
pip install -r requirements.txt
MONOREPO_PATH=../monorepo \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000/monorepo
```

Sans `MONOREPO_PATH`, l'app cherche `../monorepo`,
`../sathancabrol-monorepo` puis `/home/user/sathancabrol-monorepo`,
sinon 503 explicite.
