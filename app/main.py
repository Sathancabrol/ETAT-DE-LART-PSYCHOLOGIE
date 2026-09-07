from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import re
import sqlite3
import subprocess
import sys
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

# ──────────────── PANORAMA GITHUB (repos > branches > modules) ────────────────
# Snapshot genere par scripts/github_inventory.py (token GitHub COTE SERVEUR
# uniquement, jamais expose au client). L'API ne fait que lire le JSON.

INVENTORY_PATH = os.environ.get("GITHUB_INVENTORY_PATH", "data/github_inventory.json")
INVENTORY_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "scripts", "github_inventory.py")


@app.get("/repos", response_class=HTMLResponse)
def repos_page(request: Request):
    """Page dediee : panorama des depots GitHub + volet lateral + vue fusion."""
    return templates.TemplateResponse(request, "repos.html", {"request": request})


def load_inventory() -> Dict[str, Any]:
    if not os.path.exists(INVENTORY_PATH):
        raise HTTPException(
            status_code=503,
            detail="Snapshot GitHub introuvable. Lancez "
                   "'python3 scripts/github_inventory.py' ou POST /api/github/refresh.")
    with open(INVENTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def repo_summary(r: Dict[str, Any]) -> Dict[str, Any]:
    commits = r.get("recent_commits", []) or []
    return {
        "name": r.get("name"),
        "full_name": r.get("full_name"),
        "description": r.get("description"),
        "url": r.get("url"),
        "default_branch": r.get("default_branch"),
        "primary_language": r.get("primary_language"),
        "languages": r.get("languages", {}),
        "stars": r.get("stars", 0),
        "forks": r.get("forks", 0),
        "open_issues": r.get("open_issues", 0),
        "size_kb": r.get("size_kb", 0),
        "updated_at": r.get("updated_at"),
        "pushed_at": r.get("pushed_at"),
        "topics": r.get("topics", []),
        "is_fork": r.get("is_fork", False),
        "is_archived": r.get("is_archived", False),
        "is_empty": r.get("is_empty", False),
        "status": r.get("status", "ok"),
        "error": r.get("error"),
        "branches": r.get("branches", []),
        "branch_count": len(r.get("branches", [])),
        "commit_count": len(commits),
        "last_commit": commits[0] if commits else None,
        "modules": [{"path": m.get("path"), "name": m.get("name"),
                     "kind": m.get("kind"), "manifests": m.get("manifests", []),
                     "files_count": m.get("files_count", 0),
                     "dep_count": len(m.get("dependencies", []))}
                    for m in r.get("modules", [])],
        "module_count": len(r.get("modules", [])),
        "files_total": r.get("files_total", 0),
        "dep_count": len(r.get("all_dependencies", [])),
    }


@app.get("/api/github/snapshot")
def github_snapshot():
    """Meta du snapshot + resume de chaque repo (allege pour les cartes)."""
    inv = load_inventory()
    repos = [repo_summary(r) for r in inv.get("repos", [])]
    ok = sum(1 for r in repos if r["status"] == "ok")
    return {
        "generated_at": inv.get("generated_at"),
        "owner": inv.get("owner"),
        "source": inv.get("source"),
        "api_calls": inv.get("api_calls"),
        "rate_limit": inv.get("rate_limit", {}),
        "repo_count": len(repos),
        "repo_ok": ok,
        "module_count": sum(r["module_count"] for r in repos),
        "repos": repos,
    }


@app.get("/api/github/repos/{repo_name}")
def github_repo_detail(repo_name: str):
    """Detail complet d'un repo (README, commits, modules, dependances)."""
    inv = load_inventory()
    for r in inv.get("repos", []):
        if r.get("name") == repo_name:
            return r
    raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' absent du snapshot")


@app.get("/api/github/fusion")
def github_fusion():
    """Vue fusion : graphe repos <-> modules <-> dependances partagees."""
    inv = load_inventory()
    fusion = inv.get("fusion", {})
    repos = [r for r in inv.get("repos", []) if r.get("status") == "ok"]

    nodes, links = [], []
    for r in repos:
        nodes.append({
            "id": f"repo:{r['name']}", "label": r["name"], "type": "repo",
            "group": r.get("primary_language") or "Inconnu",
            "desc": r.get("description") or "Sans description",
            "modules": len(r.get("modules", [])),
            "branches": len(r.get("branches", [])),
            "commits": len(r.get("recent_commits", [])),
            "stars": r.get("stars", 0),
        })
    for r in repos:
        for m in r.get("modules", []):
            mid = f"mod:{r['name']}/{m.get('path')}"
            nodes.append({
                "id": mid, "label": m.get("path"), "type": "module",
                "group": r["name"], "repo": r["name"],
                "kind": m.get("kind"), "manifests": m.get("manifests", []),
                "files": m.get("files_count", 0),
                "deps": len(m.get("dependencies", [])),
                "desc": f"Module '{m.get('path')}' du repo {r['name']} "
                        f"({m.get('kind')}, {len(m.get('dependencies', []))} deps).",
            })
            links.append({"source": f"repo:{r['name']}", "target": mid,
                          "type": "contains"})
    for s in fusion.get("shared_dependencies", []):
        nodes.append({
            "id": f"dep:{s['name']}", "label": s["name"], "type": "dep",
            "group": "partagee", "used_by": len(s.get("used_by", [])),
            "desc": f"Dependance partagee par {len(s.get('used_by', []))} modules.",
        })
        for u in s.get("used_by", []):
            links.append({"source": f"mod:{u['repo']}/{u['module']}",
                          "target": f"dep:{s['name']}", "type": "depends"})
    for c in fusion.get("cross_references", []):
        links.append({"source": f"repo:{c['from_repo']}",
                      "target": f"repo:{c['to_repo']}",
                      "type": "mentions", "via": c.get("via", "")})

    # retirer les liens orphelins (securite)
    ids = {n["id"] for n in nodes}
    links = [l for l in links if l["source"] in ids and l["target"] in ids]

    # matrice dependances partagees x repos (pour le tableau)
    repo_names = [r["name"] for r in repos]
    matrix = []
    for s in fusion.get("shared_dependencies", []):
        present = {u["repo"] for u in s.get("used_by", [])}
        matrix.append({"dep": s["name"],
                       "repos": {rn: (rn in present) for rn in repo_names}})

    return {
        "generated_at": inv.get("generated_at"),
        "nodes": nodes, "links": links,
        "shared_dependencies": fusion.get("shared_dependencies", []),
        "cross_references": fusion.get("cross_references", []),
        "language_groups": fusion.get("language_groups", []),
        "matrix": matrix, "repo_names": repo_names,
        "counts": {"repos": fusion.get("repo_count", 0),
                   "modules": fusion.get("module_count", 0),
                   "shared_deps": len(fusion.get("shared_dependencies", []))},
    }


@app.post("/api/github/refresh")
def github_refresh(owner: Optional[str] = None):
    """Regenere le snapshot via le script serveur (token jamais expose)."""
    inv_owner = None
    if os.path.exists(INVENTORY_PATH):
        try:
            with open(INVENTORY_PATH, encoding="utf-8") as f:
                inv_owner = json.load(f).get("owner")
        except Exception:
            pass
    target = owner or inv_owner or "Sathancabrol"
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", target):
        raise HTTPException(status_code=400, detail="Nom owner GitHub invalide")
    cmd = [sys.executable, INVENTORY_SCRIPT, "--owner", target,
           "--out", INVENTORY_PATH]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=280)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504,
                            detail="Refresh trop long (>280s), reessayez plus tard")
    if proc.returncode != 0:
        raise HTTPException(status_code=502, detail=(
            "Echec du refresh GitHub : " + (proc.stderr or proc.stdout)[-500:]))
    try:
        with open(INVENTORY_PATH, encoding="utf-8") as f:
            new = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=502,
                            detail=f"Snapshot regenere mais illisible : {e}")
    return {"status": "refreshed", "owner": target,
            "generated_at": new.get("generated_at"),
            "repo_count": len(new.get("repos", [])),
            "log": (proc.stderr or "")[-800:]}

