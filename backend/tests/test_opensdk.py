import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_opensdk_catalog(client: AsyncClient, auth_headers: dict):
    res = await client.get("/api/v1/opensdk/catalog", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_cataloged"] >= 10
    assert "STATE_RTSP_AUTHORIZATION_FAIL" in data["errors"]
    assert "STATE_DHHTTP_SERVER_ERROR" in data["errors"]


@pytest.mark.asyncio
async def test_opensdk_diagnose_rtsp_401(client: AsyncClient, auth_headers: dict):
    res = await client.post(
        "/api/v1/opensdk/diagnose",
        json={"error_identifier": "STATE_RTSP_AUTHORIZATION_FAIL"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["numeric_code"] == 401
    assert data["category"] == "RTSP Protocol"
    assert "تجدید کنید" in data["recommended_action_fa"]
    assert data["recovery_strategy"] == "reauth"


@pytest.mark.asyncio
async def test_opensdk_diagnose_numeric_dhhttp_503001(client: AsyncClient, auth_headers: dict):
    res = await client.post(
        "/api/v1/opensdk/diagnose",
        json={"error_identifier": "503001"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["code"] == "STATE_DHHTTP_SERVER_ERROR"
    assert data["recovery_strategy"] == "p2p_reconnect"


@pytest.mark.asyncio
async def test_opensdk_diagnose_decryption_key_error(client: AsyncClient, auth_headers: dict):
    res = await client.post(
        "/api/v1/opensdk/diagnose",
        json={"error_identifier": "DEC_KEY_ERROR"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "رمزگشایی" in data["description_fa"]
