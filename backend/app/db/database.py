import sqlite3
from pathlib import Path
from backend.app.core.config import settings
from backend.app.core.logging import logger


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.SQLITE_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and indexes."""
    logger.info("Initializing ClaimGuard SQLite database at %s", settings.SQLITE_PATH)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        mode TEXT NOT NULL,
        status TEXT NOT NULL,
        steps_json TEXT,
        result_id TEXT,
        error TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS results (
        id TEXT PRIMARY KEY,
        job_id TEXT,
        mode TEXT NOT NULL,
        overall_risk REAL NOT NULL,
        overall_band TEXT NOT NULL,
        image_risk REAL,
        document_risk REAL,
        identity_risk REAL,
        summary TEXT,
        json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id TEXT NOT NULL,
        evidence_id TEXT NOT NULL,
        pipeline TEXT NOT NULL,
        source TEXT NOT NULL,
        kind TEXT NOT NULL,
        raw_score REAL NOT NULL,
        calibrated_score REAL NOT NULL,
        weight REAL NOT NULL,
        effective_weight REAL NOT NULL,
        severity TEXT NOT NULL,
        title TEXT NOT NULL,
        reason TEXT NOT NULL,
        field TEXT,
        bbox_json TEXT,
        details_json TEXT,
        artifact TEXT,
        FOREIGN KEY (result_id) REFERENCES results(id)
    );

    CREATE TABLE IF NOT EXISTS image_hashes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id TEXT NOT NULL,
        phash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_evidence_result ON evidence(result_id);
    CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
    CREATE INDEX IF NOT EXISTS idx_results_created ON results(created_at);
    """)

    conn.commit()
    conn.close()
