import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.config import settings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        # 1. Pages table (spec Phase 1: url PK, lastmod, content_hash, status, attempts, last_error, fetched_at, active)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                url TEXT PRIMARY KEY,
                lastmod TEXT,
                content_hash TEXT,
                status TEXT DEFAULT 'pending', -- pending | ok | failed | removed
                attempts INTEGER DEFAULT 0,
                last_error TEXT,
                fetched_at TEXT,
                active BOOLEAN DEFAULT 1
            )
        """)

        # 2. Articles table (structured parsed content)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                raw_html TEXT,
                parsed_text TEXT,
                headings_json TEXT,
                images_json TEXT,
                lastmod TEXT,
                content_hash TEXT,
                updated_at TEXT,
                active BOOLEAN DEFAULT 1,
                source_type TEXT DEFAULT 'crawled' -- crawled | expert
            )
        """)

        # 3. FTS5 Virtual table for hybrid keyword search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_articles USING fts5(
                article_id UNINDEXED,
                title,
                content,
                tokenize = 'porter unicode61'
            )
        """)

        # 4. Escalations table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                context TEXT,
                status TEXT DEFAULT 'open', -- open | resolved
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                resolved_by TEXT,
                answer TEXT
            )
        """)

        # 5. Expert Answers table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expert_answers (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                expert_answer TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                source_type TEXT DEFAULT 'expert',
                active BOOLEAN DEFAULT 1
            )
        """)

        # 6. Ingestion runs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_runs (
                id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                added INTEGER DEFAULT 0,
                updated INTEGER DEFAULT 0,
                removed INTEGER DEFAULT 0,
                failed INTEGER DEFAULT 0,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                log TEXT
            )
        """)
    conn.close()

# Helper queries
def upsert_page(url: str, lastmod: Optional[str], content_hash: Optional[str], status: str, attempts: int = 0, last_error: Optional[str] = None, active: bool = True):
    conn = get_db_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute("""
            INSERT INTO pages (url, lastmod, content_hash, status, attempts, last_error, fetched_at, active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                lastmod=COALESCE(excluded.lastmod, pages.lastmod),
                content_hash=COALESCE(excluded.content_hash, pages.content_hash),
                status=excluded.status,
                attempts=excluded.attempts,
                last_error=excluded.last_error,
                fetched_at=excluded.fetched_at,
                active=excluded.active
        """, (url, lastmod, content_hash, status, attempts, last_error, now, 1 if active else 0))
    conn.close()

def upsert_article(article_id: str, url: str, title: str, raw_html: str, parsed_text: str, headings: List[str], images: List[Dict[str, Any]], lastmod: Optional[str], content_hash: str, source_type: str = "crawled"):
    conn = get_db_connection()
    now = datetime.now(timezone.utc).isoformat()
    with conn:
        conn.execute("""
            INSERT INTO articles (id, url, title, raw_html, parsed_text, headings_json, images_json, lastmod, content_hash, updated_at, active, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(url) DO UPDATE SET
                id=excluded.id,
                title=excluded.title,
                raw_html=excluded.raw_html,
                parsed_text=excluded.parsed_text,
                headings_json=excluded.headings_json,
                images_json=excluded.images_json,
                lastmod=excluded.lastmod,
                content_hash=excluded.content_hash,
                updated_at=excluded.updated_at,
                active=1,
                source_type=excluded.source_type
        """, (article_id, url, title, raw_html, parsed_text, json.dumps(headings), json.dumps(images), lastmod, content_hash, now, source_type))

        # Update FTS5 index
        conn.execute("DELETE FROM fts_articles WHERE article_id = ?", (article_id,))
        conn.execute("INSERT INTO fts_articles (article_id, title, content) VALUES (?, ?, ?)", (article_id, title, parsed_text))
    conn.close()

def mark_page_removed(url: str):
    conn = get_db_connection()
    with conn:
        conn.execute("UPDATE pages SET status='removed', active=0 WHERE url = ?", (url,))
        conn.execute("UPDATE articles SET active=0 WHERE url = ?", (url,))
        row = conn.execute("SELECT id FROM articles WHERE url = ?", (url,)).fetchone()
        if row:
            conn.execute("DELETE FROM fts_articles WHERE article_id = ?", (row["id"],))
    conn.close()

def search_fts5(query_str: str, top_k: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    # Sanitize query for FTS5
    safe_query = "".join([c if c.isalnum() or c.isspace() else " " for c in query_str]).strip()
    if not safe_query:
        return []
    
    # Formulate FTS terms
    terms = " OR ".join([f'"{t}"' for t in safe_query.split() if len(t) > 2])
    if not terms:
        terms = f'"{safe_query}"'

    try:
        cursor = conn.execute("""
            SELECT f.article_id, f.title, a.url, a.parsed_text, rank
            FROM fts_articles f
            JOIN articles a ON a.id = f.article_id
            WHERE fts_articles MATCH ? AND a.active = 1
            ORDER BY rank
            LIMIT ?
        """, (terms, top_k))
        results = [dict(r) for r in cursor.fetchall()]
    except Exception:
        results = []
    finally:
        conn.close()
    return results
