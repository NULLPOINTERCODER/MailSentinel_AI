from datetime import datetime, timezone
from bson import ObjectId
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_database, get_user_service
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.main import app
from app.schemas.user import UserRegister
from app.services.user_service import UserService


class InMemoryUsersCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, query: dict):
        if "_id" in query:
            return self.docs.get(str(query["_id"]))
        if "email" in query:
            email_q = query["email"].lower()
            for doc in self.docs.values():
                if doc["email"].lower() == email_q:
                    return doc
        return None

    async def insert_one(self, doc: dict):
        new_id = ObjectId()
        doc_copy = dict(doc)
        doc_copy["_id"] = new_id
        self.docs[str(new_id)] = doc_copy
        class InsertResult:
            inserted_id = new_id
        return InsertResult()


class MockDB:
    def __init__(self):
        self.collections = {"users": InMemoryUsersCollection()}

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = InMemoryUsersCollection()
        return self.collections[name]


@pytest.fixture
def mock_user_service():
    mock_db = MockDB()
    return UserService(mock_db)


@pytest.fixture
def client(mock_user_service):
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_password_hashing():
    raw = "SuperSecret123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_jwt_token_generation_and_decoding():
    user_id = str(ObjectId())
    token = create_access_token(subject=user_id)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id


def test_register_success(client):
    payload = {
        "email": "user@example.com",
        "password": "Password123!",
        "full_name": "Test User",
        "whatsapp_number": "+1234567890",
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["full_name"] == "Test User"


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "Duplicate User",
    }
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"]


def test_login_success(client):
    payload = {
        "email": "login@example.com",
        "password": "Password123!",
        "full_name": "Login User",
    }
    client.post("/auth/register", json=payload)

    login_res = client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_invalid_password(client):
    payload = {
        "email": "wrongpass@example.com",
        "password": "Password123!",
    }
    client.post("/auth/register", json=payload)

    login_res = client.post(
        "/auth/login",
        json={"email": "wrongpass@example.com", "password": "IncorrectPassword"},
    )
    assert login_res.status_code == 401
    assert "Invalid email or password" in login_res.json()["detail"]


def test_get_me_authenticated(client):
    payload = {
        "email": "me@example.com",
        "password": "Password123!",
        "full_name": "Me User",
    }
    reg_res = client.post("/auth/register", json=payload)
    token = reg_res.json()["access_token"]

    me_res = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "me@example.com"
    assert data["full_name"] == "Me User"


def test_get_me_unauthorized(client):
    r = client.get("/auth/me")
    assert r.status_code == 401
