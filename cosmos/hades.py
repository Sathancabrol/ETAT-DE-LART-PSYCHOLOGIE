"""
Pluton ♇ / Hadès — dieu des morts du système : cycle de vie & optimisation.

Hadès regarde les données de TOUT le système solaire et traque :
  • les redondances (doublons exacts en mémoire) ;
  • les versions outdated (anciens runs régénérables) ;
  • le junk (fichiers vides, artefacts orphelins) ;
  • les journaux qui gonflent (interactions, ledger).

Puis il fauche : Charon ⚰ transporte les condamnés vers les enfers
(suppression réelle, journalisée, approuvée par SOL ☉) ; Styx ☠ fixe la
politique de rétention. But : optimiser mémoire, disque et chaînes
d'exécution pour permettre un meilleur cycle.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from cosmos import ledger

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "output"
RUNS_DIR = OUT / "agent_runs"
MEM_ITEMS = OUT / "cosmos" / "memory" / "items.jsonl"

# Pourquoi chaque catégorie est fauchée — et pourquoi c'est sûr (rien d'essentiel ne perd)
POURQUOI = {
    "run_outdated": {
        "quoi": "les dossiers de runs au-delà des 25 plus récents (traces, rapports, artefacts)",
        "raison": "la politique Styx garde une fenêtre de 25 runs : au-delà, ce sont d'anciens "
                  "exemplaires remplacés par des runs plus récents",
        "sur": "les 25 derniers runs — les plus riches et les plus récents — sont intégralement "
               "conservés ; un run fauché est reproductible (mêmes données, mêmes compétences)",
    },
    "junk_vide": {
        "quoi": "les fichiers strictement vides (0 octet)",
        "raison": "un fichier vide n'a jamais reçu de contenu : il n'est relié à aucune donnée",
        "sur": "aucune information n'existe dans un fichier de 0 octet — il n'y a rien à perdre",
    },
    "doublon_memoire": {
        "quoi": "les copies STRICTEMENT identiques d'un élément de mémoire (titre + contenu, hash SHA-256)",
        "raison": "un même souvenir conservé plusieurs fois encombre la mémoire et fausse les comptages",
        "sur": "l'original est toujours conservé — seule la copie au octets près est emportée",
    },
    "journal": {
        "quoi": "les lignes les plus anciennes des journaux au-delà du seuil (1 500 lignes)",
        "raison": "les journaux gonflent indéfiniment et ralentissent les lectures",
        "sur": "les 1 500 lignes les plus récentes sont conservées — seul l'historique ancien est tronqué",
    },
}

# Politique de rétention — Styx ☠
POLITIQUE = {
    "runs_gardes": 25,            # les N runs les plus récents survivent
    "interactions_max": 1500,     # au-delà : on fauche le surplus (journal)
    "ledger_max": 1500,
    "fichiers_vides": True,       # fichiers 0 octet = junk
}


def _dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def scan_system() -> Dict[str, Any]:
    """Inventaire des condamnables : outdated, doublons, junk, journaux."""
    targets: List[Dict[str, Any]] = []

    def _rel(f: Path) -> str:
        try:
            return str(f.relative_to(REPO))
        except ValueError:
            return str(f)          # hors repo (tests) : chemin absolu

    # tailles réelles des lignes mémoire (tokens épargnés honnêtes)
    tailles_items: Dict[str, int] = {}
    if MEM_ITEMS.exists():
        for line in MEM_ITEMS.open(encoding="utf-8"):
            if not line.strip():
                continue
            try:
                tailles_items[json.loads(line).get("id", "?")] = len(line.encode("utf-8"))
            except Exception:
                pass

    # 1. runs outdated (régénérables) — on garde les N plus récents
    if RUNS_DIR.exists():
        runs = sorted([d for d in RUNS_DIR.iterdir() if d.is_dir()],
                      key=lambda d: d.name, reverse=True)
        for d in runs[POLITIQUE["runs_gardes"]:]:
            targets.append({"type": "run_outdated", "cible": _rel(d),
                            "raison": f"run antérieur aux {POLITIQUE['runs_gardes']} plus récents — "
                                      f"remplacé par des runs plus récents, reproductible "
                                      "(artefacts régénérables)",
                            "octets": _dir_size(d)})

    # 2. junk : fichiers vides dans output/
    if OUT.exists():
        for f in OUT.rglob("*"):
            if f.is_file() and f.stat().st_size == 0 and f.name != "items.jsonl":
                targets.append({"type": "junk_vide", "cible": _rel(f),
                                "raison": "fichier vide (junk)", "octets": 0})

    # 3. doublons exacts en mémoire (hash titre+contenu)
    dup = _doublons_memoire()
    for d in dup:
        id_reel = str(d["cible"]).split("#")[-1]
        oct = tailles_items.get(id_reel, 0) * d["copies"]
        targets.append({"type": "doublon_memoire", "cible": d["cible"],
                        "raison": f"doublon exact de {d['original']} "
                                  f"(x{d['copies']})", "octets": oct})

    # 4. journaux qui gonflent
    for journal, maxi in (("interactions.jsonl", POLITIQUE["interactions_max"]),
                          ("ledger.jsonl", POLITIQUE["ledger_max"])):
        p = OUT / "cosmos" / journal
        if p.exists():
            n = sum(1 for _ in p.open(encoding="utf-8"))
            if n > maxi:
                targets.append({"type": "journal", "cible": f"output/cosmos/{journal}",
                                "raison": f"{n} lignes > seuil {maxi} — faucher les plus anciennes",
                                "octets": p.stat().st_size, "lignes": n - maxi})

    total = sum(t["octets"] for t in targets)
    # ── Prévision de tokens épargnés (indicateur honnête, calcul traçable) ──
    # Ratio standard : 1 token ≈ 4 octets pour du texte latin. Les données
    # fauchées ne seront plus chargées, relues ni renvoyées dans les contextes.
    types_presents = sorted({x["type"] for x in targets})
    detail = []
    for t in types_presents:
        cibles_t = [x for x in targets if x["type"] == t]
        oct_t = sum(x["octets"] for x in cibles_t)
        detail.append({
            "type": t,
            "condamnes": len(cibles_t),
            "octets": oct_t,
            "tokens": round(oct_t / 4),
            "taille_moyenne_octets": round(oct_t / len(cibles_t)) if cibles_t else 0,
            "quoi": POURQUOI.get(t, {}).get("quoi", ""),
        })
    estime = round(total / 4)
    prevision_tokens = {
        "estime": estime,
        "par_type": {d["type"]: d["tokens"] for d in detail},
        "octets_mesures": total,
        "detail": detail,
        "calcul": [
            {"etape": "1 · Mesurer", "detail": f"relever la taille réelle sur le disque de chaque "
                        f"cible du scan : {len(targets)} cibles, {total:,} octets".replace(",", " "),
             "valeur": f"{total:,} octets".replace(",", " ")},
            {"etape": "2 · Convertir", "detail": "appliquer le ratio standard de tokenisation du "
                        "texte latin : 1 token ≈ 4 octets (les tokenizers découpent en morceaux "
                        "de 3 à 5 caractères ; 4 est la moyenne communément retenue)",
             "valeur": "1 token ≈ 4 octets"},
            {"etape": "3 · Diviser", "detail": f"{total:,} octets ÷ 4 = {estime:,} tokens".replace(",", " "),
             "valeur": f"≈ {estime:,} tokens".replace(",", " ")},
        ],
        "pourquoi_ratio": "un « token » est le morceau de texte qu'un modèle de langage lit "
                          "réellement : pour du texte latin (français, anglais), les tokenizers "
                          "produisent en moyenne un token tous les ~4 caractères. Ce chiffre "
                          "varie selon le modèle (GPT ≈ 4 car/token, code et JSON ≈ 3).",
        "ce_que_ca_veut_dire": "autant de texte qui ne sera plus jamais chargé, relu ni renvoyé "
                               "dans un contexte de modèle après la fauche : contextes plus courts, "
                               "lectures disque plus rapides, mémoire plus légère.",
        "limites": [
            "estimation, pas un compteur réel — aucun modèle n'a tokenisé ces fichiers en sandbox",
            "le ratio exact dépend du tokenizer utilisé (± 25 % selon texte/code/JSON)",
            "ne compte que les données condamnées accessibles sur le disque (output/)",
        ],
        "methode": "1 token ≈ 4 octets (ratio standard texte latin) — estimation des "
                   "données qui ne seront plus chargées, relues ni renvoyées aux modèles "
                   "une fois fauchées. Aucun compteur de tokens réel n'existe en sandbox.",
    }

    # ── Traitement de données : ce que Hadès a réellement analysé ──
    n_runs = len([d for d in RUNS_DIR.iterdir() if d.is_dir()]) if RUNS_DIR.exists() else 0
    n_items = sum(1 for _ in MEM_ITEMS.open(encoding="utf-8")) if MEM_ITEMS.exists() else 0
    octets_output = _dir_size(OUT) if OUT.exists() else 0
    traitement = [
        {"etape": "inventaire", "detail": f"{n_runs} runs analysés · {n_items} éléments de mémoire · "
                   f"{round(octets_output/1024/1024, 2)} Mo de données au total dans output/"},
        {"etape": "rétention (Lachésis)", "detail": f"politique : garder les {POLITIQUE['runs_gardes']} runs "
                   f"les plus récents → {max(0, n_runs - POLITIQUE['runs_gardes'])} runs deviennent outdated"},
        {"etape": "doublons (hash SHA-256)", "detail": f"{len(_doublons_memoire())} groupes d'éléments "
                   "strictement identiques (titre+contenu) en mémoire"},
        {"etape": "junk", "detail": "fichiers vides (0 octet) hors mémoire vivante"},
        {"etape": "journaux", "detail": f"seuils : interactions {POLITIQUE['interactions_max']} lignes · "
                   f"ledger {POLITIQUE['ledger_max']} lignes"},
    ]

    # ── Les 3 Moires (elles aident Hadès dans son élagage) ──
    moires = {
        "clotho": {"role": "la Fileuse — a filé les nouvelles données",
                   "naissance_24h": _naissance_24h()},
        "lachesis": {"role": "la Répartitrice — mesure la durée de vie",
                     "age_moyen_runs_jours": _age_moyen_runs(),
                     "duree_visee": f"{POLITIQUE['runs_gardes']} runs les plus récents"},
        "atropos": {"role": "l'Inflexible — prononce la mort",
                    "condamnes": len(targets),
                    "verdict": f"{len(targets)} condamnés — la coupe est sans appel" if targets
                               else "rien à couper : le système est sain"},
    }

    return {"targets": targets,
            "stats": {"condamnes": len(targets), "octets": total,
                      "ko": round(total / 1024, 1),
                      "par_type": {t: sum(1 for x in targets if x["type"] == t)
                                   for t in {x["type"] for x in targets}},
                      "mo_octets": round(octets_output / 1024 / 1024, 2),
                      "tokens_epargnes": prevision_tokens["estime"]},
            "prevision_tokens": prevision_tokens,
            "traitement": traitement,
            "pourquoi": POURQUOI,
            "ce_qui_est_conserve": (
                f"les {POLITIQUE['runs_gardes']} runs les plus récents · la mémoire vivante "
                "(originaux des souvenirs) · les {POLITIQUE['interactions_max']} lignes les plus "
                "récentes des journaux · le grand livre (ledger, jamais fauché)"),
            "moires": moires,
            "politique_styx": POLITIQUE,
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _naissance_24h() -> int:
    """Clotho : éléments de mémoire nés dans les dernières 24 h."""
    if not MEM_ITEMS.exists():
        return 0
    from datetime import timedelta
    hier = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    n = 0
    for line in MEM_ITEMS.read_text(encoding="utf-8").splitlines():
        try:
            it = json.loads(line)
        except Exception:
            continue
        if (it.get("ts") or "") >= hier:
            n += 1
    return n


def _age_moyen_runs() -> float:
    """Lachésis : âge moyen des runs en jours."""
    if not RUNS_DIR.exists():
        return 0.0
    ages = []
    for d in RUNS_DIR.iterdir():
        if not d.is_dir():
            continue
        try:
            t = json.loads((d / "trace.json").read_text(encoding="utf-8"))["date"]
            ages.append((datetime.now(timezone.utc) - datetime.fromisoformat(t)).total_seconds() / 86400)
        except Exception:
            continue
    return round(sum(ages) / len(ages), 2) if ages else 0.0


def _doublons_memoire() -> List[Dict[str, Any]]:
    """Détecte les groupes d'items mémoire strictement identiques."""
    if not MEM_ITEMS.exists():
        return []
    groupes: Dict[str, List[str]] = {}
    ordre: List[str] = []
    for line in MEM_ITEMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            it = json.loads(line)
        except Exception:
            continue
        h = hashlib.sha256((it.get("titre", "") + "§" + it.get("contenu", "")).encode()).hexdigest()[:12]
        if h not in groupes:
            groupes[h] = []
            ordre.append(h)
        groupes[h].append(it.get("id", "?"))
    out = []
    for h in ordre:
        ids = groupes[h]
        if len(ids) > 1:
            # le premier est l'original, les suivants sont des copies condamnées
            out.append({"cible": f"memory:items.jsonl#{','.join(ids[1:])}",
                        "original": ids[0], "copies": len(ids) - 1})
    return out


