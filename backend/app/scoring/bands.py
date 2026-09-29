from typing import List, Literal, Optional
from backend.app.core.config import settings
from backend.app.schemas.evidence import Evidence
from backend.app.schemas.result import DetectorStatus, QualityWarning


def get_risk_band(risk: float) -> Literal["LOW", "MEDIUM", "HIGH"]:
    if risk < settings.BAND_LOW_MAX:
        return "LOW"
    elif risk < settings.BAND_MED_MAX:
        return "MEDIUM"
    else:
        return "HIGH"


def determine_confidence(
    evidence_list: List[Evidence],
    detector_statuses: List[DetectorStatus],
    quality_warnings: List[QualityWarning],
) -> Literal["high", "medium", "low"]:
    """
    Computes confidence level:
    Start at 'high' and step down for:
    - Any detector failed
    - Significant quality discounting (gated weights by > 30%)
    - Fewer than 2 independent evidence sources
    - Strong disagreement between AI detector and forensics
    """
    confidence_score = 3  # 3: high, 2: medium, 1: low

    # Factor 1: Detector failures
    failed_detectors = [d for d in detector_statuses if d.status == "failed"]
    if failed_detectors:
        confidence_score -= 1

    # Factor 2: Quality warnings with severe discounting
    severe_warning_codes = {"LOW_RESOLUTION", "HEAVY_COMPRESSION", "UNCERTAIN_OCR"}
    if any(w.code in severe_warning_codes for w in quality_warnings):
        confidence_score -= 1

    # Factor 3: Source diversity
    active_sources = {e.source for e in evidence_list if e.kind == "risk" and e.calibrated_score >= 0.2}
    if len(active_sources) < 2 and len(evidence_list) > 0:
        confidence_score -= 1

    # Factor 4: AI vs forensic discrepancy (e.g. AI is high but forensic is completely clear)
    ai_ev = next((e for e in evidence_list if e.id == "IMG-AI-01"), None)
    ela_ev = next((e for e in evidence_list if e.id == "IMG-ELA-01"), None)
    if ai_ev and ela_ev:
        if ai_ev.calibrated_score >= 0.85 and ela_ev.calibrated_score < 0.20:
            confidence_score -= 1

    if confidence_score >= 3:
        return "high"
    elif confidence_score == 2:
        return "medium"
    else:
        return "low"
