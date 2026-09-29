from fastapi import APIRouter
from backend.app.core.errors import JobNotFoundError
from backend.app.db.repository import get_job
from backend.app.schemas.job import JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Polls real-time step status and progress for an analysis job."""
    job = get_job(job_id)
    if not job:
        raise JobNotFoundError(job_id)
    return job