# ──────────────── MONOREPO NAVIGATEUR + PREVIEWS ────────────────
# Lit le monorepo local (sathancabrol-monorepo) : exploration des fichiers
# et previews web servies en same-origin (iframe navigable).
import mimetypes

mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/json", ".geojsonl")
mimetypes.add_type("text/javascript", ".mjs")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONOREPO_CANDIDATES = [
    os.environ.get("MONOREPO_PATH", ""),
    os.path.join(REPO_ROOT, "monorepo"),
    os.path.join(REPO_ROOT, "..", "monorepo"),
    os.path.join(REPO_ROOT, "..", "sathancabrol-monorepo"),
    "/home/user/sathancabrol-monorepo",
]

BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg",
               ".pdf", ".zip", ".gz", ".mp3", ".wav", ".ogg", ".mp4", ".webm",
               ".woff", ".woff2", ".ttf", ".eot", ".wasm", ".pyc", ".patch"}
CODE_EXTS = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".json",
             ".jsonl", ".geojsonl", ".html", ".css", ".scss", ".xml", ".yml",
             ".yaml", ".toml", ".ini", ".cfg", ".md", ".rst", ".txt", ".csv",
             ".sh", ".c", ".h", ".java", ".go", ".rs", ".sql", ".vue"}
LANG_MAP = {".py": "python", ".js": "javascript", ".mjs": "javascript",
            ".cjs": "javascript", ".ts": "typescript", ".tsx": "tsx",
            ".jsx": "jsx", ".json": "json", ".html": "xml", ".css": "css",
            ".yml": "yaml", ".yaml": "yaml", ".toml": "ini", ".sh": "bash",
            ".md": "markdown", ".xml": "xml", ".sql": "sql"}

