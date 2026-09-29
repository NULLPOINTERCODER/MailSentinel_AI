import json
import logging
import re
from groq import AsyncGroq

from app.ai.base import AIProvider
from app.ai.prompts import (
    EMAIL_ANALYSIS_SYSTEM_PROMPT,
    EMAIL_ANALYSIS_USER_TEMPLATE,
    RAG_QUERY_SYSTEM_PROMPT,
    RAG_QUERY_USER_TEMPLATE,
)
from app.core.config import get_settings
from app.schemas.ai import AIAnalysisResult, EmailCategory, UrgencyLevel

logger = logging.getLogger(__name__)


def extract_json_block(text: str) -> dict:
    """Extract and parse JSON from LLM response text safely."""
    text = text.strip()
    # If wrapped in markdown ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Direct JSON search
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])
    return json.loads(text)


class GroqProvider(AIProvider):
    """Primary LLM provider using official Groq API with structured JSON output."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.groq_api_key
        # Default to llama-3.3-70b-versatile or configurable from .env
        self.model = model or settings.groq_model or "openai/gpt-oss-120b"
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    async def analyze_email(
        self,
        sender: str,
        subject: str,
        body_text: str,
        received_at: str = "",
    ) -> AIAnalysisResult:
        if not self.client:
            logger.warning("GROQ_API_KEY is not configured. Falling back to heuristic baseline.")
            return self._heuristic_fallback(sender, subject, body_text)

        # Truncate extremely long email bodies (cost & context optimization)
        truncated_body = body_text[:4000] if len(body_text) > 4000 else body_text
        user_message = EMAIL_ANALYSIS_USER_TEMPLATE.format(
            sender=sender,
            subject=subject,
            received_at=received_at,
            body_text=truncated_body,
        )

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": EMAIL_ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                model=self.model,
                temperature=0.1,  # Low temperature for strict factual extraction
                response_format={"type": "json_object"},
            )

            raw_response = chat_completion.choices[0].message.content
            parsed = extract_json_block(raw_response)
            return AIAnalysisResult(**parsed)
        except Exception as exc:
            logger.error("Groq API error during email analysis: %s. Using heuristic fallback.", exc)
            return self._heuristic_fallback(sender, subject, body_text)

    async def answer_rag_query(
        self,
        query: str,
        context: str,
    ) -> str:
        """Synthesize a factual, grounded answer using retrieved email context."""
        if not self.client:
            logger.warning("GROQ_API_KEY is not set. Generating mock/fallback answer.")
            return (
                f"Based on your retrieved emails, here is the relevant context found for '{query}':\n\n"
                f"{context[:400]}...\n\n"
                f"*(Configure GROQ_API_KEY in .env for full Groq LLM synthesis)*"
            )

        user_content = RAG_QUERY_USER_TEMPLATE.format(query=query, context=context)

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": RAG_QUERY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                model=self.model,
                temperature=0.2,
            )
            return chat_completion.choices[0].message.content or "No response generated."
        except Exception as e:
            logger.error("Groq RAG query error: %s", e)
            return f"Error querying Groq AI: {str(e)}"

    def _heuristic_fallback(self, sender: str, subject: str, body: str) -> AIAnalysisResult:
        """Safe heuristic fallback if Groq API is temporarily unreachable or unconfigured."""
        combined = f"{subject} {body}".lower()
        if "offer" in combined:
            cat = EmailCategory.OFFER
            imp = 95
            urg = UrgencyLevel.HIGH
        elif "interview" in combined or "assessment" in combined:
            cat = EmailCategory.INTERVIEW
            imp = 90
            urg = UrgencyLevel.HIGH
        elif "security" in combined or "password" in combined or "alert" in combined:
            cat = EmailCategory.SECURITY
            imp = 85
            urg = UrgencyLevel.CRITICAL
        elif "newsletter" in combined or "unsubscribe" in combined:
            cat = EmailCategory.NEWSLETTER
            imp = 15
            urg = UrgencyLevel.LOW
        elif "sale" in combined or "discount" in combined or "promo" in combined:
            cat = EmailCategory.PROMOTION
            imp = 10
            urg = UrgencyLevel.LOW
        else:
            cat = EmailCategory.GENERAL
            imp = 50
            urg = UrgencyLevel.MEDIUM

        return AIAnalysisResult(
            category=cat,
            importance=imp,
            urgency=urg,
            action_required=imp >= 75,
            deadline=None,
            summary=f"Email from {sender} regarding '{subject}'.",
            action="Review email details and respond if necessary." if imp >= 75 else None,
            reason="Heuristic evaluation baseline.",
        )
