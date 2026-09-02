from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
import os
from typing import Optional, List, Dict, Any

from app.database import init_db, get_db_connection, DB_PATH

app = FastAPI(title="Cognitorium v4", version="4.0")

@app.on_event("startup")
def startup_event():
    init_db()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

class MetacognitiveTraceCreate(BaseModel):
    session_id: str
    phase: str
    objective: Optional[str] = None
    criteria: Optional[str] = None
    constraints: Optional[str] = None
    ai_query: Optional[str] = None
    ai_response: Optional[str] = None
    evaluation: Optional[str] = None
    confidence: Optional[int] = None
    action_plan: Optional[str] = None

@app.on_event("startup")
def _warm_imports():
    """Pré-importe les modules chargés paresseusement par les endpoints dans
    le thread principal — évite les deadlocks _ModuleLock quand plusieurs
    requêtes concurrentes déclenchent le même import (vu en prod sur
    /api/dashboard/metrics)."""
    try:
        import agent.core.registry  # noqa: F401
    except Exception:
        pass


@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

# ──────────────── DATABASE API ────────────────

@app.get("/api/nodes")
def get_nodes(search: Optional[str] = None, domain: Optional[str] = None,
              type_pub: Optional[str] = None, niveau: Optional[str] = None):
    conn = get_db_connection()
    query = "SELECT * FROM references_table WHERE 1=1"
    params = []
    if search:
        query += " AND (reference_courte LIKE ? OR theme LIKE ? OR question_scientifique LIKE ? OR tags LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    if domain and domain != "all":
        query += " AND sous_domaine = ?"
        params.append(domain)
    if type_pub and type_pub != "all":
        query += " AND type_publication = ?"
        params.append(type_pub)
    if niveau and niveau != "all":
        query += " AND niveau_preuve = ?"
        params.append(niveau)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

