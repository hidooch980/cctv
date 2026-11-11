import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_camera(client: AsyncClient, auth_headers: dict):
    # Create camera
    new_camera = {
        "name": "Warehouse Perimeter #1",
        "location": "North Zone",
        "group_name": "Warehouse",
        "vendor": "Dahua / Lechange",
        "device_ip": "192.168.1.150",
        "device_port": 554,
        "device_username": "admin",
        "device_password": "SecretPassword123",
        "resolution": "1920x1080",
        "fps": 25,
        "bitrate_kbps": 2048,
        "ptz_supported": True,
        "ai_enabled": True,
    }
    create_res = await client.post(
        "/api/v1/cameras", json=new_camera, headers=auth_headers
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["name"] == "Warehouse Perimeter #1"
    assert created_data["id"] is not None
    cam_id = created_data["id"]

    # List cameras
    list_res = await client.get("/api/v1/cameras", headers=auth_headers)
    assert list_res.status_code == 200
    cameras = list_res.json()
    assert any(c["id"] == cam_id for c in cameras)

    # PTZ control
    ptz_res = await client.post(
        f"/api/v1/cameras/{cam_id}/ptz",
        json={"action": "pan_left", "speed": 0.5},
        headers=auth_headers,
    )
    assert ptz_res.status_code == 200
    ptz_data = ptz_res.json()
    assert ptz_data["action"] == "pan_left"
    assert ptz_data["status"] == "executed"

    # Get stream info
    stream_res = await client.get(
        f"/api/v1/cameras/{cam_id}/stream", headers=auth_headers
    )
    assert stream_res.status_code == 200
    stream_data = stream_res.json()
    assert "webrtc_url" in stream_data
    assert "rtsp_sanitized" in stream_data
    # Verify password was sanitized
    assert "SecretPassword123" not in stream_data["rtsp_sanitized"]


@pytest.mark.asyncio
async def test_camera_discovery(client: AsyncClient, auth_headers: dict):
    res = await client.post("/api/v1/cameras/discover", headers=auth_headers)
    assert res.status_code == 200
    devices = res.json()
    assert len(devices) > 0
    assert any("Dahua" in d["manufacturer"] for d in devices)
