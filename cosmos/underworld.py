"""
Le royaume d'Hadès ♇ — l'Underworld : rien ne disparaît jamais vraiment.

Quand Hadès fauche, l'entité n'est pas anéantie : une **fraction de données,
juste assez pour la reconstruire**, descend aux Enfers (monde de l'eau, le
royaume d'Hadès et de Perséphone). Le royaume se divise en régions selon le
destin des âmes :

  • 🌟 **Champs Élysées** — les âmes vertueuses : les runs qui ont produit
    des artefacts (ils ont bien servi, on les honore) ;
  • 🌾 **Plaines d'Asphodèle** — la majorité des âmes ordinaires : runs
    obsolètes sans gloire particulière ;
  • 🔥 **Tartare** — l'abîme des criminels : junk vide et doublons (les
    péchés contre l'ordre : néant et redondance), prison des Titans.

L'accès se fait par les fleuves infernaux — le Styx ☠ veillé par le passeur
Charon ⚰. Et à la porte, **Cerbère 🐾🐕🐕**, le tricéphale : il empêche les
morts de sortir et interdit l'accès aux vivants. Aucune âme ne remonte sans
l'accord explicite du souverain (l'utilisateur) — c'est la résurrection.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
UNDERWORLD = REPO / "output" / "underworld"
SOULS = UNDERWORLD / "souls.jsonl"
KEPT = UNDERWORLD / "kept"

REGIONS = {
    "elysees": {"nom": "Champs Élysées", "icon": "🌟",
                "desc": "les âmes vertueuses — runs qui ont produit des artefacts"},
    "asphodele": {"nom": "Plaines d'Asphodèle", "icon": "🌾",
                  "desc": "la majorité des âmes ordinaires — runs obsolètes sans gloire"},
    "tartare": {"nom": "Tartare", "icon": "🔥",
                "desc": "l'abîme des criminels — junk, doublons ; prison des Titans"},
}

GARDIEN = {"chien": "Cerbère 🐾", "passeur": "Charon ⚰", "fleuve": "Styx ☠",
           "roi": "Hadès ♇", "reine": "Perséphone 🌸"}


def _region(type_: str, vertueux: bool = False) -> str:
    if type_ in ("junk_vide", "doublon_memoire"):
        return "tartare"
    if type_ == "run_outdated" and vertueux:
        return "elysees"
    return "asphodele"


def record_soul(soul: Dict[str, Any]) -> Dict[str, Any]:
    """Inscrit une âme au registre des morts et conserve sa fraction vitale."""
    UNDERWORLD.mkdir(parents=True, exist_ok=True)
    SOULS.open("a", encoding="utf-8").write(json.dumps(soul, ensure_ascii=False) + "\n")
    return soul


def reap_run(d: Path, raison: str) -> Dict[str, Any]:
    """Fraction conservée d'un run : sa trace (identité complète) + manifeste.

    Le dossier lourd (artefacts) est dissous dans le Styx — la trace suffit
    à reconstruire l'identité et l'historique de l'âme.
    """
    sid = d.name + "-" + datetime.now(timezone.utc).strftime("%H%M%S")
    vertueux = False
    trace_min: Dict[str, Any] = {}
    fichiers: List[Dict[str, Any]] = []
    tj = d / "trace.json"
    if tj.exists():
        try:
            t = json.loads(tj.read_text(encoding="utf-8"))
            trace_min = {k: t.get(k) for k in ("run_id", "tache", "statut", "date", "cerveau")}
            trace_min["steps"] = [s.get("skill") for s in t.get("steps", [])]
            vertueux = bool(t.get("steps") and any(s.get("artifacts") for s in t.get("steps", [])))
        except Exception:
            pass
    total = 0
    for f in sorted(d.rglob("*")):
        if f.is_file():
            s = f.stat().st_size
            total += s
            fichiers.append({"nom": f.name, "octets": s})
    # conserver la trace dans le royaume
    if tj.exists():
        kdir = KEPT / sid
        kdir.mkdir(parents=True, exist_ok=True)
        (kdir / "trace.json").write_text(tj.read_text(encoding="utf-8"), encoding="utf-8")
    return record_soul({
        "id": sid, "type": "run_outdated", "region": _region("run_outdated", vertueux),
        "cible": str(d.relative_to(REPO)) if str(d).startswith(str(REPO)) else str(d),
        "raison": raison, "octets": total, "fichiers": fichiers,
        "trace": trace_min, "gardien": GARDIEN["chien"],
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


def reap_doublons(ids: List[str], lignes: List[Dict[str, Any]], raison: str) -> None:
    """Les doublons partent au Tartare — leur contenu (léger) est conservé entier."""
    record_soul({
        "id": "dup-" + datetime.now(timezone.utc).strftime("%H%M%S%f")[-6:],
        "type": "doublon_memoire", "region": "tartare",
        "cible": "memory:items.jsonl#" + ",".join(ids), "raison": raison,
        "octets": sum(len(str(l.get("titre", "")) + str(l.get("contenu", ""))) for l in lignes),
        "ames": [{"id": l.get("id"), "titre": str(l.get("titre", ""))[:120],
                  "contenu": str(l.get("contenu", ""))[:200]} for l in lignes[:30]],
        "gardien": GARDIEN["chien"],
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


def reap_journal(cible: str, lignes_coupees: int, octets: int) -> None:
    record_soul({
        "id": "jou-" + datetime.now(timezone.utc).strftime("%H%M%S"),
        "type": "journal", "region": "asphodele", "cible": cible,
        "raison": f"{lignes_coupees} lignes anciennes au-delà du seuil",
        "octets": octets, "lignes": lignes_coupees, "gardien": GARDIEN["chien"],
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


def reap_junk(f: Path) -> None:
    record_soul({
        "id": "junk-" + datetime.now(timezone.utc).strftime("%H%M%S%f")[-6:],
        "type": "junk_vide", "region": "tartare",
        "cible": str(f.relative_to(REPO)) if str(f).startswith(str(REPO)) else str(f),
        "raison": "fichier vide (0 octet) — le néant est criminel au Tartare",
        "octets": 0, "gardien": GARDIEN["chien"],
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })


def souls(limit: int = 5000) -> List[Dict[str, Any]]:
    if not SOULS.exists():
        return []
    out = []
    for line in SOULS.read_text(encoding="utf-8").splitlines()[-limit:]:
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out[::-1]


def state() -> Dict[str, Any]:
    ss = souls()
    par_region = {r: sum(1 for s in ss if s["region"] == r) for r in REGIONS}
    return {"royaume": "Les Enfers — le royaume d'Hadès ♇ et de Perséphone 🌸",
            "gardiens": GARDIEN, "regions": REGIONS, "par_region": par_region,
            "ames_total": len(ss),
            "octets_au_royaume": sum(s.get("octets", 0) for s in ss),
            "ames": ss[:400],
            "loi": "Rien n'est jamais vraiment disparu : chaque entité fauchée laisse "
                   "une fraction de données suffisante pour la reconstruire. Cerbère 🐾 "
                   "garde la porte — aucune âme ne remonte sans l'accord du souverain."}


def resurrect(soul_id: str, confirm: bool = False) -> Dict[str, Any]:
    """Cerbère laisse remonter une âme — reconstruction à partir de sa fraction.

    Run : la trace conservée est rendue au monde des vivants (le dossier est
    recréé avec trace.json → le run redevient listable et auditable).
    Doublon : les lignes mémoire sont ré-appendées.
    """
    ss = souls()
    s = next((x for x in ss if x["id"] == soul_id), None)
    if not s:
        return {"ok": False, "statut": "Cerbère ne connaît pas cette âme."}
    if not confirm:
        return {"ok": False, "statut": "Cerbère 🐾 bloque la porte — confirmez la "
                "résurrection (aucune âme ne remonte sans l'accord du souverain).",
                "ame": {k: s.get(k) for k in ("id", "type", "region", "cible", "raison")}}
    if s["type"] == "run_outdated":
        kdir = KEPT / s["id"]
        tj = kdir / "trace.json"
        if tj.exists():
            import shutil
            dest = REPO / s["cible"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(kdir, dest)
            statut = (f"🌟 {s['cible']} ressuscite — trace restituée, le run redevient "
                      f"listable et auditable (les artefacts lourds restent dissous dans le Styx).")
        else:
            statut = "la fraction conservée est incomplète — Cerbère refuse."
            return {"ok": False, "statut": statut}
    elif s["type"] == "doublon_memoire":
        mem = REPO / "output" / "cosmos" / "memory" / "items.jsonl"
        ajoutes = 0
        with mem.open("a", encoding="utf-8") as f:
            for a in s.get("ames", []):
                f.write(json.dumps({"id": a["id"], "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                    "type": "memoire", "titre": a["titre"], "contenu": a["contenu"],
                                    "tags": ["résurrection"], "source": "underworld",
                                    "corps": "pluton"}, ensure_ascii=False) + "\n")
                ajoutes += 1
        statut = f"🌾 {ajoutes} âme(s) mémoire remontée(s) des plaines d'Asphodèle vers la mémoire vivante."
    else:
        statut = ("cette catégorie d'âme ne peut remonter (junk dissous, journal fondu dans le "
                  "Styx) — Cerbère tourne ses trois têtes.")
        return {"ok": False, "statut": statut}
    # retirer l'âme du registre (elle vit de nouveau)
    restantes = [x for x in ss if x["id"] != soul_id]
    SOULS.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in restantes[::-1]),
                     encoding="utf-8")
    return {"ok": True, "statut": statut, "ame": {k: s.get(k) for k in ("id", "type", "region", "cible")}}
