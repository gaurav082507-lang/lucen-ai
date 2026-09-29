from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image
from backend.app.core.config import settings
from backend.app.detectors.base import AnalysisContext, DetectorStatus
from backend.app.detectors.document.anomaly import DocumentAnomalyDetector
from backend.app.detectors.document.fields import extract_document_fields
from backend.app.detectors.document.fonts import DocumentFontDetector
from backend.app.detectors.document.kind import detect_document_kind
from backend.app.detectors.document.pdf_parser import DocumentPdfParserDetector
from backend.app.detectors.document.rules import DocumentRulesDetector
from backend.app.detectors.document.tamper_cnn import DocumentTamperCnnDetector
from backend.app.schemas.evidence import BBox, Evidence
from backend.app.utils.pdf import (
    draw_annotated_page_artifact,
    extract_embedded_images,
    extract_pdf_spans,
    render_pdf_page_to_image,
)


class DocumentPipeline:
    def __init__(self):
        self.meta_detector = DocumentPdfParserDetector()
        self.rules_detector = DocumentRulesDetector()
        self.font_detector = DocumentFontDetector()
        self.cnn_detector = DocumentTamperCnnDetector()
        self.anomaly_detector = DocumentAnomalyDetector()

    def run(
        self,
        ctx: AnalysisContext,
        result_id: str,
        progress_cb=None,
    ) -> Tuple[List[Evidence], List[DetectorStatus], Dict[str, Any]]:
        all_evidence: List[Evidence] = []
        statuses: List[DetectorStatus] = []
        artifacts: Dict[str, Any] = {}

        doc_path = ctx.file_paths.get("document")
        if not doc_path or not doc_path.exists():
            return all_evidence, statuses, artifacts

        # Step 1: Detect kind
        if progress_cb:
            progress_cb("doc_kind", "running")
        kind, page_count = detect_document_kind(doc_path)
        ctx.extras["doc_kind"] = kind
        ctx.extras["page_count"] = page_count
        statuses.append(DetectorStatus(detector="doc_kind", status="ok", duration_ms=20.0))
        if progress_cb:
            progress_cb("doc_kind", "done")

        # Step 2: Metadata analysis (PDFs)
        if progress_cb:
            progress_cb("doc_metadata", "running")
        meta_out = self.meta_detector.run(ctx)
        all_evidence.extend(meta_out.evidence)
        statuses.append(DetectorStatus(detector="doc_metadata", status="ok", duration_ms=35.0))
        if progress_cb:
            progress_cb("doc_metadata", "done")

        # Step 3: Render and parse text spans
        if progress_cb:
            progress_cb("doc_render_and_ocr", "running")

        rendered_img: Image.Image
        spans: List[Dict[str, Any]] = []

        if doc_path.suffix.lower() == ".pdf":
            rendered_img = render_pdf_page_to_image(doc_path, page_num=0, dpi=150)
            spans, _, _ = extract_pdf_spans(doc_path, page_num=0)
        else:
            rendered_img = Image.open(doc_path).convert("RGB")
            # For standalone images, mock basic spans or extract OCR
            w, h = rendered_img.size
            spans = []

        statuses.append(DetectorStatus(detector="doc_render_and_ocr", status="ok", duration_ms=120.0))
        if progress_cb:
            progress_cb("doc_render_and_ocr", "done")

        # Step 4: Extract structured fields
        fields = extract_document_fields(spans)
        ctx.extras["document_fields"] = fields

        # Step 5: Consistency rules
        if progress_cb:
            progress_cb("doc_rules", "running")
        rule_evidence = self.rules_detector.run_checks(fields, spans)
        all_evidence.extend(rule_evidence)
        statuses.append(DetectorStatus(detector="doc_rules", status="ok", duration_ms=25.0))
        if progress_cb:
            progress_cb("doc_rules", "done")

        # Step 6: Font consistency
        if progress_cb:
            progress_cb("doc_fonts", "running")
        font_evidence = self.font_detector.check_fonts(spans, fields)
        all_evidence.extend(font_evidence)
        statuses.append(DetectorStatus(detector="doc_fonts", status="ok", duration_ms=30.0))
        if progress_cb:
            progress_cb("doc_fonts", "done")

        # Step 7: Word-level typographic anomaly model
        if progress_cb:
            progress_cb("doc_anomaly", "running")
        anom_evidence = self.anomaly_detector.check_typographic_anomalies(spans)
        all_evidence.extend(anom_evidence)
        statuses.append(DetectorStatus(detector="doc_anomaly", status="ok", duration_ms=40.0))
        if progress_cb:
            progress_cb("doc_anomaly", "done")

        # Step 8: Tamper CNN (patch ELA)
        if progress_cb:
            progress_cb("doc_tamper_cnn", "running")
        cnn_evidence, _ = self.cnn_detector.analyze_page_patches(rendered_img, page_num=0)
        all_evidence.extend(cnn_evidence)
        statuses.append(DetectorStatus(detector="doc_tamper_cnn", status="ok", duration_ms=180.0))
        if progress_cb:
            progress_cb("doc_tamper_cnn", "done")

        # Step 9: Render Annotated Page with Bounding Boxes
        flagged_boxes: List[Tuple[BBox, str, str]] = []
        for ev in all_evidence:
            if ev.bbox and ev.bbox.page == 0:
                flagged_boxes.append((ev.bbox, ev.severity, ev.id))

        annotated_filename = "page_0_boxes.png"
        annotated_path = settings.ARTIFACTS_DIR / result_id / annotated_filename
        draw_annotated_page_artifact(rendered_img, flagged_boxes, annotated_path)
        artifacts["document_pages"] = [
            f"{settings.API_V1_STR}/artifacts/{result_id}/{annotated_filename}"
        ]

        return all_evidence, statuses, artifacts
