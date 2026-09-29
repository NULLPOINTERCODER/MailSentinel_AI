from fastapi import APIRouter

from app.core.config import get_settings
from app.core.database import ping_mongo

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": get_settings().app_name}


@router.get("/health/db")
async def health_db() -> dict[str, str]:
    connected = await ping_mongo()
    return {"status": "ok" if connected else "unavailable", "database": "mongodb"}
