from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.config import settings
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.camera import Camera
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    PTZCommand,
    DiscoveredDevice,
)
from app.services.camera_service import CameraService

router = APIRouter()


@router.get("", response_model=List[CameraResponse])
async def list_cameras(
    group: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Camera).order_by(Camera.id)
    if group:
        query = query.filter(Camera.group_name == group)
    if status:
        query = query.filter(Camera.status == status)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_in: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Enforce initial capacity limit (100 cameras)
    count_res = await db.execute(select(func.count(Camera.id)))
    current_count = count_res.scalar() or 0
    if current_count >= settings.MAX_CAMERAS_CAPACITY:
        raise HTTPException(
            status_code=400,
            detail=f"Camera capacity limit reached ({settings.MAX_CAMERAS_CAPACITY} max). Upgrade license or scale cluster.",
        )

    # Sanitize / construct default RTSP URL if omitted
    rtsp = camera_in.rtsp_url
    if not rtsp and camera_in.device_ip:
        user = camera_in.device_username or "admin"
        pwd = camera_in.device_password or "admin"
        rtsp = f"rtsp://{user}:{pwd}@{camera_in.device_ip}:{camera_in.device_port or 554}/cam/realmonitor?channel={camera_in.channel_id + 1}&subtype=0"

    camera_data = camera_in.model_dump()
    camera_data["rtsp_url"] = rtsp

    camera = Camera(**camera_data)
    db.add(camera)
    await db.commit()
    await db.refresh(camera)
    return camera


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera).filter(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return camera


@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_in: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera).filter(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    update_data = camera_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(camera, field, val)

    await db.commit()
    await db.refresh(camera)
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera).filter(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    await db.delete(camera)
    await db.commit()
    return None


@router.get("/{camera_id}/stream")
async def get_camera_stream_info(
    camera_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera).filter(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # Return stream endpoints (WebRTC, HLS, RTSP proxy)
    return {
        "camera_id": camera.id,
        "name": camera.name,
        "status": camera.status,
        "webrtc_url": f"/api/v1/streams/webrtc/{camera.id}",
        "hls_url": f"/api/v1/streams/hls/{camera.id}/index.m3u8",
        "rtsp_sanitized": CameraService.sanitize_rtsp_url(camera.rtsp_url),
        "fps": camera.fps,
        "resolution": camera.resolution,
    }


@router.post("/{camera_id}/ptz")
async def control_ptz(
    camera_id: int,
    command: PTZCommand,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Camera).filter(Camera.id == camera_id))
    camera = result.scalars().first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not camera.ptz_supported:
        raise HTTPException(status_code=400, detail="PTZ is not supported on this camera")

    try:
        return CameraService.execute_ptz(camera_id, command)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/discover", response_model=List[DiscoveredDevice])
async def discover_devices(
    current_user: User = Depends(get_current_user),
):
    """
    Scan local network for ONVIF and Dahua / OpenSDK compatible cameras.
    """
    devices = await CameraService.discover_local_cameras()
    return devices
