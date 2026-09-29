import pytest
from datetime import datetime, timezone
from bson import ObjectId
from mongomock_motor import AsyncMongoMockClient

from app.schemas.notification import NotificationStatus
from app.schemas.settings import UserSettingsUpdate
from app.services.notification_service import NotificationService
from app.services.settings_service import SettingsService
from app.services.whatsapp_cloud_provider import WhatsAppCloudProvider
from app.services.whatsapp_provider import WhatsAppProvider


class MockWhatsAppProvider(WhatsAppProvider):
    """Test Mock Provider that tracks dispatches."""

    def __init__(self):
        self.sent_messages = []

    async def send_text_message(self, to_phone: str, message: str) -> dict:
        self.sent_messages.append({"to_phone": to_phone, "message": message})
        return {
            "success": True,
            "provider_message_id": f"mock_wamid_{len(self.sent_messages)}",
            "recipient": to_phone,
        }


@pytest.fixture
def mock_db():
    client = AsyncMongoMockClient()
    return client["test_mailsentinel"]


@pytest.fixture
def mock_whatsapp():
    return MockWhatsAppProvider()


@pytest.fixture
def notification_service(mock_db, mock_whatsapp):
    return NotificationService(db=mock_db, whatsapp_provider=mock_whatsapp)


@pytest.fixture
def settings_service(mock_db):
    return SettingsService(db=mock_db)


@pytest.mark.asyncio
async def test_message_formatting(notification_service):
    """Verify the WhatsApp message string conforms to MailSentinel AI specifications."""
    message = notification_service.format_whatsapp_message(
        sender="Google Careers <recruiting@google.com>",
        subject="Technical Interview Invitation - Software Engineer",
        summary="You have been invited for a 45-minute technical interview with the engineering team.",
        deadline="October 15, 2026 at 2:00 PM",
        action="Confirm availability and select an interview slot via the candidate portal.",
        importance=95,
    )

    assert "🚨 *IMPORTANT EMAIL*" in message
    assert "🏢 *Google Careers*" in message
    assert "📧 *Technical Interview Invitation - Software Engineer*" in message
    assert "🧠 *Summary:*\nYou have been invited" in message
    assert "⏰ *Deadline:*\nOctober 15, 2026 at 2:00 PM" in message
    assert "⚡ *Action:*\nConfirm availability" in message
    assert "🎯 *Importance:*\n95/100" in message


@pytest.mark.asyncio
async def test_phone_number_normalization():
    """Verify phone numbers are cleaned into digits only for Meta WhatsApp Cloud API."""
    provider = WhatsAppCloudProvider()
    assert provider.normalize_phone_number("+91 98765-43210") == "919876543210"
    assert provider.normalize_phone_number("+1 (555) 019-2834") == "15550192834"
    assert provider.normalize_phone_number("919876543210") == "919876543210"


@pytest.mark.asyncio
async def test_settings_crud(settings_service):
    """Test getting defaults and updating user preferences."""
    user_id = "user_test_123"

    # Default settings check
    defaults = await settings_service.get_user_settings(user_id)
    assert defaults.whatsapp_phone_number is None
    assert defaults.minimum_importance_threshold == 80
    assert "INTERVIEW" in defaults.enabled_categories

    # Update settings
    updated = await settings_service.update_user_settings(
        user_id=user_id,
        update_data=UserSettingsUpdate(
            whatsapp_phone_number="+919876543210",
            minimum_importance_threshold=75,
            enabled_categories=["INTERVIEW", "ASSESSMENT", "OFFER"],
        ),
    )
    assert updated.whatsapp_phone_number == "+919876543210"
    assert updated.minimum_importance_threshold == 75
    assert len(updated.enabled_categories) == 3


