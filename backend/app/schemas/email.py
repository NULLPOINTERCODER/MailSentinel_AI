from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SignalDetail(BaseModel):
    signal: str
    weight: int


class EmailResponse(BaseModel):
    """Normalized email response object."""

    id: str
    user_id: str
    account_id: str
    message_id: str
    thread_id: str | None = None
    provider: str = "gmail"
    sender_name: str
    sender_email: str
    recipient: str
    subject: str
    snippet: str
    body_text: str
    received_at: str
    is_unread: bool
    content_hash: str
    rule_score: int
    is_potentially_important: bool
    positive_signals: list[SignalDetail] = []
    negative_signals: list[SignalDetail] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailSyncResult(BaseModel):
    """Result of an inbox sync operation."""

    synced_accounts: int
    total_fetched: int
    new_emails_saved: int
    duplicates_skipped: int
    potentially_important: int


class EmailStatsResponse(BaseModel):
    """Inbox metrics summary."""

    total_emails: int
    unread_emails: int
    potentially_important: int
    critical_signals_detected: int
