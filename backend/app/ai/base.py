from abc import ABC, abstractmethod
from app.schemas.ai import AIAnalysisResult


class AIProvider(ABC):
    """Abstract base class for Large Language Model triage providers."""

    @abstractmethod
    async def analyze_email(
        self,
        sender: str,
        subject: str,
        body_text: str,
        received_at: str = "",
    ) -> AIAnalysisResult:
        """Analyze an email and return structured category, importance, summary, action, and deadline."""
        raise NotImplementedError

    @abstractmethod
    async def answer_rag_query(
        self,
        query: str,
        context: str,
    ) -> str:
        """Answer a natural language question using retrieved email context without hallucination."""
        raise NotImplementedError

