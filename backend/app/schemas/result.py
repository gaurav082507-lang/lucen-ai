from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.evidence import Evidence


class DetectorStatus(BaseModel):
    detector: str
    status: Literal["ok", "skipped", "failed"]
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class PipelineScore(BaseModel):
    pipeline: str
    risk: float = Field(..., ge=0.0, le=1.0)
    authenticity: float = Field(..., ge=0.0, le=1.0)
    band: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["high", "medium", "low"] = "high"
    evidence_ids: list[str] = Field(default_factory=list)


class QualityWarning(BaseModel):
    code: str
    message: str


class OverallScore(BaseModel):
    risk: float = Field(..., ge=0.0, le=1.0)
    band: Literal["LOW", "MEDIUM", "HIGH"]
    confidence: Literal["high", "medium", "low"] = "high"
    summary: str


class AnalysisResult(BaseModel):
    id: str
    mode: Literal["image", "document", "claim"]
    created_at: str
    image: Optional[PipelineScore] = None
    document: Optional[PipelineScore] = None
    identity: Optional[PipelineScore] = None
    overall: OverallScore
    evidence: list[Evidence] = Field(default_factory=list)
    detector_status: list[DetectorStatus] = Field(default_factory=list)
    quality_warnings: list[QualityWarning] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    versions: dict[str, str] = Field(default_factory=dict)
