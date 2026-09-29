from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language question about emails")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant emails to retrieve")


class RAGSourceDocument(BaseModel):
    email_id: str
    subject: str
    sender: str
    received_at: str
    snippet: str
    similarity_score: float | None = None
    category: str | None = None
    importance: int | None = None
    deadline: str | None = None
    action: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[RAGSourceDocument] = []
    context_emails_count: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)


class RAGIndexStatusResponse(BaseModel):
    indexed_emails: int
    total_emails: int
    status: str
    collection_name: str
