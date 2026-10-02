import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "saathi-api"
    assert "timestamp" in data


@pytest.mark.integration
async def test_readiness_check(async_client: AsyncClient):
    response = await async_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"