@app.get("/api/nodes/{node_id}")
def get_node_detail(node_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM references_table WHERE id = ?", (node_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Not found")
    node_data = dict(row)
    cursor.execute("""
        SELECT target_id, relation_type FROM reference_relations WHERE source_id = ?
        UNION
        SELECT source_id as target_id, relation_type FROM reference_relations WHERE target_id = ?
    """, (node_id, node_id))
    node_data["relations_parsed"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return node_data

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM references_table")
    total = c.fetchone()[0]
    c.execute("SELECT AVG(trust_factor),MIN(trust_factor),MAX(trust_factor) FROM references_table")
    avg_t, min_t, max_t = c.fetchone()
    c.execute("SELECT sous_domaine,COUNT(*) FROM references_table GROUP BY sous_domaine HAVING sous_domaine IS NOT NULL")
    subdomain = {r[0]:r[1] for r in c.fetchall()}
    c.execute("SELECT type_publication,COUNT(*) FROM references_table GROUP BY type_publication HAVING type_publication IS NOT NULL")
    pubtype = {r[0]:r[1] for r in c.fetchall()}
    c.execute("SELECT niveau_preuve,COUNT(*) FROM references_table GROUP BY niveau_preuve HAVING niveau_preuve IS NOT NULL")
    preuve = {r[0]:r[1] for r in c.fetchall()}
    c.execute("SELECT AVG(citations_google_scholar) FROM references_table")
    avg_cit = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM reference_relations")
    total_rel = c.fetchone()[0]
    conn.close()
    return {"total_references": total, "average_trust_factor": round(avg_t or 0, 1),
            "min_trust": min_t, "max_trust": max_t, "average_citations": round(avg_cit, 1),
            "subdomain_distribution": subdomain, "publication_distribution": pubtype,
            "preuve_distribution": preuve, "total_relations": total_rel}

@app.get("/api/timeline")
def get_timeline():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT id, reference_courte, annee, type_publication, sous_domaine, theme,
                 trust_factor, niveau_preuve, citations_google_scholar, consensus_actuel
                 FROM references_table ORDER BY annee, trust_factor DESC""")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/api/pyramid")
def get_pyramid():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, reference_courte, niveau_preuve, trust_factor, sous_domaine FROM references_table")
    refs = [dict(r) for r in c.fetchall()]
    levels = [
        {"level":7,"name":"Open Science / Pré-enregistrement","color":"#7c6cff","refs":[]},
        {"level":6,"name":"Méta-analyse","color":"#6366f1","refs":[]},
        {"level":5,"name":"Revue systématique","color":"#3b82f6","refs":[]},
        {"level":4,"name":"Neuroimagerie contrôlée","color":"#06b6d4","refs":[]},
        {"level":3,"name":"Expérimental contrôlé","color":"#10b981","refs":[]},
        {"level":2,"name":"Corrélationnel / Perspective","color":"#f59e0b","refs":[]},
        {"level":1,"name":"Théorique / Philosophique","color":"#ef4444","refs":[]}
    ]
    nm = {"tres_eleve":[6,5],"eleve":[4,3],"modere_eleve":[4,3],"modere":[3,2],"faible_modere":[2],"theorique":[1]}
    for ref in refs:
        n = ref.get("niveau_preuve","faible")
        for lv in levels:
            if lv["level"] in nm.get(n,[1]):
                lv["refs"].append(ref); break
    conn.close()
    return levels

@app.get("/api/concepts-4e")
def get_concepts_4e():
    return [
        {"id":"incarnee","name":"Cognition Incarnée (Embodied)","definition":"La cognition est fondamentalement ancrée dans le corps, ses sensations et ses actions. Les concepts concrets naissent de l'interaction sensorimotrice.","solidite":4,"refs":["fuchs2026_embodied_concepts","frontiers2026_embodied_stem"],"mecanismes":["Simulation sensorimotrice","Résonance corporelle","Métaphore incarnée","Grounding sémantique"],"applications":["Gestes pédagogiques","Interfaces corporelles","Manipulation directe","Résonance émotionnelle"],"gaps":["Scaling up vers concepts abstraits","Opérationnalisation mesurable","Validation longitudinale"]},
        {"id":"situee","name":"Cognition Située / Embedded","definition":"La cognition émerge de l'interaction dynamique entre organisme et environnement structuré. Le contexte n'est pas un bruit mais un constituant.","solidite":4,"refs":["pascucci2026_spatiotemporal","tuncok2025_prf"],"mecanismes":["Couplage organisme-environnement","Scaffolding environnemental","Contexte spatio-temporel","Routines perceptives"],"applications":["Environnements riches","Contexte écologique","Routines spatio-temporelles","Parcours situés"],"gaps":["Validation empirique des routines","Généralisation hors labo","Quantification du couplage"]},
        {"id":"enactivisme","name":"Énactivisme Autopoïétique","definition":"La cognition n'est pas représentation mais émergence par action. Seul l'énactivisme autopoïétique (Varela, Thompson, Di Paolo) rompt radicalement avec le cognitivisme.","solidite":3,"refs":["exception2026_enactivism","fuchs2026_embodied_concepts"],"mecanismes":["Autopoïèse","Sense-making","Adaptation structurelle","Identité biologique"],"applications":["Design constructiviste radical","Exploration libre","Absence de modèle imposé"],"gaps":["Débat épistémologique non tranché","Opérationnalisation radicale manquante","Tension avec approches computationnelles"]},
        {"id":"etendue","name":"Cognition Étendue (Extended)","definition":"Les outils et artefacts externes (smartphone, graphe, tableau) font constitutivement partie du système cognitif, pas seulement des aides.","solidite":3,"refs":["rosen2025_distributed_cognition"],"mecanismes":["Couplage cognitif outil","Offloading cognitif","Extension fonctionnelle","Trust in tools"],"applications":["Graphes interactifs","Aides mnésiques externes","Dashboards cognitifs","Annotations augmentées"],"gaps":["Frontière interne/externe floue","Mesure du couplage","Parity principle controversé"]},
        {"id":"affordance","name":"Affordance Écologique","definition":"Possibilités d'action perçues directement dans l'environnement, sans médiation représentationnelle (Gibson). Le baseline shift cortical en est un substrat neural.","solidite":4,"refs":["tuncok2025_prf","pascucci2026_spatiotemporal"],"mecanismes":["Perception directe","Pré-activation motrice","Baseline shift cortical","pRF displacement"],"applications":["Design d'interfaces actionnables","Pré-cues visuels","Signaux affordants","Mise en page prédictive"],"gaps":["Quantification du champ d'affordances","Interaction multi-affordances","Écologie vs labo"]},
        {"id":"act_in","name":"Théorie ACT-IN (Versace)","definition":"Modèle intégré combinant Action, perception et Cognition dans un cycle continu. Mémoires sensorielles comme simulations réactivées.","solidite":3,"refs":["fuchs2026_embodied_concepts","pascucci2026_spatiotemporal"],"mecanismes":["Boucle perception-action","Intégration multisensorielle","Simulation incarnée","Réactivation mnésique"],"applications":["Formation par l'action","Feedback immédiat","Parcours sensori-moteur","Réactivation contextuelle"],"gaps":["Validation du modèle intégratif","Mesure de la boucle","Comparaison avec modèles concurrents"]},
        {"id":"charge_cognitive","name":"Charge Cognitive (Sweller)","definition":"Ressources attentionnelles limitées. Distinction charge intrinsèque/extrinsèque/germane. Évolution : alignement fonctionnel comme modérateur clé.","solidite":5,"refs":["lee2026_attention_control","alter2009_tribes_fluency"],"mecanismes":["Capacité limitée WMC","Contrôle attentionnel","Fluence vs disfluence","Suppression interférence"],"applications":["Design épuré","Segmentation temporelle","Alignement fonctionnel","Hiérarchie visuelle"],"gaps":["Mesure en contexte écologique","Charge germane controversée","Interaction avec motivation"]},
        {"id":"agence","name":"Sense of Agency (SoAS)","definition":"Sentiment d'être l'auteur de ses actions et de leurs effets. Mesurable via SoAS (scale validée en allemand et turc).","solidite":4,"refs":["frontiers2026_embodied_stem"],"mecanismes":["Comparateur forward","Monitoring d'action","Attribution causale","Temporal binding"],"applications":["Feedback d'action","Auto-évaluation","Traçabilité des décisions","Empowerment"],"gaps":["Mesure temps réel","Biais d'attribution","Variabilité interindividuelle"]},
        {"id":"emotion","name":"Émotion & Cognition","definition":"Les émotions ne sont pas séparées mais modulent fondamentalement la cognition. La fluence déclenche un affect positif attribué aux stimuli.","solidite":4,"refs":["knight2025_crossmodal_fluency","alter2009_tribes_fluency"],"mecanismes":["Attribution affective","Intégration crossmodale","Affect-as-information","Marqueur somatique"],"applications":["Design émotionnel","Feedback affectif","Motivation intrinsèque","Disfluence utile"],"gaps":["Mesure physiologique en contexte","Causalité bidirectionnelle","Régulation émotionnelle"]},
        {"id":"echec_couplage","name":"Échec de Couplage","definition":"Rupture de l'interaction organisme-environnement. Mène à confusion, désorientation, abandon. Indicateur critique pour le design.","solidite":3,"refs":["pascucci2026_spatiotemporal","exception2026_enactivism"],"mecanismes":["Perte de contingence","Désalignement temporel","Surcharge attentionnelle","Rupture de flow"],"applications":["Détection de décrochage","Signaux de recalage","Adaptation dynamique","Alertes métacognitives"],"gaps":["Indicateurs observables","Prédiction temps réel","Seuils de rupture"]}
    ]

@app.get("/api/metacognitive-traces")
def get_traces():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM metacognitive_traces ORDER BY created_at DESC LIMIT 50")
    traces = [dict(r) for r in c.fetchall()]
    conn.close()
    return traces

@app.post("/api/metacognitive-traces")
def create_trace(trace: MetacognitiveTraceCreate):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO metacognitive_traces 
        (session_id,phase,objective,criteria,constraints,ai_query,ai_response,evaluation,confidence,action_plan)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (trace.session_id,trace.phase,trace.objective,trace.criteria,trace.constraints,
         trace.ai_query,trace.ai_response,trace.evaluation,trace.confidence,trace.action_plan))
    conn.commit()
    tid = c.lastrowid
    conn.close()
    return {"status":"success","id":tid}

# ──────────────── OBSIDIAN GRAPH API ────────────────

@app.get("/api/obsidian-graph")
def get_obsidian_graph():
    """Graphe enrichi style Obsidian : études + concepts + méthodes + théories + paradigmes."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM references_table")
    studies = [dict(r) for r in c.fetchall()]
    c.execute("SELECT source_id, target_id, relation_type FROM reference_relations")
    study_links = [dict(r) for r in c.fetchall()]
    conn.close()

    nodes = []
    links = []

    # ── Études (type: "study") ──
    for s in studies:
        nodes.append({
            "id": s["id"],
            "label": s["reference_courte"],
            "type": "study",
            "group": s.get("sous_domaine", "Autre"),
            "trust": s.get("trust_factor", 50),
            "year": s.get("annee", 2024),
            "desc": s.get("consensus_actuel", ""),
            "gap": s.get("gap_actuel", ""),
            "tags": s.get("tags", ""),
            "question": s.get("question_scientifique", ""),
            "citations": s.get("citations_google_scholar", 0),
            "pubtype": s.get("type_publication", "")
        })

    # ── Study-to-study links ──
    for l in study_links:
        links.append({"source": l["source_id"], "target": l["target_id"], "type": l["relation_type"]})

    # ── Concepts (type: "concept") ──
    concepts = [
        {"id":"c_attention_controle","label":"Contrôle Attentionnel","group":"Attention","desc":"Maintien du but, suppression interférence, désengagement. Explique 75.6% variance multitâche."},
        {"id":"c_baseline_shift","label":"Baseline Shift","group":"Attention","desc":"Modification pré-stimulus du cortex visuel par l'attention covert. Substrat neural de l'affordance."},
        {"id":"c_prf","label":"pRF Displacement","group":"Attention","desc":"Déplacement des champs récepteurs populationnels vers la localisation attendue."},
        {"id":"c_wmc","label":"Mémoire de Travail (WMC)","group":"Mémoire","desc":"Boucle phonologique + calepin visuo-spatial + contrôle attentionnel (Lee & Engle 2026)."},
        {"id":"c_nback","label":"Tâche n-back","group":"Mémoire","desc":"Validité construit faible : progrès via chunking/familiarité pas vrai gain WMC."},
        {"id":"c_fluence","label":"Fluence de Traitement","group":"Métacognition","desc":"Expérience subjective de facilité. Indice métacognitif ubiquitaire influençant vérité, confiance, liking."},
        {"id":"c_disfluence","label":"Disfluence Volontaire","group":"Métacognition","desc":"Introduction stratégique de difficulté pour déclencher pensée analytique."},
        {"id":"c_crossmodal","label":"Intégration Crossmodale","group":"Perception","desc":"Fluence audio-visuelle : transfert persiste avec décalage → intégration pas simple regroupement."},
        {"id":"c_embodied_stem","label":"Embodied STEM","group":"Cognition incarnée","desc":"4 mécanismes : geste, structuration perceptivo-spatiale, offloading, interaction sociale. SMD=0.448."},
        {"id":"c_enaction","label":"Énaction","group":"Cognition incarnée","desc":"Cognition = action, pas représentation. Seul l'énactivisme autopoïétique rompt avec le cognitivisme."},
        {"id":"c_affordance","label":"Affordance","group":"Cognition incarnée","desc":"Possibilités d'action perçues directement. Gibson → baseline shift cortical."},
        {"id":"c_routines","label":"Routines Spatio-temporelles","group":"Attention","desc":"Mécanismes intégrant structure spatiale + temporelle pour guider perception. Paradigm shift."},
        {"id":"c_temporal_structures","label":"Structures Temporelles","group":"Attention","desc":"4 types : cues, hazard rates, rythmes, séquences. Amplifient l'attention spatiale."},
        {"id":"c_ac_mediation","label":"AC médie WMC→gF","group":"Mémoire","desc":"r WMC-gF passe de 0.63 à 0.40 quand AC contrôlé. Mécanisme sous-jacent."},
        {"id":"c_transfer_lointain","label":"Transfert Lointain","group":"Entraînement","desc":"Pas consensus. Effet plafond chez humains. Schémas abstraits médiateurs possibles."},
        {"id":"c_metacognition","label":"Métacognition","group":"Métacognition","desc":"Monitoring + contrôle des processus cognitifs. Base du SRL."},
        {"id":"c_srl","label":"Self-Regulated Learning","group":"Métacognition","desc":"Boucle planification → monitoring → contrôle → réflexion. Fondement Cognitorium."},
        {"id":"c_genai","label":"GenAI Encadrée","group":"Éducation","desc":"IA générative avec scaffolding métacognitif. Prompts structurés, évaluation critique."},
        {"id":"c_distributed_cognition","label":"Cognition Distribuée","group":"Neurosciences","desc":"Réseaux d'ordre supérieur, pas aires primaires. Recrutement inattendu régions contrôle moteur."},
        {"id":"c_charge_cognitive","label":"Charge Cognitive","group":"Design","desc":"Ressources limitées. Intrinsèque + extrinsèque + germane. Alignement fonctionnel clé."},
        {"id":"c_alignement_fonctionnel","label":"Alignement Fonctionnel","group":"Design","desc":"L'incarnation supplante la charge, pas l'additionne. Modérateur clé en STEM."},
        {"id":"c_affect_attribution","label":"Attribution Affective","group":"Émotion","desc":"Fluence → affect positif → attribué à tort aux objets. Biais systématique."},
        {"id":"c_covert_attention","label":"Attention Covert","group":"Attention","desc":"Orientation attentionnelle sans mouvement oculaire. Décodable en temps réel depuis préfrontal."},
        {"id":"c_open_science","label":"Open Science","group":"Méthodologie","desc":"Pré-enregistrement, données ouvertes, réplication. Standard émergent en psychologie."},
        {"id":"c_preregistration","label":"Pré-enregistrement","group":"Méthodologie","desc":"Hypothèses et analyses déclarées avant collecte. Réduit HARKing et p-hacking."},
        {"id":"c_4e","label":"Paradigme 4E","group":"Paradigme","desc":"Embodied, Embedded, Enacted, Extended. Alternative au cognitivisme classique."},
        {"id":"c_cognitivisme","label":"Cognitivisme Classique","group":"Paradigme","desc":"Cognition = computation sur représentations. Remis en question par 4E."},
        {"id":"c_predictive_coding","label":"Predictive Coding","group":"Théorie","desc":"Cerveau = machine à prédictions. Erreur de prédiction comme signal d'apprentissage."},
        {"id":"c_free_energy","label":"Free Energy Principle","group":"Théorie","desc":"Friston : minimisation de l'énergie libre. Unifie perception, action, apprentissage."},
        {"id":"c_ecological_psychology","label":"Psychologie Écologique","group":"Paradigme","desc":"Gibson : perception directe des affordances. Pas de représentation intermédiaire."},
    ]

    for co in concepts:
        nodes.append({
            "id": co["id"], "label": co["label"], "type": "concept",
            "group": co["group"], "desc": co["desc"], "trust": 70, "year": 2025
        })

    # ── Methods (type: "method") ──
    methods = [
        {"id":"m_fmri_7t","label":"fMRI 7T","group":"Neuroimagerie","desc":"Imagerie à ultra-haut champ. Résolution submillimétrique. pRF mapping."},
        {"id":"m_eeg","label":"EEG Alpha/Bêta","group":"Neuroimagerie","desc":"Rythmes alpha (8-12Hz) liés à l'inhibition, bêta (13-30Hz) au maintien."},
        {"id":"m_psychophysics","label":"Psychophysique","group":"Méthode","desc":"Mesure des seuils perceptifs. Cueing, compétition vs non-compétition."},
        {"id":"m_latent_variables","label":"Variables Latentes","group":"Méthode","desc":"Modélisation SEM. Facteurs communs extraits de multiples tâches."},
        {"id":"m_meta_analysis","label":"Méta-analyse","group":"Méthode","desc":"Agrégation quantitative d'effets. SMD, hétérogénéité, modérateurs."},
        {"id":"m_systematic_review","label":"Revue Systématique","group":"Méthode","desc":"Protocole PRISMA. Inclusion/exclusion rigoureux. Synthèse narrative."},
        {"id":"m_prf_modeling","label":"pRF Modeling","group":"Méthode","desc":"Modélisation des champs récepteurs populationnels. Mesure des shifts attentionnels."},
        {"id":"m_mvpA","label":"MVPA / Décodage","group":"Méthode","desc":"Multi-voxel pattern analysis. Décodage temps réel de l'attention covert."},
        {"id":"m_crossmodal_design","label":"Design Crossmodal","group":"Méthode","desc":"Audio-visuel avec décalage temporel. Teste intégration vs regroupement."},
    ]

    for me in methods:
        nodes.append({
            "id": me["id"], "label": me["label"], "type": "method",
            "group": me["group"], "desc": me["desc"], "trust": 65, "year": 2024
        })

    # ── Theorists (type: "theorist") ──
    theorists = [
        {"id":"t_sweller","label":"Sweller","group":"Théoricien","desc":"Théorie de la charge cognitive (1988). Évolution vers l'alignement fonctionnel."},
        {"id":"t_gibson","label":"Gibson JJ","group":"Théoricien","desc":"Psychologie écologique. Affordances. Perception directe sans représentation."},
        {"id":"t_varela","label":"Varela","group":"Théoricien","desc":"Énactivisme autopoïétique. The Embodied Mind (1991). Sense-making."},
        {"id":"t_engle","label":"Engle RW","group":"Théoricien","desc":"Working Memory Capacity → Attention Control. Framework exécutif."},
        {"id":"t_friston","label":"Friston K","group":"Théoricien","desc":"Free Energy Principle. Predictive coding. Cerveau bayésien."},
        {"id":"t_baddeley","label":"Baddeley","group":"Théoricien","desc":"Modèle multi-composants de la mémoire de travail (1974)."},
        {"id":"t_nobre","label":"Nobre AC","group":"Théoricien","desc":"Attention temporelle. Structures temporelles. Synergie spatio-temporelle."},
        {"id":"t_carrasco","label":"Carrasco M","group":"Théoricien","desc":"Attention spatiale covert. Performance field. fMRI 7T."},
    ]

    for th in theorists:
        nodes.append({
            "id": th["id"], "label": th["label"], "type": "theorist",
            "group": th["group"], "desc": th["desc"], "trust": 80, "year": 2020
        })

    # ── Concept-to-study links ──
    concept_study_links = [
        ("tuncok2025_prf","c_baseline_shift","instantiates"),
        ("tuncok2025_prf","c_prf","uses"),
        ("tuncok2025_prf","c_covert_attention","studies"),
        ("tuncok2025_prf","c_affordance","supports"),
        ("lee2026_attention_control","c_attention_controle","defines"),
        ("lee2026_attention_control","c_wmc","redefines"),
        ("lee2026_attention_control","c_ac_mediation","demonstrates"),
        ("huang2025_nback","c_nback","critiques"),
        ("huang2025_nback","c_wmc","questions"),
        ("chen2025_transfer","c_transfer_lointain","reviews"),
        ("fuchs2026_embodied_concepts","c_enaction","develops"),
        ("fuchs2026_embodied_concepts","c_4e","contributes"),
        ("frontiers2026_embodied_stem","c_embodied_stem","quantifies"),
        ("frontiers2026_embodied_stem","c_alignement_fonctionnel","identifies"),
        ("exception2026_enactivism","c_enaction","analyzes"),
        ("exception2026_enactivism","c_cognitivisme","contrasts"),
        ("benhamed2025_decoding","c_covert_attention","decodes"),
        ("pascucci2026_spatiotemporal","c_routines","introduces"),
        ("tian2026_temporal","c_temporal_structures","extends"),
        ("nobre2017_temporal","c_temporal_structures","foundational"),
        ("nobre2017_temporal","c_predictive_coding","relates"),
        ("alter2009_tribes_fluency","c_fluence","foundational"),
        ("alter2009_tribes_fluency","c_metacognition","contributes"),
        ("knight2025_crossmodal_fluency","c_crossmodal","demonstrates"),
        ("knight2025_crossmodal_fluency","c_affect_attribution","shows"),
        ("knight2025_crossmodal_fluency","c_fluence","extends"),
        ("rosen2025_distributed_cognition","c_distributed_cognition","evidence"),
    ]

    for src, tgt, rel in concept_study_links:
        links.append({"source": src, "target": tgt, "type": rel})

    # ── Concept-to-concept links ──
    concept_links = [
        ("c_attention_controle","c_wmc","underlies"),
        ("c_baseline_shift","c_affordance","substrate"),
        ("c_baseline_shift","c_covert_attention","mechanism"),
        ("c_fluence","c_metacognition","index"),
        ("c_fluence","c_affect_attribution","triggers"),
        ("c_disfluence","c_fluence","opposes"),
        ("c_enaction","c_4e","pillar"),
        ("c_affordance","c_ecological_psychology","rooted_in"),
        ("c_routines","c_temporal_structures","integrates"),
        ("c_routines","c_baseline_shift","leverages"),
        ("c_ac_mediation","c_attention_controle","mediates"),
        ("c_metacognition","c_srl","foundation"),
        ("c_srl","c_genai","scaffolds"),
        ("c_embodied_stem","c_alignement_fonctionnel","moderated_by"),
        ("c_charge_cognitive","c_alignement_fonctionnel","constrained_by"),
        ("c_distributed_cognition","c_4e","relates"),
        ("c_predictive_coding","c_free_energy","instantiates"),
        ("c_cognitivisme","c_4e","contrasts"),
        ("c_open_science","c_preregistration","includes"),
        ("c_crossmodal","c_affect_attribution","enables"),
        ("c_nback","c_wmc","measures"),
        ("c_covert_attention","c_attention_controle","requires"),
    ]

    for src, tgt, rel in concept_links:
        links.append({"source": src, "target": tgt, "type": rel})

    # ── Method-to-study links ──
    method_links = [
        ("tuncok2025_prf","m_fmri_7t","uses"),
        ("tuncok2025_prf","m_psychophysics","uses"),
        ("tuncok2025_prf","m_prf_modeling","uses"),
        ("benhamed2025_decoding","m_mvpA","uses"),
        ("benhamed2025_decoding","m_eeg","reviews"),
        ("lee2026_attention_control","m_latent_variables","uses"),
        ("lee2026_attention_control","m_systematic_review","uses"),
        ("frontiers2026_embodied_stem","m_meta_analysis","uses"),
        ("knight2025_crossmodal_fluency","m_crossmodal_design","uses"),
        ("huang2025_nback","m_systematic_review","uses"),
        ("chen2025_transfer","m_systematic_review","uses"),
        ("tian2026_temporal","m_psychophysics","uses"),
        ("alter2009_tribes_fluency","m_systematic_review","uses"),
    ]

    for src, tgt, rel in method_links:
        links.append({"source": src, "target": tgt, "type": rel})

    # ── Theorist-to-concept links ──
    theorist_links = [
        ("t_sweller","c_charge_cognitive","created"),
        ("t_gibson","c_affordance","created"),
        ("t_gibson","c_ecological_psychology","founded"),
        ("t_varela","c_enaction","founded"),
        ("t_engle","c_attention_controle","pioneered"),
        ("t_engle","c_wmc","redefined"),
        ("t_friston","c_free_energy","created"),
        ("t_friston","c_predictive_coding","developed"),
        ("t_baddeley","c_wmc","created"),
        ("t_nobre","c_temporal_structures","pioneered"),
        ("t_carrasco","c_baseline_shift","discovered"),
        ("t_carrasco","c_covert_attention","pioneered"),
    ]

    for src, tgt, rel in theorist_links:
        links.append({"source": src, "target": tgt, "type": rel})

    # ── OER / Open Access Books & Resources (type: source) ──
    oer_sources = [
        # Classifications & Institutions
        {"id":"oer_dsm5tr","label":"DSM-5-TR (APA Psychiatric)","group":"Classification","desc":"Manuel diagnostique et statistique des troubles mentaux, 5e éd. révisée. American Psychiatric Association. Critères diagnostiques standardisés.","trust":95,"year":2022},
        {"id":"oer_cim11","label":"CIM-11 (OMS)","group":"Classification","desc":"Classification Internationale des Maladies, ch.06 : troubles mentaux, comportementaux et neurodéveloppementaux. Norme légale internationale. Navigateur web gratuit.","trust":95,"year":2022},
        {"id":"oer_cif","label":"CIF / ICF (OMS)","group":"Classification","desc":"Classification du Fonctionnement, du Handicap et de la Santé. Complète la CIM : activité, participation, facteurs environnementaux.","trust":90,"year":2001},
        {"id":"oer_apa_div","label":"APA 54 Divisions","group":"Institution","desc":"American Psychological Association. 54 divisions spécialisées : clinique, sociale, cognitive, développement, éducation, santé, travail, etc.","trust":95,"year":2025},
        {"id":"oer_has","label":"HAS (France)","group":"Institution","desc":"Haute Autorité de Santé. Recommandations de bonne pratique clinique (autisme, dépression, TDAH). Référence française.","trust":90,"year":2025},
        {"id":"oer_inserm","label":"INSERM Expertises","group":"Institution","desc":"Expertises collectives sur neurodéveloppement, santé mentale, addictions, prévention.","trust":90,"year":2025},
        # Databases
        {"id":"oer_psyinfo","label":"APA PsycINFO","group":"Base de données","desc":"5+ millions de notices bibliographiques en psychologie et sciences comportementales. Base mondiale de référence.","trust":95,"year":2025},
        {"id":"oer_pubmed","label":"PubMed","group":"Base de données","desc":"National Library of Medicine. Neuropsychologie, psychiatrie, neurosciences, essais cliniques.","trust":95,"year":2025},
        {"id":"oer_cochrane","label":"Cochrane Library","group":"Base de données","desc":"Revues systématiques sur les interventions de santé. Gold standard méta-analyses cliniques.","trust":95,"year":2025},
        {"id":"oer_openalex","label":"OpenAlex","group":"Base de données","desc":"Catalogue ouvert de travaux scientifiques et relations de citation. Alternative libre à WoS/Scopus.","trust":85,"year":2025},
        {"id":"oer_cairn","label":"Cairn.info","group":"Base de données","desc":"Plateforme francophone de référence pour revues et ouvrages universitaires en sciences humaines.","trust":85,"year":2025},
        {"id":"oer_openscience","label":"Open Science Framework","group":"Science ouverte","desc":"Guides : pré-enregistrement, dépôt de données, versionnage, reproductibilité.","trust":85,"year":2025},
        # OER Textbooks - General
        {"id":"oer_openstax_psych","label":"OpenStax Psychology 2e","group":"Manuel OER","desc":"Spielman, Jenkins & Lovett. Manuel généraliste CC BY 4.0. Arborescence complète : histoire, méthodes, cerveau, perception, cognition, développement, personnalité, social, clinique, travail.","trust":90,"year":2020},
        {"id":"oer_research_methods","label":"Research Methods in Psychology","group":"Manuel OER","desc":"Cuttler, Jhangiani & Leighton, 4e éd. Plans expérimentaux, variables, échantillonnage, validité, analyses, éthique. Indispensable pour évaluer les articles.","trust":88,"year":2023},
        {"id":"oer_stangor","label":"Stangor — Introduction to Psychology","group":"Manuel OER","desc":"Alternative généraliste centrée sur les principes empiriques et l'organisation conceptuelle de la discipline.","trust":85,"year":2022},
        # OER Textbooks - Cognitive & Neuro
        {"id":"oer_memory_cognition","label":"Memory & Cognition (Jhangiani)","group":"Manuel OER","desc":"Mémoire, imagerie mentale, décision, raisonnement, cognition interdisciplinaire. Gratuit, web/PDF.","trust":88,"year":2023},
        {"id":"oer_bio_psych","label":"Biological Psychology (Garrett)","group":"Manuel OER","desc":"Gènes, hormones, neurotransmetteurs, structures cérébrales, cognition, émotions et comportement.","trust":88,"year":2022},
        {"id":"oer_kolb_whishaw","label":"Behavioral Neuroscience (Kolb)","group":"Manuel OER","desc":"Kolb & Whishaw, 8e éd. Référence dense sur les relations cerveau-comportement. Accès libre via PMC.","trust":90,"year":2021},
        # OER Textbooks - Development & Education
        {"id":"oer_lifespan","label":"Lifespan Development (Lumen)","group":"Manuel OER","desc":"Développement physique, cognitif, social et émotionnel de la conception au vieillissement.","trust":85,"year":2022},
        {"id":"oer_whole_child","label":"Understanding the Whole Child","group":"Manuel OER","desc":"Paris et al. Développement prénatal, cognitif, langagier, socio-émotionnel, adolescence.","trust":85,"year":2022},
        {"id":"oer_hutchison","label":"Lifespan Development (Hutchison)","group":"Manuel OER","desc":"4e éd. Théories et changements développementaux sur toute la vie.","trust":85,"year":2022},
        {"id":"oer_edu_psych","label":"Educational Psychology (Seifert)","group":"Manuel OER","desc":"Théories de l'apprentissage, motivation, évaluation, instruction, diversité et climat scolaire.","trust":88,"year":2020},
        # OER Textbooks - HCI & Ergonomics
        {"id":"oer_hornbaek_hci","label":"Introduction to HCI (Hornbæk)","group":"Manuel OER","desc":"Open access CC BY-NC-ND. Design, ingénierie, méthodes empiriques, UX, IA et VR.","trust":88,"year":2024},
        {"id":"oer_ixdf","label":"IxDF Encyclopedia of HCI","group":"Manuel OER","desc":"Interaction Design Foundation. 4000+ pages : interaction, perception, design, évaluation, accessibilité.","trust":85,"year":2024},
        {"id":"oer_bastien_scapin","label":"Bastien & Scapin RT-0156","group":"Référentiel","desc":"Critères ergonomiques IHM : guidage, charge, contrôle, adaptabilité, erreurs, compatibilité. INRIA.","trust":88,"year":1993},
        # OER Textbooks - Statistics & Methods
        {"id":"oer_openintro_stats","label":"OpenIntro Statistics","group":"Manuel OER","desc":"Statistiques descriptives, inférentielles, modèles de base. Gratuit, PDF.","trust":85,"year":2023},
        # Tools & Experiment Libraries
        {"id":"oer_psytoolkit","label":"PsyToolkit Library","group":"Outil","desc":"Expériences cognitives exécutables : Stroop, N-back, rotation mentale, Simon, Flanker, Posner, Go/No-Go. Code réutilisable.","trust":85,"year":2025},
        {"id":"oer_rome","label":"France Travail ROME","group":"Référentiel","desc":"Répertoire Opérationnel des Métiers et Emplois. Compétences, activités, mobilités professionnelles.","trust":85,"year":2025},
        # Posters / Expériences classiques enrichis
        {"id":"poster_sherif","label":"Poster: Sherif — Norme","group":"Poster","desc":"Quand l'incertitude fabrique une norme. Autocinétique → convergence → internalisation. Transfert : avis en ligne, orientation, compétences floues.","trust":80,"year":1935},
        {"id":"poster_asch","label":"Poster: Asch — Conformité","group":"Poster","desc":"Dire B quand on voit C. 37% conformité. Variables : taille majorité, allié, réponse publique. Transfert : likes, réunions, IA.","trust":80,"year":1951},
        {"id":"poster_bandura","label":"Poster: Bandura — Bobo","group":"Poster","desc":"Observer → coder → reproduire. 4 processus : attention, rétention, reproduction, motivation. Transfert : tutoriels, modèles IA.","trust":80,"year":1961},
        {"id":"poster_stroop","label":"Poster: Stroop — Interférence","group":"Poster","desc":"Lire le mot ou nommer la couleur ? Coût ~200ms. Voie lecture vs contrôle exécutif. Transfert : notifications, UX contradictoires.","trust":80,"year":1935},
        {"id":"poster_loftus","label":"Poster: Loftus — Faux souvenirs","group":"Poster","desc":"Vu, imaginé ou suggéré ? Souvenir = fragments colorés (observé/inféré/suggéré). Transfert : témoignages, révisions, sources IA.","trust":80,"year":1974},
        {"id":"poster_calibration","label":"Poster: Calibration","group":"Poster","desc":"Être sûr ≠ avoir raison. Confiance vs performance. 4 profils. Transfert Cognitorium : auto-évaluation + vérification.","trust":80,"year":2025},
        # Revues majeures
        {"id":"oer_psych_bulletin","label":"Psychological Bulletin","group":"Revue","desc":"Revue APA. Grandes méta-analyses et revues théoriques.","trust":95,"year":2025},
        {"id":"oer_nat_rev_psych","label":"Nature Reviews Psychology","group":"Revue","desc":"Synthèses à haut facteur d'impact. Perspectives et reviews.","trust":95,"year":2025},
        {"id":"oer_cog_psych","label":"Cognitive Psychology","group":"Revue","desc":"Référence pour les processus cognitifs : mémoire, attention, décision.","trust":90,"year":2025},
        {"id":"oer_jpss","label":"JPSP","group":"Revue","desc":"Journal of Personality and Social Psychology. Référence en psychologie sociale.","trust":90,"year":2025},
    ]

    for s in oer_sources:
        nodes.append({
            "id": s["id"], "label": s["label"], "type": "source",
            "group": s["group"], "desc": s["desc"], "trust": s["trust"], "year": s["year"]
        })

    # ── OER → Concept/Study links ──
    oer_links = [
        # Posters → Studies & Concepts
        ("poster_sherif","sherif1935_norm","illustrates"),
        ("poster_asch","asch1951_conformity","illustrates"),
        ("poster_bandura","bandura1961_bobo","illustrates"),
        ("poster_stroop","stroop1935_interference","illustrates"),
        ("poster_loftus","loftus1974_false_memory","illustrates"),
        ("poster_calibration","c_metacognition","teaches"),
        ("poster_calibration","c_calibration","teaches"),
        ("poster_calibration","c_srl","applies"),
        # OER Books → Concepts
        ("oer_openstax_psych","c_metacognition","covers"),
        ("oer_openstax_psych","c_wmc","covers"),
        ("oer_openstax_psych","c_conformity","covers"),
        ("oer_openstax_psych","c_dissonance","covers"),
        ("oer_research_methods","m_meta_analysis","teaches"),
        ("oer_research_methods","m_preregistration","teaches"),
        ("oer_memory_cognition","c_wmc","covers"),
        ("oer_memory_cognition","c_false_memory","covers"),
        ("oer_memory_cognition","c_testing_effect","covers"),
        ("oer_bio_psych","c_distributed_cognition","covers"),
        ("oer_bio_psych","c_predictive_coding","covers"),
        ("oer_kolb_whishaw","c_baseline_shift","covers"),
        ("oer_edu_psych","c_srl","covers"),
        ("oer_edu_psych","c_self_efficacy","covers"),
        ("oer_edu_psych","c_growth_mindset","covers"),
        ("oer_edu_psych","c_flow","covers"),
        ("oer_lifespan","c_consolidation","covers"),
        ("oer_hornbaek_hci","c_charge_cognitive","covers"),
        ("oer_hornbaek_hci","c_bastien_scapin","covers"),
        ("oer_hornbaek_hci","c_affordance_ui","covers"),
        ("oer_hornbaek_hci","c_mental_models","covers"),
        ("oer_ixdf","c_compatibility","covers"),
        ("oer_ixdf","c_affordance_ui","covers"),
        ("oer_psytoolkit","c_stroop_effect","implements"),
        ("oer_psytoolkit","c_nback","implements"),
        ("oer_psytoolkit","c_selective_attention","implements"),
        ("oer_openintro_stats","m_meta_analysis","teaches"),
        ("oer_openscience","m_preregistration","teaches"),
        ("oer_bastien_scapin","c_bastien_scapin","defines"),
        ("oer_rome","c_srl","applies"),
        # Institutions
        ("oer_apa_div","oer_psyinfo","maintains"),
        ("oer_apa_div","oer_psych_bulletin","publishes"),
        ("oer_cim11","oer_dsm5tr","complements"),
        ("oer_cim11","oer_cif","complements"),
        ("oer_has","c_srl","recommends"),
        ("oer_inserm","c_metacognition","evaluates"),
        # Databases index studies
        ("oer_psyinfo","lee2026_attention_control","indexes"),
        ("oer_psyinfo","frontiers2026_embodied_stem","indexes"),
        ("oer_pubmed","benhamed2025_decoding","indexes"),
        ("oer_pubmed","tuncok2025_prf","indexes"),
        ("oer_cochrane","deboer2018_metacog","indexes"),
        ("oer_cochrane","donker2014_strategies","indexes"),
    ]

    for src, tgt, rel in oer_links:
        links.append({"source": src, "target": tgt, "type": rel})

    # Filter out broken links (source or target not in nodes)
    node_ids = {n["id"] for n in nodes}
    links = [l for l in links if l["source"] in node_ids and l["target"] in node_ids]

    return {"nodes": nodes, "links": links}

