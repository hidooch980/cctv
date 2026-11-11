from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CameraBase(BaseModel):
    name: str = Field(..., max_length=100)
    location: Optional[str] = "Main Site"
    group_name: Optional[str] = "General"
    vendor: Optional[str] = "Generic"
    stream_type: Optional[str] = "rtsp"  # rtsp, onvif, opensdk, webrtc, hls
    rtsp_url: Optional[str] = None
    substream_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    
    device_ip: Optional[str] = None
    device_port: Optional[int] = 80
    device_username: Optional[str] = None
    device_serial: Optional[str] = None
    channel_id: Optional[int] = 0
    
    resolution: Optional[str] = "1920x1080"
    fps: Optional[int] = 25
    bitrate_kbps: Optional[int] = 2048
    codec: Optional[str] = "H.264"
    
    ptz_supported: Optional[bool] = False
    audio_supported: Optional[bool] = False
    ai_enabled: Optional[bool] = True
    recording_mode: Optional[str] = "motion"


class CameraCreate(CameraBase):
    device_password: Optional[str] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    group_name: Optional[str] = None
    vendor: Optional[str] = None
    stream_type: Optional[str] = None
    rtsp_url: Optional[str] = None
    substream_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    device_ip: Optional[str] = None
    device_port: Optional[int] = None
    device_username: Optional[str] = None
    device_password: Optional[str] = None
    device_serial: Optional[str] = None
    channel_id: Optional[int] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    bitrate_kbps: Optional[int] = None
    codec: Optional[str] = None
    ptz_supported: Optional[bool] = None
    audio_supported: Optional[bool] = None
    ai_enabled: Optional[bool] = None
    recording_mode: Optional[str] = None


class CameraResponse(CameraBase):
    id: int
    status: str
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PTZCommand(BaseModel):
    action: str = Field(..., description="pan_left, pan_right, tilt_up, tilt_down, zoom_in, zoom_out, stop")
    speed: float = Field(0.5, ge=0.1, le=1.0)


class DiscoveredDevice(BaseModel):
    ip: str
    port: int
    manufacturer: str
    model: Optional[str] = "IP-Camera"
    firmware_version: Optional[str] = "1.0"
    mac_address: Optional[str] = None
    onvif_uri: Optional[str] = None
    supports_ptz: bool = False
