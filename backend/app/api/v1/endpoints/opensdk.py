from typing import List, Dict, Any
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.opensdk_errors import (
    resolve_opensdk_error,
    ErrorResolution,
    OPENSDK_ERROR_CATALOG,
)

router = APIRouter()


class DiagnoseRequest(BaseModel):
    error_identifier: str
    camera_id: int | None = None
    context: str | None = None


class BatchDiagnoseResponse(BaseModel):
    diagnoses: List[ErrorResolution]


@router.get("/catalog")
async def get_error_catalog(current_user: User = Depends(get_current_user)):
    """
    Returns the comprehensive OpenSDK error catalog (RTSP, DHHTTP, Decoder, Bluetooth).
    """
    return {
        "total_cataloged": len(OPENSDK_ERROR_CATALOG),
        "errors": OPENSDK_ERROR_CATALOG,
    }


@router.post("/diagnose", response_model=ErrorResolution)
async def diagnose_error(
    request: DiagnoseRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Diagnose an OpenSDK status or error code and provide immediate bilingual
    recovery instructions and automated strategy.
    """
    resolution = resolve_opensdk_error(request.error_identifier)
    return resolution
