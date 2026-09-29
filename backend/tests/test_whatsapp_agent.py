import pytest
from bson import ObjectId
from mongomock_motor import AsyncMongoMockClient

from app.ai.base import AIProvider
from app.schemas.ai import AIAnalysisResult, EmailCategory, UrgencyLevel
from app.services.whatsapp_agent import WhatsAppConversationalAgent
from app.services.whatsapp_provider import WhatsAppProvider


class MockWhatsAppProvider(WhatsAppProvider):
    def __init__(self):
        self.sent_messages = []

    async def send_text_message(self, to_phone: str, message: str) -> dict:
        self.sent_messages.append({"to_phone": to_phone, "message": message})
        return {"success": True, "provider_message_id": f"mock_wamid_{len(self.sent_messages)}"}


class MockAIProvider(AIProvider):
    async def analyze_email(self, sender, subject, body_text, received_at=""):
        return AIAnalysisResult(
            category=EmailCategory.INTERVIEW,
            importance=95,
            urgency=UrgencyLevel.HIGH,
            action_required=True,
            deadline=None,
            summary="Interview email",
            action=None,
            reason="Test",
        )

    async def answer_rag_query(self, query: str, context: str) -> str:
        return f"RAG Agent answer for: '{query}'"


@pytest.fixture
def mock_db():
    client = AsyncMongoMockClient()
    return client["test_whatsapp_agent_db"]


@pytest.fixture
def mock_whatsapp():
    return MockWhatsAppProvider()


@pytest.fixture
def agent(mock_db, mock_whatsapp):
    return WhatsAppConversationalAgent(
        db=mock_db,
        whatsapp_provider=mock_whatsapp,
        ai_provider=MockAIProvider(),
    )


@pytest.mark.asyncio
async def test_unregistered_phone_handler(mock_whatsapp, agent):
    """If incoming message is from a non-linked number, reply with registration guidance."""
    res = await agent.process_inbound_message(
        from_phone="+910000000000",
        text="Show my important emails",
    )
    assert res["status"] == "unregistered"
    assert len(mock_whatsapp.sent_messages) == 1
    assert "Number Not Linked" in mock_whatsapp.sent_messages[0]["message"]


@pytest.mark.asyncio
async def test_registered_user_intents(mock_db, mock_whatsapp, agent):
    """Test full conversational routing for linked user."""
    user_id = str(ObjectId())
    phone = "+919876543210"

    # Link phone in preferences
    await mock_db["user_preferences"].insert_one({
        "user_id": user_id,
        "whatsapp_phone_number": phone,
        "whatsapp_notifications_enabled": True,
    })

    # Insert test emails
    email1 = {
        "_id": ObjectId(),
        "user_id": user_id,
        "sender_name": "Google Recruiter",
        "subject": "Interview Invitation",
        "final_importance": 95,
        "summary": "Google technical interview invite.",
        "category": "INTERVIEW",
        "deadline": "Friday 10:00 AM",
        "action": "Select a slot",
        "body_text": "Please confirm your availability for the Google technical screen.",
    }
    email2 = {
        "_id": ObjectId(),
        "user_id": user_id,
        "sender_name": "Meta Careers",
        "subject": "Online Assessment Round",
        "final_importance": 90,
        "summary": "Meta HackerRank assessment link.",
        "category": "ASSESSMENT",
        "deadline": "Sunday midnight",
        "action": "Complete test",
        "body_text": "Here is your online coding challenge link.",
    }

    await mock_db["emails"].insert_many([email1, email2])
    await agent.rag_service.index_single_email(user_id, email1)
    await agent.rag_service.index_single_email(user_id, email2)

    # 1. Intent: Help
    help_res = await agent.process_inbound_message(from_phone=phone, text="help")
    assert "MailSentinel AI Assistant" in help_res["reply"]

    # 2. Intent: Show important emails
    imp_res = await agent.process_inbound_message(from_phone=phone, text="Show my important emails")
    assert "TOP IMPORTANT EMAILS" in imp_res["reply"]
    assert "Google Recruiter" in imp_res["reply"]

    # 3. Intent: Check deadlines
    deadlines_res = await agent.process_inbound_message(from_phone=phone, text="Do I have any deadlines this week?")
    assert "UPCOMING DEADLINES" in deadlines_res["reply"]
    assert "Friday 10:00 AM" in deadlines_res["reply"]

    # 4. Intent: Summarize recruiters
    rec_res = await agent.process_inbound_message(from_phone=phone, text="summarize all recruiters")
    assert "RECRUITER & APPLICATION SUMMARY" in rec_res["reply"]

    # 5. Intent: Custom Query via RAG
    rag_res = await agent.process_inbound_message(from_phone=phone, text="What did Google say about my interview?")
    assert "RAG Agent answer" in rag_res["reply"]
