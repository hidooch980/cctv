import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.auth import (
    AuthError, bootstrap_admin, create_member, init_auth_schema, login,
    logout, resolve_principal,
)


@pytest.fixture
def auth_db(tmp_path):
    path = tmp_path / "auth.sqlite3"
    init_auth_schema(path)
    return path


def bootstrap(path):
    tenant_id = bootstrap_admin(
        path, configured_secret="one-time-bootstrap-secret",
        supplied_secret="one-time-bootstrap-secret",
        email="admin@example.test", password="a sufficiently long password",
        tenant_name="Example Site", tenant_slug="example",
    )
    return tenant_id


def test_first_admin_bootstrap_is_one_time_and_requires_secret(auth_db):
    with pytest.raises(AuthError):
        bootstrap_admin(
            auth_db, configured_secret="expected", supplied_secret="wrong",
            email="admin@example.test", password="a sufficiently long password",
            tenant_name="Example", tenant_slug="example",
        )
    tenant_id = bootstrap(auth_db)
    assert tenant_id
    with pytest.raises(AuthError, match="bootstrap_already_used"):
        bootstrap(auth_db)


def test_manager_can_create_employee_and_viewer_but_not_manager(auth_db):
    tenant_id = bootstrap(auth_db)
    token, _ = login(auth_db, email="admin@example.test",
                     password="a sufficiently long password", tenant_slug="example")
    manager = resolve_principal(auth_db, token, tenant_id)
    employee_id = create_member(auth_db, manager, email="staff@example.test",
                                password="another sufficiently long password", role="employee")
    viewer_id = create_member(auth_db, manager, email="read@example.test",
                              password="another sufficiently long password", role="viewer")
    assert employee_id != viewer_id
    with pytest.raises(AuthError, match="invalid_role"):
        create_member(auth_db, manager, email="other@example.test",
                      password="another sufficiently long password", role="manager")


def test_roles_and_tenant_scope_are_enforced_in_principal(auth_db):
    tenant_id = bootstrap(auth_db)
    admin_token, _ = login(auth_db, email="admin@example.test",
                            password="a sufficiently long password", tenant_slug="example")
    manager = resolve_principal(auth_db, admin_token)
    create_member(auth_db, manager, email="viewer@example.test",
                  password="viewer sufficiently long password", role="viewer")
    viewer_token, _ = login(auth_db, email="viewer@example.test",
                             password="viewer sufficiently long password", tenant_slug="example")
    viewer = resolve_principal(auth_db, viewer_token, tenant_id)
    assert viewer.allows("camera:read")
    assert viewer.allows("stream:view")
    assert not viewer.allows("camera:write")
    assert not viewer.allows("user:manage")
    with pytest.raises(AuthError, match="invalid_session"):
        resolve_principal(auth_db, viewer_token, "another-tenant-id")


def test_logout_revokes_session_and_expiry_is_checked(auth_db):
    tenant_id = bootstrap(auth_db)
    token, expires_at = login(auth_db, email="admin@example.test",
                              password="a sufficiently long password",
                              tenant_slug="example", now=1000)
    assert expires_at > 1000
    assert resolve_principal(auth_db, token, tenant_id, now=1001).role == "manager"
    logout(auth_db, token, now=1002)
    with pytest.raises(AuthError, match="invalid_session"):
        resolve_principal(auth_db, token, tenant_id, now=1003)


def test_login_failures_are_persisted_and_locked(auth_db):
    bootstrap(auth_db)
    for _ in range(7):
        with pytest.raises(AuthError, match="invalid_credentials"):
            login(auth_db, email="admin@example.test", password="wrong password",
                  tenant_slug="example", now=1000)
    with pytest.raises(AuthError, match="login_rate_limited"):
        login(auth_db, email="admin@example.test", password="wrong password",
              tenant_slug="example", now=1000)
    with pytest.raises(AuthError, match="login_rate_limited"):
        login(auth_db, email="admin@example.test",
              password="a sufficiently long password", tenant_slug="example", now=1001)


def test_mediamtx_token_is_path_transport_and_session_bound(auth_db):
    from app.auth import issue_media_token, verify_media_token

    tenant_id = bootstrap(auth_db)
    token, _ = login(auth_db, email="admin@example.test",
                     password="a sufficiently long password", tenant_slug="example")
    principal = resolve_principal(auth_db, token, tenant_id)
    media_token, expiry = issue_media_token(
        auth_db, principal, media_path="tenant/site-a/camera-1/sub", ttl_seconds=300, now=2000,
    )
    assert expiry == 2300
    assert verify_media_token(
        auth_db, token=media_token, media_path="tenant/site-a/camera-1/sub",
        action="read", protocol="webrtc", now=2001,
    ) == 2300
    with pytest.raises(AuthError, match="invalid_media_token"):
        verify_media_token(
            auth_db, token=media_token, media_path="tenant/other/camera-1/sub",
            action="read", protocol="webrtc", now=2001,
        )
    with pytest.raises(AuthError, match="media_action_forbidden"):
        verify_media_token(
            auth_db, token=media_token, media_path="tenant/site-a/camera-1/sub",
            action="publish", protocol="webrtc", now=2001,
        )
    with pytest.raises(AuthError, match="media_action_forbidden"):
        verify_media_token(
            auth_db, token=media_token, media_path="tenant/site-a/camera-1/sub",
            action="read", protocol="rtsp", now=2001,
        )
    logout(auth_db, token, now=2002)
    with pytest.raises(AuthError, match="invalid_media_token"):
        verify_media_token(
            auth_db, token=media_token, media_path="tenant/site-a/camera-1/sub",
            action="read", protocol="hls", now=2003,
        )
