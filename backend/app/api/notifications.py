from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_database
from app.schemas.notification import (
    NotificationListResponse,
    SendNotificationRequest,
    TestWhatsAppRequest,
)
from app.schemas.user import UserResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def get_notification_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> NotificationService:
    return NotificationService(db)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
    """List notification history and audit logs for the current user."""
    items, total = await notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        skip=skip,
    )
    return NotificationListResponse(items=items, total=total)


@router.post("/send/{email_id}")
async def send_email_alert(
    email_id: str,
    force_resend: bool = Query(default=False),
    current_user: UserResponse = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Trigger an instant WhatsApp alert for a specific analyzed email."""
    result = await notification_service.send_email_whatsapp_alert(
        email_id=email_id,
        user_id=current_user.id,
        force_resend=force_resend,
    )
    return result


@router.post("/test-whatsapp")
async def send_test_whatsapp_ping(
    payload: TestWhatsAppRequest,
    current_user: UserResponse = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Send a live WhatsApp test verification message to test WhatsApp credentials."""
    result = await notification_service.send_test_message(
        user_id=current_user.id,
        phone_number=payload.phone_number,
        custom_text=payload.message,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to dispatch test WhatsApp message."),
        )
    return result