# ──────────────── TAXONOMY API ────────────────

@app.get("/api/taxonomy")
def get_taxonomy():
    """Taxonomie enrichée de la psychologie cognitive."""
    return {
        "name": "Psychologie Scientifique",
        "desc": "Discipline étudiant les processus mentaux, le comportement et leurs bases neurobiologiques.",
        "cognitorium": "Socle ontologique global.",
        "children": [
            {
                "name": "Pilier 1 : Biologique & Neurosciences",
                "desc": "Bases neurobiologiques et physiologiques du comportement.",
                "cognitorium": "Substrats neuro-anatomiques pour valider les modèles.",
                "children": [
                    {"name": "Neurosciences cognitives", "desc": "Imagerie cérébrale, connectomique, corrélats neuronaux des fonctions mentales.", "cognitorium": "Validation des modèles de monitoring et de contrôle.",
                     "children": [
                         {"name": "Neuroimagerie fonctionnelle", "desc": "fMRI, PET, NIRS. Mesure de l'activité cérébrale en temps réel.", "cognitorium": "Validation des modèles attentionnels."},
                         {"name": "Connectomique", "desc": "Cartographie des connexions neuronales. Réseaux à grande échelle.", "cognitorium": "Architecture des graphes de connaissances."},
                         {"name": "Neurosciences computationnelles", "desc": "Modèles mathématiques du fonctionnement cérébral.", "cognitorium": "Algorithmes de recommandation adaptative."},
                         {"name": "Optogénétique & Causality", "desc": "Manipulation causale de circuits neuronaux.", "cognitorium": "Compréhension des mécanismes d'apprentissage."}
                     ]},
                    {"name": "Neuropsychologie", "desc": "Lésions cérébrales et dissociations fonctionnelles.", "cognitorium": "Analyse des déficits exécutifs et compensations.",
                     "children": [
                         {"name": "Lésions préfrontales", "desc": "Dysexécutif, perte de flexibilité, persévérations.", "cognitorium": "Design de scaffolding pour fonctions exécutives."},
                         {"name": "Aphasies & Langage", "desc": "Troubles acquis du langage. Double dissociation.", "cognitorium": "Adaptation linguistique des interfaces."},
                         {"name": "Héminégligence", "desc": "Trouble attentionnel spatial. Biais latéralisé.", "cognitorium": "Design spatial équilibré."}
                     ]},
                    {"name": "Psychophysiologie", "desc": "Mesures autonomes : ECG, EDA, EMG, pupillométrie.", "cognitorium": "Traces physiologiques de charge cognitive et engagement.",
                     "children": [
                         {"name": "EEG & Rythmes cérébraux", "desc": "Alpha (inhibition), Bêta (maintien), Gamma (binding), Theta (mémoire).", "cognitorium": "Feedback neuro-adaptatif en temps réel."},
                         {"name": "Pupillométrie", "desc": "Dilatation pupillaire = indice de charge cognitive et surprise.", "cognitorium": "Mesure non-invasive de l'engagement."},
                         {"name": "Variabilité cardiaque (HRV)", "desc": "Indice de régulation autonome et flexibilité cognitive.", "cognitorium": "Détection du stress en formation."}
                     ]},
                    {"name": "Psycho-endocrinologie", "desc": "Cortisol, dopamine, noradrénaline et cognition.", "cognitorium": "Modélisation du stress et de la motivation.",
                     "children": [
                         {"name": "Axe HPA & Stress", "desc": "Cortisol : effet inverted-U sur la mémoire et l'attention.", "cognitorium": "Adaptation au niveau de stress de l'apprenant."},
                         {"name": "Dopamine & Récompense", "desc": "Système de récompense, prediction error, motivation.", "cognitorium": "Gamification et récompenses adaptatives."}
                     ]},
                    {"name": "Conscience & Sommeil", "desc": "États de conscience, consolidation mnésique nocturne.", "cognitorium": "Optimisation du timing d'apprentissage.",
                     "children": [
                         {"name": "Consolidation mnésique", "desc": "Rejeu hippocampique pendant le sommeil. Spindles et SWR.", "cognitorium": "Recommandations de sommeil pour l'apprentissage."},
                         {"name": "États modifiés", "desc": "Méditation, flow, hypnose. Modulation attentionnelle.", "cognitorium": "Techniques de focalisation attentionnelle."}
                     ]}
                ]
            },
            {
                "name": "Pilier 2 : Psychologie Cognitive",
                "desc": "Science des fonctions mentales : acquisition, traitement, stockage et utilisation de l'information.",
                "cognitorium": "Cœur fonctionnel et algorithmique du Cognitorium.",
                "children": [
                    {
                        "name": "A. Perception",
                        "desc": "Organisation et interprétation des signaux sensoriels.",
                        "children": [
                            {"name": "Perception visuelle", "desc": "Formes, profondeur, mouvement, illusions, constances perceptives.", "cognitorium": "Design UI/UX visuel optimal.",
                             "children": [
                                 {"name": "Voie ventrale (What)", "desc": "Identification des objets. V1→V2→V4→IT.", "cognitorium": "Reconnaissance des patterns de compétences."},
                                 {"name": "Voie dorsale (Where/How)", "desc": "Localisation et guidage de l'action. V1→V2→MT→pariétal.", "cognitorium": "Interaction spatiale avec les graphes."},
                                 {"name": "Illusions & Biais perceptifs", "desc": "Témoignent des heuristiques du système visuel.", "cognitorium": "Design exploitant les constances perceptives."}
                             ]},
                            {"name": "Perception auditive", "desc": "Localisation, parole, musique, streaming auditif.", "cognitorium": "Feedback audio et notifications sonores.",
                             "children": [
                                 {"name": "Parole & Phonèmes", "desc": "Catégorisation perceptive, effet McGurk.", "cognitorium": "Interfaces vocales adaptatives."},
                                 {"name": "Scènes auditives", "desc": "Ségrégation source, streaming, attention auditive.", "cognitorium": "Design audio non surchargeant."}
                             ]},
                            {"name": "Perception multisensorielle", "desc": "Intégration vue-ouïer-toucher. Effet McGurk, ventriloquisme.", "cognitorium": "Interfaces multimodales cohérentes.",
                             "children": [
                                 {"name": "Intégration bayésienne", "desc": "Combinaison optimale des signaux selon leur fiabilité.", "cognitorium": "Fusion de sources d'information."},
                                 {"name": "Crossmodal fluence", "desc": "Fluence audio-visuelle améliore les jugements (Knight 2025).", "cognitorium": "Synchronisation audio-visuelle optimale."}
                             ]},
                            {"name": "Perception & Action (4E)", "desc": "Couplage sensorimoteur. Cognition incarnée. Affordances.", "cognitorium": "Interaction directe et incarnée avec les données."}
                        ]
                    },
                    {
                        "name": "B. Attention",
                        "desc": "Mécanismes de sélection, concentration et contrôle de l'information.",
                        "children": [
                            {"name": "Attention sélective", "desc": "Filtrage de l'information pertinente. Stroop, recherche visuelle.", "cognitorium": "Réduction des distracteurs UI.",
                             "children": [
                                 {"name": "Recherche visuelle", "desc": "Feature search (parallèle) vs conjunction search (sériel). Guided Search.", "cognitorium": "Hiérarchie visuelle des éléments importants."},
                                 {"name": "Inhibition de retour (IOR)", "desc": "Difficulté à revenir sur une localisation déjà inspectée.", "cognitorium": "Navigation qui évite les retours inutiles."},
                                 {"name": "Effet Stroop", "desc": "Interférence entre traitement automatique et contrôlé.", "cognitorium": "Mesure du contrôle inhibiteur."}
                             ]},
                            {"name": "Attention soutenue", "desc": "Vigilance sur longue période. Décrément temporel.", "cognitorium": "Gestion de la fatigue cognitive et pauses.",
                             "children": [
                                 {"name": "Vigilance & Décrément", "desc": "Baisse de performance après 20-30 min. Mind-wandering.", "cognitorium": "Segmentation des sessions d'apprentissage."},
                                 {"name": "Mind-wandering", "desc": "Pensées hors-tâche. 30-50% du temps éveillé.", "cognitorium": "Détection et recentrage de l'attention."}
                             ]},
                            {"name": "Attention divisée / Multitâche", "desc": "Partage des ressources limitées. Coût de switch.", "cognitorium": "Éviter la surcharge en formation.",
                             "children": [
                                 {"name": "Coût de switch", "desc": "Perte de temps et précision lors du changement de tâche.", "cognitorium": "Minimiser les alternances de contexte."},
                                 {"name": "Dual-task paradigm", "desc": "Performance en double tâche révèle les ressources partagées.", "cognitorium": "Dimensionnement des activités simultanées."}
                             ]},
                            {"name": "Attention exécutive", "desc": "Inhibition, flexibilité, contrôle. Liée au contrôle attentionnel.", "cognitorium": "Pilotage des flux d'orientation.",
                             "children": [
                                 {"name": "Contrôle inhibiteur", "desc": "Suppression des réponses prépotentes. Go/NoGo, Stop-Signal.", "cognitorium": "Tâches d'inhibition comme mesure AC."},
                                 {"name": "Flexibilité cognitive", "desc": "Alternance entre règles et ensembles mentaux.", "cognitorium": "Adaptation aux changements de contexte."}
                             ]},
                            {"name": "Attention Spatiale (Covert)", "desc": "Orientation sans mouvement oculaire. Baseline shift. pRF displacement.", "cognitorium": "Pré-cues visuels et mise en page prédictive.",
                             "children": [
                                 {"name": "Cueing spatial (Posner)", "desc": "Valid/invalid cues. Coût/bénéfice attentionnel.", "cognitorium": "Signaux d'orientation dans l'interface."},
                                 {"name": "Baseline shift cortical", "desc": "Modification pré-stimulus du cortex visuel (Tünçok 2025).", "cognitorium": "Pré-activation par repères visuels."},
                                 {"name": "Zoom attentionnel", "desc": "Élargissement/rétrécissement du focus spatial.", "cognitorium": "Niveaux de détail adaptatifs."}
                             ]},
                            {"name": "Attention Temporelle", "desc": "Orientation dans le temps. 4 structures : cues, hazard rates, rythmes, séquences.", "cognitorium": "Temporalité optimisée des parcours.",
                             "children": [
                                 {"name": "Hazard rates", "desc": "Probabilité conditionnelle d'apparition d'un stimulus.", "cognitorium": "Timing prédictible des feedbacks."},
                                 {"name": "Rythmes & Entraînement", "desc": "Synchronisation aux rythmes externes. Oscillations neurales.", "cognitorium": "Rythme des interactions et notifications."},
                                 {"name": "Routines spatio-temporelles", "desc": "Intégration structure spatiale + temporelle (Pascucci 2026).", "cognitorium": "Contextes riches et prévisibles."},
                                 {"name": "Facilitation pré-compétitive", "desc": "Attention temporelle améliore perception même sans compétition (Tian 2026).", "cognitorium": "Préparation temporelle avant contenu."}
                             ]}
                        ]
                    },
                    {
                        "name": "C. Mémoire & Apprentissage",
                        "desc": "Encodage, stockage, récupération et modification durable.",
                        "children": [
                            {"name": "Mémoire sensorielle", "desc": "Iconique (~300ms) et échoïque (~3-4s). Buffer ultra-bref.", "cognitorium": "Micro-interactions et feedback immédiat."},
                            {"name": "Mémoire de travail (WMC)", "desc": "Baddeley : boucle phonologique + calepin + administrateur central + buffer épisodique. Engle : contrôle attentionnel.", "cognitorium": "Dimensionnement des tâches cognitives.",
                             "children": [
                                 {"name": "Boucle phonologique", "desc": "Stockage verbal ~2s. Effet de longueur de mot.", "cognitorium": "Instructions verbales concises."},
                                 {"name": "Calepin visuo-spatial", "desc": "Stockage d'images mentales. Interférence spatiale.", "cognitorium": "Visualisations spatiales des données."},
                                 {"name": "Contrôle attentionnel (AC)", "desc": "Lee & Engle 2026 : AC explique 75.6% variance multitâche. Maintien but + suppression interférence.", "cognitorium": "Mesurer AC, pas stockage. Tâches avec distracteurs."},
                                 {"name": "Buffer épisodique", "desc": "Intégration multimodale temporaire. Interface avec MLT.", "cognitorium": "Intégration de contextes multi-sources."}
                             ]},
                            {"name": "Mémoire à long terme", "desc": "Épisodique, sémantique, procédurale. Capacité illimitée.", "cognitorium": "Base de connaissances des métiers et compétences.",
                             "children": [
                                 {"name": "Mémoire épisodique", "desc": "Souvenirs personnels contextualisés. Rappel vs reconnaissance.", "cognitorium": "Traçabilité des expériences d'apprentissage."},
                                 {"name": "Mémoire sémantique", "desc": "Connaissances générales décontextualisées. Réseaux sémantiques.", "cognitorium": "Ontologie des compétences et métiers."},
                                 {"name": "Mémoire procédurale", "desc": "Savoir-faire automatisé. Apprentissage implicite.", "cognitorium": "Automatisation par pratique répétée."}
                             ]},
                            {"name": "Apprentissage & Consolidation", "desc": "Répétition espacée, sommeil, interleaving, testing effect.", "cognitorium": "Algorithmes de révision adaptative.",
                             "children": [
                                 {"name": "Répétition espacée", "desc": "Courbe d'oubli d'Ebbinghaus. Algorithmes SM-2, Anki.", "cognitorium": "Planning de révision personnalisé."},
                                 {"name": "Testing effect", "desc": "Le test améliore la rétention plus que la relecture.", "cognitorium": "Quiz et auto-évaluation fréquents."},
                                 {"name": "Interleaving", "desc": "Alternance de types de problèmes. Améliore le transfert.", "cognitorium": "Mélange de compétences dans les exercices."},
                                 {"name": "Consolidation & Sommeil", "desc": "Rejeu hippocampique. Spindles. System consolidation.", "cognitorium": "Recommandations de timing de sommeil."}
                             ]},
                            {"name": "Métamémoire", "desc": "Jugements de confiance, prédictions de performance (JOL, FOK).", "cognitorium": "Widgets d'auto-évaluation et calibration.",
                             "children": [
                                 {"name": "Judgment of Learning (JOL)", "desc": "Prédiction de rappel futur. Souvent biaisée par la fluence.", "cognitorium": "Calibration des jugements de confiance."},
                                 {"name": "Feeling of Knowing (FOK)", "desc": "Sentiment de savoir avant récupération.", "cognitorium": "Indicateurs de familiarité vs maîtrise."}
                             ]},
                            {"name": "Entraînement cognitif", "desc": "Transfert proche vs lointain. Pas consensus sur transfert lointain (Chen & Yan 2025).", "cognitorium": "Programmes d'entraînement adaptatifs.",
                             "children": [
                                 {"name": "Tâche n-back", "desc": "Validité construit faible : chunking/familiarité pas vrai gain WMC (Huang 2025).", "cognitorium": "Éviter métrique unique. Multi-tâches."},
                                 {"name": "Dual n-back", "desc": "Version multi-modale. Jaeggi 2008 contesté.", "cognitorium": "Avec prudence et mesures multiples."},
                                 {"name": "Transfert lointain", "desc": "Amélioration sur tâches non entraînées. Rare et contesté.", "cognitorium": "Mesurer le transfert écologique, pas labo."}
                             ]}
                        ]
                    },
                    {
                        "name": "D. Langage (Psycholinguistique)",
                        "desc": "Compréhension, production et acquisition du langage.",
                        "children": [
                            {"name": "Phonologie & Syntaxe", "desc": "Traitement des sons et structures grammaticales.", "cognitorium": "NLP pour fiches métiers.",
                             "children": [
                                 {"name": "Parsing syntaxique", "desc": "Analyse incrémentale vs différée. Garden-path.", "cognitorium": "Structure des instructions."},
                                 {"name": "Prosodie", "desc": "Intonation, accent, rythme de la parole.", "cognitorium": "Feedback vocal naturel."}
                             ]},
                            {"name": "Sémantique & Pragmatique", "desc": "Sens des mots, inférences, théorie de l'esprit.", "cognitorium": "Sémantique des graphes de compétences.",
                             "children": [
                                 {"name": "Réseaux sémantiques", "desc": "Propagation d'activation. Priming sémantique.", "cognitorium": "Navigation associative dans les connaissances."},
                                 {"name": "Inférences & Pragmatique", "desc": "Implicatures, présuppositions, théorie de l'esprit.", "cognitorium": "Compréhension des intentions de l'apprenant."}
                             ]},
                            {"name": "Acquisition & Troubles", "desc": "Bilinguisme, dyslexie, compréhension de texte.", "cognitorium": "Accessibilité et adaptation textuelle.",
                             "children": [
                                 {"name": "Dyslexie", "desc": "Trouble spécifique de l'apprentissage de la lecture.", "cognitorium": "Adaptations typographiques et audio."},
                                 {"name": "Bilinguisme", "desc": "Avantage exécutif controversé. Code-switching.", "cognitorium": "Interfaces multilingues adaptatives."}
                             ]}
                        ]
                    },
                    {
                        "name": "E. Raisonnement & Décision",
                        "desc": "Formation de concepts, inférences et résolution de problèmes.",
                        "children": [
                            {"name": "Catégorisation", "desc": "Prototypes, exemplaires, théorie-theory.", "cognitorium": "Classification des compétences.",
                             "children": [
                                 {"name": "Prototypes", "desc": "Représentation centrale d'une catégorie. Rosch.", "cognitorium": "Exemples typiques de métiers."},
                                 {"name": "Exemplaires", "desc": "Stockage de tous les membres rencontrés.", "cognitorium": "Base de cas concrets."}
                             ]},
                            {"name": "Raisonnement déductif", "desc": "Syllogismes, logique, biais de confirmation.", "cognitorium": "Évaluation critique des réponses IA.",
                             "children": [
                                 {"name": "Biais de confirmation", "desc": "Tendance à chercher des informations confirmant ses croyances.", "cognitorium": "Présentation de perspectives alternatives."},
                                 {"name": "Raisonnement conditionnel", "desc": "Wason selection task. Modus ponens vs tollens.", "cognitorium": "Tâches de logique intégrées."}
                             ]},
                            {"name": "Décision & Jugement", "desc": "Heuristiques, prospect theory, framing.", "cognitorium": "Aide à la décision d'orientation.",
                             "children": [
                                 {"name": "Prospect Theory (Kahneman)", "desc": "Aversion à la perte. Fonction de valeur asymétrique.", "cognitorium": "Présentation des gains/pertes d'orientation."},
                                 {"name": "Heuristiques", "desc": "Availability, representativeness, anchoring.", "cognitorium": "Debiasing dans les recommandations."},
                                 {"name": "Nudge & Architecture de choix", "desc": "Influence douce des décisions. Defaults.", "cognitorium": "Defaults adaptatifs dans les parcours."}
                             ]},
                            {"name": "Résolution de problèmes", "desc": "Espace de problème, moyens-ends, insight.", "cognitorium": "Scaffolding de la résolution.",
                             "children": [
                                 {"name": "Insight & Impasse", "desc": "Restructuration soudaine. Aha! moment.", "cognitorium": "Favoriser les moments d'insight."},
                                 {"name": "Expertise", "desc": "Chunking, pattern recognition, 10000 heures.", "cognitorium": "Parcours vers l'expertise."}
                             ]}
                        ]
                    },
                    {
                        "name": "F. Métacognition & SRL",
                        "desc": "Connaissance et contrôle des processus cognitifs propres.",
                        "children": [
                            {"name": "Monitoring métacognitif", "desc": "Évaluation en temps réel de la compréhension et de la performance.", "cognitorium": "Dashboards de progression et calibration.",
                             "children": [
                                 {"name": "Calibration", "desc": "Adéquation entre confiance et performance réelle.", "cognitorium": "Feedback de calibration régulier."},
                                 {"name": "Illusion de compétence", "desc": "Surconfiance après lecture fluide. Dunning-Kruger.", "cognitorium": "Tests de vérification après lecture."}
                             ]},
                            {"name": "Contrôle métacognitif", "desc": "Ajustement des stratégies basé sur le monitoring.", "cognitorium": "Boucle SRL : plan → monitor → control → reflect.",
                             "children": [
                                 {"name": "Allocation du temps", "desc": "Décider combien de temps passer sur chaque item.", "cognitorium": "Recommandations de temps adaptatives."},
                                 {"name": "Sélection de stratégie", "desc": "Choisir la stratégie la plus adaptée au contexte.", "cognitorium": "Suggestions de stratégies contextuelles."}
                             ]},
                            {"name": "Self-Regulated Learning (SRL)", "desc": "Zimmerman : forethought → performance → self-reflection.", "cognitorium": "Architecture complète du module Cognitorium.",
                             "children": [
                                 {"name": "Phase Forethought", "desc": "Planification, fixation de buts, croyances motivationnelles.", "cognitorium": "Étape de planification du module."},
                                 {"name": "Phase Performance", "desc": "Auto-contrôle, auto-observation, stratégies.", "cognitorium": "Traces et monitoring en temps réel."},
                                 {"name": "Phase Self-reflection", "desc": "Auto-évaluation, auto-réaction, attribution.", "cognitorium": "Étape d'évaluation du module."}
                             ]},
                            {"name": "Fluence de traitement", "desc": "Expérience subjective de facilité. Indice métacognitif ubiquitaire (Alter 2009).", "cognitorium": "Design fluide + disfluence stratégique.",
                             "children": [
                                 {"name": "Fluence perceptive", "desc": "Clarté visuelle, contraste, police lisible.", "cognitorium": "Design UI optimisé pour la lisibilité."},
                                 {"name": "Fluence conceptuelle", "desc": "Facilité de compréhension sémantique.", "cognitorium": "Explications claires et progressives."},
                                 {"name": "Disfluence utile", "desc": "Difficulté désirable qui améliore l'apprentissage profond.", "cognitorium": "Introduction stratégique de complexité."}
                             ]}
                        ]
                    },
                    {
                        "name": "G. Fonctions Exécutives",
                        "desc": "Contrôle cognitif de haut niveau. Miyake : inhibition, flexibilité, mise à jour.",
                        "children": [
                            {"name": "Inhibition", "desc": "Suppression des réponses prépotentes et distracteurs.", "cognitorium": "Tâches de Stroop, Go/NoGo, antisaccade.",
                             "children": [
                                 {"name": "Inhibition motrice", "desc": "Stop-Signal. SSRT comme mesure.", "cognitorium": "Mesure de l'inhibition comme proxy AC."},
                                 {"name": "Inhibition cognitive", "desc": "Résistance à l'interférence. Flanker, Simon.", "cognitorium": "Design résistant aux distracteurs."}
                             ]},
                            {"name": "Flexibilité (Shifting)", "desc": "Alternance entre tâches, règles, ensembles mentaux.", "cognitorium": "Adaptation aux changements de contexte.",
                             "children": [
                                 {"name": "Task-switching", "desc": "Coût de switch, mélange de coûts.", "cognitorium": "Minimiser les changements de contexte."},
                                 {"name": "Flexibilité créative", "desc": "Pensée divergente, usage alternatif.", "cognitorium": "Exercices de pensée divergente."}
                             ]},
                            {"name": "Mise à jour (Updating)", "desc": "Modification du contenu de la mémoire de travail.", "cognitorium": "Mise à jour dynamique des connaissances.",
                             "children": [
                                 {"name": "N-back", "desc": "Tâche de mise à jour continue. Validité construit débattue.", "cognitorium": "Avec mesures convergentes."},
                                 {"name": "Running memory", "desc": "Mise à jour de listes en évolution.", "cognitorium": "Suivi de flux d'information."}
                             ]},
                            {"name": "Planification", "desc": "Organisation séquentielle d'actions vers un but. Tour de Hanoï/Londres.", "cognitorium": "Scaffolding de la planification d'apprentissage."}
                        ]
                    },
                    {
                        "name": "H. Émotion & Cognition",
                        "desc": "Interactions bidirectionnelles entre affect et cognition.",
                        "children": [
                            {"name": "Régulation émotionnelle", "desc": "Réévaluation cognitive, suppression, distraction.", "cognitorium": "Outils de recadrage constructif.",
                             "children": [
                                 {"name": "Réévaluation cognitive", "desc": "Reframing de la signification émotionnelle. Gross.", "cognitorium": "Techniques de recadrage dans le module SRL."},
                                 {"name": "Mindfulness", "desc": "Acceptation sans jugement. Réduction du stress.", "cognitorium": "Exercices de pleine conscience intégrés."}
                             ]},
                            {"name": "Affect & Apprentissage", "desc": "Émotions académiques : ennui, frustration, fierté, confusion.", "cognitorium": "Détection et gestion des émotions.",
                             "children": [
                                 {"name": "Confusion productive", "desc": "Confusion modérée favorise apprentissage profond (D'Mello).", "cognitorium": "Niveau optimal de défi."},
                                 {"name": "Flow (Csikszentmihalyi)", "desc": "État d'immersion optimal. Challenge = skills.", "cognitorium": "Équilibrage challenge/compétence."}
                             ]}
                        ]
                    },
                    {
                        "name": "I. Cognition Incarnée (4E)",
                        "desc": "Embodied, Embedded, Enacted, Extended. Alternative au cognitivisme classique.",
                        "children": [
                            {"name": "Embodied Cognition", "desc": "Cognition ancrée dans le corps. Gestes, posture, simulation.", "cognitorium": "Interfaces corporelles et gestuelles.",
                             "children": [
                                 {"name": "Simulation sensorimotrice", "desc": "Compréhension par réactivation des aires sensori-motrices.", "cognitorium": "Manipulation directe des concepts."},
                                 {"name": "Métaphore incarnée", "desc": "Concepts abstraits par extension métaphorique du corps (Lakoff).", "cognitorium": "Métaphores spatiales pour concepts abstraits."},
                                 {"name": "Effets corporels", "desc": "Posture, mouvement, température influencent le jugement.", "cognitorium": "Design environnemental favorable."}
                             ]},
                            {"name": "Situated / Embedded", "desc": "Cognition dans et par l'environnement. Scaffolding.", "cognitorium": "Environnements riches et structurés.",
                             "children": [
                                 {"name": "Scaffolding environnemental", "desc": "L'environnement supporte et structure la cognition.", "cognitorium": "Organisation spatiale de l'information."},
                                 {"name": "Couplage organisme-environnement", "desc": "Interaction dynamique continue. Pas de frontière stricte.", "cognitorium": "Boucles interactives temps réel."}
                             ]},
                            {"name": "Énactivisme", "desc": "Cognition = action. Sense-making. Autopoïèse (Varela).", "cognitorium": "Apprentissage par exploration active.",
                             "children": [
                                 {"name": "Sense-making", "desc": "Création de sens par interaction, pas par représentation.", "cognitorium": "Construction active de compréhension."},
                                 {"name": "Autopoïèse", "desc": "Auto-production du système vivant. Identité biologique.", "cognitorium": "Système adaptatif auto-organisé."}
                             ]},
                            {"name": "Cognition Étendue", "desc": "Outils et artefacts comme partie constitutive du système cognitif.", "cognitorium": "Graphes, dashboards, annotations comme extensions cognitives.",
                             "children": [
                                 {"name": "Offloading cognitif", "desc": "Déchargement sur l'environnement : notes, listes, cartes.", "cognitorium": "Outils de déchargement intégrés."},
                                 {"name": "Parity principle", "desc": "Si un processus externe joue le même rôle qu'un processus interne, il est cognitif.", "cognitorium": "Justification des extensions technologiques."}
                             ]}
                        ]
                    }
                ]
            },
            {
                "name": "Pilier 3 : Développement",
                "desc": "Évolution des fonctions psychologiques au cours de la vie.",
                "cognitorium": "Adaptation développementale des parcours.",
                "children": [
                    {"name": "Développement cognitif enfant", "desc": "Piaget, Vygotsky, théorie de l'esprit, fonctions exécutives en croissance.", "cognitorium": "Modules pour collèges/lycées.",
                     "children": [
                         {"name": "Stades piagétiens", "desc": "Sensorimoteur, préopératoire, concret, formel.", "cognitorium": "Adaptation au niveau développemental."},
                         {"name": "Zone proximale (Vygotsky)", "desc": "Écart entre performance seule et avec aide.", "cognitorium": "Scaffolding adaptatif au niveau de l'apprenant."},
                         {"name": "Théorie de l'esprit", "desc": "Compréhension des états mentaux d'autrui. Faux-croyance.", "cognitorium": "Collaboration et perspective-taking."}
                     ]},
                    {"name": "Développement adolescent", "desc": "Maturation préfrontale tardive. Prise de risque. Identité.", "cognitorium": "Orientation scolaire et identité vocationnelle.",
                     "children": [
                         {"name": "Maturation préfrontale", "desc": "Cortex préfrontal mature à ~25 ans. Contrôle exécutif en développement.", "cognitorium": "Scaffolding renforcé pour adolescents."},
                         {"name": "Identité vocationnelle", "desc": "Exploration et engagement. Modèle de Marcia.", "cognitorium": "Parcours d'exploration de métiers."}
                     ]},
                    {"name": "Vieillissement cognitif", "desc": "Déclin de la WMC, compensation par expertise et cristallisé.", "cognitorium": "Reconversion et formation continue.",
                     "children": [
                         {"name": "Réserve cognitive", "desc": "Protection contre le déclin par stimulation continue.", "cognitorium": "Programmes de stimulation cognitive."},
                         {"name": "Sagesse & Expertise", "desc": "Connaissances cristallisées compensent le déclin fluide.", "cognitorium": "Valorisation de l'expérience."}
                     ]}
                ]
            },
            {
                "name": "Pilier 4 : Sociale & Personnalité",
                "desc": "Influence du contexte social et des traits stables.",
                "cognitorium": "Personnalisation des profils d'orientation.",
                "children": [
                    {"name": "Psychologie Sociale", "desc": "Attitudes, influence, normes, désinformation.", "cognitorium": "Résilience face aux biais.",
                     "children": [
                         {"name": "Biais cognitifs sociaux", "desc": "Attribution, halo, conformité, polarisation de groupe.", "cognitorium": "Debiasing dans les recommandations."},
                         {"name": "Désinformation", "desc": "Propagation, inoculation, pensée critique.", "cognitorium": "Évaluation critique des sources IA."}
                     ]},
                    {"name": "Personnalité (Big Five / HEXACO)", "desc": "Traits stables : OCEAN + Honnêteté-Humilité.", "cognitorium": "Matching personnalité-métier.",
                     "children": [
                         {"name": "Ouverture", "desc": "Curiosité, créativité, exploration.", "cognitorium": "Recommandations exploratoires vs focalisées."},
                         {"name": "Conscienciosité", "desc": "Organisation, persévérance, autodiscipline.", "cognitorium": "Niveau de scaffolding adapté."},
                         {"name": "Neuroticisme", "desc": "Réactivité émotionnelle, anxiété.", "cognitorium": "Support émotionnel adapté."}
                     ]},
                    {"name": "Motivation & Autodétermination", "desc": "Deci & Ryan : autonomie, compétence, relation.", "cognitorium": "Stimulation de la motivation intrinsèque.",
                     "children": [
                         {"name": "Motivation intrinsèque", "desc": "Faire pour le plaisir de l'activité elle-même.", "cognitorium": "Gamification intrinsèque."},
                         {"name": "Goal-setting", "desc": "Buts SMART. Difficulté optimale.", "cognitorium": "Fixation de buts adaptatifs."}
                     ]}
                ]
            },
            {
                "name": "Pilier 5 : Santé Mentale & Clinique",
                "desc": "Psychopathologie, prévention et interventions.",
                "cognitorium": "Prévention du décrochage et inclusion.",
                "children": [
                    {"name": "Psychopathologie", "desc": "Troubles anxieux, dépressifs, TDAH, TSA.", "cognitorium": "Soutien inclusif et neurodiversité.",
                     "children": [
                         {"name": "Troubles anxieux", "desc": "Anxiété généralisée, phobies, TOC.", "cognitorium": "Gestion de l'anxiété d'orientation."},
                         {"name": "TDAH", "desc": "Déficit attentionnel et hyperactivité. Impact exécutif.", "cognitorium": "Interfaces adaptées au TDAH."},
                         {"name": "Neurodiversité", "desc": "TSA, dys-, HP. Forces et défis.", "cognitorium": "Parcours personnalisés neurodivers."}
                     ]},
                    {"name": "Psychothérapies (TCC)", "desc": "Restructuration cognitive. Efficacité validée (Cuijpers).", "cognitorium": "Outils de recadrage constructif.",
                     "children": [
                         {"name": "Restructuration cognitive", "desc": "Identification et modification des pensées automatiques.", "cognitorium": "Journal de pensées intégré."},
                         {"name": "Exposition graduée", "desc": "Affrontement progressif des situations redoutées.", "cognitorium": "Progression adaptative du défi."}
                     ]}
                ]
            },
            {
                "name": "Pilier 6 : Domaines Appliqués",
                "desc": "Champs d'application opérationnelle de la psychologie.",
                "cognitorium": "Cœur opérationnel de déploiement.",
                "children": [
                    {"name": "Éducation & Sciences de l'apprentissage", "desc": "Intégration GenAI, prompts métacognitifs, LMS.", "cognitorium": "Module d'apprentissage du Cognitorium.",
                     "children": [
                         {"name": "GenAI en éducation", "desc": "ChatGPT, Claude comme tuteurs. Scaffolding nécessaire.", "cognitorium": "IA encadrée par boucle SRL."},
                         {"name": "Apprentissage adaptatif", "desc": "Algorithmes adaptant le contenu au niveau.", "cognitorium": "Parcours personnalisés."},
                         {"name": "Évaluation formative", "desc": "Feedback continu pour l'apprentissage, pas la notation.", "cognitorium": "Feedback formatif intégré."}
                     ]},
                    {"name": "Travail & Organisations (I/O)", "desc": "Ergonomie, stress, leadership, télétravail.", "cognitorium": "Module d'orientation professionnelle.",
                     "children": [
                         {"name": "Ergonomie cognitive", "desc": "Charge mentale, design de poste, fiabilité humaine.", "cognitorium": "Design des interfaces de travail."},
                         {"name": "Orientation professionnelle", "desc": "Matching compétences-métiers. Bilan de compétences.", "cognitorium": "Moteur de matching principal."}
                     ]},
                    {"name": "Ergonomie Cognitive & IHM", "desc": "Design centré utilisateur, accessibilité, UX.", "cognitorium": "Architecture UI/UX du graphe D3.",
                     "children": [
                         {"name": "Design centré utilisateur", "desc": "Itérations, tests utilisateurs, personas.", "cognitorium": "Processus de design du Cognitorium."},
                         {"name": "Accessibilité cognitive", "desc": "FALC, design universel, neurodiversité.", "cognitorium": "Accessibilité de tous les modules."},
                         {"name": "Data Visualization", "desc": "Bertin, Tufte. Perception des graphiques.", "cognitorium": "Visualisations optimales des données."}
                     ]}
                ]
            }
        ]
    }

