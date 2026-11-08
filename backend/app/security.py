"""Security primitives for Molido CCTV authentication.

These helpers deliberately do not create users, authenticate HTTP requests, or
enable streaming by themselves. Production wiring must add tenant-scoped storage,
rate limits, TLS, CSRF protection for cookie auth, and session revocation.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

_PASSWORD_SCHEME = "pbkdf2_sha256"
_PASSWORD_ITERATIONS = 310_000
_SALT_BYTES = 16
_SESSION_BYTES = 32


def hash_password(password: str, *, iterations: int = _PASSWORD_ITERATIONS) -> str:
    """Return a salted PBKDF2-SHA256 password hash suitable for database storage."""
    if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
        raise ValueError("password must contain between 12 and 1024 characters")
    if not 100_000 <= iterations <= 2_000_000:
        raise ValueError("password hashing work factor must be between 100000 and 2000000")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"{_PASSWORD_SCHEME}\u0024{iterations}\u0024{salt_text}\u0024{digest_text}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Verify a password hash safely; malformed hashes return False."""
    try:
        scheme, iteration_text, salt_text, digest_text = encoded_hash.split("$", 3)
        iterations = int(iteration_text)
        if scheme != _PASSWORD_SCHEME or not 100_000 <= iterations <= 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
        if len(salt) != _SALT_BYTES or len(expected) != hashlib.sha256().digest_size:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError, UnicodeError):
        return False


@dataclass(frozen=True)
class IssuedSessionToken:
    """Raw token is returned once; only token_hash should be persisted."""
    token: str
    token_hash: str
    expires_at: int


def issue_session_token(*, ttl_seconds: int = 900, now: int | None = None) -> IssuedSessionToken:
    """Create a cryptographically random opaque bearer token with bounded lifetime."""
    if not 60 <= ttl_seconds <= 86_400:
        raise ValueError("session lifetime must be between 60 and 86400 seconds")
    issued_at = int(time.time()) if now is None else int(now)
    token = secrets.token_urlsafe(_SESSION_BYTES)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    return IssuedSessionToken(token=token, token_hash=token_hash, expires_at=issued_at + ttl_seconds)


def hash_session_token(token: str) -> str:
    """Hash a presented opaque token for lookup; raw tokens must never be stored."""
    if not isinstance(token, str) or not 32 <= len(token) <= 256:
        raise ValueError("invalid session token")
    try:
        token.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("invalid session token") from exc
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def session_is_active(*, expires_at: int, revoked_at: int | None = None, now: int | None = None) -> bool:
    """Check expiry/revocation using Unix seconds."""
    current = int(time.time()) if now is None else int(now)
    return revoked_at is None and int(expires_at) > current
