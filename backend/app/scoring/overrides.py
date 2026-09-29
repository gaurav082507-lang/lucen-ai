from typing import List, Optional, Tuple
from backend.app.schemas.evidence import Evidence


def apply_overrides(
    evidence_list: List[Evidence],
    image_risk: Optional[float],
    document_risk: Optional[float],
    identity_risk: Optional[float],
    overall_risk: float,
) -> Tuple[Optional[float], Optional[float], Optional[float], float, List[str]]:
    """
    Applies hard override rules for decisive evidence:
    - O1: IMG-C2PA-01 present -> overall & image risk >= 0.95
    - O2: DOC-LOGIC-01 violated and DOC-CNN-01 >= 0.50 -> document risk >= 0.85
    - O3: ID-FACE-01 present -> overall risk >= 0.80
    - O4: IMG-DUP-01 present -> overall risk >= 0.85
    - O5: DOC-OVERLAY-01 present -> document risk >= 0.80
    """
    triggered_rules: List[str] = []
    evidence_ids = {e.id for e in evidence_list}

    # O1: C2PA AI credentials
    if "IMG-C2PA-01" in evidence_ids:
        overall_risk = max(overall_risk, 0.95)
        if image_risk is not None:
            image_risk = max(image_risk, 0.95)
        triggered_rules.append("Rule O1: Content credentials declare AI generation (risk >= 0.95).")

    # O2: Logic rule + Document Tamper CNN
    if "DOC-LOGIC-01" in evidence_ids and "DOC-CNN-01" in evidence_ids:
        cnn_ev = next((e for e in evidence_list if e.id == "DOC-CNN-01"), None)
        if cnn_ev and cnn_ev.calibrated_score >= 0.50:
            if document_risk is not None:
                document_risk = max(document_risk, 0.85)
            overall_risk = max(overall_risk, 0.85)
            triggered_rules.append("Rule O2: Arithmetic mismatch corroborated by Tamper CNN (document risk >= 0.85).")

    # O3: Identity face mismatch
    if "ID-FACE-01" in evidence_ids:
        if identity_risk is not None:
            identity_risk = max(identity_risk, 0.85)
        overall_risk = max(overall_risk, 0.80)
        triggered_rules.append("Rule O3: Face biometric mismatch between ID and selfie (overall risk >= 0.80).")

    # O4: Duplicate image reuse
    if "IMG-DUP-01" in evidence_ids:
        overall_risk = max(overall_risk, 0.85)
        triggered_rules.append("Rule O4: Claim image matches a previously submitted photo (overall risk >= 0.85).")

    # O5: Overlay text discrepancy
    if "DOC-OVERLAY-01" in evidence_ids:
        if document_risk is not None:
            document_risk = max(document_risk, 0.80)
        overall_risk = max(overall_risk, 0.80)
        triggered_rules.append("Rule O5: Visual text differs from hidden digital text layer (document risk >= 0.80).")

    return image_risk, document_risk, identity_risk, round(overall_risk, 4), triggered_rules
