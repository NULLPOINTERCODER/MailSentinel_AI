import logging
import re
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.base import AIProvider
from app.ai.groq_provider import GroqProvider
from app.services.rag_service import RAGService
from app.services.whatsapp_cloud_provider import WhatsAppCloudProvider
from app.services.whatsapp_provider import WhatsAppProvider

logger = logging.getLogger(__name__)

WHATSAPP_HELP_MESSAGE = (
    "🤖 *MailSentinel AI Assistant*\n\n"
    "I am your personal email intelligence bot. Here is what you can ask me:\n\n"
    "📌 *Show important emails* — Get your top high-priority emails\n"
    "⏰ *Check deadlines* — See all upcoming assessment & interview deadlines\n"
    "👥 *Summarize recruiters* — Summary of active recruiter conversations\n"
    "🔍 *What happened with [Company]?* — Deep search across your inbox history\n"
    "❓ *Help* — Display this menu"
)


class WhatsAppConversationalAgent:
    """Conversational AI Agent that processes inbound WhatsApp messages,
    classifies user intents, queries MongoDB / RAG, and responds via WhatsApp Cloud API.
    """

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        whatsapp_provider: WhatsAppProvider | None = None,
        ai_provider: AIProvider | None = None,
    ):
        self.db = db
        self.emails_col = db["emails"]
        self.settings_col = db["user_preferences"]
        self.users_col = db["users"]
        self.chat_history_col = db["whatsapp_chat_history"]
        self.whatsapp_provider = whatsapp_provider or WhatsAppCloudProvider()
        self.ai_provider = ai_provider or GroqProvider()
        self.rag_service = RAGService(db=db, ai_provider=self.ai_provider)

    def normalize_phone(self, phone: str) -> str:
        """Strip non-digit characters for matching."""
        return re.sub(r"\D", "", phone)

    async def find_user_by_phone(self, phone: str) -> tuple[str | None, dict | None]:
        """Lookup user_id by matching normalized WhatsApp phone number."""
        clean_target = self.normalize_phone(phone)
        if not clean_target:
            return None, None

        # Search in user_preferences collection
        cursor = self.settings_col.find({"whatsapp_phone_number": {"$ne": None}})
        async for doc in cursor:
            raw_phone = doc.get("whatsapp_phone_number", "")
            if self.normalize_phone(raw_phone) == clean_target or clean_target.endswith(self.normalize_phone(raw_phone)) or self.normalize_phone(raw_phone).endswith(clean_target):
                return doc["user_id"], doc

        # Fallback check in users collection
        cursor_users = self.users_col.find({"whatsapp_number": {"$ne": None}})
        async for u in cursor_users:
            raw_phone = u.get("whatsapp_number", "")
            if self.normalize_phone(raw_phone) == clean_target or clean_target.endswith(self.normalize_phone(raw_phone)):
                return str(u["_id"]), None

        return None, None

    async def handle_show_important_emails(self, user_id: str) -> str:
        """Fetch top recent important emails."""
        cursor = self.emails_col.find({
            "user_id": user_id,
            "$or": [
                {"final_importance": {"$gte": 80}},
                {"is_potentially_important": True},
            ],
        }).sort("created_at", -1).limit(4)

        emails = await cursor.to_list(length=4)
        if not emails:
            return "📭 You have no critical unread emails at the moment. Your inbox is calm!"

        lines = ["🚨 *TOP IMPORTANT EMAILS:*\n"]
        for idx, email in enumerate(emails, 1):
            sender = email.get("sender_name") or email.get("sender_email", "Unknown")
            subject = email.get("subject", "(No Subject)")
            score = email.get("final_importance") or email.get("rule_score", 0)
            summary = email.get("summary") or email.get("snippet", "")[:120]

            lines.append(
                f"{idx}. *{sender}* (Score: {score}/100)\n"
                f"   📧 *{subject}*\n"
                f"   🧠 {summary}\n"
            )

        lines.append("Reply with a company name to get more details on any thread.")
        return "\n".join(lines)

    async def handle_check_deadlines(self, user_id: str) -> str:
        """Fetch emails with upcoming active deadlines."""
        cursor = self.emails_col.find({
            "user_id": user_id,
            "deadline": {"$ne": None, "$exists": True},
        }).sort("created_at", -1).limit(5)

        emails = await cursor.to_list(length=5)
        filtered = [e for e in emails if e.get("deadline") and e.get("deadline").strip().lower() != "null"]

        if not filtered:
            return "⏰ *UPCOMING DEADLINES:*\n\nNo pending deadlines or expiration dates detected in your recent emails."

        lines = ["⏰ *UPCOMING DEADLINES & ACTIONS:*\n"]
        for idx, email in enumerate(filtered, 1):
            sender = email.get("sender_name") or email.get("sender_email", "Company")
            subject = email.get("subject", "")
            deadline = email.get("deadline", "Specified in email")
            action = email.get("action") or "Complete required steps"

            lines.append(
                f"{idx}. 🏢 *{sender}*\n"
                f"   ⏳ *Due:* {deadline}\n"
                f"   ⚡ *Action:* {action}\n"
                f"   📧 {subject}\n"
            )

        return "\n".join(lines)

    async def handle_summarize_recruiters(self, user_id: str) -> str:
        """Summarize all recruiter messages."""
        cursor = self.emails_col.find({
            "user_id": user_id,
            "category": {"$in": ["RECRUITER", "INTERVIEW", "JOB_APPLICATION", "OFFER"]},
        }).sort("created_at", -1).limit(6)

        emails = await cursor.to_list(length=6)
        if not emails:
            return "👥 No recent recruiter conversations or interview invitations found in your inbox."

        lines = ["👥 *RECRUITER & APPLICATION SUMMARY:*\n"]
        for idx, email in enumerate(emails, 1):
            sender = email.get("sender_name") or email.get("sender_email")
            category = email.get("category", "RECRUITER")
            summary = email.get("summary") or email.get("snippet", "")[:120]
            lines.append(f"{idx}. [{category}] *{sender}*: {summary}")

        return "\n".join(lines)

    async def process_inbound_message(self, from_phone: str, text: str, message_id: str | None = None) -> dict:
        """Main conversational dispatcher: receives message, identifies user, computes response, and replies."""
        clean_text = text.strip()
        lower_text = clean_text.lower()
        now = datetime.now(timezone.utc)

        # 1. User Identification
        user_id, user_prefs = await self.find_user_by_phone(from_phone)
        if not user_id:
            unregistered_reply = (
                "🔒 *MailSentinel AI — Number Not Linked*\n\n"
                f"Your WhatsApp number ({from_phone}) is not linked to any active MailSentinel AI account.\n\n"
                "To link this number:\n"
                "1. Log in to your MailSentinel AI dashboard\n"
                "2. Navigate to Settings -> WhatsApp Delivery Channel\n"
                "3. Enter this phone number and save.\n\n"
                "Once linked, you can query your emails directly from WhatsApp!"
            )
            await self.whatsapp_provider.send_text_message(to_phone=from_phone, message=unregistered_reply)
            return {"status": "unregistered", "reply": unregistered_reply}

        # 2. Intent Classification & Routing
        if lower_text in ["help", "menu", "hi", "hello", "start"]:
            reply_text = WHATSAPP_HELP_MESSAGE

        elif any(k in lower_text for k in ["important", "unread", "priority", "alerts", "show my important emails"]):
            reply_text = await self.handle_show_important_emails(user_id)

        elif any(k in lower_text for k in ["deadline", "deadlines", "due", "schedule", "interview this week", "tests this week"]):
            reply_text = await self.handle_check_deadlines(user_id)

        elif any(k in lower_text for k in ["recruiter", "recruiters", "applications", "jobs", "offers"]):
            reply_text = await self.handle_summarize_recruiters(user_id)

        else:
            # 3. Fallback to Semantic RAG Knowledge Engine over historical emails
            rag_res = await self.rag_service.query_and_answer(
                user_id=user_id,
                query=clean_text,
                top_k=4,
            )
            reply_text = f"🤖 *MailSentinel AI:*\n\n{rag_res.answer}"

        # 4. Dispatch Reply via WhatsApp Provider
        provider_res = await self.whatsapp_provider.send_text_message(
            to_phone=from_phone,
            message=reply_text,
        )

        # 5. Log chat turn in MongoDB
        log_doc = {
            "user_id": user_id,
            "sender_phone": from_phone,
            "incoming_message_id": message_id,
            "incoming_text": clean_text,
            "reply_text": reply_text,
            "provider_status": provider_res,
            "created_at": now,
        }
        await self.chat_history_col.insert_one(log_doc)

        return {
            "status": "success",
            "user_id": user_id,
            "reply": reply_text,
            "provider_response": provider_res,
        }
