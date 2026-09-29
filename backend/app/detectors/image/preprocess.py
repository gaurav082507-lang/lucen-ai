from pathlib import Path
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence
from backend.app.utils.images import compute_image_quality_metrics, load_and_orient_image


class ImagePreprocessDetector:
    name: str = "image_preprocess"
    timeout_s: float = 5.0

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        img_path = ctx.file_paths.get("image")
        if not img_path or not img_path.exists():
            return DetectorOutput()

        img = load_and_orient_image(img_path)
        metrics = compute_image_quality_metrics(img_path, img)
        ctx.quality_metrics.update(metrics)

        evidence = []
        if metrics["short_side"] < 512 or metrics["jpeg_quality"] < 50:
            evidence.append(
                Evidence(
                    id="IMG-QUAL-01",
                    pipeline="image",
                    source="preprocess",
                    kind="warning",
                    raw_score=0.0,
                    calibrated_score=0.0,
                    weight=0.0,
                    effective_weight=0.0,
                    severity="low",
                    title="Low Resolution or Heavy Compression",
                    reason=f"Image short edge is {metrics['short_side']}px with estimated JPEG quality {metrics['jpeg_quality']}.",
                    details=metrics,
                )
            )

        return DetectorOutput(
            evidence=evidence,
            extras={"decoded_image": img, "image_quality": metrics},
        )
