from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.base import AIProvider
from app.ai.groq_provider import GroqProvider
from app.schemas.ai import AIAnalysisResult, EmailTriageResponse


class AIPipelineService:
    def __init__(self, db: AsyncIOMotorDatabase, ai_provider: AIProvider | None = None):
        self.db = db
        self.emails_col = db["emails"]
        self.classifications_col = db["classifications"]
        self.ai_provider = ai_provider or GroqProvider()

    def calculate_hybrid_importance(self, rule_score: int, ai_score: int) -> int:
        """Combine rule-based score (35% weight) with AI intelligence score (65% weight)."""
        combined = (0.35 * rule_score) + (0.65 * ai_score)
        return max(0, min(100, round(combined)))

    async def triage_email(self, email_id: str, user_id: str) -> EmailTriageResponse | None:
        """Execute deep Groq AI triage on a specific email and save classification."""
        if not ObjectId.is_valid(email_id):
            return None

        email_doc = await self.emails_col.find_one({"_id": ObjectId(email_id), "user_id": user_id})
        if not email_doc:
            return None

        sender = f"{email_doc.get('sender_name', '')} <{email_doc.get('sender_email', '')}>"
        subject = email_doc.get("subject", "")
        body = email_doc.get("body_text", "")
        received_at = str(email_doc.get("received_at", ""))
        rule_score = email_doc.get("rule_score", 0)

        # 1. Call Groq AI Provider
        ai_res: AIAnalysisResult = await self.ai_provider.analyze_email(
            sender=sender,
            subject=subject,
            body_text=body,
            received_at=received_at,
        )

        # 2. Compute Hybrid Final Importance
        final_importance = self.calculate_hybrid_importance(rule_score, ai_res.importance)
        is_whatsapp_candidate = final_importance >= 80

        now = datetime.now(timezone.utc)

        # 3. Store in classifications collection
        classification_doc = {
            "user_id": user_id,
            "email_id": str(email_doc["_id"]),
            "message_id": email_doc.get("message_id"),
            "category": ai_res.category.value,
            "urgency": ai_res.urgency.value,
            "rule_score": rule_score,
            "ai_score": ai_res.importance,
            "final_importance": final_importance,
            "action_required": ai_res.action_required,
            "deadline": ai_res.deadline,
            "summary": ai_res.summary,
            "action": ai_res.action,
            "reason": ai_res.reason,
            "is_whatsapp_candidate": is_whatsapp_candidate,
            "created_at": now,
        }

        await self.classifications_col.update_one(
            {"email_id": str(email_doc["_id"])},
            {"$set": classification_doc},
            upsert=True,
        )

        # 4. Update email document
        await self.emails_col.update_one(
            {"_id": email_doc["_id"]},
            {
                "$set": {
                    "ai_processed": True,
                    "final_importance": final_importance,
                    "ai_score": ai_res.importance,
                    "category": ai_res.category.value,
                    "urgency": ai_res.urgency.value,
                    "action_required": ai_res.action_required,
                    "deadline": ai_res.deadline,
                    "summary": ai_res.summary,
                    "action": ai_res.action,
                    "reason": ai_res.reason,
                    "is_whatsapp_candidate": is_whatsapp_candidate,
                    "updated_at": now,
                }
            },
        )

        # 5. Optionally trigger auto WhatsApp alert if candidate
        if is_whatsapp_candidate:
            try:
                from app.services.notification_service import NotificationService
                notif_service = NotificationService(self.db)
                await notif_service.send_email_whatsapp_alert(
                    email_id=str(email_doc["_id"]),
                    user_id=user_id,
                    force_resend=False,
                )
            except Exception:
                pass

        return EmailTriageResponse(
            email_id=str(email_doc["_id"]),
            message_id=email_doc.get("message_id"),
            rule_score=rule_score,
            ai_score=ai_res.importance,
            final_importance=final_importance,
            category=ai_res.category,
            urgency=ai_res.urgency,
            action_required=ai_res.action_required,
            deadline=ai_res.deadline,
            summary=ai_res.summary,
            action=ai_res.action,
            reason=ai_res.reason,
            is_whatsapp_candidate=is_whatsapp_candidate,
        )

    async def batch_triage_user_emails(self, user_id: str, limit: int = 10) -> list[EmailTriageResponse]:
        """Triage pending potentially important emails for the user."""
        cursor = self.emails_col.find({
            "user_id": user_id,
            "ai_processed": {"$ne": True},
            "is_potentially_important": True,
        }).limit(limit)

        pending_emails = await cursor.to_list(length=limit)
        results = []
        for doc in pending_emails:
            res = await self.triage_email(str(doc["_id"]), user_id)
            if res:
                results.append(res)
        return results
