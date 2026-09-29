import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.repository import save_analysis_result, save_image_hash, update_job_status
from backend.app.detectors.base import AnalysisContext
from backend.app.explain.explainer import compose_explanation
from backend.app.pipelines.claim_pipeline import ClaimCrossCheckDetector
from backend.app.pipelines.document_pipeline import DocumentPipeline
from backend.app.pipelines.identity_pipeline import IdentityPipeline
from backend.app.pipelines.image_pipeline import ImagePipeline
from backend.app.schemas.evidence import Evidence
from backend.app.schemas.requests import ClaimMetadata
from backend.app.schemas.result import (
    AnalysisResult,
    DetectorStatus,
    OverallScore,
    PipelineScore,
)
from backend.app.scoring.bands import determine_confidence, get_risk_band
from backend.app.scoring.fusion import blend_overall_risk, fuse_pipeline_evidence
from backend.app.scoring.overrides import apply_overrides
from backend.app.scoring.quality import apply_quality_gating


class Orchestrator:
    def __init__(self):
        self.image_pipeline = ImagePipeline()
        self.document_pipeline = DocumentPipeline()
        self.identity_pipeline = IdentityPipeline()
        self.cross_check_detector = ClaimCrossCheckDetector()

    async def execute_analysis(
        self,
        job_id: str,
        mode: str,
        file_paths: Dict[str, Path],
        claim_metadata: Optional[ClaimMetadata] = None,
        progress_cb: Optional[Callable[[str, str], None]] = None,
    ) -> AnalysisResult:
        result_id = uuid.uuid4().hex[:12]
        created_at = datetime.now(timezone.utc).isoformat()
        ctx = AnalysisContext(
            job_id=job_id,
            file_paths=file_paths,
            claim_metadata=claim_metadata,
        )

        all_evidence: list[Evidence] = []
        detector_statuses: list[DetectorStatus] = []
        artifacts: dict[str, any] = {}

        # 1. Run Image Pipeline if image present
        image_score: Optional[PipelineScore] = None
        if "image" in file_paths:
            img_ev, img_stat, img_art = self.image_pipeline.run(ctx, result_id, progress_cb)
            all_evidence.extend(img_ev)
            detector_statuses.extend(img_stat)
            artifacts.update(img_art)

        # 2. Run Document Pipeline if document present
        document_score: Optional[PipelineScore] = None
        if "document" in file_paths:
            doc_ev, doc_stat, doc_art = self.document_pipeline.run(ctx, result_id, progress_cb)
            all_evidence.extend(doc_ev)
            detector_statuses.extend(doc_stat)
            artifacts.update(doc_art)

        # 3. Run Identity Pipeline if ID photo and selfie present
        identity_score: Optional[PipelineScore] = None
        if "id_photo" in file_paths and "selfie" in file_paths:
            id_ev, id_stat, id_art = self.identity_pipeline.run(ctx, result_id, progress_cb)
            all_evidence.extend(id_ev)
            detector_statuses.extend(id_stat)
            artifacts.update(id_art)

        # 4. Run Cross-Modal Checks if in claim mode
        if mode == "claim":
            if progress_cb:
                progress_cb("cross_checks", "running")
            cross_ev = self.cross_check_detector.run_cross_checks(ctx)
            all_evidence.extend(cross_ev)
            detector_statuses.append(DetectorStatus(detector="cross_checks", status="ok", duration_ms=20.0))
            if progress_cb:
                progress_cb("cross_checks", "done")

        # 5. Quality Gating
        gated_evidence, quality_warnings = apply_quality_gating(all_evidence, ctx.quality_metrics)

        # 6. Per-Pipeline Scoring & Fusion
        pipeline_risks = {}
        contributions: dict[str, float] = {}

        # Image score
        if "image" in file_paths:
            img_gated = [e for e in gated_evidence if e.pipeline == "image"]
            img_risk, img_contrib = fuse_pipeline_evidence(img_gated)
            pipeline_risks["image"] = img_risk
            contributions.update(img_contrib)
            image_score = PipelineScore(
                pipeline="image",
                risk=img_risk,
                authenticity=round(1.0 - img_risk, 4),
                band=get_risk_band(img_risk),
                confidence=determine_confidence(img_gated, [s for s in detector_statuses if "image" in s.detector or "ai_" in s.detector], quality_warnings),
                evidence_ids=[e.id for e in img_gated],
            )

        # Document score
        if "document" in file_paths:
            doc_gated = [e for e in gated_evidence if e.pipeline == "document"]
            doc_risk, doc_contrib = fuse_pipeline_evidence(doc_gated)
            pipeline_risks["document"] = doc_risk
            contributions.update(doc_contrib)
            document_score = PipelineScore(
                pipeline="document",
                risk=doc_risk,
                authenticity=round(1.0 - doc_risk, 4),
                band=get_risk_band(doc_risk),
                confidence=determine_confidence(doc_gated, [s for s in detector_statuses if "doc_" in s.detector], quality_warnings),
                evidence_ids=[e.id for e in doc_gated],
            )

        # Identity score
        if "id_photo" in file_paths and "selfie" in file_paths:
            id_gated = [e for e in gated_evidence if e.pipeline == "identity"]
            id_risk, id_contrib = fuse_pipeline_evidence(id_gated)
            pipeline_risks["identity"] = id_risk
            contributions.update(id_contrib)
            identity_score = PipelineScore(
                pipeline="identity",
                risk=id_risk,
                authenticity=round(1.0 - id_risk, 4),
                band=get_risk_band(id_risk),
                confidence=determine_confidence(id_gated, [s for s in detector_statuses if "face_" in s.detector], quality_warnings),
                evidence_ids=[e.id for e in id_gated],
            )

        # Cross-checks risk
        cross_gated = [e for e in gated_evidence if e.pipeline == "claim"]
        if cross_gated:
            cross_risk, cross_contrib = fuse_pipeline_evidence(cross_gated)
            pipeline_risks["cross_checks"] = cross_risk
            contributions.update(cross_contrib)

        # 7. Blend Cross-Pipeline Overall Score
        raw_overall = blend_overall_risk(pipeline_risks)

        # 8. Apply Hard Override Rules
        img_risk_val = image_score.risk if image_score else None
        doc_risk_val = document_score.risk if document_score else None
        id_risk_val = identity_score.risk if identity_score else None

        img_r, doc_r, id_r, overall_r, overrides = apply_overrides(
            gated_evidence, img_risk_val, doc_risk_val, id_risk_val, raw_overall
        )

        if image_score and img_r is not None:
            image_score.risk = img_r
            image_score.authenticity = round(1.0 - img_r, 4)
            image_score.band = get_risk_band(img_r)

        if document_score and doc_r is not None:
            document_score.risk = doc_r
            document_score.authenticity = round(1.0 - doc_r, 4)
            document_score.band = get_risk_band(doc_r)

        if identity_score and id_r is not None:
            identity_score.risk = id_r
            identity_score.authenticity = round(1.0 - id_r, 4)
            identity_score.band = get_risk_band(id_r)

        overall_band = get_risk_band(overall_r)
        overall_confidence = determine_confidence(gated_evidence, detector_statuses, quality_warnings)

        # 9. Plain-English Summary Explanation
        summary = await compose_explanation(
            overall_band, overall_r, overall_confidence, gated_evidence, contributions
        )

        overall_score = OverallScore(
            risk=overall_r,
            band=overall_band,
            confidence=overall_confidence,
            summary=summary,
        )

        # 10. Assemble AnalysisResult
        result = AnalysisResult(
            id=result_id,
            mode=mode,
            created_at=created_at,
            image=image_score,
            document=document_score,
            identity=identity_score,
            overall=overall_score,
            evidence=gated_evidence,
            detector_status=detector_statuses,
            quality_warnings=quality_warnings,
            artifacts=artifacts,
            versions={
                "detector": settings.IMAGE_MODEL_ID,
                "calibration": "2026-09-29",
                "app": settings.VERSION,
            },
        )

        # 11. Persist result & image hash
        save_analysis_result(result, job_id=job_id)
        if "phash" in ctx.extras:
            save_image_hash(result_id, ctx.extras["phash"])

        return result
