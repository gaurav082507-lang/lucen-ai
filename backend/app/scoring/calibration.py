import json
import math
from pathlib import Path
from typing import Dict, Any
from backend.app.core.config import settings


class Calibrator:
    def __init__(self, calibration_path: Path = None):
        self.path = calibration_path or (settings.MODELS_DIR / "calibration.json")
        self.params: Dict[str, Any] = self._load_params()

    def _load_params(self) -> Dict[str, Any]:
        default_params = {
            "temperature_ai_detector": 1.45,
            "ela_logistic_k": 8.0,
            "ela_logistic_x0": 0.35,
            "noise_logistic_k": 7.0,
            "noise_logistic_x0": 0.40,
            "version": "2026-09-29",
        }
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default_params

    def calibrate_ai_score(self, raw_prob: float) -> float:
        """
        Calibrates uncalibrated SigLIP probability using temperature scaling.
        Avoids extreme overconfidence on insurance photos.
        """
        raw_prob = max(1e-6, min(1.0 - 1e-6, raw_prob))
        # Logit
        logit = math.log(raw_prob / (1.0 - raw_prob))
        T = self.params.get("temperature_ai_detector", 1.45)
        scaled_logit = logit / T
        calibrated = 1.0 / (1.0 + math.exp(-scaled_logit))
        return round(calibrated, 4)

    def calibrate_logistic(self, raw_val: float, k_param: str, x0_param: str) -> float:
        """Applies a smooth sigmoid mapping to continuous statistical metrics."""
        k = self.params.get(k_param, 8.0)
        x0 = self.params.get(x0_param, 0.35)
        val = 1.0 / (1.0 + math.exp(-k * (raw_val - x0)))
        return round(val, 4)

    def calibrate_ela(self, raw_score: float) -> float:
        return self.calibrate_logistic(raw_score, "ela_logistic_k", "ela_logistic_x0")

    def calibrate_noise(self, raw_score: float) -> float:
        return self.calibrate_logistic(raw_score, "noise_logistic_k", "noise_logistic_x0")


calibrator = Calibrator()