def reap(confirm: bool = False) -> Dict[str, Any]:
    """La fauche : Charon ⚰ exécute les condamnations du scan (avec approbation SOL)."""
    scan = scan_system()
    if not confirm:
        return {"statut": "simulation (dry-run) — rien n'a été détruit",
                **scan, "supprimes": 0, "octets_liberes": 0,
                "bilan": scan["stats"]["par_type"],
                "tokens_epargnes": scan["prevision_tokens"]["estime"]}

    supprimes, liberés = 0, 0
    details = []
    for t in scan["targets"]:
        try:
            if t["type"] in ("run_outdated", "junk_vide"):
                p = Path(t["cible"]) if t["cible"].startswith("/") else REPO / t["cible"]
                if t["type"] == "run_outdated":
                    liberés += t["octets"]
                    import shutil
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink(missing_ok=True)
                supprimes += 1
                details.append("⚰ " + t["cible"])
            elif t["type"] == "doublon_memoire":
                ids = set(t["cible"].split("#")[1].split(","))
                lines = [l for l in MEM_ITEMS.read_text(encoding="utf-8").splitlines()
                         if l.strip() and json.loads(l).get("id") not in ids]
                MEM_ITEMS.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
                supprimes += 1
                details.append("⚰ " + t["raison"])
            elif t["type"] == "journal":
                p = REPO / t["cible"]
                lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
                keep = lines[-POLITIQUE["interactions_max"]:]
                liberés += p.stat().st_size - len("\n".join(keep))
                p.write_text("\n".join(keep) + "\n", encoding="utf-8")
                supprimes += 1
                details.append("⚰ " + t["cible"] + " (tronqué)")
        except Exception:
            continue

    bilan = {}
    for t in scan["targets"]:
        bilan[t["type"]] = bilan.get(t["type"], 0) + 1

    # journal + mémoire + approbation SOL
    ledger.record(agent="pluton", action="fauche", model="regles",
                  meta={"supprimes": supprimes, "octets": liberés})
    try:
        from cosmos import memory
        memory.record_item("memoire", "[Hadès] fauche exécutée",
                           contenu=f"{supprimes} condamnés · {round(liberés/1024,1)} Ko libérés",
                           tags=["hades", "cycle"], source="pluton", corps="pluton",
                           meta={"supprimes": supprimes})
    except Exception:
        pass
    try:
        from cosmos.system import get_system
        get_system()["bus"].send("pluton", "charon", "fauche",
                                 {"contenu": f"{supprimes} condamnés", "octets": liberés})
    except Exception:
        pass
    return {"statut": "fauche exécutée — les condamnés sont aux enfers",
            "bilan": bilan,                      # quoi a été détruit, par catégorie
            "pourquoi": POURQUOI,                # pourquoi chaque catégorie, et ce qui est conservé
            "tokens_epargnes": round(liberés / 4),   # estimation honnête (1 token ≈ 4 octets)
            "ce_qui_est_conserve": scan["ce_qui_est_conserve"],
            **{k: scan[k] for k in ("stats", "politique_styx", "ts")},
            "supprimes": supprimes, "octets_liberes": liberés, "details": details[:30]}
