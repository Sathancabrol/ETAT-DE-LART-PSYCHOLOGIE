"""
Mémoire évolutive du système — partagée par tous les corps.

Trois stores persistants dans output/cosmos/memory/ :
  • taxonomy.json — taxonomie enrichie : psychologie (résumée du projet) +
    branche Construction (BTP/TP → sécurité → équipement → EPI / visière →
    modèle de vision connecté IA) + branche « Émergents » auto-enrichie
    par les missions (build_dossier, questions, veilles) ;
  • items.jsonl   — base d'éléments reçus et produits : questions, références,
    articles, thèses, drafts, posters, textes, audio, vidéo, mémoires,
    dossiers, papiers, plans, graphes… (mémoire du système) ;
  • concepts.json — registre de concepts partagés, alimenté par les tags de
    la base 42 champs, les constellations des satellites/cour, les feuilles
    de taxonomie et les tags des éléments.

Tout est déterministe et versionné en JSON/JSONL lisibles.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.core.context import DATA_CSV, ROOT

MEMORY_DIR = ROOT / "output" / "cosmos" / "memory"
TAXONOMY_PATH = MEMORY_DIR / "taxonomy.json"
ITEMS_PATH = MEMORY_DIR / "items.jsonl"
CONCEPTS_PATH = MEMORY_DIR / "concepts.json"

ITEM_TYPES = {"question", "reference", "article", "these", "draft", "poster",
              "texte", "audio", "video", "memoire", "dossier", "papier",
              "plan", "graph", "rapport", "document", "veille"}

SEED_VERSION = 2

SEED_TAXONOMY: Dict[str, Any] = {
    "name": "Cognitorium",
    "children": [
        {"name": "Psychologie scientifique", "children": [
            {"name": "Cognition & attention", "children": [
                {"name": "Fonctions exécutives", "children": []},
                {"name": "Métacognition", "children": []},
                {"name": "Cognition incarnée (4E)", "children": []}]},
            {"name": "Clinique & santé", "children": [
                {"name": "Psychothérapies", "children": []},
                {"name": "Santé mentale", "children": []}]},
            {"name": "Éducation & apprentissage", "children": []},
            {"name": "Méthodologie & open science", "children": []},
        ]},
        {"name": "Construction", "children": [
            {"name": "BTP / TP", "children": [
                {"name": "Sécurité", "children": [
                    {"name": "Équipement", "children": [
                        {"name": "EPI", "children": []},
                        {"name": "Visière", "children": [
                            {"name": "Modèle de vision connecté IA", "children": []}]}]}]},
                {"name": "Administratif augmenté", "children": [
                    {"name": "Automatisation documentaire", "children": []}]},
                {"name": "Chantiers augmentés", "children": [
                    {"name": "Visière HUD terrain", "children": []},
                    {"name": "Robotique de chantier", "children": []},
                    {"name": "Drones & suivi", "children": []},
                    {"name": "Jumeaux numériques", "children": []}]},
            ]},
            {"name": "Génie civil & infrastructures", "children": [
                {"name": "Routes & terrassements", "children": []},
                {"name": "Ouvrages d'art", "children": []},
                {"name": "Réhabilitation & entretien", "children": []},
                {"name": "Management de projet (conducteur de travaux)", "children": []}]},
        ]},
        {"name": "Robotique", "children": [
            {"name": "Robotique de chantier", "children": [
                {"name": "Terrassement automatisé", "children": []},
                {"name": "Cobots de montage", "children": []},
                {"name": "Ferraillage & préfabrication", "children": []},
                {"name": "Impression 3D structurelle", "children": []}]},
            {"name": "Drones", "children": [
                {"name": "Photogrammétrie", "children": []},
                {"name": "Suivi d'avancement", "children": []},
                {"name": "Inspection d'ouvrages", "children": []}]},
            {"name": "Exosquelettes", "children": [
                {"name": "Prévention TMS", "children": []},
                {"name": "Assistance au port de charges", "children": []}]},
            {"name": "Perception & navigation", "children": [
                {"name": "SLAM & localisation", "children": []},
                {"name": "Vision par ordinateur embarquée", "children": []},
                {"name": "Capteurs & IoT chantier", "children": []}]},
            {"name": "Téléopération & autonomie", "children": [
                {"name": "Niveaux d'autonomie", "children": []},
                {"name": "Sécurité fonctionnelle", "children": []}]},
            {"name": "Éthique & réglementation robotique", "children": []},
        ]},
        {"name": "Intelligence artificielle", "children": [
            {"name": "IA génératives", "children": [
                {"name": "LLM", "children": []},
                {"name": "Agents autonomes", "children": []},
                {"name": "RAG & bases documentaires", "children": []}]},
            {"name": "Vision par ordinateur", "children": [
                {"name": "Détection de défauts", "children": []},
                {"name": "Segmentation de scènes", "children": []},
                {"name": "Suivi d'avancement par image", "children": []}]},
            {"name": "Apprentissage automatique", "children": [
                {"name": "Séries temporelles & prévision", "children": []},
                {"name": "Optimisation & planification", "children": []},
                {"name": "Transfer learning", "children": []}]},
            {"name": "IA embarquée & edge", "children": [
                {"name": "Temps réel", "children": []},
                {"name": "Sobriété énergétique", "children": []}]},
            {"name": "Humain dans la boucle", "children": [
                {"name": "Interaction homme-machine (IHM)", "children": []},
                {"name": "HUD & réalité augmentée", "children": []},
                {"name": "Explicabilité (XAI) & confiance", "children": []}]},
            {"name": "Gouvernance des données", "children": [
                {"name": "RGPD & données chantier", "children": []},
                {"name": "Cybersécurité", "children": []},
                {"name": "Jumeaux numériques & BIM", "children": []}]},
        ]},
        {"name": "Émergents (auto-enrichis)", "children": []},
    ],
}

# Où ranger automatiquement un terme nouveau selon ses mots-clés
_BRANCH_HINTS = [
    (r"s[ée]curit|epi\b|casque|visi[èe]re|gants?", "Construction", "BTP / TP", "Sécurité", "Équipement"),
    (r"robot|cobot", "Robotique", "Robotique de chantier"),
    (r"exosquel", "Robotique", "Exosquelettes"),
    (r"drone|photogramm", "Robotique", "Drones"),
    (r"slam|t[ée]l[ée]op|autonom", "Robotique", "Téléopération & autonomie"),
    (r"\bllm\b|g[ée]n[ée]rat|\brag\b|agent", "Intelligence artificielle", "IA génératives"),
    (r"machine learning|pr[ée]vision|optimi", "Intelligence artificielle", "Apprentissage automatique"),
    (r"hud|r[ée]alit[ée] (augment|mixte)|interface|homme.?machine|ihm", "Intelligence artificielle", "Humain dans la boucle"),
    (r"vision|d[ée]faut|segmentation", "Intelligence artificielle", "Vision par ordinateur"),
    (r"rgpd|cyber|jumeau|bim", "Intelligence artificielle", "Gouvernance des données"),
    (r"btp|\btp\b|chantier|construction|travaux", "Construction", "BTP / TP"),
    (r"g[ée]nie civil|route|terrassement|ouvrage", "Construction", "Génie civil & infrastructures"),
    (r"attention|m[ée]moire|executive|m[ée]tacogn", "Psychologie scientifique", "Cognition & attention"),
    (r"psychoth|d[ée]pres|anx|clinic", "Psychologie scientifique", "Clinique & santé"),
    (r"[ée]ducation|apprentissage|scolaire", "Psychologie scientifique", "Éducation & apprentissage"),
    (r"open science|pr[ée]enregist|biais|r[ée]plication", "Psychologie scientifique", "Méthodologie & open science"),
]


# ── Taxonomie ───────────────────────────────────────────────────────────────

def load_taxonomy() -> Dict[str, Any]:
    if TAXONOMY_PATH.exists():
        try:
            tree = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
            # Migration : ajouter les branches du seed absentes (ex. Robotique, IA en v2)
            known = {c["name"].lower() for c in tree.get("children", [])}
            changed = False
            for branch in SEED_TAXONOMY["children"]:
                if branch["name"].lower() not in known:
                    tree.setdefault("children", []).append(branch)
                    changed = True
            if changed:
                save_taxonomy(tree)
            return tree
        except Exception:
            pass
    save_taxonomy(SEED_TAXONOMY)
    return SEED_TAXONOMY


def save_taxonomy(tree: Dict[str, Any]) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    TAXONOMY_PATH.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_branch(tree: Dict[str, Any], path: List[str]) -> Optional[Dict[str, Any]]:
    node = tree
    for name in path:
        node = next((c for c in node.get("children", []) if c["name"].lower() == name.lower()), None)
        if node is None:
            return None
    return node


def _upsert_child(node: Dict[str, Any], name: str) -> Dict[str, Any]:
    child = next((c for c in node.get("children", []) if c["name"].lower() == name.lower()), None)
    if child is None:
        child = {"name": name, "children": []}
        node.setdefault("children", []).append(child)
    return child


def enrich_taxonomy(terms: List[str]) -> List[str]:
    """Ajoute des termes à la taxonomie (branche détectée, sinon Émergents)."""
    tree = load_taxonomy()
    added: List[str] = []
    for term in [t.strip() for t in terms if t and len(t.strip()) > 2][:12]:
        target = None
        for pattern, *path in _BRANCH_HINTS:
            if re.search(pattern, term.lower()):
                target = _find_branch(tree, list(path))
                if target is not None:
                    break
        if target is None:
            target = _find_branch(tree, ["Émergents (auto-enrichis)"]) or tree
        _upsert_child(target, term[:60])
        added.append(term[:60])
    if added:
        save_taxonomy(tree)
    return added


def taxonomy_leaves(tree: Optional[Dict[str, Any]] = None, path: str = "") -> List[str]:
    leaves = []
    for c in (tree or load_taxonomy()).get("children", []):
        p = (path + " / " + c["name"]).strip(" /")
        if c.get("children"):
            leaves.extend(taxonomy_leaves(c, p))
        else:
            leaves.append(c["name"])
    return leaves


# ── Items (base évolutive) ──────────────────────────────────────────────────

def _read_items() -> List[Dict[str, Any]]:
    if not ITEMS_PATH.exists():
        return []
    out = []
    for line in ITEMS_PATH.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def record_item(type_: str, titre: str, contenu: str = "", tags: Optional[List[str]] = None,
                source: str = "user", corps: str = "systeme", meta: Optional[Dict] = None) -> Dict[str, Any]:
    type_ = type_.lower() if type_.lower() in ITEM_TYPES else "document"
    item = {"id": uuid.uuid4().hex[:10],
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "type": type_, "titre": titre[:140], "contenu": (contenu or "")[:2000],
            "tags": [t[:40] for t in (tags or [])][:8],
            "source": source, "corps": corps, "meta": meta or {}}
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(ITEMS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
    if tags:
        enrich_taxonomy(tags)
    _sync_to_database(item)
    return item


def _sync_to_database(item: Dict[str, Any]) -> None:
    """Synchronise l'élément dans la base de données (si l'app est présente)."""
    try:
        from app.database import sync_memory_items
        sync_memory_items()
    except Exception:
        pass  # hors app (CLI) : la synchro se fera au prochain démarrage


def record_question(message: str) -> None:
    record_item("question", message[:140], contenu=message, source="user", corps="sol")


def record_mission(trace: Dict[str, Any]) -> int:
    """Archive les productions d'une mission : artefacts + références trouvées."""
    n = 0
    for step in trace.get("steps", []):
        for res in (step.get("data", {}) or {}).get("resultats", []) or []:
            if isinstance(res, dict) and res.get("titre"):
                record_item("reference", res["titre"][:140],
                            contenu=f"DOI: {res.get('doi', 'n/a')} · {res.get('auteurs', '')}",
                            tags=[res.get("base", "").lower(), str(res.get("annee", ""))],
                            source="recherche", corps="uranus",
                            meta={"doi": res.get("doi"), "citations": res.get("citations")})
                n += 1
        for a in step.get("artifacts", []) or []:
            name = a.split("/")[-1]
            type_ = ("papier" if name.startswith("paper") else
                     "plan" if name.startswith("dossier_plan") else
                     "dossier" if name.startswith("dossier") else
                     "graph" if name.endswith("_graph.json") else
                     "veille" if name.startswith("veille") else
                     "rapport" if name == "report.md" else "document")
            record_item(type_, name, contenu=f"run {trace.get('run_id')} · {step.get('skill')}",
                        tags=[step.get("skill", "")], source="generation",
                        corps="uranus", meta={"run": trace.get("run_id"), "path": a})
            n += 1
    return n


