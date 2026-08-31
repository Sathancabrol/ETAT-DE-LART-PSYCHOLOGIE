"""
Mars ♂ — l'armurier du système solaire.

Cas d'usage : un agent a besoin d'un outil spécifique pour calculer et
visualiser des données complexes. Le protocole de l'armurerie :

  1. RECHERCHE OPEN SOURCE — si un outil libre existe et peut être
     reproduit/utilisé, Mars le recommande (pas de réinvention) ;
  2. MAQUETTE — sinon, Deimos ◦ (innovation & conception) dessine une
     maquette interactive du futur outil ;
  3. FORGE — Phobos ◂ (création de software) transforme la maquette en
     outil fonctionnel autoportant (HTML+canvas, calculs réels en JS) ;
  4. LIVRAISON — l'outil est remis à l'agent demandeur, l'interaction est
     approuvée par SOL ☉ et journalisée au grand livre.

Registre persistant : output/cosmos/armory.json
Artefacts : output/cosmos/armory/{id}_maquette.html et {id}_outil.html
"""

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from cosmos import ledger

try:
    from cosmos import ledger as _ledger
    ARMORY_DIR = _ledger.COSMOS_DIR / "armory"
    ARMORY_PATH = _ledger.COSMOS_DIR / "armory.json"
except Exception:  # pragma: no cover
    from pathlib import Path
    ARMORY_DIR = Path("output/cosmos/armory")
    ARMORY_PATH = Path("output/cosmos/armory.json")

# ── Catalogue open source (reproduire / utiliser plutôt que réinventer) ──────

OSS_CATALOG: List[Dict[str, Any]] = [
    {"id": "matplotlib", "name": "Matplotlib", "licence": "PSF (BSD)",
     "pour": r"courbe|courbes|graphique\s*2d|histogram|scatter|nuage|statique|publication",
     "pourquoi": "tracé 2D scientifique de référence (Python), export publication"},
    {"id": "plotly", "name": "Plotly", "licence": "MIT",
     "pour": r"interactif|dashboard|interactiv|explorat|hover",
     "pourquoi": "graphiques interactifs web, zoom/hover, tableaux de bord"},
    {"id": "d3", "name": "D3.js", "licence": "BSD-3",
     "pour": r"graphe|réseau|reseau|liens|n[œoe]uds|force|obsidian|relation",
     "pourquoi": "graphe de forces, visualisation de réseaux et de liens en SVG"},
    {"id": "threejs", "name": "Three.js", "licence": "MIT",
     "pour": r"3d|trois\s*dimensions|volume|terrain|orbite|plan[èe]te\s*3d|surface",
     "pourquoi": "rendu 3D temps réel dans le navigateur (WebGL)"},
    {"id": "networkx", "name": "NetworkX", "licence": "BSD-3",
     "pour": r"graphe|réseau|reseau|chemin|centralit|communaut",
     "pourquoi": "calculs sur graphes : chemins, centralités, communautés"},
    {"id": "bokeh", "name": "Bokeh", "licence": "BSD-3",
     "pour": r"flux|streaming|temps\s*r[ée]el|dashboard|interactif",
     "pourquoi": "visualisation interactive de flux de données en Python"},
    {"id": "scipy", "name": "SciPy", "licence": "BSD",
     "pour": r"calcul|optimis|r[ée]gression|int[ée]grale|statistique|mod[èe]lis",
     "pourquoi": "calcul scientifique : optimisation, régression, statistiques"},
    {"id": "pandas", "name": "pandas", "licence": "BSD",
     "pour": r"donn[ée]es|tableau|csv|s[ée]rie|nettoyage|agr[ée]gat",
     "pourquoi": "manipulation et agrégation de données tabulaires"},
    {"id": "vegalite", "name": "Vega-Lite", "licence": "BSD-3",
     "pour": r"d[ée]claratif|sp[ée]cification|grammaire|rapide",
     "pourquoi": "grammaire de graphiques déclarative (JSON → chart)"},
    {"id": "manim", "name": "Manim", "licence": "MIT",
     "pour": r"animation|p[ée]dagog|vid[ée]o|expliquer",
     "pourquoi": "animations mathématiques pédagogiques (3Blue1Brown)"},
]

# ── Typage des données → gabarit d'outil ─────────────────────────────────────