@pytest.mark.asyncio
async def test_notification_delivery_and_duplicate_prevention(mock_db, notification_service, mock_whatsapp, settings_service):
    """Test end-to-end notification delivery, threshold checks, and duplicate detection."""
    user_id = "user_456"

    # Set up user phone number and preferences
    await settings_service.update_user_settings(
        user_id=user_id,
        update_data=UserSettingsUpdate(
            whatsapp_phone_number="+919999888877",
            minimum_importance_threshold=80,
            enabled_categories=["INTERVIEW", "ASSESSMENT"],
        ),
    )

    # Insert test email
    email_doc = {
        "_id": ObjectId(),
        "user_id": user_id,
        "message_id": "msg_abc_123",
        "sender_name": "Amazon Recruiter",
        "sender_email": "aws-talent@amazon.com",
        "subject": "AWS SDE Online Assessment Link",
        "body_text": "Please complete the coding assessment before Sunday.",
        "category": "ASSESSMENT",
        "final_importance": 92,
        "summary": "You have received the Amazon coding assessment.",
        "deadline": "Sunday midnight",
        "action": "Complete the online test",
        "created_at": datetime.now(timezone.utc),
    }
    await mock_db["emails"].insert_one(email_doc)
    email_id = str(email_doc["_id"])

    # 1. First Dispatch -> Should SUCCEED
    res1 = await notification_service.send_email_whatsapp_alert(
        email_id=email_id,
        user_id=user_id,
    )
    assert res1["status"] == NotificationStatus.SENT
    assert len(mock_whatsapp.sent_messages) == 1
    assert mock_whatsapp.sent_messages[0]["to_phone"] == "+919999888877"

    # Check notification collection
    notif_count = await mock_db["notifications"].count_documents({"user_id": user_id})
    assert notif_count == 1

    # Check email doc updated
    updated_email = await mock_db["emails"].find_one({"_id": email_doc["_id"]})
    assert updated_email["whatsapp_notified"] is True

    # 2. Second Dispatch without force_resend -> Should return DUPLICATE and NOT send
    res2 = await notification_service.send_email_whatsapp_alert(
        email_id=email_id,
        user_id=user_id,
        force_resend=False,
    )
    assert res2["status"] == NotificationStatus.DUPLICATE
    assert len(mock_whatsapp.sent_messages) == 1  # Not incremented!

    # 3. Third Dispatch with force_resend=True -> Should send again
    res3 = await notification_service.send_email_whatsapp_alert(
        email_id=email_id,
        user_id=user_id,
        force_resend=True,
    )
    assert res3["status"] == NotificationStatus.SENT
    assert len(mock_whatsapp.sent_messages) == 2


@pytest.mark.asyncio
async def test_threshold_and_category_skipping(mock_db, notification_service, mock_whatsapp, settings_service):
    """Test that emails below importance threshold or in disabled categories are skipped."""
    user_id = "user_789"
    await settings_service.update_user_settings(
        user_id=user_id,
        update_data=UserSettingsUpdate(
            whatsapp_phone_number="+918888777766",
            minimum_importance_threshold=85,
            enabled_categories=["INTERVIEW"],  # only INTERVIEW
        ),
    )

    # Low importance email (score 50 < 85)
    low_email = {
        "_id": ObjectId(),
        "user_id": user_id,
        "subject": "Weekly Newsletter",
        "category": "NEWSLETTER",
        "final_importance": 30,
    }
    await mock_db["emails"].insert_one(low_email)

    res_low = await notification_service.send_email_whatsapp_alert(
        email_id=str(low_email["_id"]),
        user_id=user_id,
    )
    assert res_low["status"] == NotificationStatus.SKIPPED
    assert len(mock_whatsapp.sent_messages) == 0


@pytest.mark.asyncio
async def test_multi_user_isolation(mock_db, notification_service, settings_service):
    """Ensure User A cannot trigger or view User B's notifications."""
    user_a = "user_alice"
    user_b = "user_bob"

    # Create email belonging to User B
    email_b = {
        "_id": ObjectId(),
        "user_id": user_b,
        "subject": "Bob's confidential email",
        "final_importance": 90,
    }
    await mock_db["emails"].insert_one(email_b)

    # User A tries to send alert for User B's email -> Should fail
    res = await notification_service.send_email_whatsapp_alert(
        email_id=str(email_b["_id"]),
        user_id=user_a,
    )
    assert res["status"] == NotificationStatus.FAILED
    assert res["error"] == "Email not found."
