"""Persistent multi-tenant authentication primitives for Molido CCTV.

Only password hashes and session-token hashes are persisted. This module is
intentionally independent from FastAPI so its security rules can be tested.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from app.security import hash_password, hash_session_token, issue_session_token, verify_password

ROLES = {"manager", "employee", "viewer"}
ROLE_PERMISSIONS = {
    "manager": {"camera:read", "camera:write", "device:read", "device:write", "stream:view", "user:manage", "tenant:manage"},
    "employee": {"camera:read", "camera:write", "device:read", "device:write", "stream:view"},
    "viewer": {"camera:read", "device:read", "stream:view"},
}


class AuthError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    email: str
    role: str
    session_id: str

    def allows(self, permission: str) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(path), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_auth_schema(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS tenants (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memberships (
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('manager','employee','viewer')),
            created_at INTEGER NOT NULL,
            PRIMARY KEY(user_id, tenant_id)
        );
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE, expires_at INTEGER NOT NULL,
            revoked_at INTEGER, created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_sessions_token ON auth_sessions(token_hash);
        CREATE TABLE IF NOT EXISTS media_tokens (
            id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES auth_sessions(id) ON DELETE CASCADE,
            tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            token_hash TEXT NOT NULL UNIQUE, media_path TEXT NOT NULL,
            protocol TEXT NOT NULL DEFAULT 'hls' CHECK(protocol IN ('hls','webrtc')),
            action TEXT NOT NULL CHECK(action IN ('read')),
            expires_at INTEGER NOT NULL, revoked_at INTEGER, created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_media_tokens_hash ON media_tokens(token_hash);
        CREATE TABLE IF NOT EXISTS login_attempts (
            identity TEXT PRIMARY KEY, failures INTEGER NOT NULL,
            window_started_at INTEGER NOT NULL, locked_until INTEGER NOT NULL DEFAULT 0
        );
        """)
        # Backward-compatible migration for databases created before transport binding.
        columns = {row["name"] for row in db.execute("PRAGMA table_info(media_tokens)")}
        if "protocol" not in columns:
            db.execute("ALTER TABLE media_tokens ADD COLUMN protocol TEXT NOT NULL DEFAULT 'hls'")


def bootstrap_admin(path: str | Path, *, configured_secret: str | None,
                    supplied_secret: str, email: str, password: str,
                    tenant_name: str, tenant_slug: str) -> str:
    """Create the first tenant and manager exactly once; no default account."""
    if not configured_secret or not supplied_secret or not hmac.compare_digest(configured_secret, supplied_secret):
        raise AuthError("bootstrap_not_authorized")
    normalized = email.strip().lower()
    if not normalized or len(normalized) > 254 or "@" not in normalized:
        raise AuthError("invalid_email")
    if not tenant_name.strip() or not tenant_slug.strip() or len(tenant_slug) > 80:
        raise AuthError("invalid_tenant")
    password_hash = hash_password(password)
    now = int(time.time())
    with connect(path) as db:
        if db.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            raise AuthError("bootstrap_already_used")
        tenant_id, user_id = str(uuid4()), str(uuid4())
        try:
            db.execute("INSERT INTO tenants(id,name,slug,created_at) VALUES(?,?,?,?)",
                       (tenant_id, tenant_name.strip(), tenant_slug.strip().lower(), now))
            db.execute("INSERT INTO users(id,email,password_hash,created_at) VALUES(?,?,?,?)",
                       (user_id, normalized, password_hash, now))
            db.execute("INSERT INTO memberships(user_id,tenant_id,role,created_at) VALUES(?,?,?,?)",
                       (user_id, tenant_id, "manager", now))
        except sqlite3.IntegrityError as exc:
            raise AuthError("bootstrap_conflict") from exc
    return tenant_id


def create_member(path: str | Path, principal: Principal, *, email: str,
                  password: str, role: str) -> str:
    if not principal.allows("user:manage"):
        raise AuthError("forbidden")
    if role not in ROLES:
        raise AuthError("invalid_role")
    normalized = email.strip().lower()
    if not normalized or len(normalized) > 254 or "@" not in normalized:
        raise AuthError("invalid_email")
    password_hash = hash_password(password)
    user_id, now = str(uuid4()), int(time.time())
    with connect(path) as db:
        try:
            db.execute("INSERT INTO users(id,email,password_hash,created_at) VALUES(?,?,?,?)",
                       (user_id, normalized, password_hash, now))
            db.execute("INSERT INTO memberships(user_id,tenant_id,role,created_at) VALUES(?,?,?,?)",
                       (user_id, principal.tenant_id, role, now))
        except sqlite3.IntegrityError as exc:
            raise AuthError("member_conflict") from exc
    return user_id


