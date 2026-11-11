import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin@123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "WrongPassword"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_current_user_me(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"


@pytest.mark.asyncio
async def test_qr_login_flow(client: AsyncClient, auth_headers: dict):
    # 1. Create QR login session
    session_res = await client.post("/api/v1/auth/qr/session")
    assert session_res.status_code == 200
    session_data = session_res.json()
    session_id = session_data["session_id"]
    assert "molido://auth/qr" in session_data["qr_payload"]

    # 2. Check pending status
    status_res = await client.get(f"/api/v1/auth/qr/status/{session_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "pending"

    # 3. Simulate mobile scan
    scan_res = await client.post(f"/api/v1/auth/qr/scan/{session_id}")
    assert scan_res.status_code == 200

    # 4. Mobile authorizes login with JWT
    auth_res = await client.post(
        "/api/v1/auth/qr/authorize",
        json={"session_id": session_id},
        headers=auth_headers
    )
    assert auth_res.status_code == 200

    # 5. Check approved status and retrieve web token
    final_status = await client.get(f"/api/v1/auth/qr/status/{session_id}")
    assert final_status.status_code == 200
    final_data = final_status.json()
    assert final_data["status"] == "approved"
    assert final_data["token"] is not None
    assert final_data["token"]["username"] == "admin"
    assert final_data["token"]["role"] == "admin"
