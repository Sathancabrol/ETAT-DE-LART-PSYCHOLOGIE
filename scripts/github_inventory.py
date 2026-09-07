#!/usr/bin/env python3
"""Inventaire GitHub -> snapshot JSON pour l'interface unifiee.

Recupere, pour un utilisateur/org GitHub donne :
  repos > branches > commits recents > modules detectes > dependances
et produit une vue "fusion" (dependances partagees, references croisees,
groupes par langage) permettant de comprendre comment les repos
fonctionnent ensemble.

Le token GitHub (GITHUB_TOKEN ou GH_TOKEN) est lu COTE SERVEUR uniquement
et n'est jamais ecrit dans le snapshot ni expose au client.

Usage :
    python3 scripts/github_inventory.py [--owner Sathancabrol]
        [--repos COGNITORIUM,watchtower] [--max-commits 20]
        [--out data/github_inventory.json]

Dependances : bibliotheque standard uniquement (urllib).
"""

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

# Fichiers manifestes servant a detecter un "module"
MANIFESTS = {
    "package.json": "node",
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "requirements.txt": "python",
    "Pipfile": "python",
    "poetry.lock": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "composer.json": "php",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "docker-compose.yaml": "docker",
}
REQUIREMENTS_RE = re.compile(r"^requirements.*\.txt$")
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build"}
MAX_BLOB_BYTES = 100_000  # on ne telecharge pas les manifestes plus gros


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


class GitHubClient:
    """Mini client REST GitHub (stdlib). Conserve les infos de rate limit."""

    def __init__(self):
        self.rate_limit = {}
        self.calls = 0

    def _headers(self):
        h = {"Accept": "application/vnd.github+json",
             "User-Agent": "github-inventory-script/1.0"}
        if TOKEN:
            h["Authorization"] = f"Bearer {TOKEN}"
        return h

    def get(self, path):
        """GET sur l'API. Retourne (data, headers). Leve GitHubError sinon."""
        url = path if path.startswith("http") else API + path
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.calls += 1
                headers = dict(resp.headers.items())
                self._track_rate(headers)
                return json.loads(resp.read().decode("utf-8")), headers
        except urllib.error.HTTPError as e:
            self.calls += 1
            try:
                body = e.read().decode("utf-8")
                payload = json.loads(body) if body else {}
            except Exception:
                payload = {}
            headers = dict(e.headers.items()) if e.headers else {}
            self._track_rate(headers)
            raise GitHubError(e.code, payload.get("message", f"HTTP {e.code}"),
                              headers, payload)

    def _track_rate(self, headers):
        for k in ("X-RateLimit-Limit", "X-RateLimit-Remaining",
                  "X-RateLimit-Reset", "X-RateLimit-Used"):
            if k in headers:
                self.rate_limit[k.split("-", 2)[-1].lower()] = headers[k]

    def paginated(self, path, per_page=100, max_pages=5):
        out = []
        for page in range(1, max_pages + 1):
            sep = "&" if "?" in path else "?"
            data, _ = self.get(f"{path}{sep}per_page={per_page}&page={page}")
            if not isinstance(data, list) or not data:
                break
            out.extend(data)
            if len(data) < per_page:
                break
        return out


class GitHubError(Exception):
    def __init__(self, status, message, headers=None, payload=None):
        super().__init__(message)
        self.status = status
        self.headers = headers or {}
        self.payload = payload or {}


# ---------------------------------------------------------------- parsers

def parse_package_json(text):
    try:
        data = json.loads(text)
    except Exception:
        return []
    deps = []
    for section in ("dependencies", "devDependencies",
                    "peerDependencies", "optionalDependencies"):
        block = data.get(section) or {}
        if isinstance(block, dict):
            deps.extend(sorted(block.keys()))
    return deps


def parse_requirements(text):
    deps = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        line = line.split("#", 1)[0].strip().rstrip("\\;")
        m = re.match(r"^([A-Za-z0-9_.\-]+(\[[^\]]+\])?)", line)
        if m:
            deps.append(m.group(1).split("[")[0])
    return sorted(set(deps))


