import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app, init_database

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(app.state, "database_path", str(tmp_path / "cameras.sqlite3"))
    init_database()


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
        "password": "must-not-be-stored",
    }
    created = client.post("/api/v1/cameras", json=payload)
    assert created.status_code == 201
    assert "password" not in created.json()
    assert "username" not in created.json()
    assert created.json()["status"] == "pending"

    listed = client.get("/api/v1/cameras")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_camera_survives_application_state_reset(tmp_path) -> None:
    payload = {"name": "Persisted", "brand": "Generic", "protocol": "rtsp", "host": "192.0.2.11"}
    created = client.post("/api/v1/cameras", json=payload)
    assert created.status_code == 201
    app.state.cameras = {}  # Legacy in-memory state must not affect persisted inventory.
    listed = client.get("/api/v1/cameras")
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Persisted"


def test_camera_not_found() -> None:
    response = client.get("/api/v1/cameras/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 404


def test_host_rejects_embedded_url() -> None:
    payload = {"name": "Invalid", "brand": "Generic", "protocol": "rtsp", "host": "rtsp://user:pass@example.test/stream"}
    response = client.post("/api/v1/cameras", json=payload)
    assert response.status_code == 422


def test_delete_camera() -> None:
    created = client.post("/api/v1/cameras", json={"name":"Door","brand":"Generic","protocol":"onvif","host":"192.0.2.12"})
    camera_id = created.json()["id"]
    assert client.delete(f"/api/v1/cameras/{camera_id}").status_code == 204
    assert client.get(f"/api/v1/cameras/{camera_id}").status_code == 404

def test_camera_capacity_is_limited_to_one_hundred() -> None:
    for index in range(100):
        response = client.post(
            "/api/v1/cameras",
            json={"name": f"Camera {index}", "brand": "Generic", "protocol": "rtsp", "host": f"192.0.2.{index + 1}"},
        )
        assert response.status_code == 201
    overflow = client.post(
        "/api/v1/cameras",
        json={"name": "Overflow", "brand": "Generic", "protocol": "rtsp", "host": "198.51.100.1"},
    )
    assert overflow.status_code == 409
    assert len(client.get("/api/v1/cameras").json()) == 100
