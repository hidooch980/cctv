from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def setup_function() -> None:
    app.state.cameras.clear()


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_list_camera_without_exposing_credentials() -> None:
    payload = {
        "name": "Front Gate",
        "brand": "ONVIF-compatible",
        "protocol": "onvif",
        "host": "192.0.2.10",
        "username": "operator",
        "password": "not-returned",
    }
    created = client.post("/api/v1/cameras", json=payload)
    assert created.status_code == 201
    assert "password" not in created.json()
    assert "username" not in created.json()

    listed = client.get("/api/v1/cameras")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_camera_not_found() -> None:
    response = client.get("/api/v1/cameras/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


def test_host_rejects_embedded_url() -> None:
    payload = {
        "name": "Invalid",
        "brand": "Generic",
        "protocol": "rtsp",
        "host": "rtsp://user:pass@example.test/stream",
    }
    response = client.post("/api/v1/cameras", json=payload)
    assert response.status_code == 422
