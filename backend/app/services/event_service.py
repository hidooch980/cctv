import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.event import Event
from app.schemas.event import EventCreate


class EventService:
    @staticmethod
    async def create_event(db: AsyncSession, event_in: EventCreate) -> Event:
        event = Event(
            camera_id=event_in.camera_id,
            event_type=event_in.event_type,
            severity=event_in.severity,
            confidence=event_in.confidence,
            title=event_in.title,
            description=event_in.description,
            metadata_json=event_in.metadata_json,
            snapshot_path=event_in.snapshot_path,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_recent_events(
        db: AsyncSession,
        limit: int = 50,
        camera_id: Optional[int] = None,
        event_type: Optional[str] = None,
    ) -> List[Event]:
        query = select(Event).order_by(desc(Event.created_at)).limit(limit)
        if camera_id is not None:
            query = query.filter(Event.camera_id == camera_id)
        if event_type is not None:
            query = query.filter(Event.event_type == event_type)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def acknowledge_event(db: AsyncSession, event_id: int, username: str) -> Optional[Event]:
        result = await db.execute(select(Event).filter(Event.id == event_id))
        event = result.scalars().first()
        if not event:
            return None
        event.acknowledged = True
        event.acknowledged_by = username
        await db.commit()
        await db.refresh(event)
        return event
