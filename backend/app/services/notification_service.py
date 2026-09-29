import hashlib
import logging
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.notification import (
    NotificationChannel,
    NotificationResponse,
    NotificationStatus,
)
from app.services.settings_service import SettingsService
from app.services.whatsapp_cloud_provider import WhatsAppCloudProvider
from app.services.whatsapp_provider import WhatsAppProvider

logger = logging.getLogger(__name__)


class NotificationService:
    """Service to handle notification preparation, threshold checks, deduplication, and delivery."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        whatsapp_provider: WhatsAppProvider | None = None,
    ):
        self.db = db
        self.emails_col = db["emails"]
        self.notifications_col = db["notifications"]
        self.whatsapp_provider = whatsapp_provider or WhatsAppCloudProvider()
        self.settings_service = SettingsService(db)

    def generate_content_hash(self, email_id: str, subject: str, body: str) -> str:
        """Create a deterministic hash to prevent identical notifications."""
        raw = f"{email_id}:{subject}:{body[:200]}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def format_whatsapp_message(
        self,
        sender: str,
        subject: str,
        summary: str,
        deadline: str | None,
        action: str | None,
        importance: int,
    ) -> str:
        """Format the WhatsApp alert strictly following the MailSentinel AI design specification."""
        clean_sender = sender.split("<")[0].strip().replace('"', '') if "<" in sender else sender.strip()
        if not clean_sender:
            clean_sender = "Important Contact"

        deadline_str = deadline if deadline and deadline.strip() else "None specified"
        action_str = action if action and action.strip() else "No immediate action required"

        return (
            f"🚨 *IMPORTANT EMAIL*\n\n"
            f"🏢 *{clean_sender}*\n\n"
            f"📧 *{subject}*\n\n"
            f"🧠 *Summary:*\n{summary}\n\n"
            f"⏰ *Deadline:*\n{deadline_str}\n\n"
            f"⚡ *Action:*\n{action_str}\n\n"
            f"🎯 *Importance:*\n{importance}/100"
        )

    async def send_email_whatsapp_alert(
        self,
        email_id: str,
        user_id: str,
        force_resend: bool = False,
    ) -> dict:
        """Evaluate, format, and dispatch a WhatsApp notification for an email."""
        if not ObjectId.is_valid(email_id):
            return {"status": NotificationStatus.FAILED, "error": "Invalid email ID."}

        email_doc = await self.emails_col.find_one({"_id": ObjectId(email_id), "user_id": user_id})
        if not email_doc:
            return {"status": NotificationStatus.FAILED, "error": "Email not found."}

        # 1. Fetch user preferences
        user_settings = await self.settings_service.get_user_settings(user_id)
        if not user_settings.whatsapp_phone_number:
            return {
                "status": NotificationStatus.SKIPPED,
                "reason": "WhatsApp phone number is not configured in user settings.",
            }

        if not user_settings.whatsapp_notifications_enabled:
            return {
                "status": NotificationStatus.SKIPPED,
                "reason": "WhatsApp notifications are disabled by the user.",
            }

        # 2. Check Importance and Category Thresholds
        final_importance = email_doc.get("final_importance") or email_doc.get("rule_score", 0)
        category = email_doc.get("category", "GENERAL")

        if not force_resend:
            if final_importance < user_settings.minimum_importance_threshold:
                return {
                    "status": NotificationStatus.SKIPPED,
                    "reason": f"Importance ({final_importance}) is below threshold ({user_settings.minimum_importance_threshold}).",
                }

            if category not in user_settings.enabled_categories:
                return {
                    "status": NotificationStatus.SKIPPED,
                    "reason": f"Category '{category}' is disabled in user preferences.",
                }

        # 3. Duplicate Detection Check
        message_id = email_doc.get("message_id")
        existing_notification = await self.notifications_col.find_one({
            "user_id": user_id,
            "email_id": str(email_doc["_id"]),
            "status": NotificationStatus.SENT.value,
        })

        if existing_notification and not force_resend:
            logger.info("Notification for email %s already sent to user %s. Skipping duplicate.", email_id, user_id)
            return {
                "status": NotificationStatus.DUPLICATE,
                "notification_id": str(existing_notification["_id"]),
                "reason": "Notification already dispatched for this email.",
            }

        # 4. Prepare message payload
        sender = f"{email_doc.get('sender_name', '')} {email_doc.get('sender_email', '')}".strip()
        subject = email_doc.get("subject", "(No Subject)")
        summary = email_doc.get("summary") or email_doc.get("snippet", "An important email requires your attention.")
        deadline = email_doc.get("deadline")
        action = email_doc.get("action")

        message_body = self.format_whatsapp_message(
            sender=sender,
            subject=subject,
            summary=summary,
            deadline=deadline,
            action=action,
            importance=final_importance,
        )

        recipient_phone = user_settings.whatsapp_phone_number
        now = datetime.now(timezone.utc)

        # 5. Send via WhatsApp Provider
        provider_res = await self.whatsapp_provider.send_text_message(
            to_phone=recipient_phone,
            message=message_body,
        )

        is_success = provider_res.get("success", False)
        status = NotificationStatus.SENT if is_success else NotificationStatus.FAILED
        provider_msg_id = provider_res.get("provider_message_id")
        error_msg = provider_res.get("error")

        # 6. Save Notification Record in MongoDB
        notif_doc = {
            "user_id": user_id,
            "email_id": str(email_doc["_id"]),
            "message_id": message_id,
            "channel": NotificationChannel.WHATSAPP.value,
            "recipient": recipient_phone,
            "subject": subject,
            "sender": sender,
            "importance": final_importance,
            "category": category,
            "message_body": message_body,
            "status": status.value,
            "provider_response_id": provider_msg_id,
            "error_message": error_msg,
            "created_at": now,
        }

        insert_res = await self.notifications_col.insert_one(notif_doc)
        notif_id = str(insert_res.inserted_id)

        # 7. Update Email Document
        if is_success:
            await self.emails_col.update_one(
                {"_id": email_doc["_id"]},
                {
                    "$set": {
                        "whatsapp_notified": True,
                        "whatsapp_notification_id": notif_id,
                        "notified_at": now,
                    }
                },
            )

        return {
            "status": status,
            "notification_id": notif_id,
            "provider_message_id": provider_msg_id,
            "error": error_msg,
            "simulated": provider_res.get("simulated", False),
        }

    async def send_test_message(self, user_id: str, phone_number: str, custom_text: str | None = None) -> dict:
        """Send a test WhatsApp verification ping message."""
        test_body = custom_text or (
            "✅ *MailSentinel AI Connected!*\n\n"
            "Your WhatsApp notification channel has been verified successfully.\n"
            "You will now receive real-time alerts for critical emails, interviews, and deadlines."
        )

        provider_res = await self.whatsapp_provider.send_text_message(
            to_phone=phone_number,
            message=test_body,
        )

        is_success = provider_res.get("success", False)
        status = NotificationStatus.SENT if is_success else NotificationStatus.FAILED
        now = datetime.now(timezone.utc)

        notif_doc = {
            "user_id": user_id,
            "email_id": None,
            "message_id": None,
            "channel": NotificationChannel.WHATSAPP.value,
            "recipient": phone_number,
            "subject": "WhatsApp Channel Verification Test",
            "sender": "MailSentinel AI System",
            "importance": 100,
            "category": "SYSTEM",
            "message_body": test_body,
            "status": status.value,
            "provider_response_id": provider_res.get("provider_message_id"),
            "error_message": provider_res.get("error"),
            "created_at": now,
        }

        await self.notifications_col.insert_one(notif_doc)
        return provider_res

    async def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[list[NotificationResponse], int]:
        """Fetch past notification logs for a user with pagination."""
        filter_query = {"user_id": user_id}
        total = await self.notifications_col.count_documents(filter_query)
        cursor = (
            self.notifications_col.find(filter_query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        items = []
        async for doc in cursor:
            items.append(
                NotificationResponse(
                    id=str(doc["_id"]),
                    user_id=doc["user_id"],
                    email_id=doc.get("email_id"),
                    message_id=doc.get("message_id"),
                    channel=NotificationChannel(doc.get("channel", "WHATSAPP")),
                    recipient=doc.get("recipient", ""),
                    subject=doc.get("subject"),
                    sender=doc.get("sender"),
                    importance=doc.get("importance"),
                    category=doc.get("category"),
                    message_body=doc.get("message_body", ""),
                    status=NotificationStatus(doc.get("status", "SENT")),
                    provider_response_id=doc.get("provider_response_id"),
                    error_message=doc.get("error_message"),
                    created_at=doc.get("created_at", datetime.now(timezone.utc)),
                )
            )

        return items, total