# ──────────────── AGENT CHERCHEUR API ────────────────

class AgentRunRequest(BaseModel):
    task: str
    max_results: int = 10
    use_llm: Optional[bool] = None
    skills: List[str] = []      # compétences choisies via le bouton (+)
    subjects: List[str] = []     # sujets ajoutés via le bouton (+)

@app.get("/agent", response_class=HTMLResponse)
def agent_page(request: Request):
    from agent.core.context import AGENT_NAME, AGENT_SYMBOL, AGENT_TAGLINE
    return templates.TemplateResponse(request, "agent.html",
                                      {"request": request,
                                       "agent_name": AGENT_NAME,
                                       "agent_symbol": AGENT_SYMBOL,
                                       "agent_tagline": AGENT_TAGLINE})

@app.get("/api/agent/skills")
def agent_skills():
    from agent.core.registry import catalog
    return catalog()

@app.get("/api/agent/status")
def agent_status():
    from agent.core import llm as llm_mod
    from agent.core.context import AGENT_NAME, AGENT_SYMBOL
    st = llm_mod.llm_status()
    st.update({"name": AGENT_NAME, "symbol": AGENT_SYMBOL})
    return st

@app.post("/api/agent/run")
def agent_run(req: AgentRunRequest):
    """Exécute une tâche via l'agent chercheur (synchrone, borné)."""
    from agent import Agent
    if not req.task or not req.task.strip():
        raise HTTPException(status_code=400, detail="Tâche vide")
    agent = Agent(max_results=min(req.max_results, 50), use_llm=req.use_llm)
    try:
        trace = agent.run(req.task.strip()[:500],
                          force_skills=[s for s in req.skills if s][:8],
                          subjects=[s for s in req.subjects if s.strip()][:6])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur agent : {e}")
    return _trace_public(trace)

