import pytest
from bson import ObjectId
import chromadb
from mongomock_motor import AsyncMongoMockClient

from app.ai.base import AIProvider
from app.schemas.ai import AIAnalysisResult, EmailCategory, UrgencyLevel
from app.services.rag_service import RAGService


class MockRAGAIProvider(AIProvider):
    async def analyze_email(self, sender, subject, body_text, received_at=""):
        return AIAnalysisResult(
            category=EmailCategory.INTERVIEW,
            importance=95,
            urgency=UrgencyLevel.HIGH,
            action_required=True,
            deadline="Friday 10 AM",
            summary="Interview with Google recruiter.",
            action="Confirm time",
            reason="Interview invitation",
        )

    async def answer_rag_query(self, query: str, context: str) -> str:
        return f"Synthesized answer for '{query}' based on {len(context)} context characters."


@pytest.fixture
def mock_db():
    client = AsyncMongoMockClient()
    return client["test_mailsentinel_rag"]


@pytest.fixture
def in_memory_chroma():
    return chromadb.EphemeralClient()


@pytest.fixture
def rag_service(mock_db, in_memory_chroma):
    return RAGService(
        db=mock_db,
        ai_provider=MockRAGAIProvider(),
        chroma_client=in_memory_chroma,
    )


@pytest.mark.asyncio
async def test_document_text_preparation(rag_service):
    email_doc = {
        "_id": ObjectId(),
        "sender_name": "Stripe Hiring",
        "sender_email": "jobs@stripe.com",
        "subject": "Staff Backend Engineer - Next Steps",
        "summary": "You have passed the preliminary screening call.",
        "action": "Schedule technical deep dive",
        "deadline": "October 20, 2026",
        "body_text": "Congratulations! We would like to invite you to the system design round.",
    }
    prepared = rag_service._prepare_document_text(email_doc)
    assert "Sender: Stripe Hiring <jobs@stripe.com>" in prepared
    assert "Subject: Staff Backend Engineer - Next Steps" in prepared
    assert "AI Summary: You have passed the preliminary screening call." in prepared
    assert "Action: Schedule technical deep dive" in prepared
    assert "Deadline: October 20, 2026" in prepared


@pytest.mark.asyncio
async def test_multi_user_vector_isolation(mock_db, rag_service):
    """Verify that vector retrieval strictly isolates emails by user_id."""
    user_alice = "user_alice_111"
    user_bob = "user_bob_222"

    # Alice's email: Amazon Job Offer
    alice_email = {
        "_id": ObjectId(),
        "user_id": user_alice,
        "sender_name": "Amazon HR",
        "sender_email": "offers@amazon.com",
        "subject": "Amazon SDE-2 Formal Offer Letter",
        "summary": "Formal offer letter for SDE-2 in Seattle.",
        "body_text": "We are pleased to offer you the position with starting compensation of $180k.",
    }
    await mock_db["emails"].insert_one(alice_email)
    await rag_service.index_single_email(user_alice, alice_email)

    # Bob's email: Netflix Interview
    bob_email = {
        "_id": ObjectId(),
        "user_id": user_bob,
        "sender_name": "Netflix Talent",
        "sender_email": "recruiting@netflix.com",
        "subject": "Netflix Technical Screen Invitation",
        "summary": "Invitation to Netflix engineering screen.",
        "body_text": "Please confirm your availability for next Wednesday.",
    }
    await mock_db["emails"].insert_one(bob_email)
    await rag_service.index_single_email(user_bob, bob_email)

    # 1. Bob queries for "Amazon offer" -> MUST NOT return Alice's Amazon email (User isolation)
    bob_result = await rag_service.query_and_answer(
        user_id=user_bob,
        query="Amazon offer compensation",
    )
    assert not any(s.email_id == str(alice_email["_id"]) for s in bob_result.sources)
    assert not any("Amazon" in s.subject for s in bob_result.sources)

    # 2. Alice queries for "Amazon offer" -> MUST find her offer document
    alice_result = await rag_service.query_and_answer(
        user_id=user_alice,
        query="Amazon offer compensation",
    )
    assert len(alice_result.sources) >= 1
    assert any(s.email_id == str(alice_email["_id"]) for s in alice_result.sources)
    assert any("Amazon" in s.subject for s in alice_result.sources)


@pytest.mark.asyncio
async def test_reindexing_and_query_flow(mock_db, rag_service):
    """Test bulk re-indexing and retrieval pipeline."""
    user_id = "user_charlie_333"

    email1 = {
        "_id": ObjectId(),
        "user_id": user_id,
        "sender_name": "HackerRank Assessment",
        "sender_email": "support@hackerrank.com",
        "subject": "Goldman Sachs Coding Challenge Link",
        "summary": "Goldman Sachs 90-minute coding assessment on algorithms.",
        "deadline": "Sunday midnight",
        "action": "Complete test before expiry",
        "body_text": "Your coding challenge is now live. Click here to start.",
    }
    email2 = {
        "_id": ObjectId(),
        "user_id": user_id,
        "sender_name": "Uber Recruiter",
        "sender_email": "talent@uber.com",
        "subject": "Recruiter Screen Follow-up",
        "summary": "Uber recruiter scheduled introductory screening call.",
        "body_text": "Let's connect over Zoom to discuss the Senior Platform Engineer role.",
    }
    await mock_db["emails"].insert_many([email1, email2])

    # Reindex all emails
    reindex_res = await rag_service.reindex_all_user_emails(user_id)
    assert reindex_res.indexed_emails == 2
    assert reindex_res.status == "completed"

    # Query RAG
    query_res = await rag_service.query_and_answer(
        user_id=user_id,
        query="When is my Goldman Sachs coding challenge deadline?",
    )
    assert len(query_res.sources) >= 1
    assert query_res.context_emails_count >= 1
    assert any("Goldman Sachs" in s.subject for s in query_res.sources)
