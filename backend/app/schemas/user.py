from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Payload for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    full_name: str | None = Field(default=None, max_length=100)
    whatsapp_number: str | None = Field(
        default=None,
        description="E.164 formatted WhatsApp phone number, e.g. +919876543210",
    )


class UserLogin(BaseModel):
    """Payload for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user response data."""

    id: str
    email: EmailStr
    full_name: str | None = None
    whatsapp_number: str | None = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Response returned upon successful authentication."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