@app.get("/api/agent/runs")
def agent_runs_list():
    """Historique des runs (métadonnées)."""
    from agent.core.context import RUNS_DIR
    runs = []
    if RUNS_DIR.exists():
        for d in sorted(RUNS_DIR.iterdir(), reverse=True)[:30]:
            tj = d / "trace.json"
            if tj.exists():
                try:
                    import json
                    t = json.loads(tj.read_text(encoding="utf-8"))
                    runs.append({"run_id": t["run_id"], "tache": t["tache"], "statut": t["statut"],
                                 "cerveau": t["cerveau"], "duree_s": t["duree_s"],
                                 "etapes": len(t.get("steps", [])), "date": t["date"],
                                 "mode_degrade": t.get("mode_degrade", False)})
                except Exception:
                    continue
    return runs

@app.get("/api/agent/runs/{run_id}")
def agent_run_detail(run_id: str):
    from agent.core.context import RUNS_DIR
    tj = RUNS_DIR / run_id / "trace.json"
    if not tj.exists():
        raise HTTPException(status_code=404, detail="Run introuvable")
    import json
    return _trace_public(json.loads(tj.read_text(encoding="utf-8")))

@app.get("/api/agent/artifact")
def agent_artifact(path: str):
    """Sert un artefact markdown/html/json/csv d'un run (chemins contrôlés).

    Accepte les chemins relatifs à output/agent_runs/ ou à la racine du dépôt.
    """
    from agent.core.context import ROOT
    clean = path.replace("\\", "/").lstrip("/")
    prefix = "output/"
    if clean.startswith(prefix):
        clean = clean[len(prefix):]
    base = (ROOT / "output").resolve()
    target = (base / clean).resolve()
    if not str(target).startswith(str(base)) or not target.exists():
        raise HTTPException(status_code=404, detail="Artefact introuvable")
    if target.suffix not in {".md", ".html", ".json", ".csv"}:
        raise HTTPException(status_code=400, detail="Type non autorisé")
    return PlainTextResponse(target.read_text(encoding="utf-8"))

