from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_end_to_end_image_analysis():
    transport = ASGITransport(app=app)
    sample_img = settings.DEMO_SAMPLES_DIR / "ai_car_damage.jpg"
    assert sample_img.exists()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_img, "rb") as f:
            files = {"file": ("ai_car_damage.jpg", f.read(), "image/jpeg")}
            resp = await client.post("/api/v1/analyze/image", files=files)
            assert resp.status_code == 202
            job_data = resp.json()
            job_id = job_data["job_id"]

        # Poll job until done
        import asyncio
        for _ in range(30):
            job_resp = await client.get(f"/api/v1/jobs/{job_id}")
            assert job_resp.status_code == 200
            j = job_resp.json()
            if j["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.3)

        assert j["status"] == "done"
        result_id = j["result_id"]
        assert result_id is not None

        # Fetch result
        res_resp = await client.get(f"/api/v1/results/{result_id}")
        assert res_resp.status_code == 200
        res = res_resp.json()
        assert res["overall"]["band"] in ("HIGH", "MEDIUM")
        assert len(res["evidence"]) > 0
        assert "artifacts" in res

        # Check PDF report generation
        pdf_resp = await client.get(f"/api/v1/results/{result_id}/report.pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 1000


@pytest.mark.asyncio
async def test_end_to_end_document_analysis():
    transport = ASGITransport(app=app)
    sample_pdf = settings.DEMO_SAMPLES_DIR / "tampered_invoice.pdf"
    assert sample_pdf.exists()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with open(sample_pdf, "rb") as f:
            files = {"file": ("tampered_invoice.pdf", f.read(), "application/pdf")}
            resp = await client.post("/api/v1/analyze/document", files=files)
            assert resp.status_code == 202
            job_data = resp.json()
            job_id = job_data["job_id"]

        # Poll job until done
        import asyncio
        for _ in range(30):
            job_resp = await client.get(f"/api/v1/jobs/{job_id}")
            assert job_resp.status_code == 200
            j = job_resp.json()
            if j["status"] in ("done", "failed"):
                break
            await asyncio.sleep(0.3)

        assert j["status"] == "done"
        result_id = j["result_id"]

        res_resp = await client.get(f"/api/v1/results/{result_id}")
        assert res_resp.status_code == 200
        res = res_resp.json()
        assert res["overall"]["band"] == "HIGH"
        evidence_ids = [e["id"] for e in res["evidence"]]
        assert "DOC-LOGIC-01" in evidence_ids # Line items mismatch caught!