def parse_pyproject(text):
    try:
        data = tomllib.loads(text)
    except Exception:
        return []
    deps = []
    proj = data.get("project", {})
    for req in proj.get("dependencies", []) or []:
        m = re.match(r"^([A-Za-z0-9_.\-]+)", str(req).strip())
        if m:
            deps.append(m.group(1))
    for group in (data.get("dependency-groups") or {}).values():
        for req in group or []:
            m = re.match(r"^([A-Za-z0-9_.\-]+)", str(req).strip())
            if m:
                deps.append(m.group(1))
    tool_poetry = ((data.get("tool") or {}).get("poetry") or {})
    for section in ("dependencies", "dev-dependencies", "group"):
        block = tool_poetry.get(section)
        if isinstance(block, dict):
            deps.extend([k for k in block if k.lower() != "python"])
    return sorted(set(deps))


def parse_go_mod(text):
    deps, in_block = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("require ("):
            in_block = True
            continue
        if in_block and s == ")":
            in_block = False
            continue
        if in_block and s and not s.startswith("//"):
            deps.append(s.split()[0])
        elif s.startswith("require ") and "(" not in s:
            parts = s.split()
            if len(parts) >= 2:
                deps.append(parts[1])
    return sorted(set(deps))


def parse_manifest(filename, text):
    base = os.path.basename(filename)
    if base == "package.json":
        return parse_package_json(text)
    if base == "pyproject.toml":
        return parse_pyproject(text)
    if base == "go.mod":
        return parse_go_mod(text)
    if base == "requirements.txt" or REQUIREMENTS_RE.match(base):
        return parse_requirements(text)
    return []


# --------------------------------------------------------------- inventaire

def fetch_blob(client, owner, repo, path):
    """Contenu texte d'un fichier du repo (None si binaire/trop gros)."""
    try:
        data, _ = client.get(
            f"/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}")
    except GitHubError:
        return None
    if isinstance(data, list) or data.get("encoding") != "base64":
        return None
    if (data.get("size") or 0) > MAX_BLOB_BYTES:
        return None
    try:
        raw = base64.b64decode(data["content"])
        return raw.decode("utf-8", errors="strict")
    except Exception:
        return None


def detect_modules(tree_paths, repo_default_branch):
    """Detecte les modules : dossiers racine + dossiers contenant un manifeste."""
    root_dirs = set()
    manifest_dirs = {}  # dir -> [manifestes]
    ext_by_dir = {}     # dir racine -> {ext: count}
    files_by_dir = {}   # dir -> nb fichiers

    for p in tree_paths:
        if "/" in p:
            top = p.split("/", 1)[0]
            if top in SKIP_DIRS or top.startswith("."):
                continue
            root_dirs.add(top)
            ext = os.path.splitext(p)[1].lower().lstrip(".") or "(sans ext)"
            d = ext_by_dir.setdefault(top, {})
            d[ext] = d.get(ext, 0) + 1
            # compte tous les niveaux pour le module racine
            files_by_dir[top] = files_by_dir.get(top, 0) + 1
        base = os.path.basename(p)
        is_manifest = base in MANIFESTS or REQUIREMENTS_RE.match(base)
        if is_manifest and p.count("/") <= 3:  # profondeur raisonnable
            d = os.path.dirname(p) or "."
            manifest_dirs.setdefault(d, []).append(base)

    modules = []
    # 1) dossiers a manifeste (priorite)
    for d, mans in sorted(manifest_dirs.items()):
        name = d if d != "." else "(racine)"
        top = d.split("/")[0] if d != "." else None
        modules.append({
            "path": d, "name": name, "kind": "manifest",
            "manifests": sorted(set(mans)),
            "files_count": files_by_dir.get(top, 0) if top else 0,
            "top_extensions": dict(sorted(
                (ext_by_dir.get(top) or {}).items(),
                key=lambda kv: -kv[1])[:8]) if top else {},
            "dependencies": [],
        })
    seen = {m["path"] for m in modules}
    # 2) dossiers racine sans manifeste
    for top in sorted(root_dirs):
        if top in seen:
            continue
        modules.append({
            "path": top, "name": top, "kind": "folder",
            "manifests": [],
            "files_count": files_by_dir.get(top, 0),
            "top_extensions": dict(sorted(
                ext_by_dir.get(top, {}).items(),
                key=lambda kv: -kv[1])[:8]),
            "dependencies": [],
        })
    return modules


