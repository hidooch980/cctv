from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class CapacityInfo(BaseModel):
    max_cameras: int
    active_cameras: int
    offline_cameras: int
    error_cameras: int
    utilization_percentage: float


class StorageInfo(BaseModel):
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percentage: float
    retention_days: int


class NetworkInfo(BaseModel):
    total_inbound_mbps: float
    total_outbound_mbps: float
    active_sessions: int


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    capacity: CapacityInfo
    storage: StorageInfo
    network: NetworkInfo
    supported_vendors: List[str]
    ai_engine_status: str
