from typing import Dict, List, Tuple
from backend.app.schemas.evidence import Evidence
from backend.app.schemas.result import QualityWarning


def apply_quality_gating(
    evidence_list: List[Evidence],
    quality_metrics: Dict[str, any],
) -> Tuple[List[Evidence], List[QualityWarning]]:
    """
    Adjusts effective weights based on input quality limitations.
    A lower quality discounts affected detectors rather than penalizing the claim.
    """
    warnings: List[QualityWarning] = []
    gated_evidence: List[Evidence] = []

    # Quality Flags
    short_side = quality_metrics.get("short_side", 1024)
    jpeg_quality = quality_metrics.get("jpeg_quality", 85)
    is_screenshot = quality_metrics.get("is_screenshot", False)
    is_jpeg = quality_metrics.get("is_jpeg", True)
    low_dpi = quality_metrics.get("low_dpi", False)
    high_ocr_failure = quality_metrics.get("high_ocr_failure", False)

    # Collect quality warnings
    if short_side < 512:
        warnings.append(
            QualityWarning(
                code="LOW_RESOLUTION",
                message=f"Image resolution ({short_side}px short edge) is low; AI detection and forensic weights discounted by 30%."
            )
        )
    if jpeg_quality < 50:
        warnings.append(
            QualityWarning(
                code="HEAVY_COMPRESSION",
                message=f"Severe JPEG compression detected (quality est. {jpeg_quality}); forensic signals discounted by 50%."
            )
        )
    if is_screenshot or not is_jpeg:
        warnings.append(
            QualityWarning(
                code="NON_JPEG_OR_SCREENSHOT",
                message="File is a screenshot or non-JPEG container; compression error level analysis (ELA) is deactivated."
            )
        )
    if low_dpi:
        warnings.append(
            QualityWarning(
                code="LOW_DPI_DOCUMENT",
                message="Document scan resolution is below 100 DPI equivalent; document ML weights discounted by 40%."
            )
        )
    if high_ocr_failure:
        warnings.append(
            QualityWarning(
                code="UNCERTAIN_OCR",
                message="Multiple document fields yielded low OCR confidence; rule consistency weights discounted by 50%."
            )
        )

    # Apply gates to evidence weights
    for ev in evidence_list:
        ev_copy = ev.model_copy()
        gate = 1.0

        if short_side < 512 and ev.id in ("IMG-AI-01", "IMG-ELA-01", "IMG-NOISE-01"):
            gate *= 0.7
        if jpeg_quality < 50 and ev.id in ("IMG-ELA-01", "IMG-NOISE-01"):
            gate *= 0.5
        if (is_screenshot or not is_jpeg) and ev.id == "IMG-ELA-01":
            gate = 0.0
        if low_dpi and ev.id in ("DOC-CNN-01", "DOC-ANOM-01", "DOC-VIS-01"):
            gate *= 0.6
        if high_ocr_failure and ev.id.startswith("DOC-LOGIC-"):
            gate *= 0.5

        ev_copy.effective_weight = round(ev_copy.weight * gate, 4)

        # Update severity based on effective impact
        impact = ev_copy.calibrated_score * ev_copy.effective_weight
        if impact >= 0.50:
            ev_copy.severity = "high"
        elif impact >= 0.25:
            ev_copy.severity = "medium"
        else:
            ev_copy.severity = "low"

        gated_evidence.append(ev_copy)

    return gated_evidence, warnings
