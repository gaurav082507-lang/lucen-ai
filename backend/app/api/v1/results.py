from typing import List
from fastapi import APIRouter, Response
from backend.app.core.errors import ResultNotFoundError
from backend.app.db.repository import get_analysis_result, list_recent_results
from backend.app.schemas.result import AnalysisResult
from backend.app.services.report import generate_pdf_report

router = APIRouter(prefix="", tags=["results"])


@router.get("/results/{result_id}", response_model=AnalysisResult)
async def get_result_by_id(result_id: str):
    """Retrieves full calibrated analysis result, evidence, and scores."""
    result = get_analysis_result(result_id)
    if not result:
        raise ResultNotFoundError(result_id)
    return result


@router.get("/results/{result_id}/report.json")
async def download_json_report(result_id: str):
    """Downloads investigator report formatted as JSON."""
    result = get_analysis_result(result_id)
    if not result:
        raise ResultNotFoundError(result_id)
    return Response(
        content=result.model_dump_json(indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="claimguard_report_{result_id}.json"'},
    )


@router.get("/results/{result_id}/report.pdf")
async def download_pdf_report(result_id: str):
    """Downloads formatted PDF investigation report."""
    result = get_analysis_result(result_id)
    if not result:
        raise ResultNotFoundError(result_id)
    pdf_bytes = generate_pdf_report(result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="claimguard_report_{result_id}.pdf"'},
    )


@router.get("/history", response_model=List[dict])
async def get_analysis_history():
    """Lists recent claim analyses for audit logs and historical tracking."""
    return list_recent_results(limit=50)
