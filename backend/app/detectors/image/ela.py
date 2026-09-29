from pathlib import Path
from PIL import Image
from backend.app.core.config import settings
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence
from backend.app.scoring.calibration import calibrator
from backend.app.utils.images import compute_ela_map


class ImageElaDetector:
    name: str = "ela"
    timeout_s: float = 8.0

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        img_path = ctx.file_paths.get("image")
        if not img_path or not img_path.exists():
            return DetectorOutput()

        quality_metrics = ctx.quality_metrics
        # ELA is only applicable to JPEG files and not screenshots
        if not quality_metrics.get("is_jpeg", True) or quality_metrics.get("is_screenshot", False):
            raise NotImplementedError("ELA skipped for non-JPEG or screenshot image.")

        img = ctx.extras.get("decoded_image") or Image.open(img_path).convert("RGB")
        ela_gray, raw_anomaly, bbox = compute_ela_map(img, quality=90, scale=15.0)

        calibrated_score = calibrator.calibrate_ela(raw_anomaly)

        evidence = []
        if calibrated_score >= 0.20:
            evidence.append(
                Evidence(
                    id="IMG-ELA-01",
                    pipeline="image",
                    source="ela",
                    kind="risk",
                    raw_score=round(raw_anomaly, 4),
                    calibrated_score=calibrated_score,
                    weight=0.25,
                    effective_weight=0.25,
                    severity="high" if calibrated_score >= 0.65 else ("medium" if calibrated_score >= 0.35 else "low"),
                    title="Compression Error Level Inconsistency",
                    reason="Localized regions exhibit differing JPEG compression rates, indicating splicing or local editing.",
                    bbox=bbox,
                    details={"raw_anomaly": round(raw_anomaly, 4), "score": calibrated_score},
                )
            )

        return DetectorOutput(
            evidence=evidence,
            extras={"ela_map": ela_gray, "ela_score": calibrated_score, "ela_bbox": bbox},
        )
