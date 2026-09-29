import logging
import re
import httpx

from app.core.config import get_settings
from app.services.whatsapp_provider import WhatsAppProvider

logger = logging.getLogger(__name__)


class WhatsAppCloudProvider(WhatsAppProvider):
    """Official Meta WhatsApp Cloud API Provider.
    
    Uses Meta Graph API v20.0 to send WhatsApp messages directly to verified phone numbers.
    If Meta Cloud API credentials are not yet configured in development, it simulates sending
    and logs the message cleanly without failing.
    """

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
    ):
        settings = get_settings()
        self.access_token = access_token or settings.whatsapp_access_token
        self.phone_number_id = phone_number_id or settings.whatsapp_phone_number_id
        self.api_version = "v20.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def normalize_phone_number(self, phone: str) -> str:
        """Strip non-numeric characters for Meta API (Meta requires digits only e.g. 919876543210)."""
        return re.sub(r"\D", "", phone)

    async def send_text_message(self, to_phone: str, message: str) -> dict:
        clean_phone = self.normalize_phone_number(to_phone)
        if not clean_phone:
            raise ValueError("Invalid phone number provided for WhatsApp delivery.")

        # Check if production credentials exist
        if not self.access_token or not self.phone_number_id:
            logger.warning(
                "WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID is not configured. "
                "Simulating WhatsApp message delivery in Sandbox/Dev mode."
            )
            logger.info("--- [DEV SIMULATED WHATSAPP MESSAGE TO: %s] ---\n%s\n---------------------------------------", clean_phone, message)
            return {
                "success": True,
                "simulated": True,
                "provider_message_id": f"sim_wamid_{clean_phone[-4:]}_dev",
                "recipient": clean_phone,
            }

        endpoint = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(endpoint, json=payload, headers=headers)
                data = response.json()

                if response.status_code >= 400:
                    error_msg = data.get("error", {}).get("message", "Unknown Meta API Error")
                    logger.error("WhatsApp Cloud API error (%s): %s", response.status_code, error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "status_code": response.status_code,
                        "details": data,
                    }

                provider_msg_id = None
                if "messages" in data and len(data["messages"]) > 0:
                    provider_msg_id = data["messages"][0].get("id")

                logger.info("WhatsApp message successfully dispatched to %s (ID: %s)", clean_phone, provider_msg_id)
                return {
                    "success": True,
                    "provider_message_id": provider_msg_id,
                    "recipient": clean_phone,
                    "response": data,
                }
            except httpx.RequestError as exc:
                logger.error("HTTP request error sending WhatsApp message: %s", exc)
                return {
                    "success": False,
                    "error": str(exc),
                }