DATA_KINDS = [
    ("reseau", r"r[ée]seau|graphe|liens?|n[œoe]uds?|relation|constellation|arbre"),
    ("distribution", r"distribution|histogram|statistique|[ée]chantillon|variance|moyenne"),
    ("series", r"s[ée]rie|temporel|temps|courbe|[ée]volution|tendanc|chronolog"),
    ("surface", r"surface|3d|terrain|champ|carte\s*de\s*chaleur|heatmap|volum"),
]


def detect_data_kind(besoin: str) -> str:
    m = (besoin or "").lower()
    for kind, pat in DATA_KINDS:
        if re.search(pat, m):
            return kind
    return "dashboard"


def search_opensource(besoin: str) -> List[Dict[str, Any]]:
    """Cherche un outil libre couvrant le besoin (moteur à règles, classement)."""
    m = (besoin or "").lower()
    scored = []
    for tool in OSS_CATALOG:
        hits = re.findall(tool["pour"], m)
        if hits:
            scored.append({**tool, "score": len(hits)})
    scored.sort(key=lambda t: -t["score"])
    return scored


# ── Registre ─────────────────────────────────────────────────────────────────

def _load() -> Dict[str, Any]:
    if ARMORY_PATH.exists():
        try:
            return json.loads(ARMORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"requests": []}


def _save(data: Dict[str, Any]) -> None:
    ARMORY_DIR.mkdir(parents=True, exist_ok=True)
    ARMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARMORY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:40] or "outil"


def list_requests() -> List[Dict[str, Any]]:
    return _load()["requests"]


def get_request(rid: str) -> Dict[str, Any] | None:
    return next((r for r in _load()["requests"] if r["id"] == rid), None)


def request_tool(agent: str, besoin: str, donnees: str = "") -> Dict[str, Any]:
    """Protocole de l'armurerie : recherche OSS → maquette Deimos le cas échéant.

    L'agent demandeur s'adresse à Mars ; l'interaction est approuvée par SOL.
    """
    besoin = (besoin or "").strip()
    if not besoin:
        raise ValueError("description du besoin requise")
    agent = (agent or "user").strip().lower()[:30] or "user"

    data = _load()
    base = _slug(besoin)
    rid, n = base, 2
    while any(r["id"] == rid for r in data["requests"]):
        rid = f"{base}-{n}"
        n += 1

    kind = detect_data_kind(besoin + " " + donnees)
    oss = search_opensource(besoin + " " + donnees)
    strong = bool(oss) and oss[0]["score"] >= 2

    req = {
        "id": rid, "agent": agent, "besoin": besoin[:400],
        "donnees": (donnees or "")[:200], "data_kind": kind,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "opensource": oss[:3] if oss else [],
        "statut": ("opensource recommandé" if strong else "maquette conçue"),
        "etapes": [], "forgeur": None, "concepteur": None,
    }
    if strong:
        best = oss[0]
        req["recommandation"] = {
            "outil": best["name"], "licence": best["licence"],
            "pourquoi": best["pourquoi"],
            "consigne": f"reproduire / utiliser {best['name']} (libre, {best['licence']}) "
                        "plutôt que réinventer — Mars fournit l'intégration"}
        req["etapes"].append(f"recherche open source : {best['name']} couvre le besoin")
    else:
        req["etapes"].append("recherche open source : aucun outil libre ne couvre le besoin")
        # Deimos ◦ conçoit la maquette
        ARMORY_DIR.mkdir(parents=True, exist_ok=True)
        path = ARMORY_DIR / f"{rid}_maquette.html"
        path.write_text(_maquette_html(req), encoding="utf-8")
        req["maquette"] = str(path)
        req["concepteur"] = "deimos"
        req["etapes"].append("Deimos ◦ a conçu la maquette — prête pour la forge de Phobos")
    data["requests"].append(req)
    _save(data)

    # SOL approuve l'interaction agent → Mars, puis journal
    try:
        from cosmos.system import get_system
        get_system()["bus"].send(agent, "mars", "demande_outil",
                                 {"contenu": besoin[:200], "outil": rid})
    except Exception:
        pass
    ledger.record(agent="mars", action=f"demande_outil:{rid}", model="regles",
                  meta={"agent": agent, "statut": req["statut"]})
    try:
        from cosmos import memory
        memory.record_item("outil", f"[armurerie] {besoin[:80]}",
                           contenu=(f"statut : {req['statut']} ; "
                                    + (f"recommandation {req['recommandation']['outil']}"
                                       if req.get("recommandation") else "maquette Deimos prête")),
                           tags=["armurerie", "mars", kind], source="mars", corps="mars",
                           meta={"request": rid})
    except Exception:
        pass
    return req


