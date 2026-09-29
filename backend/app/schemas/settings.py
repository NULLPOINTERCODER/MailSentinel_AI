from enum import Enum
from pydantic import BaseModel, Field


class EmailCategorySetting(str, Enum):
    INTERVIEW = "INTERVIEW"
    ASSESSMENT = "ASSESSMENT"
    JOB_APPLICATION = "JOB_APPLICATION"
    RECRUITER = "RECRUITER"
    OFFER = "OFFER"
    MEETING = "MEETING"
    COLLEGE = "COLLEGE"
    FINANCE = "FINANCE"
    SECURITY = "SECURITY"
    PERSONAL = "PERSONAL"
    NEWSLETTER = "NEWSLETTER"
    PROMOTION = "PROMOTION"
    SPAM = "SPAM"
    GENERAL = "GENERAL"


class UserSettingsBase(BaseModel):
    whatsapp_phone_number: str | None = Field(
        default=None,
        description="E.164 formatted international phone number, e.g. +919876543210",
    )
    whatsapp_notifications_enabled: bool = Field(
        default=True,
        description="Master toggle for sending WhatsApp alert messages",
    )
    minimum_importance_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Only emails with final importance >= this score trigger WhatsApp notifications",
    )
    enabled_categories: list[str] = Field(
        default=[
            "INTERVIEW",
            "ASSESSMENT",
            "JOB_APPLICATION",
            "RECRUITER",
            "OFFER",
            "MEETING",
            "SECURITY",
            "FINANCE",
        ],
        description="List of email categories permitted to send WhatsApp alerts",
    )
    auto_notify_on_sync: bool = Field(
        default=True,
        description="Automatically send WhatsApp alert as soon as an important email is triaged",
    )


class UserSettingsUpdate(BaseModel):
    whatsapp_phone_number: str | None = None
    whatsapp_notifications_enabled: bool | None = None
    minimum_importance_threshold: int | None = Field(default=None, ge=0, le=100)
    enabled_categories: list[str] | None = None
    auto_notify_on_sync: bool | None = None


class UserSettingsResponse(UserSettingsBase):
    user_id: str
