from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.camera import Camera
from app.models.event import Event
from app.api.v1.api import api_router


async def seed_initial_data():
    """Seed initial admin and realistic sample cameras for demo & testing."""
    async with AsyncSessionLocal() as db:
        # Check admin
        admin_res = await db.execute(
            select(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME)
        )
        if not admin_res.scalars().first():
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin)

        # Check cameras
        cam_res = await db.execute(select(Camera))
        if not cam_res.scalars().first():
            cams = [
                Camera(
                    name="Main Gate - Entrance 01",
                    location="Perimeter North",
                    group_name="Entrance",
                    vendor="Dahua / Lechange",
                    stream_type="rtsp",
                    rtsp_url="rtsp://admin:Demo1234@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0",
                    device_ip="192.168.1.101",
                    device_port=554,
                    device_serial="DH4K9921008123",
                    status="online",
                    resolution="1920x1080",
                    fps=25,
                    bitrate_kbps=2500,
                    ptz_supported=False,
                    ai_enabled=True,
                    recording_mode="continuous",
                ),
                Camera(
                    name="Lobby & Reception",
                    location="Building A Ground Floor",
                    group_name="Indoor",
                    vendor="Hikvision",
                    stream_type="rtsp",
                    rtsp_url="rtsp://admin:Demo1234@192.168.1.102:554/Streaming/Channels/101",
                    device_ip="192.168.1.102",
                    device_port=554,
                    status="online",
                    resolution="2560x1440",
                    fps=30,
                    bitrate_kbps=3500,
                    ptz_supported=False,
                    ai_enabled=True,
                    recording_mode="motion",
                ),
                Camera(
                    name="Parking Lot West PTZ",
                    location="Outdoor West Lot",
                    group_name="Perimeter",
                    vendor="Dahua PTZ",
                    stream_type="rtsp",
                    rtsp_url="rtsp://admin:Demo1234@192.168.1.105:554/cam/realmonitor?channel=1&subtype=0",
                    device_ip="192.168.1.105",
                    device_port=554,
                    status="online",
                    resolution="1920x1080",
                    fps=30,
                    bitrate_kbps=3000,
                    ptz_supported=True,
                    ai_enabled=True,
                    recording_mode="continuous",
                ),
                Camera(
                    name="Server Room Access",
                    location="Secure Zone Basement",
                    group_name="Critical",
                    vendor="Uniview",
                    stream_type="rtsp",
                    rtsp_url="rtsp://admin:Demo1234@192.168.1.103:554/unicast/c1/s0/live",
                    device_ip="192.168.1.103",
                    device_port=554,
                    status="online",
                    resolution="1920x1080",
                    fps=25,
                    bitrate_kbps=2000,
                    ptz_supported=False,
                    ai_enabled=True,
                    recording_mode="motion",
                ),
            ]
            db.add_all(cams)
            await db.flush()

            # Seed sample AI events
            events = [
                Event(
                    camera_id=1,
                    event_type="vehicle",
                    severity="info",
                    confidence=0.96,
                    title="Vehicle Detected at Entrance",
                    description="White sedan entered license detection zone.",
                    metadata_json='{"class": "vehicle", "plate": "68-B-129-21", "color": "white"}',
                ),
                Event(
                    camera_id=2,
                    event_type="person",
                    severity="info",
                    confidence=0.94,
                    title="Person Detected in Lobby",
                    description="Pedestrian entered main reception foyer.",
                    metadata_json='{"class": "person", "box": [120, 80, 240, 480]}',
                ),
                Event(
                    camera_id=4,
                    event_type="line_crossing",
                    severity="warning",
                    confidence=0.98,
                    title="Perimeter Line Crossed - Server Room",
                    description="Virtual tripwire line crossed outside working hours.",
                    metadata_json='{"zone": "server_entry_tripwire"}',
                ),
            ]
            db.add_all(events)

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    await init_db()
    await seed_initial_data()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Multi-brand CCTV & AI Video Management Platform API",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "molido-cctv-backend", "version": settings.VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }
