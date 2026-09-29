import logging
import re
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.email import EmailResponse, EmailStatsResponse, EmailSyncResult, SignalDetail
from app.services.email_account_service import EmailAccountService
from app.services.email_normalizer import EmailNormalizer
from app.services.gmail_service import GmailService
from app.services.importance_scorer import ImportanceScorer

logger = logging.getLogger(__name__)


def email_doc_to_response(doc: dict) -> EmailResponse:
    """Convert MongoDB email document to EmailResponse Pydantic schema."""
    return EmailResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        account_id=str(doc["account_id"]),
        message_id=doc["message_id"],
        thread_id=doc.get("thread_id"),
        provider=doc.get("provider", "gmail"),
        sender_name=doc.get("sender_name", ""),
        sender_email=doc.get("sender_email", ""),
        recipient=doc.get("recipient", ""),
        subject=doc.get("subject", "No Subject"),
        snippet=doc.get("snippet", ""),
        body_text=doc.get("body_text", ""),
        received_at=str(doc.get("received_at", "")),
        is_unread=doc.get("is_unread", True),
        content_hash=doc.get("content_hash", ""),
        rule_score=doc.get("rule_score", 0),
        is_potentially_important=doc.get("is_potentially_important", False),
        positive_signals=[SignalDetail(**s) for s in doc.get("positive_signals", [])],
        negative_signals=[SignalDetail(**s) for s in doc.get("negative_signals", [])],
        # AI Fields
        ai_processed=doc.get("ai_processed", False),
        ai_score=doc.get("ai_score"),
        final_importance=doc.get("final_importance"),
        category=doc.get("category"),
        urgency=doc.get("urgency"),
        action_required=doc.get("action_required"),
        deadline=doc.get("deadline"),
        summary=doc.get("summary"),
        action=doc.get("action"),
        reason=doc.get("reason"),
        is_whatsapp_candidate=doc.get("is_whatsapp_candidate"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
    )


class EmailService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["emails"]
        self.account_service = EmailAccountService(db)

    async def check_duplicate(self, user_id: str, message_id: str, content_hash: str) -> bool:
        existing = await self.collection.find_one({
            "user_id": user_id,
            "$or": [
                {"message_id": message_id},
                {"content_hash": content_hash},
            ],
        })
        return existing is not None

    async def ingest_email(self, user_id: str, account_id: str, raw_email: dict, provider: str = "gmail") -> dict | None:
        normalized = EmailNormalizer.normalize(raw_email, provider=provider)

        if await self.check_duplicate(user_id, normalized["message_id"], normalized["content_hash"]):
            return None

        score_result = ImportanceScorer.calculate_rule_score(
            subject=normalized["subject"],
            body_text=normalized["body_text"],
            sender_email=normalized["sender_email"],
            is_unread=normalized["is_unread"],
        )

        now = datetime.now(timezone.utc)
        email_doc = {
            "user_id": user_id,
            "account_id": account_id,
            **normalized,
            "rule_score": score_result["rule_score"],
            "is_potentially_important": score_result["is_potentially_important"],
            "positive_signals": score_result["positive_signals"],
            "negative_signals": score_result["negative_signals"],
            "ai_processed": False,
            "notified": False,
            "created_at": now,
            "updated_at": now,
        }

        res = await self.collection.insert_one(email_doc)
        email_doc["_id"] = res.inserted_id
        return email_doc

    async def sync_user_inboxes(self, user_id: str, max_per_account: int = 20) -> EmailSyncResult:
        accounts = await self.account_service.get_user_accounts(user_id)
        total_fetched = 0
        new_saved = 0
        duplicates = 0
        potentially_important_count = 0

        for account_doc in accounts:
            try:
                gmail_service = GmailService(account_doc)
                raw_emails = await gmail_service.get_unread_emails(max_results=max_per_account)
                total_fetched += len(raw_emails)

                for raw_mail in raw_emails:
                    saved = await self.ingest_email(
                        user_id=user_id,
                        account_id=str(account_doc["_id"]),
                        raw_email=raw_mail,
                        provider=account_doc.get("provider", "gmail"),
                    )
                    if saved:
                        new_saved += 1
                        if saved.get("is_potentially_important"):
                            potentially_important_count += 1
                    else:
                        duplicates += 1
            except Exception as exc:
                logger.error("Error syncing account %s for user %s: %s", account_doc.get("email"), user_id, exc)

        return EmailSyncResult(
            synced_accounts=len(accounts),
            total_fetched=total_fetched,
            new_emails_saved=new_saved,
            duplicates_skipped=duplicates,
            potentially_important=potentially_important_count,
        )

    async def list_emails(
        self,
        user_id: str,
        only_important: bool = False,
        only_unread: bool = False,
        search_query: str | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[dict]:
        query = {"user_id": user_id}
        if only_important:
            query["is_potentially_important"] = True
        if only_unread:
            query["is_unread"] = True
        if search_query:
            regex_query = {"$regex": re.escape(search_query), "$options": "i"}
            query["$or"] = [
                {"subject": regex_query},
                {"sender_name": regex_query},
                {"sender_email": regex_query},
                {"snippet": regex_query},
            ]

        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_email_by_id(self, email_id: str, user_id: str) -> dict | None:
        if not ObjectId.is_valid(email_id):
            return None
        return await self.collection.find_one({
            "_id": ObjectId(email_id),
            "user_id": user_id,
        })

    async def get_email_stats(self, user_id: str) -> EmailStatsResponse:
        total = await self.collection.count_documents({"user_id": user_id})
        unread = await self.collection.count_documents({"user_id": user_id, "is_unread": True})
        important = await self.collection.count_documents({"user_id": user_id, "is_potentially_important": True})
        critical = await self.collection.count_documents({
            "user_id": user_id,
            "positive_signals.signal": {"$in": ["offer", "interview", "shortlisted", "security_alert"]},
        })
        ai_triaged = await self.collection.count_documents({"user_id": user_id, "ai_processed": True})

        return EmailStatsResponse(
            total_emails=total,
            unread_emails=unread,
            potentially_important=important,
            critical_signals_detected=critical,
            ai_triaged_count=ai_triaged,
        )
