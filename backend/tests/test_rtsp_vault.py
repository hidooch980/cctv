import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.rtsp_vault import RTSPPolicyError, RTSPSecretVault, validate_rtsp_destination


KEY = base64.urlsafe_b64encode(b"k" * 32).decode().rstrip("=")


def fake_resolver(host, port, type):
    assert host == "camera.internal"
    return [(None, None, None, None, ("10.20.0.15", port))]


def test_vault_round_trip_and_context_binding():
    vault = RTSPSecretVault(KEY)
    encrypted = vault.encrypt("camera-password", context="tenant-a/recorder-1")
    assert "camera-password" not in encrypted
    assert vault.decrypt(encrypted, context="tenant-a/recorder-1") == "camera-password"
    with pytest.raises(RTSPPolicyError):
        vault.decrypt(encrypted, context="tenant-b/recorder-1")


def test_vault_rejects_bad_key():
    with pytest.raises(RTSPPolicyError):
        RTSPSecretVault("bad")


def test_rtsp_destination_requires_explicit_cidr_allowlist():
    with pytest.raises(RTSPPolicyError):
        validate_rtsp_destination("rtsp://10.20.0.15/live", allowed_cidrs=[])


def test_rtsp_destination_accepts_allowlisted_private_camera():
    result = validate_rtsp_destination(
        "rtsp://camera.internal:554/live/ch01",
        allowed_cidrs=["10.20.0.0/24"], resolver=fake_resolver,
    )
    assert result.hostname == "camera.internal"
    assert result.resolved_addresses == ("10.20.0.15",)


@pytest.mark.parametrize("uri", [
    "http://10.20.0.15/live",
    "rtsp://user:password@10.20.0.15/live",
    "rtsp://127.0.0.1/live",
    "rtsp://169.254.1.2/live",
    "rtsp://10.20.0.15/live?token=secret",
    "rtsp://10.20.0.15/live#fragment",
])
def test_rtsp_destination_rejects_unsafe_uri(uri):
    with pytest.raises(RTSPPolicyError):
        validate_rtsp_destination(uri, allowed_cidrs=["10.20.0.0/24"])


def test_rtsp_destination_rejects_dns_rebinding_outside_allowlist():
    def resolver(host, port, type):
        return [(None, None, None, None, ("127.0.0.1", port))]
    with pytest.raises(RTSPPolicyError):
        validate_rtsp_destination(
            "rtsp://camera.internal/live",
            allowed_cidrs=["10.20.0.0/24"], resolver=resolver,
        )
