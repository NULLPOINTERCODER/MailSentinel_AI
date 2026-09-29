import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_database
from app.core.config import get_settings
from app.schemas.email_account import (
    EmailAccountResponse,
    GmailProfileResponse,
    OAuthCallbackPayload,
    OAuthUrlResponse,
)
from app.schemas.user import UserResponse
from app.services.email_account_service import EmailAccountService, email_account_doc_to_response
from app.services.gmail_service import (
    GmailService,
    exchange_google_code_for_tokens,
    get_google_oauth_url,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


def get_email_account_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> EmailAccountService:
    return EmailAccountService(db)


@router.get("/oauth/url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    current_user: UserResponse = Depends(get_current_user),
) -> OAuthUrlResponse:
    """Generate the Google OAuth 2.0 consent URL for the authenticated user."""
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured on the backend.",
        )

    # State binds user_id + random nonce to prevent CSRF attacks
    state_nonce = secrets.token_urlsafe(16)
    state = f"{current_user.id}:{state_nonce}"

    url = get_google_oauth_url(state=state)
    return OAuthUrlResponse(url=url, state=state)


@router.post("/oauth/callback", response_model=EmailAccountResponse)
async def oauth_callback(
    payload: OAuthCallbackPayload,
    current_user: UserResponse = Depends(get_current_user),
    account_service: EmailAccountService = Depends(get_email_account_service),
) -> EmailAccountResponse:
    """Exchange OAuth authorization code for tokens and save encrypted credentials."""
    # Verify state matches current user
    state_parts = payload.state.split(":")
    if not state_parts or state_parts[0] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state verification failed. Possible CSRF attempt.",
        )

    try:
        token_data = await exchange_google_code_for_tokens(payload.code)
    except Exception as exc:
        logger.error("OAuth token exchange failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange authorization code with Google: {exc}",
        )

    expires_in = token_data.get("expires_in", 3600)
    token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    account_doc = await account_service.upsert_account(
        user_id=current_user.id,
        email=token_data["email"],
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_expiry=token_expiry,
        scopes=token_data.get("scopes", []),
        provider="gmail",
    )

    return email_account_doc_to_response(account_doc)


@router.get("/accounts", response_model=list[EmailAccountResponse])
async def list_connected_accounts(
    current_user: UserResponse = Depends(get_current_user),
    account_service: EmailAccountService = Depends(get_email_account_service),
) -> list[EmailAccountResponse]:
    """List all connected Gmail accounts for the authenticated user."""
    accounts = await account_service.get_user_accounts(current_user.id)
    return [email_account_doc_to_response(acc) for acc in accounts]


@router.delete("/accounts/{account_id}", status_code=status.HTTP_200_OK)
async def disconnect_account(
    account_id: str,
    current_user: UserResponse = Depends(get_current_user),
    account_service: EmailAccountService = Depends(get_email_account_service),
) -> dict:
    """Disconnect and delete an email account."""
    deleted = await account_service.delete_account(account_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found or unauthorized.",
        )
    return {"status": "ok", "message": "Email account disconnected successfully."}


@router.get("/accounts/{account_id}/test", response_model=GmailProfileResponse)
async def test_account_connection(
    account_id: str,
    current_user: UserResponse = Depends(get_current_user),
    account_service: EmailAccountService = Depends(get_email_account_service),
) -> GmailProfileResponse:
    """Test Gmail API connection and fetch account statistics."""
    account_doc = await account_service.get_by_id(account_id, current_user.id)
    if not account_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found.",
        )

    try:
        gmail_service = GmailService(account_doc)
        profile = await gmail_service.get_profile()
        return GmailProfileResponse(**profile)
    except Exception as exc:
        logger.error("Gmail connection test failed for %s: %s", account_doc.get("email"), exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to communicate with Gmail API: {exc}",
        )


@router.get("/accounts/{account_id}/unread")
async def fetch_unread_messages(
    account_id: str,
    max_results: int = 10,
    current_user: UserResponse = Depends(get_current_user),
    account_service: EmailAccountService = Depends(get_email_account_service),
) -> dict:
    """Fetch recent unread emails via Gmail API."""
    account_doc = await account_service.get_by_id(account_id, current_user.id)
    if not account_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email account not found.",
        )

    try:
        gmail_service = GmailService(account_doc)
        emails = await gmail_service.get_unread_emails(max_results=max_results)
        return {
            "account_id": account_id,
            "email": account_doc["email"],
            "count": len(emails),
            "emails": emails,
        }
    except Exception as exc:
        logger.error("Failed to fetch unread emails: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gmail API error: {exc}",
        )
