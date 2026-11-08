from __future__ import annotations

from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MOLIDO_CCTV_", extra="ignore")
    app_name: str = "Molido CCTV AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/api/docs")


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
    # Credentials are accepted only for future secret-vault integration.
    # They are never returned by the API or written to logs.
    username: str | None = Field(default=None, max_length=120)
    password: SecretStr | None = None

    @field_validator("host")
    @classmethod
    def reject_url_credentials(cls, value: str) -> str:
        if "://" in value or "@" in value:
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
    status: CameraStatus = CameraStatus.pending


class CameraRecord(CameraRead):
    username: str | None = None
    password: SecretStr | None = None


app.state.cameras = {}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@app.get("/api/v1/cameras", response_model=list[CameraRead])
def list_cameras() -> list[CameraRead]:
    return [CameraRead.model_validate(item.model_dump()) for item in app.state.cameras.values()]


@app.post("/api/v1/cameras", response_model=CameraRead, status_code=status.HTTP_201_CREATED)
def create_camera(payload: CameraCreate) -> CameraRead:
    if len(app.state.cameras) >= 100:
        raise HTTPException(status_code=409, detail="Initial camera capacity (100) reached")
    record = CameraRecord(id=uuid4(), **payload.model_dump())
    app.state.cameras[record.id] = record
    return CameraRead.model_validate(record.model_dump())


@app.get("/api/v1/cameras/{camera_id}", response_model=CameraRead)
def get_camera(camera_id: UUID) -> CameraRead:
    record = app.state.cameras.get(camera_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraRead.model_validate(record.model_dump())


@app.delete("/api/v1/cameras/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: UUID) -> None:
    if app.state.cameras.pop(camera_id, None) is None:
        raise HTTPException(status_code=404, detail="Camera not found")
