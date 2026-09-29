import io
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Lucen AI"


@pytest.mark.asyncio
async def test_samples_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/samples")
        assert response.status_code == 200
        samples = response.json()
        assert len(samples) >= 4
        sample_ids = [s["id"] for s in samples]
        assert "sample-ai-damage" in sample_ids


@pytest.mark.asyncio
async def test_unsupported_file_type():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_zip = io.BytesIO(b"PK\x03\x04fakearchivecontent")
        files = {"file": ("test.zip", fake_zip, "application/zip")}
        response = await client.post("/api/v1/analyze/image", files=files)
        assert response.status_code == 415
        data = response.json()
        assert data["error"]["code"] == "UNSUPPORTED_FILE_TYPE"
