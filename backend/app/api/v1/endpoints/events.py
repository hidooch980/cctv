from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.event import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter()


@router.get("", response_model=List[EventResponse])
async def list_events(
    camera_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = await EventService.get_recent_events(
        db=db, limit=limit, camera_id=camera_id, event_type=event_type
    )
    return events


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_in: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = await EventService.create_event(db=db, event_in=event_in)
    return event


@router.post("/{event_id}/acknowledge", response_model=EventResponse)
async def acknowledge_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = await EventService.acknowledge_event(
        db=db, event_id=event_id, username=current_user.username
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
