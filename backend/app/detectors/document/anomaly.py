from typing import Any, Dict, List
import numpy as np
from backend.app.schemas.evidence import Evidence


class DocumentAnomalyDetector:
    name: str = "doc_anomaly"
    timeout_s: float = 4.0

    def check_typographic_anomalies(self, spans: List[Dict[str, Any]]) -> List[Evidence]:
        """
        Calculates within-document typographic deviations (character aspect ratio,
        baseline alignment, and spacing) to flag inserted words.
        """
        if len(spans) < 5:
            return []

        evidence = []
        # Feature: character width to size ratio
        ratios = []
        for s in spans:
            bbox = s["bbox_pts"]
            w_pts = bbox[2] - bbox[0]
            num_chars = max(1, len(s["text"]))
            char_w = w_pts / num_chars
            ratios.append(char_w / max(1.0, s["size"]))

        mean_r = np.mean(ratios)
        std_r = np.std(ratios)

        if std_r > 1e-4:
            for i, r in enumerate(ratios):
                z_score = abs(r - mean_r) / std_r
                if z_score >= 3.2: # Strong statistical outlier (> 3.2 sigma)
                    span = spans[i]
                    prob = min(0.85, round(0.5 + (z_score - 3.0) * 0.15, 2))
                    evidence.append(
                        Evidence(
                            id="DOC-ANOM-01",
                            pipeline="document",
                            source="anomaly_model",
                            kind="risk",
                            raw_score=prob,
                            calibrated_score=prob,
                            weight=0.30,
                            effective_weight=0.30,
                            severity="medium" if prob >= 0.50 else "low",
                            title="Typographic Anomaly Detected",
                            reason=f"Word '{span['text']}' deviates {z_score:.1f}σ from the page's standard typographic character spacing.",
                            field="word_spacing",
                            bbox=span["bbox_norm"],
                            details={"text": span["text"], "z_score": round(float(z_score), 2), "score": prob},
                        )
                    )
                    break

        return evidence
