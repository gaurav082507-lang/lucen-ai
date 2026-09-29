from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from backend.app.core.config import settings

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{result_id}/{filename}")
async def get_artifact_file(result_id: str, filename: str):
    """Serves generated heatmaps, PDF overlays, and visual artifacts."""
    safe_filename = Path(filename).name
    artifact_path = settings.ARTIFACTS_DIR / result_id / safe_filename
    if not artifact_path.exists() or not artifact_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{filename}' not found for result '{result_id}'.",
        )

    ext = artifact_path.suffix.lower()
    media_type = "image/png"
    if ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif ext == ".pdf":
        media_type = "application/pdf"

    return FileResponse(artifact_path, media_type=media_type)
