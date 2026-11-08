from __future__ import annotations

import os
import sqlite3
import ipaddress
from datetime import datetime, timezone
from contextvars import ContextVar
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Iterator
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.adapters import registry
from app.auth import AuthError, init_auth_schema, issue_media_token, resolve_principal, verify_media_token, router as auth_router
from app.streaming import StreamProfile, StreamTransport


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOLIDO_CCTV_", extra="ignore")
    app_name: str = "Molido CCTV AI"
    environment: str = "development"
    database_path: str = "data/cameras.db"


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.3.0", docs_url="/api/docs")
_tenant_database: ContextVar[str | None] = ContextVar("tenant_database", default=None)
app.state.auth_database_path = os.getenv("MOLIDO_CCTV_AUTH_DATABASE_PATH", settings.database_path)
app.state.bootstrap_secret = os.getenv("MOLIDO_CCTV_BOOTSTRAP_SECRET")
app.state.mediamtx_enabled = os.getenv("MOLIDO_CCTV_MEDIAMTX_ENABLED", "false").lower() == "true"
app.state.mediamtx_playback_enabled = os.getenv("MOLIDO_CCTV_MEDIAMTX_PLAYBACK_ENABLED", "false").lower() == "true"
app.state.mediamtx_allowed_cidrs = [
    item.strip() for item in os.getenv("MOLIDO_CCTV_MEDIAMTX_ALLOWED_CIDRS", "").split(",")
    if item.strip()
]


class CameraProtocol(str, Enum):
    onvif = "onvif"
    rtsp = "rtsp"
    vendor_api = "vendor_api"


class CameraStatus(str, Enum):
    pending = "pending"
    online = "online"
    offline = "offline"
    error = "error"


