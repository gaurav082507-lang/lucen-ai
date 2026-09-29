"""
AI-Generated Image Detector
============================
Uses a spectral Fourier frequency heuristic to detect AI-generated images.
No external model downloads required — runs entirely on numpy.
"""
import math
from pathlib import Path
import numpy as np
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence
from backend.app.scoring.calibration import calibrator


class ImageAiDetector:
    name: str = "ai_detector"
    timeout_s: float = 15.0

    def _compute_frequency_ai_heuristic(self, img: Image.Image) -> float:
        """
        Spectral Fourier heuristic: detects periodic grid peaks and unnatural
        high-frequency roll-off common in diffusion/GAN-synthesised images.
        Returns probability in [0.05, 0.95].
        """
        np_img = np.array(img.convert("L").resize((256, 256)))
        f = np.fft.fft2(np_img)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-6)

        h, w = magnitude_spectrum.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

        mid_band = magnitude_spectrum[(r >= 30) & (r < 70)]
        high_band = magnitude_spectrum[r >= 70]

        ratio = float(np.mean(high_band) / (np.mean(mid_band) + 1e-4))
        # Generative models often have abnormally smooth or peaked high frequencies
        score = 1.0 / (1.0 + math.exp(-6.0 * (ratio - 0.72)))
        return float(np.clip(score, 0.05, 0.95))

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        img_path = ctx.file_paths.get("image")
        if not img_path or not img_path.exists():
            return DetectorOutput()

        img = ctx.extras.get("decoded_image") or Image.open(img_path).convert("RGB")

        raw_p_ai = self._compute_frequency_ai_heuristic(img)
        model_source = "frequency_heuristic"

        # Apply temperature calibration
        calibrated_p = calibrator.calibrate_ai_score(raw_p_ai)

        evidence = [
            Evidence(
                id="IMG-AI-01",
                pipeline="image",
                source="ai_detector",
                kind="risk",
                raw_score=round(raw_p_ai, 4),
                calibrated_score=calibrated_p,
                weight=0.65,
                effective_weight=0.65,
                severity="high" if calibrated_p >= 0.65 else ("medium" if calibrated_p >= 0.35 else "low"),
                title="AI-Generated Image Probability",
                reason=f"Frequency-domain analysis estimates a {calibrated_p:.0%} probability of synthetic or AI generation.",
                details={
                    "p_ai": calibrated_p,
                    "raw_score": round(raw_p_ai, 4),
                    "model": model_source,
                },
            )
        ]

        return DetectorOutput(
            evidence=evidence,
            extras={"p_ai": calibrated_p, "raw_ai_prob": raw_p_ai},
        )
