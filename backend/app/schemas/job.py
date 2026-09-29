from typing import Literal, Optional
from pydantic import BaseModel, Field


class StepProgress(BaseModel):
    name: str
    status: Literal["pending", "running", "done", "skipped", "failed"] = "pending"
    duration_ms: Optional[float] = None
    detail: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "done", "failed"]
    mode: Literal["image", "document", "claim"]
    steps: list[StepProgress] = Field(default_factory=list)
    result_id: Optional[str] = None
    error: Optional[str] = None
