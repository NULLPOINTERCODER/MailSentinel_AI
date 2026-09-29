from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_database
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate
from app.schemas.user import UserResponse
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_settings_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> SettingsService:
    return SettingsService(db)


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: UserResponse = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service),
) -> UserSettingsResponse:
    """Retrieve settings and WhatsApp notification preferences for the logged-in user."""
    return await settings_service.get_user_settings(user_id=current_user.id)


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    payload: UserSettingsUpdate,
    current_user: UserResponse = Depends(get_current_user),
    settings_service: SettingsService = Depends(get_settings_service),
) -> UserSettingsResponse:
    """Update settings (e.g. WhatsApp number, importance threshold, enabled categories)."""
    return await settings_service.update_user_settings(
        user_id=current_user.id,
        update_data=payload,
    )
