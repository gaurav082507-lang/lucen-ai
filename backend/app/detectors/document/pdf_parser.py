import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import fitz
from backend.app.detectors.base import AnalysisContext, DetectorOutput
from backend.app.schemas.evidence import Evidence


SUSPICIOUS_PDF_PRODUCERS = [
    "ilovepdf", "smallpdf", "pdfescape", "sejda", "canva", "pdf2go",
    "sodapdf", "photoshop", "gimp", "pdf editor", "foxit phantompdf"
]


class DocumentPdfParserDetector:
    name: str = "pdf_metadata"
    timeout_s: float = 6.0

    def run(self, ctx: AnalysisContext) -> DetectorOutput:
        doc_path = ctx.file_paths.get("document")
        if not doc_path or doc_path.suffix.lower() != ".pdf":
            return DetectorOutput()

        doc = fitz.open(doc_path)
        meta = doc.metadata or {}
        producer = str(meta.get("producer", "")).lower()
        creator = str(meta.get("creator", "")).lower()
        creation_date_raw = str(meta.get("creationDate", ""))
        mod_date_raw = str(meta.get("modDate", ""))

        evidence: List[Evidence] = []

        # 1. Suspicious PDF producer / consumer tool
        tool_found = next((t for t in SUSPICIOUS_PDF_PRODUCERS if t in producer or t in creator), None)
        if tool_found:
            evidence.append(
                Evidence(
                    id="DOC-META-01",
                    pipeline="document",
                    source="pdf_meta",
                    kind="risk",
                    raw_score=0.75,
                    calibrated_score=0.75,
                    weight=0.15,
                    effective_weight=0.15,
                    severity="low",
                    title="Online / Consumer PDF Editor Used",
                    reason=f"PDF metadata reveals file was generated or edited via consumer tool: '{tool_found}'.",
                    details={"producer": meta.get("producer", tool_found), "creator": meta.get("creator", "")},
                )
            )

        # 2. Modified long after creation
        def parse_pdf_date(date_str: str):
            # Format: D:YYYYMMDDHHmmSS or similar
            clean = re.sub(r"[^0-9]", "", date_str)[:14]
            if len(clean) >= 8:
                try:
                    return datetime.strptime(clean[:8], "%Y%m%d")
                except Exception:
                    return None
            return None

        dt_create = parse_pdf_date(creation_date_raw)
        dt_mod = parse_pdf_date(mod_date_raw)

        if dt_create and dt_mod:
            delta_days = (dt_mod - dt_create).days
            if delta_days > 7:
                evidence.append(
                    Evidence(
                        id="DOC-META-02",
                        pipeline="document",
                        source="pdf_meta",
                        kind="risk",
                        raw_score=0.60,
                        calibrated_score=0.60,
                        weight=0.20,
                        effective_weight=0.20,
                        severity="low",
                        title="PDF Modified Long After Creation",
                        reason=f"Document was altered {delta_days} days after its original generation.",
                        details={"created": dt_create.strftime("%Y-%m-%d"), "modified": dt_mod.strftime("%Y-%m-%d")},
                    )
                )

        # 3. Check for multiple appended revisions (%%EOF heuristic)
        with open(doc_path, "rb") as f:
            content = f.read()
            eof_count = content.count(b"%%EOF")
            if eof_count > 2:
                evidence.append(
                    Evidence(
                        id="DOC-META-03",
                        pipeline="document",
                        source="pdf_meta",
                        kind="risk",
                        raw_score=0.70,
                        calibrated_score=0.70,
                        weight=0.20,
                        effective_weight=0.20,
                        severity="low",
                        title="Appended PDF Revisions Detected",
                        reason=f"PDF file contains {eof_count} appended revision trailers, indicating post-save modifications.",
                        details={"eof_count": eof_count},
                    )
                )

        doc.close()
        return DetectorOutput(
            evidence=evidence,
            extras={"pdf_metadata": meta, "dt_create": dt_create, "dt_mod": dt_mod},
        )
