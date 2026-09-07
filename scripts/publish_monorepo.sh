#!/usr/bin/env bash
# Reconstruit le monorepo depuis zero et le pousse vers
# https://github.com/Sathancabrol/monorepo
#
# Usage :
#   bash scripts/publish_monorepo.sh [target_dir] [--no-push] [--skip-build]
#
# Le script (destructif sur target_dir uniquement) :
#   1. clone le depot distant (conserve son commit initial),
#   2. importe les 8 projets (snapshot depth-1, .git retires),
#   3. ecrit .gitignore / MANIFEST.json (SHA reels) / README.md,
#   4. build les 3 apps vite avec --base=./ (previews statiques),
#   5. commit + push vers origin/main.
set -euo pipefail

TARGET="${1:-/home/user/sathancabrol-monorepo}"
[[ "${2:-}" == "--no-push" || "${3:-}" == "--no-push" ]] && NO_PUSH=1 || NO_PUSH=0
[[ "${2:-}" == "--skip-build" || "${3:-}" == "--skip-build" ]] && SKIP_BUILD=1 || SKIP_BUILD=0
REMOTE="https://github.com/Sathancabrol/monorepo.git"
OWNER="Sathancabrol"
PROJECTS="watchtower COGNITORIUM animation-chronos Language-decoder ETAT-DE-LART-PSYCHOLOGIE reaserch-engine proto-cognitorium HCSM"

command -v git >/dev/null || { echo "git requis"; exit 1; }
command -v python3 >/dev/null || { echo "python3 requis"; exit 1; }
if [[ "$SKIP_BUILD" == "0" ]]; then
  command -v npm >/dev/null || { echo "npm requis (ou --skip-build)"; exit 1; }
fi

echo "== 1/5 clone distant -> $TARGET"
rm -rf "$TARGET"
git clone -q "$REMOTE" "$TARGET"
cd "$TARGET"
git config user.name "Sathancabrol"
git config user.email "sathancabrol@users.noreply.github.com"
mkdir -p projects
STAGE="$(mktemp -d)"

echo "== 2/5 import des 8 projets"
> "$STAGE/shas.txt"
for r in $PROJECTS; do
  git clone -q --depth 1 "https://github.com/$OWNER/$r.git" "$STAGE/$r"
  echo "$r $(git -C "$STAGE/$r" rev-parse --short HEAD)" >> "$STAGE/shas.txt"
  rm -rf "$STAGE/$r/.git"
  mv "$STAGE/$r" projects/
  echo "  - $r"
done

echo "== 3/5 .gitignore / MANIFEST.json / README.md"
cat > .gitignore << 'EOF'
# Dependances regenerables (ne jamais commiter)
node_modules/
.venv/
__pycache__/
.pytest_cache/
*.pyc
*.log
cognitorium.db
.DS_Store
# Environnements locaux
.env
.env.local
EOF

python3 - "$STAGE/shas.txt" << 'EOF'
import json, sys
shas = dict(line.split() for line in open(sys.argv[1]) if line.strip())
stacks = {
    "watchtower": "vite + cesium + tailwind",
    "COGNITORIUM": "html/js statique",
    "animation-chronos": "vite + react + tailwind",
    "Language-decoder": "indeterminee (1 fichier)",
    "ETAT-DE-LART-PSYCHOLOGIE": "fastapi + sqlite + d3",
    "reaserch-engine": "python",
    "proto-cognitorium": "vite + react + express",
    "HCSM": "python",
}
manifest = {
    "monorepo": "Sathancabrol/monorepo",
    "generated_at": "2026-09-07",
    "source_owner": "Sathancabrol",
    "method": "snapshot-import (branche par defaut, HEAD au jour de l'import, historique conserve dans les depots d'origine)",
    "projects": {
        name: {
            "url": f"https://github.com/Sathancabrol/{name}",
            "branch": "main",
            "sha": shas.get(name, "?"),
            "stack": stacks[name],
        } for name in stacks
    },
}
json.dump(manifest, open("MANIFEST.json", "w"), ensure_ascii=False, indent=2)
print("  MANIFEST.json OK")
EOF

cat > README.md << 'EOF'
# monorepo

Monorepo reunissant les 8 depots publics de **Sathancabrol** en un seul
projet navigable : https://github.com/Sathancabrol/monorepo

