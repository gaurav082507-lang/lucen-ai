from backend.app.schemas.evidence import Evidence
from backend.app.scoring.bands import get_risk_band
from backend.app.scoring.fusion import blend_overall_risk, fuse_pipeline_evidence


def test_worked_example_fusion_and_blend():
    # 1. Image Pipeline Evidence
    img_evidence = [
        Evidence(
            id="IMG-AI-01", pipeline="image", source="ai_detector", kind="risk",
            calibrated_score=0.97, weight=0.70, effective_weight=0.70,
            title="AI Image", reason="AI detected"
        ),
        Evidence(
            id="IMG-ELA-01", pipeline="image", source="ela", kind="risk",
            calibrated_score=0.70, weight=0.25, effective_weight=0.25,
            title="ELA", reason="ELA anomaly"
        ),
        Evidence(
            id="IMG-EXIF-01", pipeline="image", source="exif", kind="risk",
            calibrated_score=0.50, weight=0.10, effective_weight=0.10,
            title="EXIF", reason="No EXIF"
        ),
    ]

    img_risk, img_contrib = fuse_pipeline_evidence(img_evidence)
    assert abs(img_risk - 0.748) < 0.015, f"Expected img_risk ~0.748, got {img_risk}"
    assert get_risk_band(img_risk) == "HIGH"

    # 2. Document Pipeline Evidence
    doc_evidence = [
        Evidence(
            id="DOC-LOGIC-01", pipeline="document", source="rules", kind="risk",
            calibrated_score=1.00, weight=0.80, effective_weight=0.80,
            title="Logic", reason="Line items mismatch"
        ),
        Evidence(
            id="DOC-CNN-01", pipeline="document", source="cnn", kind="risk",
            calibrated_score=0.75, weight=0.50, effective_weight=0.50,
            title="CNN", reason="Tamper CNN patch"
        ),
        Evidence(
            id="DOC-FONT-01", pipeline="document", source="font", kind="risk",
            calibrated_score=0.60, weight=0.30, effective_weight=0.30,
            title="Font", reason="Font mismatch"
        ),
        Evidence(
            id="DOC-META-02", pipeline="document", source="pdf_meta", kind="risk",
            calibrated_score=0.50, weight=0.15, effective_weight=0.15,
            title="Meta", reason="Modified after creation"
        ),
    ]

    doc_risk, doc_contrib = fuse_pipeline_evidence(doc_evidence)
    assert abs(doc_risk - 0.905) < 0.015, f"Expected doc_risk ~0.905, got {doc_risk}"
    assert get_risk_band(doc_risk) == "HIGH"

    # 3. Overall Blend
    overall = blend_overall_risk({"image": img_risk, "document": doc_risk})
    assert abs(overall - 0.882) < 0.015, f"Expected overall ~0.882, got {overall}"
    assert get_risk_band(overall) == "HIGH"
