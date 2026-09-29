"""
Evidence Catalog with Default Weights.
Stable reference IDs mapped to initial prior weights.
"""

DEFAULT_WEIGHTS = {
    # Image pipeline
    "IMG-C2PA-01": 0.95,   # Content credentials declare AI generation
    "IMG-C2PA-02": 0.00,   # Camera-signed provenance (info)
    "IMG-AI-01": 0.65,     # AI-generated image probability (SigLIP)
    "IMG-ELA-01": 0.25,    # Error Level Analysis anomaly
    "IMG-NOISE-01": 0.20,  # Noise residual inconsistency
    "IMG-EXIF-01": 0.10,   # Missing camera EXIF
    "IMG-EXIF-02a": 0.80,  # Software tag names an AI generator
    "IMG-EXIF-02b": 0.35,  # Software tag names an image editor
    "IMG-EXIF-03": 0.30,   # Timestamp inconsistency
    "IMG-DUP-01": 0.70,    # Duplicate image submission
    "IMG-QUAL-01": 0.00,   # Low quality warning

    # Document pipeline
    "DOC-META-01": 0.15,   # Consumer / online editor producer
    "DOC-META-02": 0.20,   # Modified long after creation
    "DOC-META-03": 0.20,   # Appended revisions in xref
    "DOC-META-04": 0.35,   # Inconsistent creation date
    "DOC-FONT-01": 0.40,   # Font differs within a field group
    "DOC-FONT-02": 0.30,   # Size, baseline or stroke inconsistency
    "DOC-OVERLAY-01": 0.70,# Visible text differs from hidden text
    "DOC-OCR-01": 0.15,    # Low-confidence words in numbers
    "DOC-LOGIC-01": 0.80,  # Line items do not add up to total
    "DOC-LOGIC-02": 0.50,  # Tax calculation mismatch
    "DOC-LOGIC-03": 0.50,  # Date logic violation
    "DOC-LOGIC-04": 0.50,  # Policy / ID checksum failed
    "DOC-LOGIC-05": 0.60,  # Cross-page field disagreement
    "DOC-LOGIC-06": 0.25,  # Formatting inconsistency
    "DOC-LOGIC-07": 0.70,  # Words vs digits mismatch
    "DOC-CNN-01": 0.50,    # Tamper CNN detected edited regions
    "DOC-ANOM-01": 0.30,   # Isolation Forest word anomaly
    "DOC-VIS-01": 0.25,    # Scan compression anomaly
    "DOC-QUAL-01": 0.00,   # Document quality warning

    # Identity pipeline
    "ID-FACE-01": 0.85,    # Faces do not match
    "ID-FACE-02": 0.45,    # Ambiguous match / morph suspicion
    "ID-DEEP-01": 0.70,    # Selfie appears AI-generated
    "ID-QUAL-01": 0.00,    # No usable face warning

    # Cross-modal claim checks
    "CLM-X-01": 0.40,      # Capture time outside incident window
    "CLM-X-02": 0.50,      # Document total != claimed amount
    "CLM-X-03": 0.45,      # Claimant name mismatch
    "CLM-X-04": 0.70,      # Same image reused across claims
    "CLM-X-05": 0.40,      # Document created after filing date
    "CLM-X-06": 0.35,      # GPS outside incident area
}


def get_default_weight(evidence_id: str) -> float:
    return DEFAULT_WEIGHTS.get(evidence_id, 0.40)