Chaque projet vit dans `projects/<nom>/`, importe tel quel depuis sa
branche par defaut (voir `MANIFEST.json` pour l'URL, la branche et le SHA
d'origine de chaque import).

## Contenu

| Projet | Stack | Apercu web |
|---|---|---|
| `projects/watchtower` | Vite + Cesium + Tailwind | `dist/` (build inclus) |
| `projects/COGNITORIUM` | HTML/JS statique | `learning/index.html`, `watchtower-mods/index.html` |
| `projects/animation-chronos` | Vite + React + Tailwind | `dist/` (build inclus) |
| `projects/Language-decoder` | 1 fichier (proto) | - (code uniquement) |
| `projects/ETAT-DE-LART-PSYCHOLOGIE` | FastAPI + SQLite + D3 | `output/visual/*.html` (statique) + app FastAPI |
| `projects/reaserch-engine` | Python | - (code uniquement) |
| `projects/proto-cognitorium` | Vite + React + Express | `dist/` (build inclus, frontend seul) |
| `projects/HCSM` | Python | - (code + docs) |

> Methode d'import : **snapshot** (pas d'historique git fusionne).
> L'historique complet reste disponible dans chaque depot d'origine ;
> les SHA importes sont references dans `MANIFEST.json`.

## Cloner

```bash
git clone https://github.com/Sathancabrol/monorepo.git
cd monorepo
```

## Navigation + previews

L'application de navigation (explorateur de fichiers + previews web
navigables) se trouve dans le depot `ETAT-DE-LART-PSYCHOLOGIE`
(page `/monorepo`) :

```bash
git clone https://github.com/Sathancabrol/ETAT-DE-LART-PSYCHOLOGIE.git
cd ETAT-DE-LART-PSYCHOLOGIE
pip install -r requirements.txt
MONOREPO_PATH=/chemin/vers/monorepo \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000/monorepo
```

Sans `MONOREPO_PATH`, l'app cherche `../monorepo`,
`../sathancabrol-monorepo` puis `/home/user/sathancabrol-monorepo`.

## Reconstruire les previews JS

Les `dist/` sont commitees (les previews marchent sans build), mais pour
reconstruire apres modification des sources :

```bash
cd projects/animation-chronos && npm install && npx vite build --base=./
cd ../proto-cognitorium    && npm install && npx vite build --base=./
cd ../watchtower           && npm install && npx vite build --base=./
```

`--base=./` rend les assets relatifs pour que les previews fonctionnent
sous n'importe quel sous-chemin (`/mono/<projet>/dist/...`).
Note : pour `watchtower`, exporter `PUPPETEER_SKIP_DOWNLOAD=1` avant
`npm install` si le telechargement Chrome est bloque.
EOF

git add -A
git commit -qm "Import initial : 8 projets (snapshot HEAD, voir MANIFEST.json)"

if [[ "$SKIP_BUILD" == "0" ]]; then
  echo "== 4/5 builds vite (--base=./)"
  for p in animation-chronos proto-cognitorium; do
    ( cd "projects/$p" && npm install --no-audit --no-fund >/dev/null 2>&1 \
      && npx vite build --base=./ 2>&1 | tail -1 )
  done
  ( cd projects/watchtower \
    && export PUPPETEER_SKIP_DOWNLOAD=1 \
    && npm install --no-audit --no-fund >/dev/null 2>&1 \
    && npx vite build --base=./ 2>&1 | tail -1 )
  sed -i 's#"/logo.svg"#"./logo.svg"#g' projects/watchtower/dist/index.html || true
  rm -rf projects/*/node_modules
  git add -A
  git commit -qm "Build previews statiques (vite --base=./) : watchtower, animation-chronos, proto-cognitorium"
else
  echo "== 4/5 builds ignores (--skip-build)"
fi

rm -rf "$STAGE"
git log --oneline | head -4

if [[ "$NO_PUSH" == "1" ]]; then
  echo "== 5/5 push ignore (--no-push)"
  exit 0
fi
echo "== 5/5 push vers $REMOTE"
if git push -u origin main 2>&1 | tail -3; then
  echo "PUSH OK : https://github.com/Sathancabrol/monorepo"
else
  echo "ECHEC DU PUSH (probablement 403 : l'app GitHub Arena n'a pas acces au depot)."
  echo "Donnez-lui acces (Settings > Applications > Arena > Repository access), puis relancez :"
  echo "  cd $TARGET && git push -u origin main"
  exit 3
fi
