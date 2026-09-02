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

    # 4. Memory items (synchro mémoire des agents ↔ base de données)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory_items (
        id TEXT PRIMARY KEY,
        ts TEXT, type TEXT, titre TEXT, contenu TEXT,
        tags TEXT, source TEXT, corps TEXT, meta TEXT
    )""")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_items(type)")

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


def sync_memory_items() -> int:
    """Synchronise la mémoire des agents (items.jsonl) dans la base de données.

    Idempotent : chaque élément est inséré ou mis à jour par id.
    Retourne le nombre d'éléments synchronisés.
    """
    import json as _json
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS memory_items (
        id TEXT PRIMARY KEY, ts TEXT, type TEXT, titre TEXT, contenu TEXT,
        tags TEXT, source TEXT, corps TEXT, meta TEXT)""")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_items(type)")
    cursor.execute("""CREATE TABLE IF NOT EXISTS references_table (
        id TEXT PRIMARY KEY, reference_courte TEXT, reference_complete TEXT,
        doi TEXT, annee INTEGER, theme TEXT, notes_internes TEXT)""")
    n = 0
    mem_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "output", "cosmos", "memory", "items.jsonl")
    if os.path.exists(mem_path):
        with open(mem_path, encoding="utf-8") as f:
            for line in f:
                try:
                    it = _json.loads(line)
                except Exception:
                    continue
                cursor.execute("""INSERT INTO memory_items
                    (id, ts, type, titre, contenu, tags, source, corps, meta)
                    VALUES (?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(id) DO UPDATE SET ts=excluded.ts, type=excluded.type,
                        titre=excluded.titre, contenu=excluded.contenu, tags=excluded.tags,
                        source=excluded.source, corps=excluded.corps, meta=excluded.meta""",
                    (it.get("id"), it.get("ts"), it.get("type"), it.get("titre"),
                     it.get("contenu", "")[:2000], ", ".join(it.get("tags", [])),
                     it.get("source"), it.get("corps"),
                     _json.dumps(it.get("meta", {}), ensure_ascii=False)))
                n += 1
                # Les références versées en mémoire par les recherches alimentent aussi
                # la table scientifique references_table (synchro complète mémoire → DB)
                if it.get("type") == "reference":
                    meta = it.get("meta", {}) or {}
                    doi = (meta.get("doi") or it.get("doi") or "").strip() or None
                    ref_courte = (meta.get("reference_courte")
                                  or f"{it.get('titre', '')[:80]} ({(it.get('ts') or '')[:4]})")
                    try:
                        cursor.execute("""INSERT OR REPLACE INTO references_table
                            (id, reference_courte, reference_complete, doi, annee, theme, notes_internes)
                            VALUES (?,?,?,?,?,?,?)""",
                            ("mem_" + it.get("id", ""), ref_courte[:200],
                             (it.get("contenu", "") or "")[:600], doi,
                             int(meta["annee"]) if str(meta.get("annee", "")).isdigit() else None,
                             (meta.get("theme") or it.get("titre", ""))[:200],
                             "versé en mémoire par " + (it.get("source") or "agent")
                             + " le " + (it.get("ts") or "")[:10]))
                    except Exception:
                        pass  # une référence malformée ne bloque pas la synchro
        conn.commit()
    conn.close()
    return n


def get_memory_items(type_filter=None, limit=500):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if type_filter:
        cursor.execute("SELECT * FROM memory_items WHERE type=? ORDER BY ts DESC LIMIT ?",
                       (type_filter, limit))
    else:
        cursor.execute("SELECT * FROM memory_items ORDER BY ts DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
