"""Encrypted RTSP source-secret storage and strict destination validation.

The module never opens an RTSP connection. Callers must validate the destination
again immediately before provisioning/connecting and use the returned resolved
addresses to pin the upstream connection (DNS rebinding protection).
"""
from __future__ import annotations

import base64
import ipaddress
import json
import os
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class RTSPPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedRTSPSource:
    scheme: str
    hostname: str
    port: int
    path: str
    resolved_addresses: tuple[str, ...]


def _configured_key(value: str | None = None) -> bytes:
    encoded = value if value is not None else os.getenv("MOLIDO_CCTV_RTSP_VAULT_KEY", "")
    try:
        key = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except (ValueError, TypeError) as exc:
        raise RTSPPolicyError("RTSP vault key must be URL-safe base64") from exc
    if len(key) != 32:
        raise RTSPPolicyError("RTSP vault key must decode to exactly 32 bytes")
    return key


class RTSPSecretVault:
    """AES-256-GCM envelope for a single RTSP credential or URI secret."""

    def __init__(self, key: str | None = None):
        self._cipher = AESGCM(_configured_key(key))

    def encrypt(self, plaintext: str, *, context: str) -> str:
        if not plaintext or len(plaintext) > 4096 or not context or len(context) > 512:
            raise RTSPPolicyError("invalid secret or encryption context")
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(nonce, plaintext.encode("utf-8"), context.encode("utf-8"))
        return "v1." + base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii").rstrip("=")

    def decrypt(self, envelope: str, *, context: str) -> str:
        if not envelope.startswith("v1.") or not context:
            raise RTSPPolicyError("unsupported secret envelope")
        try:
            raw = base64.urlsafe_b64decode(envelope[3:] + "=" * (-len(envelope[3:]) % 4))
            if len(raw) < 29:
                raise ValueError("short envelope")
            return self._cipher.decrypt(raw[:12], raw[12:], context.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            raise RTSPPolicyError("secret authentication failed") from exc


def validate_rtsp_destination(
    uri: str,
    *,
    allowed_cidrs: list[str] | tuple[str, ...],
    resolver=None,
) -> ValidatedRTSPSource:
    """Validate RTSP(S) URI and require every DNS/IP result inside approved CIDRs."""
    if not isinstance(uri, str) or len(uri) > 2048:
        raise RTSPPolicyError("invalid RTSP URI")
    try:
        parsed = urlsplit(uri)
        if parsed.scheme.lower() not in {"rtsp", "rtsps"}:
            raise RTSPPolicyError("only rtsp and rtsps schemes are allowed")
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            raise RTSPPolicyError("URI must have a host and credentials must be stored separately")
        if parsed.fragment or parsed.query or not parsed.path.startswith("/"):
            raise RTSPPolicyError("RTSP URI query and fragment are not allowed")
        host = parsed.hostname.rstrip(".").lower()
        port = parsed.port or (322 if parsed.scheme.lower() == "rtsps" else 554)
        if not 1 <= port <= 65535:
            raise RTSPPolicyError("invalid RTSP port")
        networks = [ipaddress.ip_network(item, strict=False) for item in allowed_cidrs]
        if not networks:
            raise RTSPPolicyError("an explicit RTSP destination CIDR allowlist is required")
        lookup = resolver or socket.getaddrinfo
        try:
            literal = ipaddress.ip_address(host)
            addresses = [literal]
        except ValueError:
            answers = lookup(host, port, type=socket.SOCK_STREAM)
            addresses = sorted({ipaddress.ip_address(item[4][0].split("%", 1)[0]) for item in answers}, key=str)
        if not addresses:
            raise RTSPPolicyError("RTSP hostname did not resolve")
        for address in addresses:
            if (address.is_loopback or address.is_link_local or address.is_multicast
                    or address.is_unspecified or address.is_reserved
                    or not any(address in network for network in networks)):
                raise RTSPPolicyError("RTSP destination resolves outside the approved CIDR allowlist")
        return ValidatedRTSPSource(
            scheme=parsed.scheme.lower(), hostname=host, port=port,
            path=parsed.path, resolved_addresses=tuple(str(item) for item in addresses),
        )
    except RTSPPolicyError:
        raise
    except (ValueError, OSError, TypeError) as exc:
        raise RTSPPolicyError("invalid or unresolvable RTSP destination") from exc