def login(path: str | Path, *, email: str, password: str, tenant_slug: str,
          ttl_seconds: int = 3600, now: int | None = None) -> tuple[str, int]:
    current = int(time.time()) if now is None else int(now)
    identity = email.strip().lower()[:254]
    with connect(path) as db:
        attempt = db.execute("SELECT failures,window_started_at,locked_until FROM login_attempts WHERE identity=?",
                             (identity,)).fetchone()
        if attempt and attempt["locked_until"] > current:
            raise AuthError("login_rate_limited")
        row = db.execute("""
            SELECT u.id AS user_id,u.email,u.password_hash,u.is_active,
                   t.id AS tenant_id,m.role
            FROM users u JOIN memberships m ON m.user_id=u.id
            JOIN tenants t ON t.id=m.tenant_id
            WHERE u.email=? AND t.slug=?
        """, (identity, tenant_slug.strip().lower())).fetchone()
        valid = bool(row and row["is_active"] and verify_password(password, row["password_hash"]))
        if not valid:
            if attempt and current - attempt["window_started_at"] <= 300:
                failures = attempt["failures"] + 1
                started = attempt["window_started_at"]
            else:
                failures, started = 1, current
            locked = current + 900 if failures >= 8 else 0
            db.execute("""INSERT INTO login_attempts(identity,failures,window_started_at,locked_until)
                          VALUES(?,?,?,?) ON CONFLICT(identity) DO UPDATE SET
                          failures=excluded.failures,window_started_at=excluded.window_started_at,
                          locked_until=excluded.locked_until""", (identity, failures, started, locked))
            db.commit()
            raise AuthError("login_rate_limited" if locked else "invalid_credentials")
        db.execute("DELETE FROM login_attempts WHERE identity=?", (identity,))
        issued = issue_session_token(ttl_seconds=ttl_seconds, now=current)
        session_id = str(uuid4())
        db.execute("""INSERT INTO auth_sessions
                      (id,user_id,tenant_id,token_hash,expires_at,created_at)
                      VALUES(?,?,?,?,?,?)""",
                   (session_id, row["user_id"], row["tenant_id"], issued.token_hash,
                    issued.expires_at, current))
    return issued.token, issued.expires_at


def resolve_principal(path: str | Path, token: str, tenant_id: str | None = None,
                      now: int | None = None) -> Principal:
    try:
        token_hash = hash_session_token(token)
    except (TypeError, ValueError):
        raise AuthError("invalid_session")
    current = int(time.time()) if now is None else int(now)
    with connect(path) as db:
        row = db.execute("""
            SELECT s.id AS session_id,s.tenant_id,s.expires_at,s.revoked_at,
                   u.id AS user_id,u.email,u.is_active,m.role
            FROM auth_sessions s JOIN users u ON u.id=s.user_id
            JOIN memberships m ON m.user_id=u.id AND m.tenant_id=s.tenant_id
            WHERE s.token_hash=?
        """, (token_hash,)).fetchone()
        if (not row or not row["is_active"] or row["revoked_at"] is not None
                or row["expires_at"] <= current
                or (tenant_id is not None and tenant_id != row["tenant_id"])):
            raise AuthError("invalid_session")
        return Principal(row["user_id"], row["tenant_id"], row["email"],
                         row["role"], row["session_id"])


def logout(path: str | Path, token: str, now: int | None = None) -> None:
    token_hash = hash_session_token(token)
    current = int(time.time()) if now is None else int(now)
    with connect(path) as db:
        db.execute("UPDATE auth_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",
                   (current, token_hash))


def issue_media_token(path: str | Path, principal: Principal, *,
                      media_path: str, protocol: str = "hls", ttl_seconds: int = 300,
                      now: int | None = None) -> tuple[str, int]:
    """Issue a one-time opaque credential bound to one session and one MediaMTX path."""
    if not principal.allows("stream:view"):
        raise AuthError("forbidden")
    if not 60 <= ttl_seconds <= 900:
        raise AuthError("invalid_media_token_ttl")
    if protocol not in {"hls", "webrtc"}:
        raise AuthError("media_action_forbidden")
    if not media_path or len(media_path) > 512 or media_path.startswith("/") or ".." in media_path:
        raise AuthError("invalid_media_path")
    current = int(time.time()) if now is None else int(now)
    issued = issue_session_token(ttl_seconds=ttl_seconds, now=current)
    with connect(path) as db:
        session = db.execute(
            "SELECT id,tenant_id,expires_at,revoked_at FROM auth_sessions WHERE id=? AND user_id=?",
            (principal.session_id, principal.user_id),
        ).fetchone()
        if not session or session["tenant_id"] != principal.tenant_id or session["revoked_at"] is not None or session["expires_at"] <= current:
            raise AuthError("invalid_session")
        db.execute("""INSERT INTO media_tokens
                      (id,session_id,tenant_id,token_hash,media_path,protocol,action,expires_at,created_at)
                      VALUES(?,?,?,?,?,?,?,?,?)""",
                   (str(uuid4()), principal.session_id, principal.tenant_id,
                    issued.token_hash, media_path, protocol, "read", issued.expires_at, current))
    return issued.token, issued.expires_at