def inventory_repo(client, owner, name, max_commits=20, fetch_blobs=True):
    repo = {"name": name, "status": "ok", "error": None}
    try:
        meta, _ = client.get(f"/repos/{owner}/{name}")
    except GitHubError as e:
        repo["status"] = "error"
        repo["error"] = classify_error(e, name)
        return repo

    repo.update({
        "full_name": meta.get("full_name"),
        "description": meta.get("description"),
        "url": meta.get("html_url"),
        "default_branch": (meta.get("default_branch") or "main"),
        "primary_language": meta.get("language"),
        "stars": meta.get("stargazers_count", 0),
        "forks": meta.get("forks_count", 0),
        "open_issues": meta.get("open_issues_count", 0),
        "size_kb": meta.get("size", 0),
        "created_at": meta.get("created_at"),
        "updated_at": meta.get("updated_at"),
        "pushed_at": meta.get("pushed_at"),
        "topics": meta.get("topics", []),
        "is_fork": bool(meta.get("fork")),
        "is_archived": bool(meta.get("archived")),
        "is_empty": bool(meta.get("size", 1) == 0),
    })

    # branches
    try:
        branches = client.paginated(f"/repos/{owner}/{name}/branches")
        repo["branches"] = [{
            "name": b.get("name"),
            "protected": bool(b.get("protected")),
            "last_commit_sha": ((b.get("commit") or {}).get("sha") or "")[:7],
        } for b in branches]
    except GitHubError as e:
        repo["branches"] = []
        repo["branches_error"] = classify_error(e, name)

    # langages (octets par langage)
    try:
        repo["languages"], _ = client.get(f"/repos/{owner}/{name}/languages")
    except GitHubError:
        repo["languages"] = {}

    # commits recents (branche par defaut)
    try:
        commits, _ = client.get(
            f"/repos/{owner}/{name}/commits?per_page={max_commits}"
            f"&sha={urllib.parse.quote(repo['default_branch'])}")
        repo["recent_commits"] = [{
            "sha": (c.get("sha") or "")[:7],
            "message": ((c.get("commit") or {}).get("message") or "").split("\n")[0][:200],
            "date": ((c.get("commit") or {}).get("author") or {}).get("date"),
            "author": ((c.get("commit") or {}).get("author") or {}).get("name"),
            "author_login": (c.get("author") or {}).get("login") if c.get("author") else None,
            "url": c.get("html_url"),
        } for c in (commits if isinstance(commits, list) else [])]
    except GitHubError as e:
        repo["recent_commits"] = []
        repo["commits_error"] = classify_error(e, name)

    # arbre complet (1 appel) -> modules + entrees racine
    tree_paths, root_entries = [], []
    try:
        tree, _ = client.get(
            f"/repos/{owner}/{name}/git/trees/"
            f"{urllib.parse.quote(repo['default_branch'])}?recursive=1")
        items = tree.get("tree", []) if isinstance(tree, dict) else []
        repo["tree_truncated"] = bool(tree.get("truncated"))
        for it in items:
            if it.get("type") == "blob":
                tree_paths.append(it.get("path", ""))
            if "/" not in (it.get("path") or ""):
                root_entries.append({
                    "name": it.get("path"),
                    "type": it.get("type"),
                    "size": it.get("size", 0),
                })
    except GitHubError as e:
        repo["tree_error"] = classify_error(e, name)
        if e.status == 409:  # repo vide
            repo["is_empty"] = True
    repo["root_entries"] = sorted(root_entries, key=lambda x: x["name"] or "")
    repo["files_total"] = len(tree_paths)

    modules = detect_modules(tree_paths, repo["default_branch"])

    # README (extrait)
    readme_text = None
    for candidate in ("README.md", "README.rst", "README", "readme.md"):
        readme_text = fetch_blob(client, owner, name, candidate)
        if readme_text:
            repo["readme_file"] = candidate
            break
    repo["readme_excerpt"] = (readme_text or "")[:1500]

    # dependances par module (contenu des manifestes)
    if fetch_blobs:
        for mod in modules:
            deps = set()
            for mf in mod["manifests"]:
                rel = mf if mod["path"] in (".", "") else f"{mod['path']}/{mf}"
                text = fetch_blob(client, owner, name, rel)
                if text:
                    try:
                        deps.update(parse_manifest(mf, text))
                    except Exception:
                        pass
            mod["dependencies"] = sorted(deps)
    repo["modules"] = modules
    repo["all_dependencies"] = sorted({d for m in modules for d in m["dependencies"]})
    repo["readme_text_for_links"] = readme_text or ""
    return repo