def forge_tool(rid: str) -> Dict[str, Any]:
    """Phobos ◂ forge l'outil fonctionnel à partir de la maquette de Deimos."""
    data = _load()
    req = next((r for r in data["requests"] if r["id"] == rid), None)
    if req is None:
        raise ValueError(f"demande inconnue : {rid}")
    if req["statut"] == "outil livré":
        return req

    ARMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = ARMORY_DIR / f"{rid}_outil.html"
    path.write_text(_tool_html(req), encoding="utf-8")
    req["outil"] = str(path)
    req["statut"] = "outil livré"
    req["forgeur"] = "phobos"
    if not req.get("concepteur"):
        req["concepteur"] = "deimos"
    req["etapes"].append("Phobos ◂ a forgé l'outil fonctionnel — livré à " + req["agent"])
    _save(data)

    try:
        from cosmos.system import get_system
        get_system()["bus"].send("phobos", req["agent"], "livraison_outil",
                                 {"contenu": rid, "path": str(path)})
    except Exception:
        pass
    ledger.record(agent="phobos", action=f"forge_outil:{rid}", model="regles",
                  meta={"destinataire": req["agent"]})
    return req


# ── Gabarits HTML (maquette Deimos / outil Phobos) ───────────────────────────

def _shell(req: Dict[str, Any], body: str, badge: str, badge_color: str) -> str:
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{'Maquette' if badge == 'MAQUETTE' else 'Outil'} — {req['id']} · armurerie de Mars ♂</title>
<style>
:root{{--bg:#0b0f1a;--card:#131a2b;--border:#233149;--txt:#e2e8f0;--muted:#7c8aa5;--red:#f87171;--purple:#c084fc}}
*{{box-sizing:border-box;margin:0}}
body{{background:radial-gradient(1200px 600px at 70% -10%,#1c1230 0%,var(--bg) 55%);color:var(--txt);
font:14px/1.5 Inter,system-ui,sans-serif;padding:18px}}
header{{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:14px}}
h1{{font-size:16px}} .sub{{color:var(--muted);font-size:11.5px}}
.badge{{font:700 10px/1 ui-monospace,monospace;letter-spacing:.14em;color:{badge_color};
border:1px solid {badge_color}55;border-radius:99px;padding:5px 10px;background:{badge_color}14}}
.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:14px}}
.card h3{{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
canvas{{width:100%;border-radius:10px;background:#0a0e18}}
.ctl{{display:flex;align-items:center;gap:8px;margin:7px 0;font-size:12px;color:var(--muted)}}
input[type=range]{{flex:1;accent-color:var(--red)}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));gap:8px}}
.stat{{background:#0a0e18;border:1px solid var(--border);border-radius:10px;padding:8px}}
.stat b{{display:block;font:700 17px/1.2 ui-monospace,monospace;color:var(--txt)}}
.stat span{{font-size:9.5px;color:var(--muted)}}
footer{{margin-top:14px;color:var(--muted);font-size:10.5px;text-align:center}}
.wire{{border:2px dashed #3b4a68;border-radius:10px;display:flex;align-items:center;justify-content:center;
color:#5b6b8c;font-size:11px;letter-spacing:.1em;min-height:180px;background:#0a0e1899}}
</style></head><body>
<header><span style="font-size:22px">♂</span>
<h1>{req['besoin'][:90]}</h1>
<span class="badge">{badge}</span></header>
<p class="sub">demande de <b>{req['agent']}</b> · type de données : <b>{req['data_kind']}</b> ·
conception Deimos ◦ · forge Phobos ◂ · armurerie de Mars</p>
<div class="grid">{body}</div>
<footer>Mars ♂ passe son temps à chercher des solutions aux problèmes des autres agents —
{'MAQUETTE non fonctionnelle (Deimos ◦, innovation & conception)' if badge == 'MAQUETTE' else 'données de démonstration honnêtes — branchez vos vraies données dans DATA'}</footer>
</body></html>"""


def _maquette_html(req: Dict[str, Any]) -> str:
    k = req["data_kind"]
    viz = {"reseau": "ZONE GRAPHE / NŒUDS-LIENS", "distribution": "ZONE HISTOGRAMME",
           "series": "ZONE COURBES TEMPORELLES", "surface": "ZONE CARTE DE CHALEUR / SURFACE",
           "dashboard": "ZONE TABLEAU MULTI-PANNEAUX"}.get(k, "ZONE VISUALISATION")
    body = f"""
<div class="card"><h3>Visualisation — {k}</h3><div class="wire" style="min-height:260px">{viz}</div></div>
<div class="card"><h3>Curseurs de paramètres</h3>
  <div class="wire" style="min-height:38px">PARAMÈTRE A</div>
  <div class="wire" style="min-height:38px">PARAMÈTRE B</div>
  <div class="wire" style="min-height:38px">SÉLECTEUR DE MÉTRIQUE</div></div>
<div class="card"><h3>Calculs</h3><div class="wire">ZONE RÉSULTATS (moyenne, écart-type, corrélations…)</div></div>
<div class="card"><h3>Données</h3><div class="wire">TABLE / SOURCE DE DONNÉES</div></div>"""
    return _shell(req, body, "MAQUETTE", "var(--purple)")


def _tool_html(req: Dict[str, Any]) -> str:
    k = req["data_kind"]
    return _shell(req, f"""
<div class="card"><h3>Visualisation — {k}</h3><canvas id="cv" height="300"></canvas></div>
<div class="card"><h3>Paramètres</h3>
  <div class="ctl">amplitude <input id="amp" type="range" min="5" max="100" value="60"><b id="ampv" style="color:var(--txt)">60</b></div>
  <div class="ctl">bruit <input id="noise" type="range" min="0" max="100" value="25"><b id="noisev" style="color:var(--txt)">25</b></div>
  <div class="ctl">points <input id="npts" type="range" min="10" max="120" value="48"><b id="nptsv" style="color:var(--txt)">48</b></div>
  <div class="ctl">métrique <select id="metric" style="background:#0a0e18;color:var(--txt);border:1px solid var(--border);border-radius:8px;padding:4px 8px">
    <option value="brute">série brute</option><option value="lisse">moyenne mobile (5)</option><option value="cumul">cumul</option></select></div>
</div>
<div class="card"><h3>Calculs (réels, en direct)</h3><div class="stats" id="stats"></div></div>
<div class="card"><h3>Données</h3><div style="max-height:170px;overflow:auto"><table id="tbl"
style="width:100%;border-collapse:collapse;font:11px ui-monospace,monospace"></table></div></div>
<script>
// Outil forgé par Phobos ◂ sur maquette de Deimos ◦ — remplacez DATA par vos données.
const KIND={json.dumps(k)};
let DATA=[];
function gen(a,n,noise){{
  DATA=[];let v=50;
  for(let i=0;i<n;i++){{
    v+= (Math.random()-.5)*noise*.6; v=Math.max(2,Math.min(100,v));
    const seasonal= a*.5*Math.sin(i/ (3+n/24) );
    DATA.push({{x:i,y:Math.max(0,Math.min(120,v*.55+seasonal+a*.4*Math.random()))}});
  }}
}}
function serie(){{ // applique la métrique choisie
  const m=document.getElementById('metric').value;
  if(m==='lisse')return DATA.map((d,i)=>{{const w=DATA.slice(Math.max(0,i-2),i+3);
    return{{x:d.x,y:w.reduce((s,e)=>s+e.y,0)/w.length}};}});
  if(m==='cumul'){{let c=0;return DATA.map(d=>{{c+=d.y;return{{x:d.x,y:c}};}});}}
  return DATA;
}}
function stats(v){{ // calculs réels : moyenne, écart-type, min, max, tendance
  const n=v.length,mean=v.reduce((s,e)=>s+e.y,0)/n;
  const sd=Math.sqrt(v.reduce((s,e)=>s+(e.y-mean)**2,0)/n);
  const mn=Math.min(...v.map(e=>e.y)),mx=Math.max(...v.map(e=>e.y));
  const a=v[0].y,b=v[n-1].y,trend=((b-a)/Math.max(1,a)*100);
  return{{mean,sd,mn,mx,trend}};
}}
function draw(){{
  const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
  const W=cv.width=cv.clientWidth*2,H=cv.height=600;ctx.scale(1,1);
  ctx.fillStyle='#0a0e18';ctx.fillRect(0,0,W,H);
  const v=serie(),s=stats(v),maxY=Math.max(...v.map(e=>e.y))*1.1||1;
  ctx.strokeStyle='#1c2740';ctx.lineWidth=1;
  for(let g=0;g<=4;g++){{const y=H*(g/4);ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}}
  if(KIND==='distribution'){{
    const bins=16,h=new Array(bins).fill(0);
    v.forEach(e=>{{h[Math.min(bins-1,Math.floor(e.y/maxY*bins))]++;}});
    const mb=Math.max(...h);
    h.forEach((c,i)=>{{const bh=c/mb*(H-60),x=i*(W/bins)+8;
      ctx.fillStyle='#f87171cc';ctx.fillRect(x,H-30-bh,W/bins-14,bh);
      ctx.fillStyle='#7c8aa5';ctx.font='18px ui-monospace';ctx.fillText((maxY*(i+1)/bins).toFixed(0),x+6,H-8);}});
  }} else if(KIND==='reseau'){{
    const n=Math.min(24,v.length),nodes=[];
    for(let i=0;i<n;i++)nodes.push({{x:W/2+Math.cos(i*2.4)* (120+v[i].y*2.6)*Math.min(1,W/700),
      y:H/2+Math.sin(i*2.4)*(90+v[i].y*1.8),r:6+v[i].y*.12}});
    ctx.strokeStyle='#f8717155';
    nodes.forEach((a,i)=>nodes.slice(i+1).forEach(b=>{{const d=Math.hypot(a.x-b.x,a.y-b.y);
      if(d<260){{ctx.globalAlpha=1-d/260;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();}}}}));
    ctx.globalAlpha=1;nodes.forEach((nd,i)=>{{ctx.fillStyle=i?'#f87171':'#c084fc';
      ctx.beginPath();ctx.arc(nd.x,nd.y,nd.r,0,7);ctx.fill();}});
  }} else {{
    ctx.beginPath();ctx.lineWidth=4;ctx.strokeStyle='#f87171';
    ctx.shadowColor='#f8717166';ctx.shadowBlur=14;
    v.forEach((e,i)=>{{const x=i/(v.length-1)*(W-30)+15,y=H-30-(e.y/maxY)*(H-70);
      i?ctx.lineTo(x,y):ctx.moveTo(x,y);}});ctx.stroke();ctx.shadowBlur=0;
    if(KIND==='surface'){{
      ctx.globalAlpha=.35;
      for(let i=0;i<v.length-1;i++){{const x=i/(v.length-1)*(W-30)+15,x2=(i+1)/(v.length-1)*(W-30)+15;
        ctx.fillStyle='#7c3aed';ctx.beginPath();ctx.moveTo(x,H-30);ctx.lineTo(x,H-30-(v[i].y/maxY)*(H-70));
        ctx.lineTo(x2,H-30-(v[i+1].y/maxY)*(H-70));ctx.lineTo(x2,H-30);ctx.fill();}}
      ctx.globalAlpha=1;}}
  }}
  document.getElementById('stats').innerHTML=
    [['moyenne',s.mean.toFixed(1)],['écart-type',s.sd.toFixed(1)],['min',s.mn.toFixed(1)],
     ['max',s.mx.toFixed(1)],['tendance',(s.trend>0?'+':'')+s.trend.toFixed(1)+'%']]
    .map(([l,val])=>`<div class="stat"><b>${{val}}</b><span>${{l}}</span></div>`).join('');
  const tb=document.getElementById('tbl');
  tb.innerHTML='<tr><th style="text-align:left;padding:3px 6px;color:#7c8aa5">x</th>'+
    '<th style="text-align:left;padding:3px 6px;color:#7c8aa5">y</th></tr>'+
    v.slice(-10).map(e=>`<tr><td style="padding:3px 6px;border-top:1px solid #1c2740">${{e.x}}</td>`+
    `<td style="padding:3px 6px;border-top:1px solid #1c2740">${{e.y.toFixed(2)}}</td></tr>`).join('');
}}
function bind(id,fn){{const el=document.getElementById(id);
  el.oninput=()=>{{document.getElementById(id+'v')&&(document.getElementById(id+'v').textContent=el.value);fn();}};}}
function refresh(){{gen(+document.getElementById('amp').value,
  +document.getElementById('npts').value,+document.getElementById('noise').value);draw();}}
bind('amp',refresh);bind('noise',refresh);bind('npts',refresh);
document.getElementById('metric').onchange=draw;
addEventListener('resize',draw);refresh();
</script>""", "OUTIL ⚒", "var(--red)")


# ═══ Boucle d'ingénieur / R&D de Mars sur les outils open source ═════════════
# Quand un outil est open source : Mars le REGARDE, l'ANALYSE, le RECONSTRUIT
# à l'identique, l'AMÉLIORE, l'UTILISE, ré-améliore (boucle), puis PRÉSENTE.
FORGE_STAGES = ["examiner", "analyser", "reconstruire à l'identique",
                "améliorer", "utiliser", "améliorer — boucle R&D", "présenter"]

try:
    FORGE_PATH = _ledger.COSMOS_DIR / "forge.json"
except Exception:  # pragma: no cover
    FORGE_PATH = Path("output/cosmos/forge.json")

FORGE_NOTES = {
    "examiner": "lecture du code source, de la licence et des dépendances",
    "analyser": "architecture, points forts, failles, angle d'amélioration",
    "reconstruire à l'identique": "réplication fonctionnelle — on prouve qu'on comprend",
    "améliorer": "nos données/marques propres : réactivité, intégration Cognitorium",
    "utiliser": "mise en production interne (Sera Victoria, Sebas, Mercure)",
    "améliorer — boucle R&D": "retours du terrain → nouvelle itération d'amélioration",
    "présenter": "démonstration à SOL et à l'utilisateur — documentation et limites",
}


def _forge_load() -> Dict[str, Any]:
    if FORGE_PATH.exists():
        try:
            return json.loads(FORGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"forge": []}


def _forge_save(data: Dict[str, Any]) -> None:
    FORGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FORGE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def forge_find(fid: str) -> Dict[str, Any] | None:
    return next((f for f in _forge_load()["forge"] if f["id"] == fid), None)


def forge_find_by_tool(tool: str) -> Dict[str, Any] | None:
    t = (tool or "").lower().strip()
    return next((f for f in _forge_load()["forge"]
                 if t in (f.get("outil") or "").lower() or t in f["id"]), None)


def forge_start(outil: str, nom: str = "", url: str = "") -> Dict[str, Any]:
    """Mars ouvre le chantier R&D d'un outil open source."""
    outil = (outil or "").strip()[:80] or "outil inconnu"
    ex = forge_find_by_tool(outil)
    if ex:
        return {"ok": True, "deja": True, "forge": ex,
                "statut": f"⚒ {ex['outil']} est déjà au stade « {ex['stages'][ex['stage']] } »"}
    f = {"id": _slug(outil) or "forge", "outil": outil,
         "nom": nom or outil, "url": url,
         "stage": 0, "stages": FORGE_STAGES,
         "historique": [{"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "stage": FORGE_STAGES[0], "note": FORGE_NOTES[FORGE_STAGES[0]]}],
         "ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    data = _forge_load()
    data["forge"].append(f)
    _forge_save(data)
    return {"ok": True, "deja": False, "forge": f,
            "statut": f"⚒ Mars examine « {outil} » — code source, licence, dépendances"}


def forge_advance(fid: str) -> Dict[str, Any]:
    """Un cran de la boucle d'ingénieur : examiner → analyser → reconstruire →
    améliorer → utiliser → améliorer (boucle) → présenter."""
    data = _forge_load()
    f = next((x for x in data["forge"] if x["id"] == fid), None)
    if not f:
        return {"ok": False, "statut": "chantier inconnu"}
    if f["stage"] >= len(FORGE_STAGES) - 1:
        return {"ok": True, "forge": f,
                "statut": f"🏆 « {f['outil']} » est présenté — la boucle R&D continue au fil du terrain"}
    f["stage"] += 1
    st = FORGE_STAGES[f["stage"]]
    f["historique"].append({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "stage": st, "note": FORGE_NOTES[st]})
    _forge_save(data)
    return {"ok": True, "forge": f, "statut": f"⚒ « {f['outil']} » → {st} : {FORGE_NOTES[st]}"}


def forge_list() -> List[Dict[str, Any]]:
    return _forge_load()["forge"]
