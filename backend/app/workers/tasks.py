import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.services.ai_pipeline import AIPipelineService
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Utility to run asynchronous coroutines safely inside Celery worker threads."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _async_sync_all_active_users():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        email_accounts_col = db["email_accounts"]
        cursor = email_accounts_col.find({"is_active": True})
        accounts = await cursor.to_list(length=500)

        user_ids = list({acc["user_id"] for acc in accounts if "user_id" in acc})
        logger.info("Found %d active users with connected email accounts.", len(user_ids))

        email_service = EmailService(db)
        ai_pipeline = AIPipelineService(db)

        synced_count = 0
        triaged_count = 0

        for uid in user_ids:
            try:
                # 1. Ingest unread emails
                sync_res = await email_service.sync_user_emails(user_id=uid, max_per_account=25)
                synced_count += sync_res.get("new_emails_saved", 0)

                # 2. Batch AI triage newly flagged potentially important emails
                triage_res = await ai_pipeline.batch_triage_user_emails(user_id=uid, limit=10)
                triaged_count += len(triage_res)
            except Exception as e:
                logger.error("Error running periodic sync for user %s: %s", uid, e)

        return {
            "active_users_checked": len(user_ids),
            "new_emails_ingested": synced_count,
            "emails_triaged_with_ai": triaged_count,
        }
    finally:
        client.close()


async def _async_sync_single_user(user_id: str, max_per_account: int = 25):
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        email_service = EmailService(db)
        ai_pipeline = AIPipelineService(db)

        sync_res = await email_service.sync_user_emails(user_id=user_id, max_per_account=max_per_account)
        triage_res = await ai_pipeline.batch_triage_user_emails(user_id=user_id, limit=10)

        return {
            "sync": sync_res,
            "triaged_count": len(triage_res),
        }
    finally:
        client.close()


async def _async_triage_email(email_id: str, user_id: str):
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        ai_pipeline = AIPipelineService(db)
        result = await ai_pipeline.triage_email(email_id=email_id, user_id=user_id)
        return result.model_dump() if result else None
    finally:
        client.close()


async def _async_send_whatsapp(email_id: str, user_id: str, force_resend: bool = False):
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    try:
        notification_service = NotificationService(db)
        result = await notification_service.send_email_whatsapp_alert(
            email_id=email_id,
            user_id=user_id,
            force_resend=force_resend,
        )
        return result
    finally:
        client.close()


# ==========================================
# Celery Tasks
# ==========================================

@celery_app.task(name="app.workers.tasks.sync_all_active_users_task")
def sync_all_active_users_task():
    """Periodic Celery task to fetch unread emails and trigger AI triage across all accounts."""
    logger.info("Executing periodic sync across all active users...")
    return run_async(_async_sync_all_active_users())


@celery_app.task(name="app.workers.tasks.sync_single_user_task")
def sync_single_user_task(user_id: str, max_per_account: int = 25):
    """Background worker task to synchronize a specific user's connected inboxes."""
    logger.info("Executing inbox sync for user: %s", user_id)
    return run_async(_async_sync_single_user(user_id=user_id, max_per_account=max_per_account))


@celery_app.task(name="app.workers.tasks.triage_email_task")
def triage_email_task(email_id: str, user_id: str):
    """Background Groq AI email triage task."""
    logger.info("Executing background AI triage on email %s for user %s", email_id, user_id)
    return run_async(_async_triage_email(email_id=email_id, user_id=user_id))


@celery_app.task(
    name="app.workers.tasks.send_whatsapp_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_whatsapp_task(self, email_id: str, user_id: str, force_resend: bool = False):
    """Background WhatsApp notification dispatch with exponential backoff retries."""
    logger.info("Dispatching WhatsApp alert for email %s (user: %s)", email_id, user_id)
    return run_async(_async_send_whatsapp(email_id=email_id, user_id=user_id, force_resend=force_resend))
