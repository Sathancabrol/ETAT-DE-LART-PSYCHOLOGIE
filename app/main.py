from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
from typing import Optional, List

from app.database import init_db, get_db_connection, DB_PATH

app = FastAPI(
    title="Cognitorium & État de l'Art Psychologie (2020-2026)",
    description="API & Application interactive pour la cartographie critique, la taxonomie et la boucle métacognitive.",
    version="2.0"
)

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
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/nodes")
def get_nodes(
    search: Optional[str] = None,
    domain: Optional[str] = None,
    type_pub: Optional[str] = None,
    niveau: Optional[str] = None
):
    conn = get_db_connection()
    query = "SELECT * FROM references_table WHERE 1=1"
    params = []

    if search:
        query += " AND (reference_courte LIKE ? OR theme LIKE ? OR question_scientifique LIKE ? OR tags LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    if domain and domain != "all":
        query += " AND domaine = ?"
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
        raise HTTPException(status_code=404, detail="Reference not found")
    
    node_data = dict(row)

    cursor.execute("""
        SELECT target_id, relation_type FROM reference_relations WHERE source_id = ?
        UNION
        SELECT source_id as target_id, relation_type FROM reference_relations WHERE target_id = ?
    """, (node_id, node_id))
    relations = [dict(r) for r in cursor.fetchall()]
    node_data["relations_parsed"] = relations

    conn.close()
    return node_data

@app.get("/api/stats")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM references_table")
    total_refs = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(trust_factor) FROM references_table")
    avg_trust = cursor.fetchone()[0] or 0

    cursor.execute("SELECT niveau_preuve, COUNT(*) FROM references_table GROUP BY niveau_preuve")
    preuve_counts = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT type_publication, COUNT(*) FROM references_table GROUP BY type_publication")
    pub_counts = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT domaine, COUNT(*) FROM references_table GROUP BY domaine")
    domain_counts = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return {
        "total_references": total_refs,
        "average_trust_factor": round(avg_trust, 1),
        "preuve_distribution": preuve_counts,
        "publication_distribution": pub_counts,
        "domain_distribution": domain_counts
    }

@app.get("/api/graph")
def get_graph_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, reference_courte, domaine, type_publication, niveau_preuve, trust_factor, theme FROM references_table")
    refs = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT source_id, target_id, relation_type FROM reference_relations")
    rels = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "nodes": refs,
        "links": rels
    }

@app.post("/api/metacognitive-traces")
def create_trace(trace: MetacognitiveTraceCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO metacognitive_traces 
        (session_id, phase, objective, criteria, constraints, ai_query, ai_response, evaluation, confidence, action_plan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trace.session_id, trace.phase, trace.objective, trace.criteria, trace.constraints,
        trace.ai_query, trace.ai_response, trace.evaluation, trace.confidence, trace.action_plan
    ))
    conn.commit()
    trace_id = cursor.lastrowid
    conn.close()
    return {"status": "success", "id": trace_id}

@app.get("/api/metacognitive-traces")
def get_traces():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metacognitive_traces ORDER BY created_at DESC LIMIT 50")
    traces = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return traces
