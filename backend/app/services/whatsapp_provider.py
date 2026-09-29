from abc import ABC, abstractmethod


class WhatsAppProvider(ABC):
    """Abstract base class for WhatsApp delivery providers."""

    @abstractmethod
    async def send_text_message(self, to_phone: str, message: str) -> dict:
        """Send a standard formatted text message to a WhatsApp number.

        Args:
            to_phone: Recipient phone number in international format without '+' or with '+'.
            message: Formatted text body.

        Returns:
            Dict containing provider response metadata (e.g. {'status': 'success', 'message_id': '...'}).
        """
        pass
