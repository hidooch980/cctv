from fastapi import APIRouter
from app.api.v1.endpoints import auth, cameras, events, system, opensdk

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["Cameras"])
api_router.include_router(events.router, prefix="/events", tags=["Events & AI Analytics"])
api_router.include_router(system.router, prefix="/system", tags=["System Health & Metrics"])
api_router.include_router(opensdk.router, prefix="/opensdk", tags=["OpenSDK & Diagnostics"])
