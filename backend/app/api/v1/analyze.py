import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from backend.app.core.config import settings
from backend.app.core.errors import NoInputError
from backend.app.core.security import generate_secure_filename, validate_file_content
from backend.app.schemas.job import JobStatus
from backend.app.schemas.requests import ClaimMetadata
from backend.app.services.job_manager import job_manager

router = APIRouter(prefix="", tags=["analyze"])


async def save_uploaded_file(file: UploadFile, subfolder: str) -> Path:
    content = await file.read()
    mime_type, ext = validate_file_content(content, file.filename or "upload")
    filename = generate_secure_filename(ext)
    target_dir = settings.UPLOADS_DIR / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    with open(target_path, "wb") as f:
        f.write(content)
    return target_path


@router.post("/analyze/image", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """Analyze a single claim photo for deepfakes, AI generation, and manipulation."""
    temp_folder = "temp_" + generate_secure_filename("dir").split(".")[0]
    file_path = await save_uploaded_file(file, temp_folder)
    job = job_manager.create_analysis_job(
        mode="image",
        file_paths={"image": file_path},
    )
    return job


@router.post("/analyze/document", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """Analyze an invoice, repair estimate, or medical report for tampering."""
    temp_folder = "temp_" + generate_secure_filename("dir").split(".")[0]
    file_path = await save_uploaded_file(file, temp_folder)
    job = job_manager.create_analysis_job(
        mode="document",
        file_paths={"document": file_path},
    )
    return job


@router.post("/analyze/claim", response_model=JobStatus, status_code=status.HTTP_202_ACCEPTED)
async def analyze_claim_endpoint(
    image: Optional[UploadFile] = File(None),
    document: Optional[UploadFile] = File(None),
    id_photo: Optional[UploadFile] = File(None),
    selfie: Optional[UploadFile] = File(None),
    metadata: Optional[str] = Form(None),
):
    """
    Comprehensive full-claim verification combining photo, document,
    identity face matching, and cross-modal consistency checks.
    """
    if not image and not document and not id_photo and not selfie:
        raise NoInputError()

    temp_folder = "temp_" + generate_secure_filename("dir").split(".")[0]
    file_paths = {}

    if image and image.filename:
        file_paths["image"] = await save_uploaded_file(image, temp_folder)
    if document and document.filename:
        file_paths["document"] = await save_uploaded_file(document, temp_folder)
    if id_photo and id_photo.filename:
        file_paths["id_photo"] = await save_uploaded_file(id_photo, temp_folder)
    if selfie and selfie.filename:
        file_paths["selfie"] = await save_uploaded_file(selfie, temp_folder)

    parsed_meta = None
    if metadata:
        try:
            meta_dict = json.loads(metadata)
            parsed_meta = ClaimMetadata(**meta_dict)
        except Exception:
            pass

    job = job_manager.create_analysis_job(
        mode="claim",
        file_paths=file_paths,
        claim_metadata=parsed_meta,
    )
    return job