# ── Concepts partagés ───────────────────────────────────────────────────────

def _base_tags() -> List[str]:
    import csv
    if not DATA_CSV.exists():
        return []
    tags = set()
    with open(DATA_CSV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tags.update(t.strip() for t in (r.get("tags") or "").split(",") if t.strip())
    return sorted(tags)


def concepts() -> List[Dict[str, Any]]:
    """Registre de concepts partagés : base + satellites + cour + taxonomie + items."""
    from cosmos.knowledge import SATELLITE_CONCEPTS, COUR_CONCEPTS
    from cosmos.bodies import BODIES
    out: Dict[str, Dict[str, Any]] = {}

    def add(name: str, source: str, definition: str, refs: Optional[List[str]] = None):
        key = name.lower()
        e = out.setdefault(key, {"id": "concept:" + re.sub(r"[^a-z0-9]+", "-", key)[:40],
                                 "name": name, "sources": [], "definition": definition,
                                 "refs": refs or []})
        if source not in e["sources"]:
            e["sources"].append(source)

    for sat in BODIES["uranus"]["satellites"]:
        for c in SATELLITE_CONCEPTS.get(sat["id"], []):
            add(c, f"satellite {sat['name']}", f"Concept du domaine de {sat['name']}.", [sat["id"]])
    for c in BODIES["venus"]["court"]:
        for concept in COUR_CONCEPTS.get(c["id"], []):
            add(concept, f"cour {c['name']}", f"Concept financier de {c['name']}.", [c["id"]])
    for tag in _base_tags():
        add(tag, "base 42 champs", "Tag issu des références de la base.")
    for leaf in taxonomy_leaves():
        add(leaf, "taxonomie", "Feuille de la taxonomie enrichie.")
    for it in _read_items():
        for t in it.get("tags", []):
            if t:
                add(t, f"mémoire ({it['type']})", "Tag issu de la mémoire du système.")
    return list(out.values())


def save_concepts() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    CONCEPTS_PATH.write_text(json.dumps(concepts(), ensure_ascii=False, indent=2), encoding="utf-8")


# ── Vues & statistiques ─────────────────────────────────────────────────────

def items(limit: int = 200, type_: Optional[str] = None) -> List[Dict[str, Any]]:
    out = _read_items()
    if type_:
        out = [i for i in out if i["type"] == type_]
    return out[-limit:][::-1]


def stats() -> Dict[str, Any]:
    its = _read_items()
    by_type: Dict[str, int] = {}
    for i in its:
        by_type[i["type"]] = by_type.get(i["type"], 0) + 1
    return {"total": len(its), "par_type": by_type,
            "concepts": len(concepts()),
            "taxonomy_feuilles": len(taxonomy_leaves())}


def memory_graph() -> Dict[str, Any]:
    """Graphe de la mémoire : questions, items, concepts émergents."""
    nodes, links = [], []
    nodes.append({"id": "memoire", "label": "🧠 Mémoire", "type": "racine", "color": "#34d399"})
    for i in _read_items()[-60:]:
        iid = "item:" + i["id"]
        icon = {"question": "❓", "reference": "📚", "papier": "📄", "dossier": "🗂️",
                "plan": "🗺️", "graph": "🕸️", "veille": "🔔"}.get(i["type"], "•")
        nodes.append({"id": iid, "label": f"{icon} {(i['titre'] or '')[:40]}", "type": "item",
                      "color": "#38bdf8", "item_type": i["type"]})
        links.append({"source": "memoire", "target": iid, "type": "enregistre"})
        for t in i.get("tags", [])[:3]:
            tid = "ctag:" + t.lower()
            if not any(n["id"] == tid for n in nodes):
                nodes.append({"id": tid, "label": t, "type": "concept", "color": "#34d399"})
            links.append({"source": iid, "target": tid, "type": "tague"})
    return {"nodes": nodes, "links": links}
