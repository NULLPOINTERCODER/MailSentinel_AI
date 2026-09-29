from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class EmailAccountResponse(BaseModel):
    """Public representation of a connected email account."""

    id: str
    user_id: str
    provider: str
    email: EmailStr
    is_active: bool
    scopes: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OAuthUrlResponse(BaseModel):
    """Google OAuth consent URL response."""

    url: str
    state: str


class OAuthCallbackPayload(BaseModel):
    """Payload sent by frontend callback after Google OAuth consent."""

    code: str
    state: str


class GmailProfileResponse(BaseModel):
    """Status test response for a connected Gmail account."""

    email: str
    messages_total: int
    threads_total: int
    status: str
