from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.core.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    location = Column(String(100), default="Main Site")
    group_name = Column(String(50), default="General", index=True)
    vendor = Column(String(50), default="Generic")  # ONVIF, Dahua, Hikvision, Imou, Uniview, Axis, etc.
    
    # Connection details
    stream_type = Column(String(20), default="rtsp")  # rtsp, onvif, opensdk, webrtc, hls
    rtsp_url = Column(String(255), nullable=True)
    substream_url = Column(String(255), nullable=True)
    snapshot_url = Column(String(255), nullable=True)
    
    # ONVIF / OpenSDK parameters
    device_ip = Column(String(50), nullable=True)
    device_port = Column(Integer, default=80)
    device_username = Column(String(50), nullable=True)
    device_password = Column(String(100), nullable=True)  # In production, use encrypted storage
    device_serial = Column(String(100), nullable=True)     # For OpenSDK / P2P
    channel_id = Column(Integer, default=0)
    
    # Operational status
    status = Column(String(20), default="online")  # online, offline, error, connecting
    last_error_code = Column(String(50), nullable=True)
    last_error_message = Column(String(255), nullable=True)
    
    # Stream Specs
    resolution = Column(String(20), default="1920x1080")
    fps = Column(Integer, default=25)
    bitrate_kbps = Column(Integer, default=2048)
    codec = Column(String(20), default="H.264")  # H.264, H.265
    
    # Capabilities & Settings
    ptz_supported = Column(Boolean, default=False)
    audio_supported = Column(Boolean, default=False)
    ai_enabled = Column(Boolean, default=True)
    recording_mode = Column(String(20), default="motion")  # continuous, motion, event, none
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
