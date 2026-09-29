import uuid
from pathlib import Path
from typing import Tuple
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.errors import FileTooLargeError, UnsupportedFileTypeError

# Prevent decompression bomb attacks
Image.MAX_IMAGE_PIXELS = 50_000_000


def validate_file_content(content: bytes, original_filename: str) -> Tuple[str, str]:
    """
    Validates file size and magic bytes.
    Returns (detected_mime_type, file_extension).
    """
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_MB:
        raise FileTooLargeError(
            details={"file_size_mb": round(size_mb, 2), "max_size_mb": settings.MAX_UPLOAD_MB}
        )

    if len(content) < 4:
        raise UnsupportedFileTypeError(
            details={"reason": "File is empty or too short."}
        )

    # Magic byte inspection
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    elif content.startswith(b"RIFF") and len(content) > 12 and content[8:12] == b"WEBP":
        return "image/webp", "webp"
    elif content.startswith(b"%PDF-"):
        return "application/pdf", "pdf"
    else:
        raise UnsupportedFileTypeError(
            details={
                "filename": original_filename,
                "first_bytes_hex": content[:8].hex(),
                "allowed_types": ["image/jpeg", "image/png", "image/webp", "application/pdf"]
            }
        )


def generate_secure_filename(ext: str) -> str:
    """Generates an unguessable UUID-based filename."""
    clean_ext = ext.lstrip(".").lower()
    return f"{uuid.uuid4().hex}.{clean_ext}"
