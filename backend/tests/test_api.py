import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.main import app, init_database, tenant_database_path
from app.auth import bootstrap_admin, init_auth_schema, login
from app.adapters import AdapterResult
import app.main as main_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    path = str(tmp_path / "auth.sqlite3")
    monkeypatch.setattr(app.state, "database_path", path)
    monkeypatch.setattr(app.state, "auth_database_path", path)
    init_database()
    init_auth_schema(path)
    tenant_id = bootstrap_admin(
        path, configured_secret="test-bootstrap-secret",
        supplied_secret="test-bootstrap-secret", email="admin@example.test",
        password="test manager password long", tenant_name="Test Site",
        tenant_slug="test-site",
    )
    token, _ = login(path, email="admin@example.test",
                     password="test manager password long", tenant_slug="test-site")
    app.state.test_tenant_id = tenant_id
    client.headers.update({"Authorization": f"Bearer {token}"})


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



def test_create_ip_recorder_without_persisting_credentials():
    payload = {
        "name": "Main DVR", "brand": "Dahua", "recorder_type": "dvr",
        "connection_method": "ip", "host": "192.0.2.50", "port": 37777,
        "username": "operator", "password": "secret-not-to-store",
    }
    response = client.post("/api/v1/recorders", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["connection_method"] == "ip"
    assert body["host"] == "192.0.2.50"
    assert "username" not in body and "password" not in body
    with sqlite3.connect(tenant_database_path(app.state.test_tenant_id)) as db:
        stored = " ".join(str(x) for x in db.execute("SELECT * FROM recorders").fetchone())
    assert "secret-not-to-store" not in stored
    assert "operator" not in stored


def test_create_serial_recorder_requires_vendor_authorization():
    invalid = {
        "name": "Remote NVR", "brand": "Hikvision", "recorder_type": "nvr",
        "connection_method": "serial", "serial_number": "SN123456",
    }
    assert client.post("/api/v1/recorders", json=invalid).status_code == 422
    valid = {**invalid, "pairing_code": "one-time-proof"}
    response = client.post("/api/v1/recorders", json=valid)
    assert response.status_code == 201
    assert response.json()["connection_method"] == "serial"
    assert response.json()["serial_number"] == "SN123456"
    assert "pairing_code" not in response.text


def test_ip_recorder_requires_ip_login_fields():
    payload = {
        "name": "Missing login", "brand": "Generic", "recorder_type": "xvr",
        "connection_method": "ip", "host": "192.0.2.51",
    }
    assert client.post("/api/v1/recorders", json=payload).status_code == 422



def test_connection_test_discovers_and_persists_channels_without_credentials(monkeypatch):
    created = client.post("/api/v1/recorders", json={
        "name": "DVR test", "brand": "Generic", "recorder_type": "dvr",
        "connection_method": "ip", "host": "192.0.2.60", "port": 80,
        "username": "operator", "password": "transient-secret",
    })
    assert created.status_code == 201
    recorder_id = created.json()["id"]

    async def fake_discover(**kwargs):
        assert kwargs["username"] == "operator"
        assert kwargs["password"] == "transient-secret"
        return AdapterResult(
            reachable=True, adapter="onvif", manufacturer="TestVendor", model="TestDVR",
            channels=[{
                "channel_number": 1, "name": "Front Door", "profile_token": "p1",
                "stream_uri": "rtsp://192.0.2.60:554/live/1", "status": "discovered",
            }],
            capabilities=["onvif", "profiles", "rtsp_uri"], warnings=[],
        )

    monkeypatch.setattr(main_module.registry, "discover", fake_discover)
    tested = client.post(
        f"/api/v1/recorders/{recorder_id}/connect-test",
        json={"username": "operator", "password": "transient-secret"},
    )
    assert tested.status_code == 200
    assert tested.json()["reachable"] is True
    assert tested.json()["channel_count"] == 1
    assert tested.json()["credentials_persisted"] is False
    assert "stream_uri" not in tested.json()["channels"][0]
    channels = client.get(f"/api/v1/recorders/{recorder_id}/channels")
    assert channels.status_code == 200
    assert channels.json()[0]["name"] == "Front Door"
    assert "transient-secret" not in channels.text
    with sqlite3.connect(app.state.database_path) as db:
        stored = " ".join(str(value) for row in db.execute("SELECT * FROM recorder_channels") for value in row)
    assert "transient-secret" not in stored


def test_serial_connection_test_is_explicitly_not_supported_without_vendor_sdk():
    created = client.post("/api/v1/recorders", json={
        "name": "Serial NVR", "brand": "Generic", "recorder_type": "nvr",
        "connection_method": "serial", "serial_number": "SERIAL-123",
        "pairing_code": "temporary-code",
    })
    assert created.status_code == 201
    response = client.post(
        f"/api/v1/recorders/{created.json()['id']}/connect-test",
        json={"username": "operator", "password": "secret"},
    )
    assert response.status_code == 501


def test_dahua_p2p_registration_and_readiness_are_explicit():
    created = client.post("/api/v1/recorders", json={
        "name": "Remote Dahua NVR", "brand": "Dahua", "recorder_type": "nvr",
        "connection_method": "dahua_p2p", "serial_number": "DH-SERIAL-2026",
    })
    assert created.status_code == 201
    body = created.json()
    assert body["connection_method"] == "dahua_p2p"
    assert "username" not in body and "password" not in body
    status_response = client.get(f"/api/v1/recorders/{body['id']}/p2p-status")
    assert status_response.status_code == 200
    state = status_response.json()
    assert state["connection_mode"] == "official_p2p_cloud"
    assert state["integration_state"] == "not_configured"
    assert state["online"] is False
    assert state["sdk_connected"] is False
    assert state["cloud_video"] is False
    assert state["credentials_persisted"] is False
    with sqlite3.connect(tenant_database_path(app.state.test_tenant_id)) as db:
        stored = " ".join(str(value) for value in db.execute("SELECT * FROM recorders WHERE id=?", (body["id"],)).fetchone())
    assert "operator" not in stored and "p2p-pass" not in stored


def test_dahua_p2p_rejects_other_brands():
    response = client.post("/api/v1/recorders", json={
        "name": "Remote NVR", "brand": "Hikvision", "recorder_type": "nvr",
        "connection_method": "dahua_p2p", "serial_number": "SN123456",
        "username": "operator", "password": "p2p-pass",
    })
    assert response.status_code == 422


def test_dahua_p2p_connect_test_is_not_faked():
    created = client.post("/api/v1/recorders", json={
        "name": "Remote Dahua NVR", "brand": "Dahua", "recorder_type": "nvr",
        "connection_method": "dahua_p2p", "serial_number": "DH-SERIAL-2026",
    })
    response = client.post(
        f"/api/v1/recorders/{created.json()['id']}/p2p-connect-test",
        json={"username": "operator", "password": "p2p-pass"},
    )
    assert response.status_code == 501
    assert "DMSS-compatible" in response.json()["detail"]



def test_streaming_capabilities_report_provider_disabled():
    response = client.get("/api/v1/streaming/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["control_plane"] == "available"
    assert body["media_provider"] == "disabled"
    assert body["live_view"] is False
    assert body["transports"] == []


def test_stream_session_fails_closed_until_media_provider_is_configured():
    from uuid import uuid4

    created = client.post("/api/v1/recorders", json={
        "name": "Local NVR", "brand": "Dahua", "recorder_type": "nvr",
        "connection_method": "ip", "host": "192.0.2.25",
        "username": "operator", "password": "not-persisted",
    })
    assert created.status_code == 201
    recorder_id = created.json()["id"]
    channel_id = uuid4()
    with main_module.db_connection() as db:
        db.execute(
            """INSERT INTO recorder_channels
               (id,recorder_id,channel_number,name,profile_token,stream_uri,status)
               VALUES (?,?,?,?,?,?,?)""",
            (str(channel_id), recorder_id, 1, "Front gate", "profile-1",
             "rtsp://192.0.2.25:554/cam/realmonitor?channel=1&subtype=1", "discovered"),
        )

    response = client.post(
        f"/api/v1/recorders/{recorder_id}/channels/{channel_id}/stream-sessions",
        json={"transport": "webrtc", "profile": "sub", "session_ttl_seconds": 300},
    )
    assert response.status_code == 503
    assert "no stream is active" in response.json()["detail"]



def test_api_rejects_missing_bearer_token():
    saved = client.headers.get("Authorization")
    client.headers.pop("Authorization", None)
    try:
        response = client.get("/api/v1/cameras")
        assert response.status_code == 401
    finally:
        if saved:
            client.headers.update({"Authorization": saved})


def test_viewer_can_read_but_cannot_modify_inventory():
    created_user = client.post("/api/v1/auth/users", json={
        "email": "viewer@example.test",
        "password": "viewer password long enough",
        "role": "viewer",
    })
    assert created_user.status_code == 201
    token, _ = main_module.login(
        app.state.auth_database_path, email="viewer@example.test",
        password="viewer password long enough", tenant_slug="test-site",
    )
    manager_token = client.headers["Authorization"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    try:
        assert client.get("/api/v1/cameras").status_code == 200
        denied = client.post("/api/v1/cameras", json={
            "name": "Forbidden", "brand": "Generic", "protocol": "rtsp",
            "host": "192.0.2.99",
        })
        assert denied.status_code == 403
    finally:
        client.headers.update({"Authorization": manager_token})


def test_tenant_data_isolation_uses_separate_database_files(tmp_path):
    import time
    from uuid import uuid4

    with sqlite3.connect(app.state.auth_database_path) as db:
        second_tenant = str(uuid4())
        admin_id = db.execute(
            "SELECT id FROM users WHERE email=?", ("admin@example.test",)
        ).fetchone()[0]
        db.execute("INSERT INTO tenants(id,name,slug,created_at) VALUES(?,?,?,?)",
                   (second_tenant, "Second Site", "second-site", int(time.time())))
        db.execute("INSERT INTO memberships(user_id,tenant_id,role,created_at) VALUES(?,?,?,?)",
                   (admin_id, second_tenant, "manager", int(time.time())))

    second_token, _ = main_module.login(
        app.state.auth_database_path, email="admin@example.test",
        password="test manager password long", tenant_slug="second-site",
    )
    original_token = client.headers["Authorization"]
    client.headers.update({"Authorization": f"Bearer {second_token}"})
    created = client.post("/api/v1/cameras", json={
        "name": "Second tenant camera", "brand": "Generic",
        "protocol": "rtsp", "host": "198.51.100.8",
    })
    assert created.status_code == 201
    client.headers.update({"Authorization": original_token})
    first_tenant_cameras = client.get("/api/v1/cameras")
    assert first_tenant_cameras.status_code == 200
    assert all(item["name"] != "Second tenant camera"
               for item in first_tenant_cameras.json())
    assert tenant_database_path(second_tenant) != tenant_database_path(app.state.test_tenant_id)
