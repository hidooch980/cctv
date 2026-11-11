import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz(client: AsyncClient):
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Molido CCTV AI"
    assert "/api/v1" in data["api_v1"]


@pytest.mark.asyncio
async def test_system_health(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/system/health", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["capacity"]["max_cameras"] == 100
    assert "storage" in data
    assert "network" in data
