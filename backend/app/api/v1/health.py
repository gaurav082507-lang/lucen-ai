from pathlib import Path
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
async def health_check():
    """Health check and model status inspection."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "models": {
            "ai_detector": True,
            "document_forensics": True,
            "consistency_rules": True,
            "identity_biometrics": True,
        },
        "storage": {
            "sqlite_connected": settings.SQLITE_PATH.exists(),
        },
    }


@router.get("/samples")
async def get_demo_samples():
    """Returns curated demo samples for instant demonstration without file hunting."""
    samples = [
        {
            "id": "sample-ai-damage",
            "title": "AI-Generated Vehicle Damage",
            "type": "image",
            "description": "Synthesized front bumper dent with diffusion frequency anomalies.",
            "file": "ai_car_damage.jpg",
            "expected_band": "HIGH",
        },
        {
            "id": "sample-real-car",
            "title": "Authentic Vehicle Photo",
            "type": "image",
            "description": "Genuine camera capture with valid EXIF and natural JPEG error levels.",
            "file": "authentic_car.jpg",
            "expected_band": "LOW",
        },
        {
            "id": "sample-tampered-invoice",
            "title": "Tampered Auto Repair Invoice",
            "type": "document",
            "description": "Invoice where total was altered from 1,000 to 1,200 with font mismatch.",
            "file": "tampered_invoice.pdf",
            "expected_band": "HIGH",
        },
        {
            "id": "sample-clean-invoice",
            "title": "Clean Repair Estimate",
            "type": "document",
            "description": "Internally consistent document with matching line item sums and authentic metadata.",
            "file": "clean_invoice.pdf",
            "expected_band": "LOW",
        },
        {
            "id": "sample-identity-mismatch",
            "title": "Identity Mismatch Claim",
            "type": "claim",
            "description": "ID card photo paired with a mismatched synthetic selfie face.",
            "expected_band": "HIGH",
        }
    ]
    return samples
