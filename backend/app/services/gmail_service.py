import base64
import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings
from app.core.encryption import decrypt_token
from app.services.email_provider import EmailProvider

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_oauth_url(state: str) -> str:
    """Generate the Google OAuth 2.0 authorization URL."""
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",  # Request refresh_token
        "prompt": "consent",  # Always prompt to get refresh_token
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_google_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    settings = get_settings()
    payload = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.google_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()

        # Fetch connected Google user email
        access_token = token_data.get("access_token")
        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_res.raise_for_status()
        user_info = userinfo_res.json()

        return {
            "email": user_info.get("email"),
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in", 3600),
            "scopes": token_data.get("scope", "").split(" "),
        }


class GmailService(EmailProvider):
    """Production Gmail provider using official Google APIs and OAuth credentials."""

    def __init__(self, account_doc: dict):
        self.account_doc = account_doc
        self.user_id = str(account_doc["user_id"])
        self.email = account_doc["email"]
        self.settings = get_settings()

        access_token = decrypt_token(account_doc.get("encrypted_access_token"))
        refresh_token = decrypt_token(account_doc.get("encrypted_refresh_token"))

        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=GOOGLE_TOKEN_URL,
            client_id=self.settings.google_client_id,
            client_secret=self.settings.google_client_secret,
            scopes=GMAIL_SCOPES,
        )

    def _get_client(self):
        """Get or refresh google client credentials."""
        if self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
            except Exception as e:
                logger.error("Failed to refresh Google credentials for %s: %s", self.email, e)
                raise
        return build("gmail", "v1", credentials=self.credentials, cache_discovery=False)

    async def get_profile(self) -> dict:
        """Fetch user's Gmail mailbox profile and stats."""
        service = self._get_client()
        profile = service.users().getProfile(userId="me").execute()
        return {
            "email": profile.get("emailAddress", self.email),
            "messages_total": profile.get("messagesTotal", 0),
            "threads_total": profile.get("threadsTotal", 0),
            "status": "connected",
        }

    async def get_unread_emails(self, max_results: int = 20) -> list[dict]:
        """Fetch unread message headers and bodies from Gmail."""
        service = self._get_client()
        result = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=max_results)
            .execute()
        )
        messages_meta = result.get("messages", [])
        emails = []
        for meta in messages_meta:
            try:
                full_msg = await self.get_email(meta["id"])
                emails.append(full_msg)
            except Exception as exc:
                logger.warning("Error fetching email %s: %s", meta.get("id"), exc)
        return emails

    async def get_email(self, message_id: str) -> dict:
        """Retrieve full message details by ID."""
        service = self._get_client()
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        return self._parse_message(msg)

    async def get_thread(self, thread_id: str) -> list[dict]:
        """Fetch all messages within a conversation thread."""
        service = self._get_client()
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        return [self._parse_message(m) for m in thread.get("messages", [])]

    async def mark_as_read(self, message_id: str) -> bool:
        """Remove UNREAD label from a message."""
        service = self._get_client()
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()
        return True

    def _parse_message(self, msg: dict) -> dict:
        """Convert raw Gmail payload into normalized standard dictionary."""
        payload = msg.get("payload", {})
        headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}

        subject = headers.get("subject", "No Subject")
        sender = headers.get("from", "Unknown Sender")
        recipient = headers.get("to", "")
        date_str = headers.get("date", "")

        # Extract body text from parts or body
        body_text = self._extract_body(payload)

        return {
            "message_id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "body_text": body_text,
            "received_at": date_str,
            "is_unread": "UNREAD" in msg.get("labelIds", []),
            "labels": msg.get("labelIds", []),
            "snippet": msg.get("snippet", ""),
        }

    def _extract_body(self, payload: dict) -> str:
        """Extract plaintext from multipart or direct body payload."""
        if "data" in payload.get("body", {}):
            try:
                return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            except Exception:
                return ""

        parts = payload.get("parts", [])
        for part in parts:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain" and "data" in part.get("body", {}):
                try:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                except Exception:
                    continue
            elif "parts" in part:
                sub_body = self._extract_body(part)
                if sub_body:
                    return sub_body

        return ""
