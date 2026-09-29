from abc import ABC, abstractmethod


class EmailProvider(ABC):
    """Abstract base class for email integrations (Gmail, Outlook, etc.)."""

    @abstractmethod
    async def get_unread_emails(self, max_results: int = 20) -> list[dict]:
        """Fetch unread emails from the provider."""
        raise NotImplementedError

    @abstractmethod
    async def get_email(self, message_id: str) -> dict:
        """Fetch a specific email by its provider message ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_thread(self, thread_id: str) -> list[dict]:
        """Fetch all emails in a conversation thread."""
        raise NotImplementedError

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        raise NotImplementedError
