import sqlite3
import pandas as pd
import os

DB_PATH = "cognitorium.db"
CSV_PATH = "data/nodes_etat_art_psychologie.csv"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. References table (42 fields)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS references_table (
        id TEXT PRIMARY KEY,
        grand_domaine TEXT,
        domaine TEXT,
        sous_domaine TEXT,
        theme TEXT,
        question_scientifique TEXT,
        reference_courte TEXT,
        reference_complete TEXT,
        doi TEXT UNIQUE,
        annee INTEGER,
        type_publication TEXT,
        journal TEXT,
        url TEXT,
        niveau_preuve TEXT,
        sources_triangulation TEXT,
        citations_google_scholar INTEGER,
        citations_crossref INTEGER,
        citations_openalex INTEGER,
        citations_semantic_scholar INTEGER,
        citations_web_of_science INTEGER,
        date_releve_citations TEXT,
        altmetric_score REAL,
        peer_reviewed TEXT,
        open_access TEXT,
        data_open TEXT,
        code_open TEXT,
        preregistration TEXT,
        sample_size INTEGER,
        sample_type TEXT,
        study_design TEXT,
        consensus_actuel TEXT,
        gap_actuel TEXT,
        last_gap TEXT,
        trust_factor INTEGER,
        trust_niveau TEXT,
        trust_justification TEXT,
        tags TEXT,
        relations TEXT,
        date_ajout TEXT,
        date_mise_a_jour TEXT,
        ajoute_par TEXT,
        notes_internes TEXT
    )
    """)

    # 2. Relations table (parsed from relations column)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reference_relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT,
        target_id TEXT,
        relation_type TEXT,
        FOREIGN KEY(source_id) REFERENCES references_table(id),
        FOREIGN KEY(target_id) REFERENCES references_table(id)
    )
    """)

    # 3. Metacognitive traces table (Cognitorium module)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metacognitive_traces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        phase TEXT,
        objective TEXT,
        criteria TEXT,
        constraints TEXT,
        ai_query TEXT,
        ai_response TEXT,
        evaluation TEXT,
        confidence INTEGER,
        action_plan TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

    # Ingest CSV if table is empty
    ingest_csv()

def ingest_csv():
    if not os.path.exists(CSV_PATH):
        return
    df = pd.read_csv(CSV_PATH)
    conn = sqlite3.connect(DB_PATH)
    
    # Replace NaN with None
    df = df.where(pd.notnull(df), None)
    
    # Insert references
    df.to_sql("references_table", conn, if_exists="replace", index=False)
    
    # Parse and insert relations
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reference_relations")
    
    cursor.execute("SELECT id, relations FROM references_table WHERE relations IS NOT NULL AND relations != ''")
    rows = cursor.fetchall()
    
    for row in rows:
        relations_str = row[1]
        # format e.g. tuncok2025_prf:operationalization->lee2026_attention_control; ...
        parts = [p.strip() for p in relations_str.split(";") if p.strip()]
        for part in parts:
            if "->" in part and ":" in part:
                try:
                    left, target = part.split("->")
                    src, rel_type = left.split(":")
                    cursor.execute("""
                        INSERT OR IGNORE INTO reference_relations (source_id, target_id, relation_type)
                        VALUES (?, ?, ?)
                    """, (src.strip(), target.strip(), rel_type.strip()))
                except Exception as e:
                    print(f"Error parsing relation {part}: {e}")

    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
