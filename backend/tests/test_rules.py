from backend.app.detectors.document.rules import DocumentRulesDetector


def test_document_rules_detector():
    detector = DocumentRulesDetector()

    # Passing case: amounts match
    fields_clean = {
        "currency": "USD",
        "total": {"value": 1500.0, "bbox": None},
        "tax": {"value": 100.0, "bbox": None},
        "line_items": [{"value": 1000.0}, {"value": 400.0}],
    }
    evidence_clean = detector.run_checks(fields_clean, [])
    assert len([e for e in evidence_clean if e.id == "DOC-LOGIC-01"]) == 0

    # Failing case: line items mismatch total
    fields_tampered = {
        "currency": "USD",
        "total": {"value": 2000.0, "bbox": None},
        "tax": {"value": 100.0, "bbox": None},
        "line_items": [{"value": 1000.0}, {"value": 400.0}],
    }
    evidence_tampered = detector.run_checks(fields_tampered, [])
    mismatch_ev = [e for e in evidence_tampered if e.id == "DOC-LOGIC-01"]
    assert len(mismatch_ev) == 1
    assert mismatch_ev[0].severity == "high"
    assert "Line items sum to 1,400.00 USD, but the stated invoice total is 2,000.00 USD" in mismatch_ev[0].reason
