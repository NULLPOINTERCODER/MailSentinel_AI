from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SignalDetail(BaseModel):
    signal: str
    weight: int


class EmailResponse(BaseModel):
    """Normalized email response object with optional AI classification."""

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

    # Groq AI Triage Results
    ai_processed: bool = False
    ai_score: int | None = None
    final_importance: int | None = None
    category: str | None = None
    urgency: str | None = None
    action_required: bool | None = None
    deadline: str | None = None
    summary: str | None = None
    action: str | None = None
    reason: str | None = None
    is_whatsapp_candidate: bool | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmailSyncResult(BaseModel):
    synced_accounts: int
    total_fetched: int
    new_emails_saved: int
    duplicates_skipped: int
    potentially_important: int


class EmailStatsResponse(BaseModel):
    total_emails: int
    unread_emails: int
    potentially_important: int
    critical_signals_detected: int
    ai_triaged_count: int = 0
    high_importance_count: int = 0
    notifications_sent: int = 0
    active_deadlines_count: int = 0
    category_breakdown: dict[str, int] = {}

