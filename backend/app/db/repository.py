import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from backend.app.db.database import get_db_connection
from backend.app.schemas.evidence import Evidence, BBox
from backend.app.schemas.job import JobStatus, StepProgress
from backend.app.schemas.result import AnalysisResult


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(job_id: str, mode: str, steps: List[StepProgress]) -> JobStatus:
    conn = get_db_connection()
    now = now_iso()
    steps_json = json.dumps([s.model_dump() for s in steps])
    with conn:
        conn.execute(
            """
            INSERT INTO jobs (id, mode, status, steps_json, result_id, error, created_at, updated_at)
            VALUES (?, ?, ?, ?, NULL, NULL, ?, ?)
            """,
            (job_id, mode, "queued", steps_json, now, now),
        )
    conn.close()
    return JobStatus(job_id=job_id, mode=mode, status="queued", steps=steps)


def get_job(job_id: str) -> Optional[JobStatus]:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    if not row:
        return None

    steps_data = json.loads(row["steps_json"]) if row["steps_json"] else []
    steps = [StepProgress(**s) for s in steps_data]

    return JobStatus(
        job_id=row["id"],
        mode=row["mode"],
        status=row["status"],
        steps=steps,
        result_id=row["result_id"],
        error=row["error"],
    )


def update_job_status(
    job_id: str,
    status: str,
    steps: Optional[List[StepProgress]] = None,
    result_id: Optional[str] = None,
    error: Optional[str] = None,
):
    conn = get_db_connection()
    now = now_iso()
    with conn:
        if steps is not None:
            steps_json = json.dumps([s.model_dump() for s in steps])
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, steps_json = ?, result_id = COALESCE(?, result_id), error = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, steps_json, result_id, error, now, job_id),
            )
        else:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, result_id = COALESCE(?, result_id), error = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, result_id, error, now, job_id),
            )
    conn.close()


def save_analysis_result(result: AnalysisResult, job_id: Optional[str] = None):
    conn = get_db_connection()
    result_json = result.model_dump_json()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO results (
                id, job_id, mode, overall_risk, overall_band,
                image_risk, document_risk, identity_risk, summary, json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.id,
                job_id,
                result.mode,
                result.overall.risk,
                result.overall.band,
                result.image.risk if result.image else None,
                result.document.risk if result.document else None,
                result.identity.risk if result.identity else None,
                result.overall.summary,
                result_json,
                result.created_at,
            ),
        )

        for ev in result.evidence:
            bbox_json = ev.bbox.model_dump_json() if ev.bbox else None
            from backend.app.schemas.evidence import sanitize_json_value
            details_json = json.dumps(sanitize_json_value(ev.details), default=str)
            conn.execute(
                """
                INSERT INTO evidence (
                    result_id, evidence_id, pipeline, source, kind,
                    raw_score, calibrated_score, weight, effective_weight,
                    severity, title, reason, field, bbox_json, details_json, artifact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    ev.id,
                    ev.pipeline,
                    ev.source,
                    ev.kind,
                    ev.raw_score,
                    ev.calibrated_score,
                    ev.weight,
                    ev.effective_weight,
                    ev.severity,
                    ev.title,
                    ev.reason,
                    ev.field,
                    bbox_json,
                    details_json,
                    ev.artifact,
                ),
            )
    conn.close()


def get_analysis_result(result_id: str) -> Optional[AnalysisResult]:
    conn = get_db_connection()
    row = conn.execute("SELECT json FROM results WHERE id = ?", (result_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return AnalysisResult.model_validate_json(row["json"])


def list_recent_results(limit: int = 50) -> List[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, mode, overall_risk, overall_band, created_at, summary
        FROM results
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_image_hash(result_id: str, phash: str):
    conn = get_db_connection()
    now = now_iso()
    with conn:
        conn.execute(
            "INSERT INTO image_hashes (result_id, phash, created_at) VALUES (?, ?, ?)",
            (result_id, phash, now),
        )
    conn.close()


def find_duplicate_hashes(current_phash: str, max_hamming_distance: int = 6) -> List[Tuple[str, int]]:
    """Compares current perceptual hash against stored hashes."""
    conn = get_db_connection()
    rows = conn.execute("SELECT result_id, phash FROM image_hashes").fetchall()
    conn.close()

    matches = []
    try:
        import imagehash
        curr_h = imagehash.hex_to_hash(current_phash)
        for r in rows:
            stored_h = imagehash.hex_to_hash(r["phash"])
            dist = curr_h - stored_h
            if dist <= max_hamming_distance:
                matches.append((r["result_id"], dist))
    except Exception:
        pass

    return matches
