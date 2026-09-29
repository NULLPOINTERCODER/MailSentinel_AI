from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class EmailCategory(str, Enum):
    INTERVIEW = "INTERVIEW"
    ASSESSMENT = "ASSESSMENT"
    JOB_APPLICATION = "JOB_APPLICATION"
    RECRUITER = "RECRUITER"
    OFFER = "OFFER"
    MEETING = "MEETING"
    COLLEGE = "COLLEGE"
    FINANCE = "FINANCE"
    SECURITY = "SECURITY"
    PERSONAL = "PERSONAL"
    NEWSLETTER = "NEWSLETTER"
    PROMOTION = "PROMOTION"
    SPAM = "SPAM"
    GENERAL = "GENERAL"


class UrgencyLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AIAnalysisResult(BaseModel):
    """Structured output returned by Groq AI for an email."""

    category: EmailCategory = Field(description="Classified category of the email")
    importance: int = Field(..., ge=0, le=100, description="AI importance rating from 0 to 100")
    urgency: UrgencyLevel = Field(description="Urgency classification")
    action_required: bool = Field(description="Whether the recipient must perform an action")
    deadline: str | None = Field(
        default=None,
        description="Extracted date and time deadline in ISO format or descriptive string. Must be null if no deadline.",
    )
    summary: str = Field(description="Concise 1-3 sentence summary of what happened and required action")
    action: str | None = Field(default=None, description="Clear actionable next step for the user, or null")
    reason: str = Field(description="Brief explanation of why this category and score were assigned")

    model_config = ConfigDict(from_attributes=True)


class EmailTriageResponse(BaseModel):
    """Combined hybrid triage response containing rule and AI results."""

    email_id: str
    message_id: str
    rule_score: int
    ai_score: int
    final_importance: int
    category: EmailCategory
    urgency: UrgencyLevel
    action_required: bool
    deadline: str | None
    summary: str
    action: str | None
    reason: str
    is_whatsapp_candidate: bool  # Final importance >= 80

    model_config = ConfigDict(from_attributes=True)
