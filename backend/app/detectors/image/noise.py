from pathlib import Path
from PIL import Image
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence
from backend.app.scoring.calibration import calibrator
from backend.app.utils.images import compute_noise_residual


class ImageNoiseDetector:
    name: str = "noise"
    timeout_s: float = 6.0

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        img_path = ctx.file_paths.get("image")
        if not img_path or not img_path.exists():
            return DetectorOutput()

        img = ctx.extras.get("decoded_image") or Image.open(img_path).convert("RGB")
        raw_noise_score, noise_map = compute_noise_residual(img, block_size=64)
        calibrated_score = calibrator.calibrate_noise(raw_noise_score)

        evidence = []
        if calibrated_score >= 0.20:
            evidence.append(
                Evidence(
                    id="IMG-NOISE-01",
                    pipeline="image",
                    source="noise",
                    kind="risk",
                    raw_score=round(raw_noise_score, 4),
                    calibrated_score=calibrated_score,
                    weight=0.20,
                    effective_weight=0.20,
                    severity="medium" if calibrated_score >= 0.50 else "low",
                    title="Inconsistent Noise Variance",
                    reason="Spatial blocks exhibit unnatural variations in high-frequency camera sensor noise.",
                    details={"raw_dispersion": round(raw_noise_score, 4), "score": calibrated_score},
                )
            )

        return DetectorOutput(
            evidence=evidence,
            extras={"noise_map": noise_map, "noise_score": calibrated_score},
        )