def classify_error(e, repo_name):
    info = {"repo": repo_name, "http_status": e.status,
            "message": str(e), "kind": "unknown", "hint": ""}
    if e.status == 404:
        info["kind"] = "not_found_or_no_access"
        info["hint"] = ("Repo introuvable ou prive sans acces. "
                        "Verifiez le nom ou fournissez un token (scope repo).")
    elif e.status == 403 and "rate limit" in str(e).lower():
        reset = e.headers.get("X-RateLimit-Reset", "")
        info["kind"] = "rate_limit"
        info["hint"] = (f"Rate limit GitHub atteinte. Reessayez apres "
                        f"reset={reset} ou utilisez un token authentifie.")
        try:
            info["reset_at"] = dt.datetime.fromtimestamp(
                int(reset), tz=dt.timezone.utc).isoformat()
        except Exception:
            pass
    elif e.status == 401:
        info["kind"] = "bad_credentials"
        info["hint"] = "Token invalide ou expire. Regenerez un PAT."
    elif e.status == 409:
        info["kind"] = "empty_repo"
        info["hint"] = "Repo vide (aucun commit / aucune branche)."
    elif e.status == 451:
        info["kind"] = "unavailable_legal"
    return info


def build_fusion(repos):
    """Vue fusion : dependances partagees, references croisees, langages."""
    names = [r["name"] for r in repos if r.get("status") == "ok"]

    # 1) dependances partagees (>= 2 usages dans des repos differents)
    usage = {}
    for r in repos:
        if r.get("status") != "ok":
            continue
        for m in r.get("modules", []):
            for dep in m.get("dependencies", []):
                usage.setdefault(dep.lower(), []).append(
                    {"repo": r["name"], "module": m["path"]})
    shared = [{"name": dep, "used_by": sorted(
        uses, key=lambda u: (u["repo"], u["module"]))}
        for dep, uses in usage.items()
        if len({u["repo"] for u in uses}) >= 2]
    shared.sort(key=lambda s: (-len(s["used_by"]), s["name"]))

    # 2) references croisees : un repo cite un autre (README, deps, nom de module)
    cross = []
    lowered = {n: n.lower() for n in names}
    for r in repos:
        if r.get("status") != "ok":
            continue
        hay = " ".join([
            r.get("readme_text_for_links") or "",
            " ".join(r.get("all_dependencies", [])),
            " ".join(m.get("name", "") for m in r.get("modules", [])),
            r.get("description") or "",
        ]).lower()
        for other in names:
            if other == r["name"]:
                continue
            key = lowered[other].replace("-", "").replace("_", "")
            if lowered[other] in hay or (len(key) > 5 and key in hay.replace("-", "").replace("_", "")):
                via = []
                if lowered[other] in (r.get("readme_text_for_links") or "").lower():
                    via.append("README")
                if any(lowered[other] in d.lower() for d in r.get("all_dependencies", [])):
                    via.append("dependance")
                if any(lowered[other] in (m.get("name", "") or "").lower()
                       for m in r.get("modules", [])):
                    via.append("module")
                if not via:
                    via.append("mention")
                cross.append({"from_repo": r["name"], "to_repo": other,
                              "via": "+".join(via)})

    # 3) groupes par langage principal
    groups = {}
    for r in repos:
        if r.get("status") != "ok":
            continue
        lang = r.get("primary_language") or "Inconnu"
        groups.setdefault(lang, []).append(r["name"])
    language_groups = [{"language": lang, "repos": sorted(rs)}
                       for lang, rs in sorted(groups.items())]

    return {
        "shared_dependencies": shared,
        "cross_references": sorted(
            cross, key=lambda c: (c["from_repo"], c["to_repo"])),
        "language_groups": language_groups,
        "repo_count": len([r for r in repos if r.get("status") == "ok"]),
        "module_count": sum(len(r.get("modules", []))
                            for r in repos if r.get("status") == "ok"),
    }


