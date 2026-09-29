from pathlib import Path
from typing import Literal
import fitz
from backend.app.core.errors import CorruptFileError, TooManyPagesError
from backend.app.core.config import settings


Tuple_Kind = tuple[Literal["digital", "scanned", "image", "unknown"], int]


def detect_document_kind(doc_path: Path) -> Tuple_Kind:
    ext = doc_path.suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        return "image", 1

    if ext == ".pdf":
        try:
            doc = fitz.open(doc_path)
            page_count = len(doc)
            if page_count > settings.MAX_PDF_PAGES:
                doc.close()
                raise TooManyPagesError(
                    details={"page_count": page_count, "max_allowed": settings.MAX_PDF_PAGES}
                )

            total_chars = 0
            for page in doc:
                total_chars += len(page.get_text("text").strip())
            doc.close()

            avg_chars_per_page = total_chars / max(1, page_count)
            if avg_chars_per_page >= 50:
                return "digital", page_count
            else:
                return "scanned", page_count
        except TooManyPagesError:
            raise
        except Exception as e:
            raise CorruptFileError(message=f"Failed to parse PDF document: {e}")

    return "unknown", 0
