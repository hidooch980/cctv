from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Iterator
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOLIDO_CCTV_", extra="ignore")
    app_name: str = "Molido CCTV AI"
    environment: str = "development"
    database_path: str = "data/cameras.db"


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.2.0", docs_url="/api/docs")


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


def database_path() -> Path:
    configured = Path(app.state.database_path)
    configured.parent.mkdir(parents=True, exist_ok=True)
    return configured


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(database_path(), timeout=10)
    connection.row_factory = sqlite3.Row
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


def row_to_camera(row: sqlite3.Row) -> CameraRead:
    return CameraRead(
        id=UUID(row["id"]), name=row["name"], brand=row["brand"],
        model=row["model"], protocol=row["protocol"], host=row["host"],
        port=row["port"], location=row["location"], status=row["status"],
    )


app.state.database_path = os.getenv("MOLIDO_CCTV_DATABASE_PATH", settings.database_path)
init_database()


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