def _trace_public(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Allège la trace pour l'affichage web."""
    light = {k: v for k, v in trace.items() if k not in {"llm"}}
    for s in light.get("steps", []):
        data = s.get("data") or {}
        s["data"] = {k: v for k, v in data.items() if k in {"query", "total", "par_base", "distribution",
                                                            "resultats", "domaines", "identifies",
                                                            "apres_deduplication", "drafts"}}
        if isinstance(s["data"].get("resultats"), list):
            s["data"]["resultats"] = s["data"]["resultats"][:8]
    light["llm_status"] = trace.get("llm", {})
    return light

# ──────────────── COSMOS / SOL — SYSTÈME MULTI-AGENTS ────────────────

class SolChatRequest(BaseModel):
    message: str

class BudgetUpdateRequest(BaseModel):
    daily_cap_usd: Optional[float] = None
    per_mission_cap_usd: Optional[float] = None
    monthly_cap_usd: Optional[float] = None
    income_monthly_usd: Optional[float] = None

@app.get("/sol", response_class=HTMLResponse)
def sol_page(request: Request):
    from agent.core.context import AGENT_NAME
    return templates.TemplateResponse(request, "sol.html", {"request": request, "agent_name": AGENT_NAME})

@app.get("/api/cosmos/bodies")
def cosmos_bodies():
    from cosmos.bodies import celestial_registry
    return celestial_registry()

@app.get("/api/cosmos/state")
def cosmos_state():
    from cosmos import sol
    from cosmos.system import get_system
    get_system()
    return sol.system_state()

@app.get("/api/cosmos/interactions")
def cosmos_interactions(limit: int = 50):
    from cosmos.system import get_system
    sysdict = get_system()
    return sysdict["bus"].history(limit=min(max(limit, 1), 200))

@app.get("/api/cosmos/budget")
def cosmos_budget():
    from cosmos import venus
    return venus.status()

@app.post("/api/cosmos/budget")
def cosmos_budget_update(req: BudgetUpdateRequest):
    from cosmos import venus
    return venus.set_caps(daily_cap_usd=req.daily_cap_usd,
                          per_mission_cap_usd=req.per_mission_cap_usd,
                          monthly_cap_usd=req.monthly_cap_usd,
                          income_monthly_usd=req.income_monthly_usd)

@app.post("/api/cosmos/chat")
def cosmos_chat(req: SolChatRequest):
    """Chat du système — LAPLACE ✳ est l'interlocuteur principal (SOL ☉ approuve).
    Les demandes d'outils sont routées vers l'armurerie de Mars ♂."""
    from cosmos import laplace
    from cosmos.system import get_system
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message vide")
    get_system()
    return laplace.chat(req.message.strip()[:600])

@app.get("/api/cosmos/body/{body_id}")
def cosmos_body(body_id: str):
    """Fiche complète d'un corps : identité entreprise, constellation de
    connaissances, interactions approuvées, mémoire, stats."""
    from cosmos.bodies import find_body
    from cosmos.knowledge import knowledge_graph
    from cosmos import memory
    from cosmos.system import get_system
    b, par = find_body(body_id)
    if b is None:
        raise HTTPException(status_code=404, detail=f"Corps inconnu : {body_id}")
    parent = None
    if par is not None:
        from cosmos.bodies import BODIES as _BD
        pid = next(k for k, v in _BD.items()
                   if any(s["id"] == body_id for s in v.get("satellites") or [])
                   or any(c["id"] == body_id for c in v.get("court") or []))
        parent = {"id": pid, "name": par["name"], "symbol": par["symbol"],
                  "departement": par.get("departement"),
                  "cour": "court" in par}
    g = knowledge_graph(body_id) or {"nodes": [], "links": []}
    hist = [m for m in get_system()["bus"].history(limit=400)
            if body_id in (m.get("source"), m.get("target"))][:40]
    items = [i for i in memory.items(limit=400) if i.get("corps") == body_id][:40]
    return {"body": {**b, "id": body_id, "parent": parent},
            "graph": g,
            "interactions": hist,
            "memoire": items,
            "stats": {"interactions": len(hist), "memoire": len(items),
                      "concepts": sum(1 for n in g["nodes"] if n.get("type") == "concept"),
                      "references": sum(1 for n in g["nodes"] if n.get("type") == "reference")}}

@app.get("/api/cosmos/knowledge/{body_id}")
def cosmos_knowledge(body_id: str):
    """Constellation de connaissances d'un corps (graph D3 : nodes+links)."""
    from cosmos.knowledge import knowledge_graph
    g = knowledge_graph(body_id)
    if g is None:
        raise HTTPException(status_code=404, detail=f"Corps inconnu : {body_id}")
    return g

# ──────────────── CONSTELLATIONS / MÉMOIRE / DASHBOARD ────────────────

class MemoryItemRequest(BaseModel):
    type: str
    titre: str
    contenu: str = ""
    tags: List[str] = []
    source: str = "user"
    corps: str = "systeme"

@app.get("/api/cosmos/constellations")
def cosmos_constellations():
    """Catalogue des constellations (zodiac) proposées dans le sélecteur du graphe."""
    from cosmos.constellations import views
    return views()

@app.get("/api/cosmos/constellations/{view_id}")
def cosmos_constellation_graph(view_id: str):
    from cosmos.constellations import graph_for
    g = graph_for(view_id)
    if g is None:
        raise HTTPException(status_code=404, detail=f"Constellation inconnue : {view_id}")
    return g

@app.get("/api/cosmos/memory")
def cosmos_memory(type: Optional[str] = None, limit: int = 200):
    from cosmos import memory
    return {"items": memory.items(limit=min(max(limit, 1), 500), type_=type),
            "stats": memory.stats()}

@app.post("/api/cosmos/memory")
def cosmos_memory_add(req: MemoryItemRequest):
    """Ingère un élément dans la mémoire : article, thèse, draft, poster, texte, audio, vidéo…"""
    from cosmos import memory
    if not req.titre.strip():
        raise HTTPException(status_code=400, detail="Titre requis")
    return memory.record_item(req.type, req.titre.strip(), req.contenu,
                              tags=req.tags, source=req.source, corps=req.corps)

@app.get("/api/cosmos/taxonomy")
def cosmos_taxonomy():
    from cosmos import memory
    return memory.load_taxonomy()

@app.get("/api/concepts")
def all_concepts():
    """Concepts partagés : 4E (Cognitorium) + base 42 champs + satellites + cour + taxonomie + mémoire."""
    from cosmos import memory
    merged = {c["id"]: {**c, "sources": ["4E"]} for c in get_concepts_4e()}
    for c in memory.concepts():
        if c["id"] in merged:
            src = set(merged[c["id"]].get("sources", ["4E"])) | set(c["sources"])
            merged[c["id"]]["sources"] = sorted(src)
        else:
            merged[c["id"]] = {**c, "solidite": None,
                               "mecanismes": [f"relié à {r}" for r in c.get("refs", [])[:4]],
                               "applications": [], "gaps": []}
    return list(merged.values())

@app.get("/api/dashboard/metrics")
def dashboard_metrics():
    """Toutes les métriques du système — pédagogique : chaque métrique explique
    sa valeur (quoi/qui/comment), avec jauge, barres, liste réelle ou mini
    simulateur quand c'est pertinent. Les formules sont toujours affichées,
    ou signalées absentes (compteurs simples)."""
    import csv as _csv
    import json as _json
    from collections import Counter as _Counter
    from pathlib import Path as _P
    from agent.core.registry import list_skills
    from agent.skills.trust_scoring import _heuristic_trust
    from cosmos import memory, sol as sol_mod, venus as venus_mod
    from cosmos.bodies import BODIES
    from cosmos.system import get_system
    get_system()
    init_db()

    stats = get_stats()
    integ = sol_mod.integrity()
    ven = venus_mod.status()
    mem = memory.stats()

    # Données réelles : références (CSV 42 champs) et relations (SQLite)
    rows = []
    csv_path = _P("data/nodes_etat_art_psychologie.csv")
    if csv_path.exists():
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(_csv.DictReader(f))
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT source_id, target_id, relation_type FROM reference_relations LIMIT 500")
        rel_rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rel_rows = []
    conn.close()
    if not rel_rows:  # repli : champ `relations` du CSV
        for r in rows:
            for part in (r.get("relations") or "").split(";"):
                if "->" in part and ":" in part:
                    left, tgt = part.split("->")
                    if ":" in left:
                        s_, typ = left.split(":")
                        rel_rows.append({"source_id": s_.strip(), "target_id": tgt.strip(),
                                         "relation_type": typ.strip()})
    ref_by_id = {r["id"]: r for r in rows}
    rel_counts = _Counter(r["relation_type"] for r in rel_rows)

    def _cit(r):
        for k in ("citations_google_scholar", "citations_crossref", "citations_openalex"):
            v = str(r.get(k) or "").strip()
            if v.isdigit() and int(v) > 0:
                return int(v)
        return 0

    # ── Trust : moyenne + décomposition heuristique réelle ──
    declared = [int(r["trust_factor"]) for r in rows if str(r.get("trust_factor") or "").isdigit()]
    avg_trust = round(sum(declared) / len(declared), 1) if declared else None
    comp_avg = {}
    if rows:
        details = [_heuristic_trust(r)["detail"] for r in rows]
        for k in ("M", "R", "O", "C", "T", "P"):
            comp_avg[k] = round(sum(d[k] for d in details) / len(details), 1)
    trust_dist = _Counter(("faible" if int(t) < 30 else "modéré" if int(t) < 60
                           else "élevé" if int(t) < 85 else "très élevé") for t in declared)

    prisma = {"identifies": None, "dedup": None}
    ppath = _P("output/prisma_state.json")
    if ppath.exists():
        try:
            ps = _json.loads(ppath.read_text(encoding="utf-8"))
            last = ps.get("dernier") or (ps.get("historique") or [{}])[-1]
            prisma = {"identifies": last.get("identifies"), "dedup": last.get("apres_deduplication")}
        except Exception:
            pass

    n_inter = len(sol_mod._bus.history(limit=500)) if sol_mod._bus else 0
    burn = round(ven["spend_today_usd"] / ven["budget"]["daily_cap_usd"], 3) if ven["budget"]["daily_cap_usd"] else 0

    TRUST_FORMULA = ["Trust = M + R + O + C + T − P  (plafonné à 0–100)",
                     "M · Méthodologie 0–30 : méta-analyse 30 · revue systématique 25 · empirique 15 (+5 triangulation ≥3)",
                     "R · Réplication 0–20 : grand échantillon N≥1000 (+6), répliques",
                     "O · Open science 0–20 : accès ouvert 6 + données 7 + code 3 + préenregistrement 4",
                     "C · Cohérence 0–15 : question explicite 2 + tags ≥3 3",
                     "T · Transparence 0–15 : peer review 5 + justification 2",
                     "P · Pénalités 0–50 : non peer review +15 · preprint +10"]
    TRUST_ZONES = [[0, 30, "faible", "#fb7185"], [30, 60, "modéré", "#fbbf24"],
                   [60, 85, "élevé", "#34d399"], [85, 100, "très élevé", "#22d3ee"]]

    metrics = [
        {"id": "trust", "label": "Trust factor moyen", "value": avg_trust, "unit": "/100",
         "icon": "🛡️", "viz": "gauge", "gauge": {"max": 100, "zones": TRUST_ZONES},
         "formula": TRUST_FORMULA,
         "explain": [
             "Ce score mesure la **confiance** que le système peut accorder aux connaissances de la base.",
             "**100 = confiance maximale** : une méta-analyse préenregistrée, au grand échantillon répliqué, 100 % open science (accès ouvert + données + code + préenregistrement), parfaitement cohérente et transparente, sans aucune pénalité.",
             f"**{avg_trust} = la moyenne des {len(declared)} références** enregistrées. La barre ci-dessous montre d'où viennent les points perdus : tout vient de M (méthodo solide) mais O (open science) et R (réplication) ne sont pas complets sur toutes les références.",
             f"Répartition actuelle : {dict(trust_dist)}.",
             "Paliers de lecture : <30 faible · 30–59 modéré · 60–84 élevé · ≥85 très élevé."],
         "bars_caption": "Décomposition moyenne réelle (recalcul heuristique sur les références)",
         "bars": [
             {"label": "M · Méthodologie", "value": comp_avg.get("M"), "max": 30, "color": "#818cf8"},
             {"label": "R · Réplication", "value": comp_avg.get("R"), "max": 20, "color": "#34d399"},
             {"label": "O · Open science", "value": comp_avg.get("O"), "max": 20, "color": "#22d3ee"},
             {"label": "C · Cohérence", "value": comp_avg.get("C"), "max": 15, "color": "#c084fc"},
             {"label": "T · Transparence", "value": comp_avg.get("T"), "max": 15, "color": "#fbbf24"},
             {"label": "P · Pénalités (retranchées)", "value": comp_avg.get("P"), "max": 15, "color": "#fb7185"}],
         "legend": ["Moyenne des trust_factor déclarés dans la base 42 champs.",
                    "Recalcul complet par référence : compétence trust_scoring."]},

        {"id": "integrite", "label": "Intégrité du système", "value": integ["score"], "unit": "/100",
         "icon": "🟢", "status": integ["statut"], "viz": "sim",
         "formula": ["Score = 100 − min(40, taux_erreur × 100) − 15·[burn ≥ 0,8] − 10·[dégradé ≥ 50 %]",
                     "taux_erreur = interactions `failed` ÷ total — les refus de politique (⛔) ne comptent PAS : c'est SOL qui fait son travail",
                     "burn = dépense du jour ÷ cap journalier · dégradé = missions en mode hors-ligne"],
         "explain": [
             "**100 = système parfait** : aucune interaction en erreur, budget très en dessous du cap, missions en mode réel (pas dégradées).",
             f"Actuellement **{integ['score']}/100 ({integ['statut']})** : {integ['interactions_total']} interactions journalisées, taux d'erreur {integ['taux_echec']:.0%}, burn {integ['burn_rate_budget']:.0%}, part dégradée {integ['part_mode_degrade']:.0%}.",
             "**Mini-simulateur ci-dessous** : bougez les curseurs pour voir comment chaque facteur fait baisser le score et déclenche les alertes de SOL."],
         "sim": {"inputs": [
                     {"key": "err", "label": "Taux d'erreur des interactions", "min": 0, "max": 0.5, "step": 0.01, "value": integ["taux_echec"]},
                     {"key": "burn", "label": "Burn rate budgétaire (dépense/cap)", "min": 0, "max": 1.5, "step": 0.05, "value": integ["burn_rate_budget"]},
                     {"key": "deg", "label": "Part des missions en mode dégradé", "min": 0, "max": 1, "step": 0.05, "value": integ["part_mode_degrade"]}],
                 "note": "Valeurs initiales = valeurs réelles actuelles du système."},
         "legend": integ["alertes"] or ["Aucune alerte préventive — situation nominale."]},

        {"id": "references", "label": "Références (base 42 champs)", "value": stats.get("total_references"),
         "unit": "publ.", "icon": "📚", "viz": "list",
         "formula": None,
         "explain": [
             f"**{stats.get('total_references')} publications scientifiques** sont enregistrées dans la base de données du projet (fichier `data/nodes_etat_art_psychologie.csv`, 42 champs par référence).",
             "Ce sont des **articles, méta-analyses, revues systématiques** de psychologie cognitive (attention, mémoire, éducation, clinique…) et de méthodologie — la liste complète est ci-dessous.",
             "La base s'agrandit à chaque mission de recherche d'Uranus et à chaque DOI enrichi."],
         "items_caption": "Les références enregistrées (qui ?)",
         "items": [{"main": r.get("reference_courte", r["id"]),
                    "secondary": (r.get("theme") or "")[:90],
                    "badge": f"trust {r.get('trust_factor')}",
                    "badge_color": "#34d399" if str(r.get("trust_factor", "0")).isdigit() and int(r["trust_factor"]) >= 60 else "#fbbf24"}
                   for r in rows],
         "legend": ["Pas de formule — indicateur compteur (lignes validées du CSV)."]},

        {"id": "relations", "label": "Relations entre références", "value": len(rel_rows),
         "unit": "liens", "icon": "🔗", "viz": "bars+list",
         "formula": None,
         "explain": [
             f"**{len(rel_rows)} liens** relient les références entre elles : qui **opérationnalise** qui, qui **converge**, qui **synthétise**, qui **falsifie** ou **révise** qui.",
             "Exemple : une méta-analyse (Titania) *synthèse* plusieurs études primaires ; une réplication échouée *falsification* l'étude d'origine.",
             "Répartition par type de relation ci-dessous, exemples réels ensuite."],
         "bars_caption": "Répartition par type de relation",
         "bars": [{"label": t, "value": n, "max": max(rel_counts.values()) if rel_counts else 1, "color": "#818cf8"}
                  for t, n in rel_counts.most_common()],
         "items_caption": "Exemples de liens (source → type → cible)",
         "items": [{"main": f"{ref_by_id.get(r['source_id'], {}).get('reference_courte', r['source_id'])} → {r['relation_type']} → {ref_by_id.get(r['target_id'], {}).get('reference_courte', r['target_id'])}",
                    "secondary": "", "badge": "", "badge_color": ""}
                   for r in rel_rows[:12]],
         "legend": ["Pas de formule — compteur de liens inter-références."]},

        {"id": "citations", "label": "Citations (de qui ?)", "value": stats.get("average_citations"),
         "unit": "moy./réf.", "icon": "📈", "viz": "bars",
         "formula": ["moyenne = Σ citations de chaque référence ÷ nombre de références"],
         "explain": [
             "Chaque référence est citée par d'autres publications : plus une référence est citée, plus elle a influencé son domaine.",
             f"La **moyenne est de {stats.get('average_citations')} citations par référence** — tirée vers le haut par quelques travaux très majeurs (voir la répartition ci-dessous : de qui viennent les citations).",
             "Sources des comptages : Google Scholar / Crossref / OpenAlex, relevés à date dans la base."],
         "bars_caption": "Citations par référence (qui pèse combien)",
         "bars": sorted([{"label": r.get("reference_courte", r["id"]), "value": _cit(r),
                          "max": max(_cit(r) for r in rows) if rows else 1, "color": "#38bdf8"}
                         for r in rows if _cit(r) > 0], key=lambda b: -b["value"]),
         "legend": []},

        {"id": "burn", "label": "Burn rate budgétaire", "value": burn, "unit": "",
         "icon": "♀", "viz": "gauge",
         "gauge": {"max": 1.5, "zones": [[0, 0.5, "sobre", "#34d399"], [0.5, 0.8, "à surveiller", "#fbbf24"],
                                         [0.8, 1.5, "dérive", "#fb7185"]]},
         "formula": ["burn = dépense LLM du jour ÷ cap journalier",
                     "alerte automatique de SOL si burn ≥ 0,8"],
         "explain": [
             "**Vénus ♀ plafonne les dépenses** : le burn rate dit où on en est du budget du jour.",
             f"Aujourd'hui : {ven['spend_today_usd']:.4f} $ dépensés sur un cap de {ven['budget']['daily_cap_usd']} $. À 1,0 le cap est atteint — au-delà, Vénus refuse les missions LLM (bascule moteur à règles, coût nul)."],
         "legend": [f"Projection mois : {ven['forecast']['monthly_projection_usd']:.2f} $"]},

        {"id": "tokens", "label": "Tokens aujourd'hui", "value": ven["tokens_today"], "unit": "tok",
         "icon": "🪙",
         "formula": ["Σ tokens entrée et sortie des appels LLM du jour (grand livre de Thalie)"],
         "explain": ["Les tokens sont les « mots » consommés par les modèles de langage. Le grand livre les comptabilise à chaque requête pour facturer chaque mission.",
                     "Moteur à règles (par défaut ici) = 0 token, 0 $."],
         "legend": []},

        {"id": "prisma", "label": "PRISMA (dernier run)", "value": prisma["dedup"], "unit": "réf.",
         "icon": "🔀", "viz": "bars",
         "formula": ["après_déduplication = identifiés − doublons (DOI identiques + titres similaires ≥ 0,93)"],
         "explain": ["Le flux PRISMA trace le tamis documentaire : combien de références trouvées, combien conservées après suppression des doublons inter-bases."],
         "bars": [{"label": "Identifiés (toutes bases)", "value": prisma["identifies"] or 0,
                   "max": max(prisma["identifies"] or 1, prisma["dedup"] or 1), "color": "#818cf8"},
                  {"label": "Après déduplication", "value": prisma["dedup"] or 0,
                   "max": max(prisma["identifies"] or 1, prisma["dedup"] or 1), "color": "#34d399"}],
         "legend": []},

        {"id": "memoire", "label": "Mémoire du système", "value": mem["total"], "unit": "éléments",
         "icon": "🧠", "viz": "bars+list",
         "formula": None,
         "explain": [
             f"**{mem['total']} éléments** constituent la mémoire vivante du système : chaque **question** posée à SOL, chaque **référence** trouvée par Uranus, chaque **papier/dossier/plan** généré, et tout ce que vous ingérez (articles, thèses, drafts, posters, textes, audio, vidéo…).",
             "La mémoire est **partagée** par tous les agents et alimente les concepts et la taxonomie.",
             "Répartition par type ci-dessous + derniers éléments reçus."],
         "bars_caption": "À quoi correspondent ces éléments (par type)",
         "bars": [{"label": t, "value": n, "max": max(mem["par_type"].values()) if mem["par_type"] else 1, "color": "#38bdf8"}
                  for t, n in sorted(mem["par_type"].items(), key=lambda kv: -kv[1])],
         "items_caption": "Derniers éléments mémorisés",
         "items": [{"main": f"[{i['type']}] {i['titre'][:70]}", "secondary": i["ts"][:16],
                    "badge": i["corps"], "badge_color": "#fbbf24"}
                   for i in memory.items(limit=8)],
         "legend": ["Pas de formule — compteur d'éléments journalisés."]},

        {"id": "concepts", "label": "Concepts partagés", "value": mem["concepts"], "unit": "",
         "icon": "💠", "formula": None,
         "explain": ["Tous les concepts manipulés par l'app et les agents : concepts 4E, tags de la base 42 champs, domaines des satellites d'Uranus et de la cour de Vénus, feuilles de taxonomie, tags de la mémoire — fusionnés en un registre unique (onglet Concepts)."],
         "legend": ["Pas de formule — agrégation de registres."]},
        {"id": "taxonomy", "label": "Feuilles de taxonomie", "value": mem["taxonomy_feuilles"], "unit": "",
         "icon": "🌳", "formula": None,
         "explain": ["Nombre de sujets les plus fins de l'arbre de connaissances (Psychologie, Construction, Robotique, IA + Émergents). Chaque mission/question peut en ajouter."],
         "legend": ["S'enrichit automatiquement (branchage par mots-clés)."]},
        {"id": "interactions", "label": "Interactions approuvées", "value": n_inter, "unit": "",
         "icon": "☰", "formula": None,
         "explain": ["Messages échangés entre corps (SOL, Uranus, Vénus, satellites, vous) — chacun approuvé par SOL et journalisé."],
         "legend": ["Journal : output/cosmos/interactions.jsonl"]},
        {"id": "skills", "label": "Compétences Uranus", "value": len(list_skills()), "unit": "",
         "icon": "⚙️", "formula": None,
         "explain": ["Capacités exécutables d'Uranus (recherche, enrichissement DOI, validation, trust, biais, PRISMA, synthèse, papier, dossier, veille…)."],
         "legend": ["Registre extensible via le décorateur @skill."]},
        {"id": "corps", "label": "Corps du système", "value": 3 + len(BODIES["uranus"]["satellites"]) + len(BODIES["venus"]["court"]),
         "unit": "", "icon": "🪐", "formula": None,
         "explain": ["SOL ☉ + 2 planètes (Uranus ♅ recherche, Vénus ♀ finances) + 7 satellites d'Uranus + 4 analystes de la cour de Vénus."],
         "legend": []},
    ]
    return {"metrics": metrics,
            "system": {"integrite": integ, "spend_today_usd": ven["spend_today_usd"],
                       "daily_cap_usd": ven["budget"]["daily_cap_usd"]}}


# ──────────────── CONSOLE URANUS : DASHBOARD, TIMELINE 4D, LAPLACE ────────────────

@app.get("/api/agent/subjects")
def agent_subjects():
    """Sujets connus proposés par le (+) : branches de taxonomie + domaines + satellites."""
    from cosmos import memory
    from cosmos.bodies import BODIES
    tree = memory.load_taxonomy()
    branches = [c["name"] for c in tree.get("children", [])]
    leaves = memory.taxonomy_leaves()
    sats = [s["name"].split(" ")[0] for s in BODIES["uranus"]["satellites"]]
    from cosmos.knowledge import SATELLITE_CONCEPTS
    domaines = sorted({c.split(" ")[0].capitalize() for cs in SATELLITE_CONCEPTS.values() for c in cs})
    return {"branches": branches, "feuilles": leaves[:60], "satellites": sats,
            "domaines": domaines[:12]}


def _agent_metrics_for(agent_id: str):
    """Métriques d'un agent précis : interactions, mémoire, concepts, tokens."""
    from collections import Counter as _Counter
    from cosmos import memory, ledger as _ledger
    from cosmos.bodies import find_body
    from cosmos.knowledge import knowledge_graph
    from cosmos.system import get_system
    _b, _par = find_body(agent_id)
    b = _b or {}
    if _par is not None:
        b = {**b, "departement": f"{_par.get('departement')} · {_b.get('role', '')[:60]}"}
    hist = [m for m in get_system()["bus"].history(limit=1000)
            if agent_id in (m.get("source"), m.get("target"))]
    st = {"approved": sum(1 for m in hist if m.get("status") in ("approved", "delivered")),
          "denied": sum(1 for m in hist if m.get("status") == "denied"),
          "failed": sum(1 for m in hist if m.get("status") == "failed")}
    g = knowledge_graph(agent_id) or {"nodes": [], "links": []}
    items = [i for i in memory.items(limit=1000) if i.get("corps") == agent_id]
    par_type = _Counter(i["type"] for i in items)
    entries = [e for e in _ledger.read_ledger() if e.get("agent") == agent_id]
    tokens = sum(e["tokens_in"] + e["tokens_out"] for e in entries)
    n_concepts = sum(1 for n in g["nodes"] if n.get("type") == "concept")
    cards = [
        {"id": "identite", "label": "Identité", "value": None, "unit": "",
         "icon": b.get("symbol") or "◍",
         "explain": [f"**{b.get('name', agent_id)}** — {b.get('departement') or b.get('kind', 'corps')}.",
                     b.get("role", "")],
         "detail": []},
        {"id": "interactions", "label": "Interactions approuvées", "value": len(hist), "unit": "échanges",
         "icon": "✅",
         "explain": [f"{st['approved']} approuvées/livrées · {st['denied']} refusées (budget SOL) · "
                     f"{st['failed']} échecs.", "Toute interaction passe par l'approbation de ☉ SOL."],
         "detail": [{"main": f"{m.get('source')}→{m.get('target')} · {(m.get('reason') or m.get('type') or '')[:50]}",
                     "secondary": (m.get("ts") or "")[11:16],
                     "badge": m.get("status", ""), "badge_color": "#34d399"} for m in hist[:15]]},
        {"id": "memoire", "label": "Mémoire du corps", "value": len(items), "unit": "items",
         "icon": "🧠",
         "explain": ["Éléments versés en mémoire au nom de ce corps (type, titre, date)."],
         "detail": [{"main": i["titre"][:80], "secondary": i["ts"][:16],
                     "badge": i["type"], "badge_color": "#fbbf24"} for i in items[:15]]},
        {"id": "concepts", "label": "Concepts de sa constellation", "value": n_concepts,
         "unit": "concepts", "icon": "💠",
         "explain": [f"Constellation : {len(g['nodes'])} nœuds, {len(g['links'])} liens, "
                     f"{sum(1 for n in g['nodes'] if n.get('type') == 'reference')} références matchées."],
         "detail": [{"main": n["label"][:80], "secondary": n.get("type", ""),
                     "badge": (n.get("doi") or "")[:18], "badge_color": "#38bdf8"}
                    for n in g["nodes"] if n.get("type") in ("concept", "reference")][:15]},
        {"id": "tokens", "label": "Tokens consommés", "value": tokens, "unit": "tok",
         "icon": "🪙",
         "explain": [f"Coût cumulé {round(sum(e['cost_usd'] for e in entries), 6)} $ au grand livre de Vénus.",
                     "Moteur à règles = 0 token — ce corps fonctionne surtout par règles."],
         "detail": [{"main": e["model"], "secondary": f"{e['tokens_in']}+{e['tokens_out']} tok",
                     "badge": "", "badge_color": ""} for e in entries[-10:]]},
    ]
    return {"agent": agent_id, "cards": cards,
            "summary": {"interactions": len(hist), "memoire": len(items),
                        "concepts": n_concepts, "tokens": tokens,
                        "par_type": dict(par_type)}}


@app.get("/api/agent/metrics")
def agent_metrics(agent: Optional[str] = None):
    """Dashboard agent : global (Uranus) si pas de paramètre, sinon fiche de l'agent."""
    if agent and agent not in ("uranus", ""):
        return _agent_metrics_for(agent)
    import json as _json
    from collections import Counter as _Counter
    from pathlib import Path as _P
    from cosmos import memory, ledger as _ledger
    runs_dir = _P("output/agent_runs")
    runs = []
    if runs_dir.exists():
        for d in sorted(runs_dir.iterdir(), reverse=True):
            tj = d / "trace.json"
            if tj.exists():
                try:
                    runs.append(_json.loads(tj.read_text(encoding="utf-8")))
                except Exception:
                    continue
    skill_usage = _Counter(s["skill"] for t in runs for s in t.get("steps", []))
    status_count = _Counter(t.get("statut") for t in runs)
    total_dur = sum(t.get("duree_s", 0) for t in runs)
    degraded = sum(1 for t in runs if t.get("mode_degrade"))

    entries = _ledger.read_ledger()
    tokens_in = sum(e["tokens_in"] for e in entries)
    tokens_out = sum(e["tokens_out"] for e in entries)
    cost_total = round(sum(e["cost_usd"] for e in entries), 6)
    by_model = _Counter(e["model"] for e in entries)

    mem = memory.stats()
    consulted = mem["par_type"].get("reference", 0)          # ressources consultées
    provided = sum(v for k, v in mem["par_type"].items()
                   if k in {"papier", "dossier", "plan", "graph", "rapport", "document"})  # fournies
    created = mem["concepts"]                                 # connaissances créées (concepts)
    by_day = _Counter(t["date"][:10] for t in runs)

    cards = [
        {"id": "taches", "label": "Tâches accomplies", "value": len(runs), "unit": "missions",
         "icon": "✅", "explain": [f"{len(runs)} missions exécutées par Uranus "
                                   f"({status_count.get('succès', 0)} succès, "
                                   f"{status_count.get('partiel', 0)} partielles).",
                                   "Chaque mission est approuvée par SOL et journalisée."],
         "detail": [{"main": t.get("tache", "")[:80], "secondary": t["date"][:16],
                     "badge": t.get("statut", ""), "badge_color": "#34d399"}
                    for t in runs[:15]]},
        {"id": "tokens", "label": "Tokens consommés", "value": tokens_in + tokens_out, "unit": "tok",
         "icon": "🪙", "explain": [f"{tokens_in} tokens en entrée / {tokens_out} en sortie "
                                   f"— coût cumulé {cost_total} $.",
                                   "Moteur à règles = 0 token. Chaque appel LLM est compté "
                                   "au grand livre de Vénus."],
         "detail": [{"main": m, "secondary": f"{n} actions", "badge": "", "badge_color": ""}
                    for m, n in by_model.most_common()]},
        {"id": "consultees", "label": "Ressources consultées", "value": consulted, "unit": "réf.",
         "icon": "🔎", "explain": ["Références scientifiques trouvées par les recherches "
                                   "multi-bases (Crossref, OpenAlex, PubMed) et versées en mémoire."],
         "detail": [{"main": i["titre"][:80], "secondary": i["ts"][:16],
                     "badge": "réf.", "badge_color": "#38bdf8"}
                    for i in memory.items(type_="reference", limit=15)]},
        {"id": "fournies", "label": "Ressources fournies", "value": provided, "unit": "doc.",
         "icon": "📤", "explain": ["Documents produits et remis : papiers scientifiques, dossiers "
                                   "stratégiques, plans, graphes, rapports."],
         "detail": [{"main": i["titre"][:80], "secondary": i["ts"][:16],
                     "badge": i["type"], "badge_color": "#fbbf24"}
                    for i in memory.items(limit=40) if i["type"] in
                    {"papier", "dossier", "plan", "graph", "rapport", "document"}][:15]},
        {"id": "creees", "label": "Connaissances créées", "value": created, "unit": "concepts",
         "icon": "💠", "explain": ["Concepts du registre partagé (base + satellites + cour + "
                                   "taxonomie + mémoire) — croît à chaque mission et question."],
         "detail": [{"main": c["name"][:80], "secondary": ", ".join(c["sources"][:2]),
                     "badge": "", "badge_color": ""}
                    for c in memory.concepts()[:15]]},
        {"id": "competences", "label": "Compétences utilisées", "value": len(skill_usage), "unit": "skills",
         "icon": "⚙️", "explain": ["Répartition d'usage des compétences sur toutes les missions."],
         "detail": [{"main": s, "secondary": f"{n}×", "badge": "", "badge_color": ""}
                    for s, n in skill_usage.most_common()]},
    ]
    return {"cards": cards,
            "summary": {"missions": len(runs), "succes": status_count.get("succès", 0),
                        "partiels": status_count.get("partiel", 0),
                        "duree_totale_s": round(total_dur, 1), "degradees": degraded,
                        "tokens_in": tokens_in, "tokens_out": tokens_out, "cout_usd": cost_total,
                        "par_jour": dict(sorted(by_day.items())[-14:])}}


@app.get("/api/agent/timeline")
def agent_timeline(agent: Optional[str] = None, limit_runs: int = 12):
    """Timeline 4D des actions : runs d'Uranus (global) ou interactions+mémoire d'un agent."""
    import json as _json
    from datetime import datetime as _dt, timedelta as _td
    from pathlib import Path as _P
    nodes, links = [], []
    if agent and agent not in ("uranus", ""):
        from cosmos import memory
        from cosmos.system import get_system
        hist = [m for m in get_system()["bus"].history(limit=2000)
                if agent in (m.get("source"), m.get("target"))]
        anchor_ts = hist[0]["ts"] if hist else _dt.now().isoformat()
        nodes.append({"id": "corps:" + agent, "label": agent, "type": "run", "ts": anchor_ts})
        for m in hist:
            mid = "it:" + m.get("id", "")
            nodes.append({"id": mid, "label": f"{m.get('source')}→{m.get('target')}",
                          "type": "skill", "ts": m.get("ts"),
                          "ok": m.get("status") in ("approved", "delivered")})
            links.append({"source": "corps:" + agent, "target": mid, "type": "execute"})
        for it in [i for i in memory.items(limit=1000) if i.get("corps") == agent]:
            nid = "mem:" + it["id"]
            nodes.append({"id": nid, "label": it["titre"][:34], "type": "artifact", "ts": it["ts"]})
            links.append({"source": "corps:" + agent, "target": nid, "type": "produit"})
        return {"nodes": nodes, "links": links}
    runs_dir = _P("output/agent_runs")
    if not runs_dir.exists():
        return {"nodes": [], "links": []}
    for d in sorted(runs_dir.iterdir(), reverse=True)[:max(1, min(limit_runs, 40))]:
        tj = d / "trace.json"
        if not tj.exists():
            continue
        try:
            t = _json.loads(tj.read_text(encoding="utf-8"))
        except Exception:
            continue
        base = _dt.fromisoformat(t["date"])
        rid = "run:" + t["run_id"]
        nodes.append({"id": rid, "label": (t.get("tache", "")[:38] or t["run_id"]),
                      "type": "run", "ts": t["date"], "statut": t.get("statut")})
        offset = 0.0
        for s in t.get("steps", []):
            sid = f"{t['run_id']}:{s['skill']}:{s['n']}"
            ts = (base + _td(seconds=offset)).isoformat(timespec="seconds")
            offset += s.get("duration_s", 0) or 0.1
            nodes.append({"id": sid, "label": s["skill"], "type": "skill",
                          "ts": ts, "ok": s.get("ok")})
            links.append({"source": rid, "target": sid, "type": "execute"})
            for a in s.get("artifacts", []) or []:
                aid = "art:" + a.split("/")[-1] + ":" + sid.split(":")[-1]
                nodes.append({"id": aid, "label": a.split("/")[-1][:30], "type": "artifact", "ts": ts,
                              "path": a})
                links.append({"source": sid, "target": aid, "type": "produit"})
            for r in (s.get("data", {}) or {}).get("resultats", []) or []:
                if isinstance(r, dict) and r.get("titre"):
                    xid = "ref:" + (r.get("doi") or r["titre"])[:40] + ":" + sid.split(":")[-1]
                    nodes.append({"id": xid, "label": r["titre"][:34], "type": "reference",
                                  "ts": ts, "doi": r.get("doi")})
                    links.append({"source": sid, "target": xid, "type": "trouve"})
    return {"nodes": nodes, "links": links}


# ──────────────── LAPLACE ✳ / SEBAS ◉ ────────────────

class LaplaceAgentRequest(BaseModel):
    name: str
    role: str = ""
    parent: str = "uranus"
    kind: str = "satellite"
    system: str = "cognitorium"

class LaplaceImproveRequest(BaseModel):
    role: Optional[str] = None
    name: Optional[str] = None

class LaplaceSystemRequest(BaseModel):
    name: str
    star_name: str = "SOL-jumeau"

class SebasObserveRequest(BaseModel):
    sensor: str
    contenu: str
    tags: List[str] = []

@app.get("/api/laplace")
def laplace_registry():
    from cosmos import nebula
    return {"agents": nebula.list_agents(), "systems": nebula.list_systems()}

@app.post("/api/laplace/agents")
def laplace_create_agent(req: LaplaceAgentRequest):
    from cosmos import nebula
    try:
        return nebula.create_agent(req.name, req.role, req.parent, req.kind, req.system)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/laplace/agents/{agent_id}/improve")
def laplace_improve(agent_id: str, req: LaplaceImproveRequest):
    from cosmos import nebula
    try:
        return nebula.improve_agent(agent_id, req.role, req.name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/laplace/agents/{agent_id}/test")
def laplace_test(agent_id: str):
    from cosmos import nebula
    return nebula.test_agent(agent_id)

@app.post("/api/laplace/systems")
def laplace_create_system(req: LaplaceSystemRequest):
    from cosmos import nebula
    try:
        return nebula.create_system(req.name, req.star_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/sebas/sensors")
def sebas_sensors():
    from cosmos import nebula
    return nebula.sensors_status()

@app.post("/api/sebas/observe")
def sebas_observe(req: SebasObserveRequest):
    from cosmos import nebula
    try:
        return nebula.record_observation(req.sensor, req.contenu, req.tags)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ──────────────── SYNCHRO BASE DE DONNÉES ↔ MÉMOIRE ────────────────

@app.post("/api/database/sync")
def database_sync():
    from app.database import sync_memory_items
    return {"synchronises": sync_memory_items()}

@app.get("/api/memory-items")
def memory_items(type: Optional[str] = None, limit: int = 300):
    from app.database import get_memory_items, sync_memory_items
    sync_memory_items()
    return {"items": get_memory_items(type_filter=type, limit=min(max(limit, 1), 1000))}


# ──────────────── MARS ♂ : ARMURERIE DU SYSTÈME ────────────────

class MarsToolRequest(BaseModel):
    agent: str = "user"
    besoin: str
    donnees: str = ""

@app.get("/api/mars/armory")
def mars_armory():
    """Registre de l'armurerie : demandes d'outils, maquettes, outils livrés —
    classés par catégorie."""
    from cosmos import mars
    return {"requests": mars.list_requests(),
            "par_categorie": mars.armory_by_category(),
            "categories": mars.TOOL_CATEGORIES,
            "catalogue_opensource": mars.OSS_CATALOG}


class ToolUseRequest(BaseModel):
    id: str


@app.post("/api/mars/use")
def mars_use(req: ToolUseRequest):
    """Marque un outil comme utilisé (compteur — un outil ouvert n'est plus « jamais utilisé »)."""
    from cosmos import mars
    return mars.marquer_utilisation(req.id)


class PruneRequest(BaseModel):
    confirm: bool = False


@app.post("/api/mars/prune")
def mars_prune(req: PruneRequest):
    """✂ Élagage de l'inventaire par Deimos ◦ (équipe de Mars) : audit des outils
    inutiles (doublons fonctionnels, maquettes mortes) ; dry-run par défaut,
    fauche réelle (âmes au Tartare, résidu conservé) sur confirmation."""
    from cosmos import mars
    return mars.elaguer(confirm=req.confirm)

@app.post("/api/mars/request")
def mars_request(req: MarsToolRequest):
    """Protocole armurier : recherche open source → sinon maquette Deimos ◦."""
    from cosmos import mars
    try:
        return mars.request_tool(req.agent, req.besoin, req.donnees)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/mars/forge/{request_id}")
def mars_forge(request_id: str):
    """Phobos ◂ forge l'outil fonctionnel depuis la maquette de Deimos ◦."""
    from cosmos import mars
    try:
        return mars.forge_tool(request_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/mars/file")
def mars_file(id: str, kind: str = "outil"):
    """Sert la maquette ou l'outil forgé (HTML autoportant)."""
    from cosmos import mars
    req = mars.get_request(id)
    if req is None:
        raise HTTPException(status_code=404, detail=f"demande inconnue : {id}")
    path = req.get("maquette" if kind == "maquette" else "outil")
    if not path:
        raise HTTPException(status_code=404, detail=f"Pas encore de {kind} pour {id}")
    from pathlib import Path as _P
    from fastapi.responses import HTMLResponse
    return HTMLResponse(_P(path).read_text(encoding="utf-8"))


# ──────────────── MÉTATRON ✦ (méta-prompting, satellite de Laplace) ────────────────

class MetatronRequest(BaseModel):
    message: str

class MetatronSuggestRequest(BaseModel):
    mission: str

@app.post("/api/metatron/analyze")
def metatron_analyze(req: MetatronRequest):
    """Analyse méta-prompting d'une requête : intention, domaines, prompt enrichi."""
    from cosmos import metatron
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message vide")
    return metatron.analyze_request(req.message.strip()[:800])

@app.post("/api/metatron/suggest")
def metatron_suggest(req: MetatronSuggestRequest):
    """Spécification d'agent proposée par Métatron pour Laplace."""
    from cosmos import metatron
    if not req.mission.strip():
        raise HTTPException(status_code=400, detail="Mission vide")
    return metatron.suggest_agent_spec(req.mission.strip()[:800])

# ──────────────── PLUTON ♇ / HADÈS (cycle de vie & optimisation) ────────────────

@app.get("/api/hades/scan")
def hades_scan():
    """Hadès inventorie le système : redondances, outdated, junk, journaux."""
    from cosmos import hades
    return hades.scan_system()

@app.get("/api/themis/audit")
def themis_audit():
    """Thémis ⚖ juge le système : menaces, conseils, constitution démocratique."""
    from cosmos import themis
    return themis.audit()


class ThemisApplyRequest(BaseModel):
    confirm: bool = False


@app.post("/api/themis/apply")
def themis_apply(req: ThemisApplyRequest):
    """Thémis applique la justice : ordonne la fauche à Hadès (accord requis)."""
    from cosmos import themis
    return themis.appliquer(confirm=req.confirm)


@app.get("/api/hades/target")
def hades_target(cible: str, type: str):
    """Dikè instruit le dossier d'un condamné : l'entité réelle qui sera supprimée."""
    from cosmos import hades
    try:
        return hades.describe_target(cible, type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/godseye")
def godseye_state():
    """👁 God's Eye View — l'outil open source de veille mondiale que Sebas manie
    pour aider Mercure/Hermès ; inclut son agence de l'ombre (astres-espions)."""
    from cosmos import godseye
    return godseye.state()


class GodEyeSpyRequest(BaseModel):
    mission: str = ""


@app.post("/api/godseye/spy")
def godseye_spy(req: GodEyeSpyRequest):
    """Sebas demande un nouvel astre-espion (agence de l'ombre) pour récolter
    des informations utiles — création validée par le flux nébuleuse ☉ SOL."""
    from cosmos import godseye
    try:
        ag = godseye.request_shadow_astre(req.mission)
        return {"ok": True, "astre": ag,
                "statut": f"👁 {ag.get('name')} entre en orbite autour de Sebas — "
                          f"mission : {ag.get('role', '').split('— ')[-1]}"}
    except Exception as e:
        return {"ok": False, "statut": f"l'agence refuse : {e}"}


@app.get("/api/mobiglas")
def mobiglas_state():
    """🥽 MobiGlas — l'instrument cognitif : pipeline réel (monde → capteurs →
    features → modèles → inférences → action) + inférences traçables."""
    from cosmos import mobiglas
    return mobiglas.state()


@app.get("/api/shadow")
def shadow_state():
    """🕵 Bureau de l'Ombre — Sera Victoria (agent de terrain de Sebas), son
    équipe, ses outils de surveillance (OSS + forge de Mars), sa contrainte."""
    from cosmos import shadow
    return shadow.state()


class ShadowHireRequest(BaseModel):
    mission: str = ""


@app.post("/api/shadow/team")
def shadow_hire(req: ShadowHireRequest):
    """Sera recrute un assistant dans son équipe personnelle (validation ☉ SOL)."""
    from cosmos import shadow
    try:
        a = shadow.recruter(req.mission)
        return {"ok": True, "assistant": a,
                "statut": f"🕵 {a.get('name')} rejoint l'équipe de Sera Victoria — {a.get('role', '').split('— ')[-1]}"}
    except Exception as e:
        return {"ok": False, "statut": f"le bureau refuse : {e}"}


class ForgeOssRequest(BaseModel):
    outil: str
    nom: str = ""
    url: str = ""


@app.post("/api/forge/oss")
def forge_oss(req: ForgeOssRequest):
    """Mars ouvre (ou retrouve) le chantier R&D d'un outil open source :
    examiner → analyser → reconstruire à l'identique → améliorer → utiliser →
    boucle → présenter. Un cran par appel."""
    from cosmos import mars
    f = mars.forge_find_by_tool(req.outil)
    if f:
        r = mars.forge_advance(f["id"])
    else:
        r = mars.forge_start(req.outil, req.nom, req.url)
    return r


@app.get("/api/olympus")
def olympus_state():
    """🏛 Le Mont Olympe : les divinités incarnées à leur poste, en mouvement
    selon leur activité réelle (procès de Thémis, forge de Mars, Porte des
    Enfers d'Hadès…)."""
    from cosmos import olympus
    return olympus.state()


@app.get("/api/underworld")
def underworld_state():
    """🔥 INFERNO — le royaume d'Hadès : les âmes des entités fauchées."""
    from cosmos import underworld
    return underworld.state()


class UnderworldRestoreRequest(BaseModel):
    id: str
    confirm: bool = False


@app.post("/api/underworld/restore")
def underworld_restore(req: UnderworldRestoreRequest):
    """Cerbère 🐾 laisse remonter une âme (résurrection, accord du souverain requis)."""
    from cosmos import underworld
    return underworld.resurrect(req.id, confirm=req.confirm)


class HadesReapRequest(BaseModel):
    confirm: bool = False

@app.post("/api/hades/reap")
def hades_reap(req: HadesReapRequest):
    """La fauche : Charon exécute (confirm=false → simulation)."""
    from cosmos import hades
    return hades.reap(confirm=req.confirm)

# ──────────────── PROFIL COGNITIF (induit des schémas d'utilisation) ────────────────

@app.get("/api/profile/cognitive")
def profile_cognitive():
    """Profil cognitif de l'utilisateur, induit de ses interactions réelles."""
    from cosmos import cogniprofile
    return cogniprofile.build_profile()


# ──────────────── APOLLON (divinations) · SEBAS (commandes divines) · TRAITS ═══════════════

class DivinationRequest(BaseModel):
    question: str = ""

@app.post("/api/apollon/divination")
def apollon_divination(req: DivinationRequest):
    """Le chariot d'Apollon 🏆 prononce une prévision de fonctionnement du système."""
    from cosmos import apollon
    return apollon.divination(req.question.strip()[:300])

class SebasCommandRequest(BaseModel):
    commande: str
    agent: str = "laplace"

@app.post("/api/sebas/execute")
def sebas_execute(req: SebasCommandRequest):
    """Sebas ◉ exécute une commande divine de Laplace (routage règles, honnête)."""
    from cosmos import sebas
    if not req.commande.strip():
        raise HTTPException(status_code=400, detail="Commande vide")
    return sebas.execute(req.commande.strip()[:400], agent=req.agent[:30])

class TraitRequest(BaseModel):
    trait: str

@app.post("/api/profile/traits")
def profile_add_trait(req: TraitRequest):
    """Ajoute un trait déclaré par l'utilisateur à son profil cognitif (il se
    décrit lui-même — le graphe de profil devient modifiable)."""
    from cosmos import memory
    t = req.trait.strip()
    if not t:
        raise HTTPException(status_code=400, detail="Trait vide")
    item = memory.record_item("profil", t[:140], contenu="trait déclaré par l'utilisateur",
                              tags=["profil", "déclaratif"], source="user", corps="user")
    return item
