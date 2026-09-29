import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.evidence import Evidence
from backend.app.schemas.requests import ClaimMetadata
from backend.app.schemas.result import DetectorStatus


@dataclass
class AnalysisContext:
    job_id: str
    file_paths: Dict[str, Path]          # {"image": Path, "document": Path, "id_photo": Path, "selfie": Path}
    claim_metadata: Optional[ClaimMetadata] = None
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    extras: Dict[str, Any] = field(default_factory=dict) # shared inter-detector state


@dataclass
class DetectorOutput:
    evidence: List[Evidence] = field(default_factory=list)
    artifacts: Dict[str, Path] = field(default_factory=dict) # {"heatmap": Path(...)}
    extras: Dict[str, Any] = field(default_factory=dict)


class Detector(Protocol):
    name: str
    timeout_s: float

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        ...


def run_safely(detector: Detector, ctx: AnalysisContext) -> tuple[DetectorOutput, DetectorStatus]:
    """
    Executes a detector with duration tracking and safe exception containment.
    A failure never interrupts the pipeline.
    """
    t0 = time.perf_counter()
    try:
        output = detector.run(ctx)
        duration_ms = round((time.perf_counter() - t0) * 1000, 1)
        # Store extras into context for downstream detectors
        if output.extras:
            ctx.extras.update(output.extras)
        return output, DetectorStatus(detector=detector.name, status="ok", duration_ms=duration_ms)
    except NotImplementedError:
        duration_ms = round((time.perf_counter() - t0) * 1000, 1)
        return DetectorOutput(), DetectorStatus(detector=detector.name, status="skipped", duration_ms=duration_ms)
    except Exception as e:
        duration_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.warning("Detector '%s' failed safely: %s", detector.name, e, exc_info=True)
        return DetectorOutput(), DetectorStatus(
            detector=detector.name, status="failed", duration_ms=duration_ms, error=str(e)
        )
