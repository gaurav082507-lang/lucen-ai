from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class BBox(BaseModel):
    """Normalized bounding box coordinates (0.0 to 1.0)."""
    page: int = 0
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    w: float = Field(..., ge=0.0, le=1.0)
    h: float = Field(..., ge=0.0, le=1.0)


class Evidence(BaseModel):
    """Atomic unit of detection output across all pipelines."""
    id: str
    pipeline: Literal["image", "document", "identity", "claim"]
    source: str
    kind: Literal["risk", "info", "warning"] = "risk"
    raw_score: float = Field(default=0.0, ge=0.0, le=1.0)
    calibrated_score: float = Field(default=0.0, ge=0.0, le=1.0)
    weight: float = Field(default=0.5, ge=0.0, le=1.0)
    effective_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    severity: Literal["low", "medium", "high"] = "low"
    title: str
    reason: str
    field: Optional[str] = None
    bbox: Optional[BBox] = None
    details: dict[str, Any] = Field(default_factory=dict)
    artifact: Optional[str] = None
