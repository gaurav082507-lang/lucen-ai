import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.db.repository import create_job, get_job, update_job_status
from backend.app.schemas.job import JobStatus, StepProgress
from backend.app.schemas.requests import ClaimMetadata
from backend.app.services.orchestrator import Orchestrator


class JobManager:
    def __init__(self):
        self.orchestrator = Orchestrator()
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def create_analysis_job(
        self,
        mode: str,
        file_paths: Dict[str, Path],
        claim_metadata: Optional[ClaimMetadata] = None,
    ) -> JobStatus:
        job_id = uuid.uuid4().hex[:12]

        # Define anticipated pipeline steps
        steps = [StepProgress(name="validate", status="done", duration_ms=15.0)]
        if "image" in file_paths:
            steps.extend([
                StepProgress(name="preprocess", status="pending"),
                StepProgress(name="metadata", status="pending"),
                StepProgress(name="ai_detector", status="pending"),
                StepProgress(name="ela", status="pending"),
                StepProgress(name="noise", status="pending"),
                StepProgress(name="duplicates", status="pending"),
            ])
        if "document" in file_paths:
            steps.extend([
                StepProgress(name="doc_kind", status="pending"),
                StepProgress(name="doc_metadata", status="pending"),
                StepProgress(name="doc_render_and_ocr", status="pending"),
                StepProgress(name="doc_rules", status="pending"),
                StepProgress(name="doc_fonts", status="pending"),
                StepProgress(name="doc_anomaly", status="pending"),
                StepProgress(name="doc_tamper_cnn", status="pending"),
            ])
        if "id_photo" in file_paths and "selfie" in file_paths:
            steps.append(StepProgress(name="face_biometrics", status="pending"))
        if mode == "claim":
            steps.append(StepProgress(name="cross_checks", status="pending"))

        steps.append(StepProgress(name="scoring_and_explanation", status="pending"))

        job = create_job(job_id, mode, steps)

        # Launch background execution task
        task = asyncio.create_task(self._run_job_worker(job_id, mode, file_paths, claim_metadata, steps))
        self._running_tasks[job_id] = task

        return job

    async def _run_job_worker(
        self,
        job_id: str,
        mode: str,
        file_paths: Dict[str, Path],
        claim_metadata: Optional[ClaimMetadata],
        steps: List[StepProgress],
    ):
        update_job_status(job_id, status="running", steps=steps)

        def step_callback(step_name: str, step_status: str):
            for s in steps:
                if s.name == step_name:
                    s.status = step_status
            update_job_status(job_id, status="running", steps=steps)

        try:
            result = await self.orchestrator.execute_analysis(
                job_id=job_id,
                mode=mode,
                file_paths=file_paths,
                claim_metadata=claim_metadata,
                progress_cb=step_callback,
            )

            for s in steps:
                if s.name == "scoring_and_explanation":
                    s.status = "done"

            update_job_status(
                job_id,
                status="done",
                steps=steps,
                result_id=result.id,
            )
            logger.info("Job %s completed successfully with result %s", job_id, result.id)
        except Exception as e:
            logger.error("Job %s failed: %s", job_id, e, exc_info=True)
            update_job_status(job_id, status="failed", steps=steps, error=str(e))
        finally:
            self._running_tasks.pop(job_id, None)


job_manager = JobManager()
