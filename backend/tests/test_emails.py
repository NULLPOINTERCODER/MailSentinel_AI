from datetime import datetime, timezone
from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.emails import get_email_service
from app.main import app
from app.schemas.user import UserResponse
from app.services.email_normalizer import EmailNormalizer, clean_html, compute_content_hash
from app.services.email_service import EmailService
from app.services.importance_scorer import ImportanceScorer


class InMemoryCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, query: dict):
        for doc in self.docs.values():
            match = True
            for k, v in query.items():
                if k == "$or":
                    or_match = False
                    for cond in v:
                        for cond_k, cond_v in cond.items():
                            if str(doc.get(cond_k)) == str(cond_v):
                                or_match = True
                                break
                    if not or_match:
                        match = False
                        break
                elif k == "_id" and str(doc.get("_id")) != str(v):
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
                elif k == "is_unread" and doc.get("is_unread") != v:
                    match = False
                    break
            if match:
                results.append(doc)

        class AsyncCursor:
            def __init__(self, items):
                self.items = items
            def sort(self, key, direction):
                return self
            def skip(self, n):
                self.items = self.items[n:]
                return self
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

    async def count_documents(self, query: dict) -> int:
        count = 0
        for doc in self.docs.values():
            match = True
            for k, v in query.items():
                if k == "user_id" and str(doc.get("user_id")) != str(v):
                    match = False
                    break
                elif k == "is_unread" and doc.get("is_unread") != v:
                    match = False
                    break
                elif k == "is_potentially_important" and doc.get("is_potentially_important") != v:
                    match = False
                    break
            if match:
                count += 1
        return count


class MockDB:
    def __init__(self):
        self.collections = {
            "emails": InMemoryCollection(),
            "email_accounts": InMemoryCollection(),
        }

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = InMemoryCollection()
        return self.collections[name]


@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture
def mock_email_service(mock_db):
    return EmailService(mock_db)


@pytest.fixture
def mock_user():
    return UserResponse(
        id=str(ObjectId()),
        email="developer@mailsentinel.ai",
        full_name="Senior Engineer",
        whatsapp_number="+919876543210",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def client(mock_email_service, mock_user):
    app.dependency_overrides[get_email_service] = lambda: mock_email_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_clean_html_and_hash():
    raw_html = "<p>Hello <b>Candidate</b>,<br/>Please complete your <i>online assessment</i>.</p>"
    cleaned = clean_html(raw_html)
    assert "Hello Candidate" in cleaned
    assert "online assessment" in cleaned
    assert "<p>" not in cleaned

    h1 = compute_content_hash("hr@google.com", "Interview Invitation", "Please join on Monday.")
    h2 = compute_content_hash("hr@google.com", "Interview Invitation", "Please join on Monday.")
    h3 = compute_content_hash("spam@promo.com", "Sale 50% Off", "Buy now")
    assert h1 == h2
    assert h1 != h3


def test_importance_scorer_signals():
    # 1. Critical interview email
    res1 = ImportanceScorer.calculate_rule_score(
        subject="Invitation: Google Software Engineer Interview",
        body_text="Dear candidate, please join your coding test assessment before the deadline.",
        sender_email="recruiting@google.com",
    )
    assert res1["rule_score"] >= 70
    assert res1["is_potentially_important"] is True
    signal_names = [s["signal"] for s in res1["positive_signals"]]
    assert "interview" in signal_names

    # 2. Obvious marketing / newsletter email
    res2 = ImportanceScorer.calculate_rule_score(
        subject="Weekly Sale: 50% discount on all items!",
        body_text="Click here to manage preferences or unsubscribe from this promotional newsletter.",
        sender_email="deals@promotions.shop",
    )
    assert res2["rule_score"] < 20
    assert res2["is_potentially_important"] is False
    assert len(res2["negative_signals"]) > 0


@pytest.mark.asyncio
async def test_ingest_email_and_deduplication(mock_email_service, mock_user):
    user_id = mock_user.id
    account_id = str(ObjectId())

    raw_mail = {
        "message_id": "msg_unique_101",
        "thread_id": "th_101",
        "sender": "IBM Recruiting <recruiter@ibm.com>",
        "recipient": "developer@mailsentinel.ai",
        "subject": "IBM Online Assessment Deadline",
        "body_text": "Please complete your online assessment before Friday deadline.",
        "received_at": "Tue, 29 Sep 2026 10:00:00 GMT",
        "is_unread": True,
    }

    # 1. First ingestion -> Succeeds
    saved = await mock_email_service.ingest_email(user_id, account_id, raw_mail)
    assert saved is not None
    assert saved["subject"] == "IBM Online Assessment Deadline"
    assert saved["sender_email"] == "recruiter@ibm.com"
    assert saved["rule_score"] >= 60
    assert saved["is_potentially_important"] is True

    # 2. Duplicate ingestion with same message_id -> Returns None (Skipped)
    duplicate = await mock_email_service.ingest_email(user_id, account_id, raw_mail)
    assert duplicate is None


def test_api_list_emails_and_stats(client, mock_email_service, mock_user):
    account_id = str(ObjectId())

    # Pre-populate 2 emails via service
    import asyncio
    asyncio.run(mock_email_service.ingest_email(
        mock_user.id,
        account_id,
        {
            "message_id": "msg_001",
            "subject": "Technical Interview Shortlist",
            "body_text": "You are shortlisted for the interview.",
            "sender": "hr@meta.com",
            "is_unread": True,
        }
    ))
    asyncio.run(mock_email_service.ingest_email(
        mock_user.id,
        account_id,
        {
            "message_id": "msg_002",
            "subject": "Weekly Newsletter",
            "body_text": "Unsubscribe here from weekly digest promo.",
            "sender": "news@store.com",
            "is_unread": False,
        }
    ))

    # 1. List all emails
    res = client.get("/api/emails")
    assert res.status_code == 200
    emails = res.json()
    assert len(emails) == 2

    # 2. Filter only potentially important
    res_important = client.get("/api/emails?only_important=true")
    assert res_important.status_code == 200
    important_emails = res_important.json()
    assert len(important_emails) == 1
    assert "Shortlist" in important_emails[0]["subject"]

    # 3. Get Stats summary
    res_stats = client.get("/api/emails/stats/summary")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_emails"] == 2
    assert stats["potentially_important"] == 1
