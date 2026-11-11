from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    camera_id: int
    event_type: str = Field(..., description="person, vehicle, motion, line_crossing, tampering, sdk_error")
    severity: Optional[str] = "info"  # info, warning, alert, critical
    confidence: Optional[float] = 0.90
    title: str
    description: Optional[str] = None
    metadata_json: Optional[str] = None
    snapshot_path: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: int
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
