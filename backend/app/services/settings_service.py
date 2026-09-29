from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate


class SettingsService:
    """Service to handle user preferences, notification rules, and WhatsApp configurations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.settings_col = db["user_preferences"]

    async def get_user_settings(self, user_id: str) -> UserSettingsResponse:
        """Fetch settings for a user or return default settings if none exist yet."""
        doc = await self.settings_col.find_one({"user_id": user_id})
        if not doc:
            # Default settings
            return UserSettingsResponse(
                user_id=user_id,
                whatsapp_phone_number=None,
                whatsapp_notifications_enabled=True,
                minimum_importance_threshold=80,
                enabled_categories=[
                    "INTERVIEW",
                    "ASSESSMENT",
                    "JOB_APPLICATION",
                    "RECRUITER",
                    "OFFER",
                    "MEETING",
                    "SECURITY",
                    "FINANCE",
                ],
                auto_notify_on_sync=True,
            )

        return UserSettingsResponse(
            user_id=user_id,
            whatsapp_phone_number=doc.get("whatsapp_phone_number"),
            whatsapp_notifications_enabled=doc.get("whatsapp_notifications_enabled", True),
            minimum_importance_threshold=doc.get("minimum_importance_threshold", 80),
            enabled_categories=doc.get("enabled_categories", [
                "INTERVIEW",
                "ASSESSMENT",
                "JOB_APPLICATION",
                "RECRUITER",
                "OFFER",
                "MEETING",
                "SECURITY",
                "FINANCE",
            ]),
            auto_notify_on_sync=doc.get("auto_notify_on_sync", True),
        )

    async def update_user_settings(
        self,
        user_id: str,
        update_data: UserSettingsUpdate,
    ) -> UserSettingsResponse:
        """Update or insert settings for a user."""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc)

        await self.settings_col.update_one(
            {"user_id": user_id},
            {"$set": update_dict},
            upsert=True,
        )

        return await self.get_user_settings(user_id)