def verify_media_token(path: str | Path, *, token: str, media_path: str,
                       action: str, protocol: str,
                       now: int | None = None) -> int:
    """Return expiry only when token, session, tenant, path and transport all match."""
    if action != "read" or protocol not in {"hls", "webrtc"}:
        raise AuthError("media_action_forbidden")
    try:
        token_hash = hash_session_token(token)
    except (TypeError, ValueError) as exc:
        raise AuthError("invalid_media_token") from exc
    current = int(time.time()) if now is None else int(now)
    with connect(path) as db:
        row = db.execute("""
            SELECT mt.expires_at,mt.revoked_at,mt.protocol,s.revoked_at AS session_revoked,
                   s.expires_at AS session_expires,u.is_active
            FROM media_tokens mt
            JOIN auth_sessions s ON s.id=mt.session_id
            JOIN users u ON u.id=s.user_id
            WHERE mt.token_hash=? AND mt.media_path=? AND mt.action=?
        """, (token_hash, media_path, "read")).fetchone()
        if (not row or row["protocol"] != protocol or row["revoked_at"] is not None or row["session_revoked"] is not None
                or not row["is_active"] or row["expires_at"] <= current
                or row["session_expires"] <= current):
            raise AuthError("invalid_media_token")
        return min(row["expires_at"], row["session_expires"])


# HTTP surface is mounted by the FastAPI application.
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class BootstrapRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=1024)
    tenant_name: str = Field(min_length=1, max_length=120)
    tenant_slug: str = Field(min_length=2, max_length=80)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=1024)
    tenant_slug: str = Field(min_length=2, max_length=80)


class CreateMemberRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=1024)
    role: str


def _auth_path(request: Request) -> str:
    return str(request.app.state.auth_database_path)


def _auth_http_error(exc: AuthError) -> HTTPException:
    status_code = 403 if exc.code == "forbidden" else 401
    if exc.code in {"bootstrap_already_used", "bootstrap_conflict", "member_conflict"}:
        status_code = 409
    if exc.code == "login_rate_limited":
        status_code = 429
    if exc.code in {"invalid_email", "invalid_tenant", "invalid_role"}:
        status_code = 422
    return HTTPException(status_code=status_code, detail=exc.code)


@router.post("/bootstrap", status_code=201)
def bootstrap_endpoint(payload: BootstrapRequest, request: Request,
                       x_bootstrap_secret: str | None = Header(default=None)) -> dict:
    try:
        tenant_id = bootstrap_admin(
            _auth_path(request),
            configured_secret=request.app.state.bootstrap_secret,
            supplied_secret=x_bootstrap_secret or "",
            email=payload.email, password=payload.password,
            tenant_name=payload.tenant_name, tenant_slug=payload.tenant_slug,
        )
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    return {"tenant_id": tenant_id, "status": "created", "next_step": "Sign in with the manager account."}


@router.post("/login")
def login_endpoint(payload: LoginRequest, request: Request) -> dict:
    try:
        token, expires_at = login(
            _auth_path(request), email=payload.email, password=payload.password,
            tenant_slug=payload.tenant_slug,
        )
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at}


@router.get("/me")
def me_endpoint(request: Request) -> dict:
    principal = request.state.principal
    return {"user_id": principal.user_id, "tenant_id": principal.tenant_id,
            "email": principal.email, "role": principal.role}


@router.post("/logout")
def logout_endpoint(request: Request) -> dict:
    token = request.state.bearer_token
    logout(_auth_path(request), token)
    return {"status": "logged_out"}


@router.post("/users", status_code=201)
def create_member_endpoint(payload: CreateMemberRequest, request: Request) -> dict:
    try:
        user_id = create_member(
            _auth_path(request), request.state.principal,
            email=payload.email, password=payload.password, role=payload.role,
        )
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    return {"user_id": user_id, "role": payload.role, "status": "created"}
