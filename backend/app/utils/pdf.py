from pathlib import Path
from typing import Any, Dict, List, Tuple
import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from backend.app.schemas.evidence import BBox


def get_pdf_info(pdf_path: Path) -> Dict[str, Any]:
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    is_encrypted = doc.is_encrypted
    metadata = dict(doc.metadata) if doc.metadata else {}
    doc.close()
    return {
        "page_count": page_count,
        "is_encrypted": is_encrypted,
        "metadata": metadata,
    }


def render_pdf_page_to_image(pdf_path: Path, page_num: int = 0, dpi: int = 150) -> Image.Image:
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def extract_pdf_spans(pdf_path: Path, page_num: int = 0) -> Tuple[List[Dict[str, Any]], float, float]:
    """
    Extracts text spans with font name, size, flags, color, and bounding box.
    Returns (spans, page_width_pts, page_height_pts).
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    rect = page.rect
    page_w, page_h = rect.width, rect.height

    spans = []
    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type") == 0:  # text block
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    bbox = span.get("bbox") # (x0, y0, x1, y1) in points
                    text = span.get("text", "").strip()
                    if text:
                        spans.append({
                            "text": text,
                            "font": span.get("font", "Unknown"),
                            "size": round(span.get("size", 10.0), 2),
                            "flags": span.get("flags", 0),
                            "color": span.get("color", 0),
                            "bbox_pts": bbox,
                            "bbox_norm": BBox(
                                page=page_num,
                                x=round(bbox[0] / page_w, 4),
                                y=round(bbox[1] / page_h, 4),
                                w=round((bbox[2] - bbox[0]) / page_w, 4),
                                h=round((bbox[3] - bbox[1]) / page_h, 4),
                            ),
                        })

    doc.close()
    return spans, page_w, page_h


def extract_embedded_images(pdf_path: Path, output_dir: Path) -> List[Path]:
    """Extracts non-trivial embedded raster images from PDF pages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    extracted_paths = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            w, h = base_image["width"], base_image["height"]

            # Filter out tiny icons, logos, bullets
            if w >= 150 and h >= 150:
                img_path = output_dir / f"page_{page_num}_img_{img_idx}.{image_ext}"
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                extracted_paths.append(img_path)

    doc.close()
    return extracted_paths


def draw_annotated_page_artifact(
    rendered_img: Image.Image,
    flagged_boxes: List[Tuple[BBox, str, str]],  # (bbox, severity, label)
    output_path: Path,
) -> Path:
    """
    Draws highlighted bounding boxes on rendered PDF page image.
    Severities: red (high), amber (medium), blue (low).
    """
    img_bgr = cv2.cvtColor(np.array(rendered_img), cv2.COLOR_RGB2BGR)
    img_h, img_w = img_bgr.shape[:2]

    color_map = {
        "high": (0, 0, 230),     # Red
        "medium": (0, 165, 255), # Amber
        "low": (200, 100, 0),    # Blue/Info
    }

    for bbox, severity, label in flagged_boxes:
        x1 = int(bbox.x * img_w)
        y1 = int(bbox.y * img_h)
        w = int(bbox.w * img_w)
        h = int(bbox.h * img_h)
        x2, y2 = x1 + w, y1 + h

        color = color_map.get(severity.lower(), (0, 0, 230))
        cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 2)

        # Draw label header
        tag = label[:24]
        cv2.putText(
            img_bgr,
            tag,
            (x1, max(15, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img_bgr)
    return output_path
