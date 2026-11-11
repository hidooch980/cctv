from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event Classification
    event_type = Column(String(50), nullable=False, index=True)  # person, vehicle, motion, line_crossing, tampering, sdk_error
    severity = Column(String(20), default="info")  # info, warning, alert, critical
    confidence = Column(Float, default=0.90)  # 0.0 - 1.0
    
    # Details & Payloads
    title = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)  # Bounding box coordinates, plate number, etc.
    snapshot_path = Column(String(255), nullable=True)
    
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