def main():
    ap = argparse.ArgumentParser(description="Inventaire GitHub -> snapshot JSON")
    ap.add_argument("--owner", default="Sathancabrol")
    ap.add_argument("--repos", default="",
                    help="Liste de repos separes par des virgules (defaut: tous ceux de l'utilisateur)")
    ap.add_argument("--max-commits", type=int, default=20)
    ap.add_argument("--out", default="data/github_inventory.json")
    ap.add_argument("--no-blobs", action="store_true",
                    help="Ne pas telecharger le contenu des manifestes/README")
    ap.add_argument("--include-forks", action="store_true")
    ap.add_argument("--include-archived", action="store_true")
    args = ap.parse_args()

    client = GitHubClient()

    if args.repos.strip():
        repo_names = [r.strip() for r in args.repos.split(",") if r.strip()]
    else:
        try:
            all_repos = client.paginated(f"/users/{args.owner}/repos?sort=updated",
                                         per_page=100, max_pages=5)
        except GitHubError as e:
            print(json.dumps({"fatal": classify_error(e, "")},
                             ensure_ascii=False, indent=2))
            return 2
        repo_names = []
        for r in all_repos:
            if r.get("fork") and not args.include_forks:
                continue
            if r.get("archived") and not args.include_archived:
                continue
            repo_names.append(r["name"])

    print(f"Inventaire de {len(repo_names)} repos de {args.owner} ...",
          file=sys.stderr)
    repos = []
    for i, name in enumerate(repo_names, 1):
        print(f"  [{i}/{len(repo_names)}] {name} ...", file=sys.stderr)
        r = inventory_repo(client, args.owner, name,
                           max_commits=args.max_commits,
                           fetch_blobs=not args.no_blobs)
        # ne pas conserver le README complet dans le snapshot public
        r.pop("readme_text_for_links", None)
        repos.append(r)
        time.sleep(0.2)  # menager l'API

    try:
        rate, _ = client.get("/rate_limit")
        core = ((rate.get("resources") or {}).get("core") or {})
    except GitHubError:
        core = {}

    snapshot = {
        "generated_at": utcnow(),
        "owner": args.owner,
        "source": "github-api-snapshot",
        "api_calls": client.calls,
        "rate_limit": {
            "limit": core.get("limit"),
            "remaining": core.get("remaining"),
            "reset": core.get("reset"),
        },
        "repos": repos,
        "fusion": build_fusion(repos),
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    ok = sum(1 for r in repos if r.get("status") == "ok")
    print(f"OK: {ok}/{len(repos)} repos, {snapshot['fusion']['module_count']} modules "
          f"-> {args.out} ({client.calls} appels API)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