class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    brand: str = Field(min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    protocol: CameraProtocol
    host: str = Field(min_length=1, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    location: str | None = Field(default=None, max_length=255)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        value = value.strip()
        if not value or "://" in value or "@" in value or "/" in value:
            raise ValueError("host must be a hostname or IP address, not a URL")
        return value


class CameraRead(BaseModel):
    id: UUID
    name: str
    brand: str
    model: str | None
    protocol: CameraProtocol
    host: str
    port: int | None
    location: str | None
    status: CameraStatus



class RecorderType(str, Enum):
    dvr = "dvr"
    nvr = "nvr"
    xvr = "xvr"


class RecorderConnectionMethod(str, Enum):
    ip = "ip"
    serial = "serial"
    dahua_p2p = "dahua_p2p"


class RecorderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    brand: str = Field(min_length=1, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    recorder_type: RecorderType
    connection_method: RecorderConnectionMethod
    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    serial_number: str | None = Field(default=None, min_length=3, max_length=128)
    location: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=128, exclude=True)
    password: str | None = Field(default=None, max_length=512, exclude=True)
    pairing_code: str | None = Field(default=None, max_length=256, exclude=True)

    @field_validator("host")
    @classmethod
    def validate_recorder_host(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value or "://" in value or "@" in value or "/" in value:
            raise ValueError("host must be a hostname or IP address, not a URL")
        return value

    @model_validator(mode="after")
    def validate_connection_fields(self):
        if self.connection_method == RecorderConnectionMethod.ip:
            if not self.host or not self.username or not self.password:
                raise ValueError("IP connection requires host, username and password")
        if self.connection_method == RecorderConnectionMethod.serial:
            if not self.serial_number or not (self.username or self.pairing_code):
                raise ValueError("Serial connection requires serial_number and vendor authorization proof")
        if self.connection_method == RecorderConnectionMethod.dahua_p2p:
            if self.brand.strip().lower() != "dahua":
                raise ValueError("dahua_p2p connection is only valid for Dahua recorders")
            if not self.serial_number:
                raise ValueError("Dahua P2P registration requires the recorder serial number")
        return self


class RecorderConnectTest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: SecretStr


class RecorderChannelRead(BaseModel):
    id: UUID
    recorder_id: UUID
    channel_number: int
    name: str
    profile_token: str | None
    stream_uri: str | None
    status: str


class RecorderRead(BaseModel):
    id: UUID
    name: str
    brand: str
    model: str | None
    recorder_type: RecorderType
    connection_method: RecorderConnectionMethod
    host: str | None
    port: int | None
    serial_number: str | None
    location: str | None
    status: str


def database_path() -> Path:
    tenant_path = _tenant_database.get()
    configured = Path(tenant_path or app.state.database_path)
    configured.parent.mkdir(parents=True, exist_ok=True)
    return configured


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(database_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database() -> None:
    with db_connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS cameras (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                model TEXT,
                protocol TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER,
                location TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.execute("CREATE INDEX IF NOT EXISTS idx_cameras_host ON cameras(host)")
        db.execute("""
            CREATE TABLE IF NOT EXISTS recorders (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, brand TEXT NOT NULL,
                model TEXT, recorder_type TEXT NOT NULL, connection_method TEXT NOT NULL,
                host TEXT, port INTEGER, serial_number TEXT, location TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_recorders_host ON recorders(host)")
        db.execute("""
            CREATE TABLE IF NOT EXISTS recorder_channels (
                id TEXT PRIMARY KEY, recorder_id TEXT NOT NULL,
                channel_number INTEGER NOT NULL, name TEXT NOT NULL,
                profile_token TEXT, stream_uri TEXT, status TEXT NOT NULL DEFAULT 'discovered',
                UNIQUE(recorder_id, channel_number),
                FOREIGN KEY(recorder_id) REFERENCES recorders(id) ON DELETE CASCADE
            )
        """)
        db.execute("CREATE INDEX IF NOT EXISTS idx_recorder_channels_recorder ON recorder_channels(recorder_id)")


def row_to_camera(row: sqlite3.Row) -> CameraRead:
    return CameraRead(
        id=UUID(row["id"]), name=row["name"], brand=row["brand"],
        model=row["model"], protocol=row["protocol"], host=row["host"],
        port=row["port"], location=row["location"], status=row["status"],
    )


app.state.database_path = os.getenv("MOLIDO_CCTV_DATABASE_PATH", settings.database_path)
init_database()
init_auth_schema(app.state.auth_database_path)
app.include_router(auth_router)


def tenant_database_path(tenant_id: str) -> str:
    root = Path(app.state.database_path).parent / "tenants"
    return str(root / tenant_id / "cameras.sqlite3")


class MediaMTXAuthRequest(BaseModel):
    user: str = Field(default="", max_length=254)
    password: str = Field(default="", max_length=512)
    token: str = Field(default="", max_length=512)
    ip: str = Field(default="", max_length=64)
    action: str = Field(min_length=1, max_length=32)
    path: str = Field(min_length=1, max_length=512)
    protocol: str = Field(min_length=1, max_length=32)
    id: str = Field(default="", max_length=128)
    query: str = Field(default="", max_length=2048)
    userAgent: str = Field(default="", max_length=512)


@app.post("/api/v1/media/mediamtx/auth", include_in_schema=False)
def mediamtx_external_auth(payload: MediaMTXAuthRequest, request: Request):
    """MediaMTX external HTTP auth callback; private-network-only and deny by default."""
    if not app.state.mediamtx_enabled or not app.state.mediamtx_allowed_cidrs:
        raise HTTPException(status_code=503, detail="MediaMTX external authentication is not enabled")
    remote = request.client.host if request.client else ""
    try:
        remote_ip = ipaddress.ip_address(remote)
        allowed = any(remote_ip in ipaddress.ip_network(cidr, strict=False)
                      for cidr in app.state.mediamtx_allowed_cidrs)
    except ValueError:
        allowed = False
    if not allowed:
        raise HTTPException(status_code=403, detail="MediaMTX callback source is not trusted")
    credential = payload.token or payload.password
    if not credential:
        raise HTTPException(status_code=401, detail="MediaMTX credentials required")
    try:
        expires_at = verify_media_token(
            app.state.auth_database_path, token=credential,
            media_path=payload.path, action=payload.action,
            protocol=payload.protocol,
        )
    except AuthError:
        raise HTTPException(status_code=401, detail="MediaMTX authorization denied")
    return {"expireAt": datetime.fromtimestamp(expires_at, timezone.utc).isoformat().replace("+00:00", "Z")}


@app.middleware("http")
async def authenticate_and_isolate_tenant(request: Request, call_next):
    path = request.url.path
    public_paths = {
        "/api/health", "/api/v1/auth/bootstrap", "/api/v1/auth/login",
        "/api/v1/media/mediamtx/auth",
    }
    if path in public_paths or not path.startswith("/api/v1/"):
        return await call_next(request)

    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return JSONResponse(status_code=401, content={"detail": "authentication_required"})
    try:
        principal = resolve_principal(
            app.state.auth_database_path, token,
            tenant_id=request.headers.get("x-tenant-id"),
        )
    except AuthError:
        return JSONResponse(status_code=401, content={"detail": "invalid_or_expired_session"})

    if path == "/api/v1/auth/logout":
        pass
    elif path == "/api/v1/auth/users":
        if not principal.allows("user:manage"):
            return JSONResponse(status_code=403, content={"detail": "forbidden"})
    elif principal.role == "viewer" and request.method not in {"GET", "HEAD", "OPTIONS"}:
        return JSONResponse(status_code=403, content={"detail": "read_only_role"})

    request.state.principal = principal
    request.state.bearer_token = token
    context_token = _tenant_database.set(tenant_database_path(principal.tenant_id))
    try:
        init_database()
        return await call_next(request)
    finally:
        _tenant_database.reset(context_token)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/api/v1/cameras", response_model=list[CameraRead])
def list_cameras() -> list[CameraRead]:
    with db_connection() as db:
        rows = db.execute(
            "SELECT id,name,brand,model,protocol,host,port,location,status FROM cameras ORDER BY created_at,id"
        ).fetchall()
    return [row_to_camera(row) for row in rows]


@app.post("/api/v1/cameras", response_model=CameraRead, status_code=status.HTTP_201_CREATED)
def create_camera(payload: CameraCreate) -> CameraRead:
    with db_connection() as db:
        count = db.execute("SELECT COUNT(*) FROM cameras").fetchone()[0]
        if count >= 100:
            raise HTTPException(status_code=409, detail="Initial camera capacity (100) reached")
        camera_id = uuid4()
        values = payload.model_dump()
        db.execute(
            """INSERT INTO cameras (id,name,brand,model,protocol,host,port,location,status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (str(camera_id), values["name"], values["brand"], values["model"],
             values["protocol"].value, values["host"], values["port"],
             values["location"], CameraStatus.pending.value),
        )
        row = db.execute(
            "SELECT id,name,brand,model,protocol,host,port,location,status FROM cameras WHERE id=?",
            (str(camera_id),),
        ).fetchone()
    return row_to_camera(row)


@app.get("/api/v1/cameras/{camera_id}", response_model=CameraRead)
def get_camera(camera_id: UUID) -> CameraRead:
    with db_connection() as db:
        row = db.execute(
            "SELECT id,name,brand,model,protocol,host,port,location,status FROM cameras WHERE id=?",
            (str(camera_id),),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return row_to_camera(row)


@app.delete("/api/v1/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: UUID) -> None:
    with db_connection() as db:
        cursor = db.execute("DELETE FROM cameras WHERE id=?", (str(camera_id),))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Camera not found")



def row_to_recorder(row: sqlite3.Row) -> RecorderRead:
    return RecorderRead(
        id=UUID(row["id"]), name=row["name"], brand=row["brand"],
        model=row["model"], recorder_type=row["recorder_type"],
        connection_method=row["connection_method"], host=row["host"],
        port=row["port"], serial_number=row["serial_number"],
        location=row["location"], status=row["status"],
    )


@app.get("/api/v1/recorders", response_model=list[RecorderRead])
def list_recorders() -> list[RecorderRead]:
    with db_connection() as db:
        rows = db.execute(
            "SELECT id,name,brand,model,recorder_type,connection_method,host,port,serial_number,location,status FROM recorders ORDER BY created_at,id"
        ).fetchall()
    return [row_to_recorder(row) for row in rows]


@app.post("/api/v1/recorders", response_model=RecorderRead, status_code=status.HTTP_201_CREATED)
def create_recorder(payload: RecorderCreate) -> RecorderRead:
    with db_connection() as db:
        count = db.execute("SELECT COUNT(*) FROM recorders").fetchone()[0]
        if count >= 100:
            raise HTTPException(status_code=409, detail="Initial recorder capacity (100) reached")
        recorder_id = uuid4()
        db.execute(
            """INSERT INTO recorders
               (id,name,brand,model,recorder_type,connection_method,host,port,serial_number,location,status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (str(recorder_id), payload.name, payload.brand, payload.model,
             payload.recorder_type.value, payload.connection_method.value,
             payload.host, payload.port, payload.serial_number, payload.location, "pending"),
        )
        row = db.execute(
            "SELECT id,name,brand,model,recorder_type,connection_method,host,port,serial_number,location,status FROM recorders WHERE id=?",
            (str(recorder_id),),
        ).fetchone()
    return row_to_recorder(row)


@app.get("/api/v1/recorders/{recorder_id}", response_model=RecorderRead)
def get_recorder(recorder_id: UUID) -> RecorderRead:
    with db_connection() as db:
        row = db.execute(
            "SELECT id,name,brand,model,recorder_type,connection_method,host,port,serial_number,location,status FROM recorders WHERE id=?",
            (str(recorder_id),),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Recorder not found")
    return row_to_recorder(row)


@app.delete("/api/v1/recorders/{recorder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recorder(recorder_id: UUID) -> None:
    with db_connection() as db:
        cursor = db.execute("DELETE FROM recorders WHERE id=?", (str(recorder_id),))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Recorder not found")



@app.post("/api/v1/recorders/{recorder_id}/connect-test")
async def test_recorder_connection(recorder_id: UUID, credentials: RecorderConnectTest) -> dict:
    with db_connection() as db:
        recorder = db.execute(
            "SELECT id,brand,connection_method,host,port FROM recorders WHERE id=?",
            (str(recorder_id),),
        ).fetchone()
    if recorder is None:
        raise HTTPException(status_code=404, detail="Recorder not found")
    if recorder["connection_method"] != "ip" or not recorder["host"]:
        raise HTTPException(
            status_code=501,
            detail="Serial/P2P connection requires the manufacturer's authorized SDK or cloud/P2P credentials; this adapter is not configured.",
        )
    result = await registry.discover(
        host=recorder["host"], port=recorder["port"], brand=recorder["brand"],
        username=credentials.username, password=credentials.password.get_secret_value(),
    )
    with db_connection() as db:
        db.execute("DELETE FROM recorder_channels WHERE recorder_id=?", (str(recorder_id),))
        for channel in result.channels:
            db.execute(
                """INSERT INTO recorder_channels
                   (id,recorder_id,channel_number,name,profile_token,stream_uri,status)
                   VALUES (?,?,?,?,?,?,?)""",
                (str(uuid4()), str(recorder_id), channel["channel_number"], channel["name"],
                 channel.get("profile_token"), channel.get("stream_uri"), channel.get("status", "discovered")),
            )
        db.execute(
            "UPDATE recorders SET status=? WHERE id=?",
            ("online" if result.reachable else "offline", str(recorder_id)),
        )
    return {
        "reachable": result.reachable,
        "adapter": result.adapter,
        "manufacturer": result.manufacturer,
        "model": result.model,
        "channel_count": len(result.channels),
        "channels": [{k: v for k, v in channel.items() if k != "stream_uri"} for channel in result.channels],
        "capabilities": result.capabilities,
        "warnings": result.warnings,
        "credentials_persisted": False,
    }


@app.get("/api/v1/recorders/{recorder_id}/p2p-status")
def dahua_p2p_status(recorder_id: UUID) -> dict:
    """Report official-cloud readiness without probing private Dahua protocols."""
    with db_connection() as db:
        recorder = db.execute(
            "SELECT connection_method,serial_number FROM recorders WHERE id=?",
            (str(recorder_id),),
        ).fetchone()
    if recorder is None:
        raise HTTPException(status_code=404, detail="Recorder not found")
    if recorder["connection_method"] != RecorderConnectionMethod.dahua_p2p.value:
        raise HTTPException(status_code=409, detail="Recorder is not registered in Dahua P2P mode")
    return {
        "vendor": "Dahua",
        "connection_mode": "official_p2p_cloud",
        "serial_number_registered": bool(recorder["serial_number"]),
        "integration_state": "not_configured",
        "device_state": "unknown",
        "online": False,
        "sdk_connected": False,
        "cloud_video": False,
        "next_step": "Configure an officially authorized Dahua third-party P2P SDK/API or partner interface. DoLynk is a separate optional enterprise path, not a prerequisite for DMSS-compatible consumer P2P.",
        "credentials_persisted": False,
    }


@app.post("/api/v1/recorders/{recorder_id}/p2p-connect-test")
def dahua_p2p_connect_test(recorder_id: UUID, payload: RecorderConnectTest) -> dict:
    with db_connection() as db:
        recorder = db.execute(
            "SELECT connection_method FROM recorders WHERE id=?",
            (str(recorder_id),),
        ).fetchone()
    if recorder is None:
        raise HTTPException(status_code=404, detail="Recorder not found")
    if recorder["connection_method"] != RecorderConnectionMethod.dahua_p2p.value:
        raise HTTPException(status_code=409, detail="Recorder is not registered in Dahua P2P mode")
    raise HTTPException(
        status_code=501,
        detail="An officially authorized Dahua DMSS-compatible third-party P2P SDK/API adapter is not configured. No cloud connection was attempted; submitted credentials were not persisted.",
    )


@app.get("/api/v1/recorders/{recorder_id}/channels", response_model=list[RecorderChannelRead])
def list_recorder_channels(recorder_id: UUID) -> list[RecorderChannelRead]:
    with db_connection() as db:
        exists = db.execute("SELECT 1 FROM recorders WHERE id=?", (str(recorder_id),)).fetchone()
        if exists is None:
            raise HTTPException(status_code=404, detail="Recorder not found")
        rows = db.execute(
            "SELECT id,recorder_id,channel_number,name,profile_token,stream_uri,status FROM recorder_channels WHERE recorder_id=? ORDER BY channel_number",
            (str(recorder_id),),
        ).fetchall()
    return [
        RecorderChannelRead(
            id=UUID(row["id"]), recorder_id=UUID(row["recorder_id"]),
            channel_number=row["channel_number"], name=row["name"],
            profile_token=row["profile_token"], stream_uri=row["stream_uri"], status=row["status"],
        )
        for row in rows
    ]



class StreamStartRequest(BaseModel):
    transport: StreamTransport = StreamTransport.webrtc
    profile: StreamProfile = StreamProfile.sub
    session_ttl_seconds: int = Field(default=300, ge=60, le=3600)


@app.get("/api/v1/streaming/capabilities")
def streaming_capabilities() -> dict:
    """Expose the honest media-plane state; no live provider is configured yet."""
    return {
        "control_plane": "available",
        "media_provider": "disabled",
        "external_auth_callback": "enabled" if app.state.mediamtx_enabled and bool(app.state.mediamtx_allowed_cidrs) else "disabled",
        "playback_token_issuance": app.state.mediamtx_playback_enabled and bool(app.state.mediamtx_allowed_cidrs),
        "live_view": False,
        "transports": [],
        "profiles": [profile.value for profile in StreamProfile],
        "session_ttl_seconds": {"minimum": 60, "maximum": 3600},
        "authorization": "production user/site authorization is a required deployment gate",
        "next_step": "Deploy and configure an authenticated media gateway and site connector.",
    }


@app.post("/api/v1/recorders/{recorder_id}/channels/{channel_id}/playback-token")
def issue_playback_token(
    recorder_id: UUID, channel_id: UUID, payload: StreamStartRequest, request: Request
) -> dict:
    """Issue a path-scoped short-lived token only after an operator enables the media plane."""
    principal = request.state.principal
    if not principal.allows("stream:view"):
        raise HTTPException(status_code=403, detail="stream_view_forbidden")
    if not app.state.mediamtx_enabled or not app.state.mediamtx_playback_enabled or not app.state.mediamtx_allowed_cidrs:
        raise HTTPException(status_code=503, detail="MediaMTX playback token issuance is disabled until the private gateway is deployed and allowlisted.")
    with db_connection() as db:
        channel = db.execute(
            """SELECT c.id,c.recorder_id,c.stream_uri,c.status,r.connection_method
               FROM recorder_channels c JOIN recorders r ON r.id=c.recorder_id
               WHERE c.id=? AND c.recorder_id=?""",
            (str(channel_id), str(recorder_id)),
        ).fetchone()
    if channel is None:
        raise HTTPException(status_code=404, detail="Recorder channel not found")
    if channel["connection_method"] == RecorderConnectionMethod.dahua_p2p.value:
        raise HTTPException(status_code=501, detail="Dahua P2P playback requires the officially authorized Dahua adapter.")
    if not channel["stream_uri"] or channel["status"] not in {"discovered", "online"}:
        raise HTTPException(status_code=409, detail="Channel has no validated, available RTSP stream.")
    media_path = f"tenant/{principal.tenant_id}/recorder/{recorder_id}/channel/{channel_id}/{payload.profile.value}"
    try:
        token, expires_at = issue_media_token(
            app.state.auth_database_path, principal, media_path=media_path,
            ttl_seconds=min(payload.session_ttl_seconds, 900),
        )
    except AuthError as exc:
        status_code = 403 if exc.code == "forbidden" else 401
        raise HTTPException(status_code=status_code, detail=exc.code) from exc
    return {
        "media_path": media_path,
        "token": token,
        "token_type": "bearer",
        "transport": payload.transport.value,
        "profile": payload.profile.value,
        "expires_at": expires_at,
        "gateway_configured": False,
        "playback_url": None,
        "note": "Token only. The gateway path/source and client playback URL must be configured before video can play.",
    }


@app.post("/api/v1/recorders/{recorder_id}/channels/{channel_id}/stream-sessions")
async def start_stream_session(
    recorder_id: UUID, channel_id: UUID, payload: StreamStartRequest
) -> dict:
    """Validate inventory references, then fail closed until auth and media provider exist."""
    with db_connection() as db:
        channel = db.execute(
            """SELECT c.id,c.recorder_id,c.stream_uri,r.connection_method
               FROM recorder_channels c JOIN recorders r ON r.id=c.recorder_id
               WHERE c.id=? AND c.recorder_id=?""",
            (str(channel_id), str(recorder_id)),
        ).fetchone()
    if channel is None:
        raise HTTPException(status_code=404, detail="Recorder channel not found")
    if channel["connection_method"] == RecorderConnectionMethod.dahua_p2p.value:
        raise HTTPException(
            status_code=501,
            detail="Dahua P2P channel streaming requires the officially authorized Dahua cloud adapter.",
        )
    if not channel["stream_uri"]:
        raise HTTPException(
            status_code=409,
            detail="No validated RTSP ingest URI is available for this channel. Run device discovery first.",
        )
    # Fail closed before constructing a session: production tenant/user authorization
    # and an authenticated media provider are not implemented yet.
    raise HTTPException(
        status_code=503,
        detail=(
            "Streaming is disabled until production user/site authorization and an "
            "authenticated media provider are configured. No production session was "
            "issued; no stream is active."
        ),
    )
