from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_database
from app.api.gmail import get_email_account_service
from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.main import app
from app.schemas.user import UserResponse
from app.services.email_account_service import EmailAccountService


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
                elif k != "_id" and doc.get(k) != v:
                    match = False
                    break
            if match:
                results.append(doc)

        class AsyncCursor:
            def __init__(self, items):
                self.items = items
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

    async def update_one(self, query: dict, update: dict):
        doc = await self.find_one(query)
        if doc and "$set" in update:
            doc.update(update["$set"])

    async def delete_one(self, query: dict):
        doc = await self.find_one(query)
        if doc:
            del self.docs[str(doc["_id"])]
            class DeleteResult:
                deleted_count = 1
            return DeleteResult()
        class DeleteResult:
            deleted_count = 0
        return DeleteResult()


class MockDB:
    def __init__(self):
        self.collections = {"email_accounts": InMemoryCollection()}

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = InMemoryCollection()
        return self.collections[name]


@pytest.fixture
def mock_db():
    return MockDB()


@pytest.fixture
def mock_account_service(mock_db):
    return EmailAccountService(mock_db)


@pytest.fixture
def mock_user():
    return UserResponse(
        id=str(ObjectId()),
        email="testuser@example.com",
        full_name="Test User",
        whatsapp_number="+1234567890",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def client(mock_account_service, mock_user):
    app.dependency_overrides[get_email_account_service] = lambda: mock_account_service
    app.dependency_overrides[get_current_user] = lambda: mock_user
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_token_encryption_and_decryption():
    raw_token = "ya29.a0AfH6SMD_sample_google_access_token_123456"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    assert decrypt_token(encrypted) == raw_token
    assert decrypt_token(None) is None
    assert decrypt_token("invalid_cipher_text") is None


def test_get_oauth_url(client, mock_user):
    settings = get_settings()
    settings.google_client_id = "test-client-id.apps.googleusercontent.com"

    res = client.get("/api/gmail/oauth/url")
    assert res.status_code == 200
    data = res.json()
    assert "accounts.google.com" in data["url"]
    assert "test-client-id.apps.googleusercontent.com" in data["url"]
    assert mock_user.id in data["state"]


@patch("app.api.gmail.exchange_google_code_for_tokens", new_callable=AsyncMock)
def test_oauth_callback_success(mock_exchange, client, mock_user):
    mock_exchange.return_value = {
        "email": "connected.gmail@gmail.com",
        "access_token": "mock_access_token_abc",
        "refresh_token": "mock_refresh_token_xyz",
        "expires_in": 3600,
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    }

    state = f"{mock_user.id}:valid_csrf_nonce"
    res = client.post(
        "/api/gmail/oauth/callback",
        json={"code": "sample_auth_code_from_google", "state": state},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "connected.gmail@gmail.com"
    assert data["user_id"] == mock_user.id
    assert data["provider"] == "gmail"
    assert data["is_active"] is True
    # Ensure sensitive tokens are NEVER leaked in response
    assert "access_token" not in data
    assert "refresh_token" not in data


def test_oauth_callback_invalid_state_fails(client, mock_user):
    res = client.post(
        "/api/gmail/oauth/callback",
        json={"code": "some_code", "state": "wrong_user_id:nonce"},
    )
    assert res.status_code == 400
    assert "CSRF" in res.json()["detail"]


@patch("app.api.gmail.exchange_google_code_for_tokens", new_callable=AsyncMock)
def test_list_and_disconnect_account(mock_exchange, client, mock_user):
    mock_exchange.return_value = {
        "email": "user.test@gmail.com",
        "access_token": "token_123",
        "refresh_token": "refresh_123",
        "expires_in": 3600,
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    }

    state = f"{mock_user.id}:random_state_123"
    connect_res = client.post(
        "/api/gmail/oauth/callback",
        json={"code": "code_123", "state": state},
    )
    account_id = connect_res.json()["id"]

    # 1. List accounts
    list_res = client.get("/api/gmail/accounts")
    assert list_res.status_code == 200
    accounts = list_res.json()
    assert len(accounts) == 1
    assert accounts[0]["id"] == account_id
    assert accounts[0]["email"] == "user.test@gmail.com"

    # 2. Delete account
    del_res = client.delete(f"/api/gmail/accounts/{account_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"

    # 3. Verify accounts list is now empty
    empty_list_res = client.get("/api/gmail/accounts")
    assert len(empty_list_res.json()) == 0
