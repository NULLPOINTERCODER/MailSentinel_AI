import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.api.deps import get_database
from app.core.config import get_settings
from app.services.whatsapp_agent import WhatsAppConversationalAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhook/whatsapp", tags=["whatsapp-webhook"])


class SimulateWhatsAppMessageRequest(BaseModel):
    phone_number: str
    message: str


def get_whatsapp_agent(db: AsyncIOMotorDatabase = Depends(get_database)) -> WhatsAppConversationalAgent:
    return WhatsAppConversationalAgent(db=db)


@router.get("")
async def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Meta WhatsApp Cloud API Webhook Verification Challenge handler."""
    settings = get_settings()
    configured_token = settings.whatsapp_verify_token or "mailsentinel_verify_token"

    if hub_mode == "subscribe" and hub_verify_token == configured_token:
        logger.info("Meta WhatsApp webhook verification successful.")
        return Response(content=hub_challenge or "", media_type="text/plain")

    logger.warning("Meta WhatsApp webhook verification failed. Token mismatch.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification token mismatch.",
    )


@router.post("")
async def receive_whatsapp_message(
    request: Request,
    agent: WhatsAppConversationalAgent = Depends(get_whatsapp_agent),
):
    """Receive inbound messages from Meta WhatsApp Cloud API."""
    try:
        body = await request.json()
        logger.info("Inbound WhatsApp Webhook payload received.")

        # Parse Meta standard payload structure
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    if msg.get("type") == "text":
                        from_phone = msg.get("from")
                        msg_body = msg.get("text", {}).get("body", "")
                        msg_id = msg.get("id")

                        logger.info("Processing inbound WhatsApp text from %s: '%s'", from_phone, msg_body)
                        await agent.process_inbound_message(
                            from_phone=from_phone,
                            text=msg_body,
                            message_id=msg_id,
                        )

        return {"status": "EVENT_RECEIVED"}
    except Exception as e:
        logger.error("Error processing Meta webhook payload: %s", e)
        return {"status": "ERROR", "detail": str(e)}


@router.post("/simulate")
async def simulate_whatsapp_chat(
    payload: SimulateWhatsAppMessageRequest,
    agent: WhatsAppConversationalAgent = Depends(get_whatsapp_agent),
):
    """Simulate an inbound WhatsApp message for local testing and web UI preview."""
    result = await agent.process_inbound_message(
        from_phone=payload.phone_number,
        text=payload.message,
        message_id="sim_msg_test_001",
    )
    return result
