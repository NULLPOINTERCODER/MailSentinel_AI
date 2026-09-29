import hashlib
import re
from datetime import datetime, timezone
from email.utils import parseaddr


def clean_html(html_text: str) -> str:
    """Strip HTML tags, scripts, styles, and convert entities to plain text."""
    if not html_text:
        return ""
    # Remove script and style elements
    text = re.sub(r"<(script|style).*?>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    # Replace line break tags with newlines
    text = re.sub(r"<(br|p|div|tr)[\s/>]", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse multiple whitespaces / blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def strip_email_signatures(text: str) -> str:
    """Strip common email signature markers (e.g. '-- ', 'Best regards', 'Sent from my iPhone')."""
    sig_patterns = [
        r"\n--\s*\n.*$",
        r"\nSent from my (iPhone|Galaxy|Android|iPad|mobile).*$",
        r"\nGet Outlook for (iOS|Android).*$",
    ]
    cleaned = text
    for pattern in sig_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


def compute_content_hash(sender: str, subject: str, body: str) -> str:
    """Generate deterministic SHA-256 hash for deduplication."""
    norm_sender = sender.lower().strip()
    norm_subject = subject.lower().strip()
    norm_body = re.sub(r"\s+", " ", body.lower().strip())
    raw = f"{norm_sender}|{norm_subject}|{norm_body[:500]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class EmailNormalizer:
    @staticmethod
    def normalize(raw_email: dict, provider: str = "gmail") -> dict:
        """Convert raw provider payload into standardized MailSentinel internal format."""
        raw_sender = raw_email.get("sender", "")
        sender_name, sender_email = parseaddr(raw_sender)
        if not sender_email:
            sender_email = raw_sender

        subject = (raw_email.get("subject") or "No Subject").strip()
        body_text = raw_email.get("body_text", "")
        if "<html" in body_text.lower() or "<body" in body_text.lower() or "<div" in body_text.lower():
            body_text = clean_html(body_text)

        body_text = strip_email_signatures(body_text)
        snippet = (raw_email.get("snippet") or body_text[:160]).strip()
        content_hash = compute_content_hash(sender_email, subject, body_text)

        return {
            "provider": provider,
            "message_id": raw_email.get("message_id"),
            "thread_id": raw_email.get("thread_id"),
            "sender_name": sender_name or sender_email.split("@")[0],
            "sender_email": sender_email.lower(),
            "recipient": raw_email.get("recipient", ""),
            "subject": subject,
            "body_text": body_text,
            "snippet": snippet,
            "received_at": raw_email.get("received_at", ""),
            "is_unread": raw_email.get("is_unread", True),
            "labels": raw_email.get("labels", []),
            "content_hash": content_hash,
            "normalized_at": datetime.now(timezone.utc),
        }
