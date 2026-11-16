import io
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image
from endovision.api.main import app


def create_test_image_bytes() -> bytes:
    """Cria uma imagem de teste para simular upload."""
    buf = io.BytesIO()
    Image.new("L", (120, 120), color=190).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.mark.anyio
async def test_health_check():
    """Valida endpoint /health."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "EndoVision"


@pytest.mark.anyio
async def test_list_presets():
    """Valida listagem de presets clínicos em /api/v1/presets."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        keys = [p["key"] for p in data["presets"]]
        assert "apical_enhancement" in keys
        assert "calcified_canals" in keys
        assert "contrast_recovery" in keys
        assert "negative_invert" in keys


@pytest.mark.anyio
async def test_enhance_endpoint_success():
    """Valida upload e processamento com preset em /api/v1/enhance."""
    img_bytes = create_test_image_bytes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("rx_teste.jpg", img_bytes, "image/jpeg")}
        data = {"preset": "apical_enhancement"}
        response = await client.post("/api/v1/enhance", files=files, data=data)

        assert response.status_code == 200
        payload = response.json()
        assert payload["preset_applied"] == "apical_enhancement"
        assert payload["image_base64"].startswith("data:image/png;base64,")
        assert "original_metrics" in payload
        assert "enhanced_metrics" in payload
        assert payload["processing_time_ms"] > 0


@pytest.mark.anyio
async def test_enhance_endpoint_invalid_file():
    """Valida retorno 400 ao enviar arquivo corrompido ou texto."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"file": ("arquivo.txt", b"nao_sou_imagem", "text/plain")}
        response = await client.post("/api/v1/enhance", files=files, data={"preset": "apical_enhancement"})
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