_mono_cache: Dict[str, Any] = {}


def monorepo_root() -> str:
    for c in MONOREPO_CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "projects")):
            return os.path.normpath(c)
    raise HTTPException(
        status_code=503,
        detail="Monorepo introuvable. Cloner 'sathancabrol-monorepo' a cote de "
               "ce depot ou definir MONOREPO_PATH. Voir docs/MONOREPO.md.")


def mono_projects_dir() -> str:
    return os.path.join(monorepo_root(), "projects")


def list_projects() -> List[str]:
    base = mono_projects_dir()
    return sorted(d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d)) and not d.startswith("."))


def safe_project_path(project: str, subpath: str = "") -> str:
    if project not in list_projects():
        raise HTTPException(status_code=404, detail=f"Projet '{project}' inconnu")
    base = os.path.realpath(os.path.join(mono_projects_dir(), project))
    target = os.path.realpath(os.path.join(base, subpath or ""))
    if target != base and not target.startswith(base + os.sep):
        raise HTTPException(status_code=400, detail="Chemin hors projet (traversal refuse)")
    return target


def project_manifest() -> Dict[str, Any]:
    try:
        with open(os.path.join(monorepo_root(), "MANIFEST.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def detect_entries(project: str) -> List[Dict[str, str]]:
    """Points d'entree web (previews) d'un projet, par priorite."""
    base = os.path.join(mono_projects_dir(), project)
    entries: List[Dict[str, str]] = []

    def exists(p: str) -> bool:
        return os.path.isfile(os.path.join(base, p))

    has_dist = exists("dist/index.html")
    if has_dist:
        entries.append({"label": "App buildée (dist)", "path": "dist/index.html"})
    for cand, label in [("index.html", "Page d'accueil"),
                        ("public/index.html", "Page publique"),
                        ("docs/index.html", "Doc d'accueil")]:
        if cand == "index.html" and has_dist:
            continue  # source vite : inutilisable sans build, dist fait foi
        if exists(cand):
            entries.append({"label": label, "path": cand})
    for extra in ["learning/index.html", "watchtower-mods/index.html"]:
        if exists(extra):
            entries.append({"label": extra.split("/")[0], "path": extra})
    vis = os.path.join(base, "output", "visual")
    if os.path.isdir(vis):
        for f in sorted(os.listdir(vis)):
            if f.endswith(".html"):
                entries.append({"label": f"visuel : {f}",
                                "path": f"output/visual/{f}"})
    return entries


def project_stats(project: str) -> Dict[str, int]:
    if project in _mono_cache:
        return _mono_cache[project]
    base = os.path.join(mono_projects_dir(), project)
    files = dirs = size = 0
    for root, dnames, fnames in os.walk(base):
        dnames[:] = [d for d in dnames if d != "node_modules"]
        dirs += len(dnames)
        for fn in fnames:
            files += 1
            try:
                size += os.path.getsize(os.path.join(root, fn))
            except OSError:
                pass
    st = {"files": files, "dirs": dirs, "size": size}
    _mono_cache[project] = st
    return st


def file_kind(name: str) -> str:
    ext = os.path.splitext(name)[1].lower()
    if ext == ".md":
        return "markdown"
    if ext == ".html":
        return "html"
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in CODE_EXTS:
        return "code"
    if ext in BINARY_EXTS:
        return "binary"
    return "other"


@app.get("/monorepo", response_class=HTMLResponse)
def monorepo_page(request: Request):
    """Explorateur du monorepo + previews web navigables."""
    return templates.TemplateResponse(request, "monorepo.html", {"request": request})


@app.get("/api/mono/projects")
def mono_projects():
    manifest = project_manifest().get("projects", {})
    out = []
    for p in list_projects():
        entries = detect_entries(p)
        st = project_stats(p)
        meta = manifest.get(p, {})
        out.append({
            "name": p, "url": meta.get("url"), "sha": meta.get("sha"),
            "branch": meta.get("branch", "main"),
            "stack": meta.get("stack", ""),
            "entries": entries,
            "preview_kind": ("built" if entries and entries[0]["path"].startswith("dist/")
                             else "static" if entries else "none"),
            **st,
        })
    return {"root": monorepo_root(), "count": len(out), "projects": out}


@app.get("/api/mono/tree")
def mono_tree(project: str = Query(...), path: str = Query(default="")):
    target = safe_project_path(project, path)
    if not os.path.isdir(target):
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    rel = os.path.relpath(target, os.path.join(mono_projects_dir(), project))
    rel = "" if rel == "." else rel
    crumbs = [{"name": project, "path": ""}]
    if rel:
        acc = []
        for part in rel.split(os.sep):
            acc.append(part)
            crumbs.append({"name": part, "path": "/".join(acc)})
    dirs, files = [], []
    for name in sorted(os.listdir(target)):
        if name in {"node_modules", ".git"} or name.startswith("."):
            continue
        full = os.path.join(target, name)
        rp = f"{rel}/{name}" if rel else name
        if os.path.isdir(full):
            dirs.append({"name": name, "path": rp})
        else:
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            files.append({"name": name, "path": rp, "size": size,
                          "ext": os.path.splitext(name)[1].lower(),
                          "kind": file_kind(name)})
    return {"project": project, "path": rel, "breadcrumbs": crumbs,
            "dirs": dirs, "files": files,
            "truncated": len(dirs) + len(files) > 2000}


@app.get("/api/mono/file")
def mono_file(project: str = Query(...), path: str = Query(...)):
    target = safe_project_path(project, path)
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    size = os.path.getsize(target)
    ext = os.path.splitext(target)[1].lower()
    kind = file_kind(os.path.basename(target))
    raw_url = f"/mono/{project}/{path}"
    if kind in {"binary", "image", "pdf"} or size > 2_000_000:
        return {"project": project, "path": path, "size": size, "kind": kind,
                "binary": True, "raw_url": raw_url}
    try:
        with open(target, "rb") as f:
            raw = f.read(300_000)
        if b"\x00" in raw:
            return {"project": project, "path": path, "size": size, "kind": "binary",
                    "binary": True, "raw_url": raw_url}
        content = raw.decode("utf-8", errors="replace")
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"project": project, "path": path, "size": size, "kind": kind,
            "binary": False, "content": content,
            "truncated": size > 300_000,
            "language": LANG_MAP.get(ext, "plaintext"), "raw_url": raw_url}


@app.get("/mono/{project}/{subpath:path}")
def mono_raw(project: str, subpath: str):
    """Fichiers bruts du monorepo (alimente l'iframe preview, same-origin)."""
    target = safe_project_path(project, subpath)
    if os.path.isdir(target):
        idx = os.path.join(target, "index.html")
        if os.path.isfile(idx):
            target = idx
        else:
            raise HTTPException(status_code=404,
                                detail="Dossier sans index.html (utilisez l'explorateur)")
    if not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    media, _ = mimetypes.guess_type(target)
    return FileResponse(target, media_type=media or "application/octet-stream")


@app.get("/mono")
def mono_index():
    return {"projects": list_projects(), "explorer": "/monorepo"}

# ──────────────── TELECHARGEMENT MONOREPO (bundle git) ────────────────
# Secours si le push direct est impossible (403) : le bundle contient
# l'historique git complet, a cloner/pousser depuis une machine autorisee.
MONOREPO_BUNDLE = os.environ.get("MONOREPO_BUNDLE_PATH", "/home/user/monorepo.bundle")


@app.get("/download/monorepo.bundle")
def download_monorepo_bundle():
    if not os.path.isfile(MONOREPO_BUNDLE):
        raise HTTPException(
            status_code=404,
            detail="Bundle introuvable. Regenerer : dans sathancabrol-monorepo, "
                   "'git bundle create /home/user/monorepo.bundle --all'.")
    return FileResponse(MONOREPO_BUNDLE, media_type="application/octet-stream",
                        filename="monorepo.bundle")
