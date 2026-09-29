from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.ai.base import AIProvider
from app.ai.groq_provider import GroqProvider, extract_json_block
from app.api.ai import get_ai_pipeline_service
from app.api.deps import get_current_user
from app.main import app
from app.schemas.ai import AIAnalysisResult, EmailCategory, UrgencyLevel
from app.schemas.user import UserResponse
from app.services.ai_pipeline import AIPipelineService


class InMemoryCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, query: dict):
        for doc in self.docs.values():
            match = True
            for k, v in query.items():
                if k == "_id" and str(doc.get("_id")) != str(v):
                    match = False
                    break
                elif k != "_id" and doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc
        return None

    def find(self, query: dict):
        results = []
        for doc in self.docs.values():
            match = True
            for k, v in query.items():
                if k == "_id" and str(doc.get("_id")) != str(v):
                    match = False
                    break
                elif k == "user_id" and str(doc.get("user_id")) != str(v):
                    match = False
                    break
                elif k == "is_potentially_important" and doc.get("is_potentially_important") != v:
                    match = False
                    break
            if match:
                results.append(doc)

        class AsyncCursor:
            def __init__(self, items):
                self.items = items
            def limit(self, n):
                self.items = self.items[:n]
                return self
            async def to_list(self, length: int):
                return self.items[:length]

        return AsyncCursor(results)

    async def insert_one(self, doc: dict):
        new_id = ObjectId()
        doc_copy = dict(doc)
        doc_copy["_id"] = new_id
        self.docs[str(new_id)] = doc_copy
        class InsertResult:
            inserted_id = new_id
        return InsertResult()

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        doc = await self.find_one(query)
        if doc:
            if "$set" in update:
                doc.update(update["$set"])
        elif upsert:
            await self.insert_one(update.get("$set", {}))


class MockDB:
    def __init__(self):
        self.collections = {
            "emails": InMemoryCollection(),
            "classifications": InMemoryCollection(),
        }

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = InMemoryCollection()
        return self.collections[name]


class MockAIProvider(AIProvider):
    async def analyze_email(self, sender: str, subject: str, body_text: str, received_at: str = "") -> AIAnalysisResult:
        return AIAnalysisResult(
            category=EmailCategory.INTERVIEW,
            importance=95,
            urgency=UrgencyLevel.HIGH,
            action_required=True,
            deadline="2026-10-02T23:59:00",
            summary="IBM has invited you to complete an online assessment before October 2, 2026.",
            action="Complete the online assessment before the deadline.",
            reason="Email contains an interview invitation with strict deadline.",
        )

    async def answer_rag_query(self, query: str, context: str) -> str:
        return f"Mock RAG Answer for: {query}"



@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture
def mock_user():
    return UserResponse(
        id=str(ObjectId()),
        email="ai_tester@mailsentinel.ai",
        full_name="AI Engineer",
        whatsapp_number="+919876543210",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_ai_pipeline(mock_db):
    return AIPipelineService(mock_db, ai_provider=MockAIProvider())


@pytest.fixture
def client(mock_ai_pipeline, mock_user):
    app.dependency_overrides[get_ai_pipeline_service] = lambda: mock_ai_pipeline
    app.dependency_overrides[get_current_user] = lambda: mock_user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_ai_analysis_result_schema():
    data = {
        "category": "INTERVIEW",
        "importance": 92,
        "urgency": "HIGH",
        "action_required": True,
        "deadline": "2026-10-05T18:00:00",
        "summary": "Technical interview with senior team.",
        "action": "Join Google Meet link on Monday.",
        "reason": "Direct interview invitation.",
    }
    result = AIAnalysisResult(**data)
    assert result.category == EmailCategory.INTERVIEW
    assert result.importance == 92
    assert result.action_required is True


def test_extract_json_block_helper():
    raw_markdown = """Here is the analysis:
```json
{
  "category": "OFFER",
  "importance": 98,
  "urgency": "CRITICAL",
  "action_required": true,
  "deadline": null,
  "summary": "Formal job offer received.",
  "action": "Sign and return offer letter.",
  "reason": "Official employment offer."
}
```"""
    parsed = extract_json_block(raw_markdown)
    assert parsed["category"] == "OFFER"
    assert parsed["importance"] == 98


def test_groq_heuristic_fallback_when_no_api_key():
    provider = GroqProvider(api_key="")
    import asyncio
    res = asyncio.run(provider.analyze_email(
        sender="hr@company.com",
        subject="Interview Shortlist",
        body_text="You are shortlisted for the coding assessment round.",
    ))
    assert res.category == EmailCategory.INTERVIEW
    assert res.importance >= 85
    assert res.action_required is True


def test_hybrid_importance_calculation(mock_ai_pipeline):
    # Rule score = 80, AI score = 90
    # (0.35 * 80) + (0.65 * 90) = 28 + 58.5 = 86.5 -> 86 or 87
    score = mock_ai_pipeline.calculate_hybrid_importance(80, 90)
    assert score in {86, 87}


@pytest.mark.asyncio
async def test_triage_single_email_pipeline(mock_db, mock_user):
    pipeline = AIPipelineService(mock_db, ai_provider=MockAIProvider())
    email_doc = {
        "user_id": mock_user.id,
        "account_id": str(ObjectId()),
        "message_id": "msg_ai_001",
        "subject": "IBM Assessment",
        "body_text": "Complete by October 2, 2026.",
        "rule_score": 75,
        "is_potentially_important": True,
        "is_unread": True,
        "created_at": datetime.now(timezone.utc),
    }
    res_insert = await mock_db["emails"].insert_one(email_doc)
    email_id = str(res_insert.inserted_id)

    triage_res = await pipeline.triage_email(email_id, mock_user.id)
    assert triage_res is not None
    assert triage_res.category == EmailCategory.INTERVIEW
    assert triage_res.deadline == "2026-10-02T23:59:00"
    assert triage_res.final_importance >= 80
    assert triage_res.is_whatsapp_candidate is True

    # Verify classification collection
    saved_classification = await mock_db["classifications"].find_one({"email_id": email_id})
    assert saved_classification is not None
    assert saved_classification["final_importance"] == triage_res.final_importance


def test_api_triage_endpoints(client, mock_db, mock_user):
    import asyncio
    # Insert test email
    email_doc = {
        "user_id": mock_user.id,
        "account_id": str(ObjectId()),
        "message_id": "msg_api_test_01",
        "subject": "Amazon Interview Invitation",
        "body_text": "Please confirm your availability for technical interview round.",
        "rule_score": 70,
        "is_potentially_important": True,
        "is_unread": True,
        "ai_processed": False,
        "created_at": datetime.now(timezone.utc),
    }
    res_insert = asyncio.run(mock_db["emails"].insert_one(email_doc))
    email_id = str(res_insert.inserted_id)

    # Call POST /api/ai/triage/{email_id}
    res = client.post(f"/api/ai/triage/{email_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "INTERVIEW"
    assert data["urgency"] == "HIGH"
    assert data["action_required"] is True
    assert data["deadline"] == "2026-10-02T23:59:00"
    assert "IBM" in data["summary"]
