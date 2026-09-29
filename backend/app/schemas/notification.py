from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class NotificationStatus(str, Enum):
    SENT = "SENT"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    DUPLICATE = "DUPLICATE"


class NotificationChannel(str, Enum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    email_id: str | None = None
    message_id: str | None = None
    channel: NotificationChannel = NotificationChannel.WHATSAPP
    recipient: str
    subject: str | None = None
    sender: str | None = None
    importance: int | None = None
    category: str | None = None
    message_body: str
    status: NotificationStatus
    provider_response_id: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int


class SendNotificationRequest(BaseModel):
    email_id: str
    force_resend: bool = Field(
        default=False,
        description="Override duplicate detection and send notification again",
    )


class TestWhatsAppRequest(BaseModel):
    phone_number: str = Field(
        ...,
        description="International phone number with country code, e.g. +919876543210 or 919876543210",
    )
    message: str | None = Field(
        default=None,
        description="Optional custom message to send. If not provided, a default test alert is used.",
    )
