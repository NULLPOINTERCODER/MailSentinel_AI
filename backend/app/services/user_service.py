from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import EmailStr

from app.core.security import hash_password, verify_password
from app.schemas.user import UserRegister, UserResponse


def user_doc_to_response(doc: dict) -> UserResponse:
    """Convert a MongoDB user document into a UserResponse schema."""
    return UserResponse(
        id=str(doc["_id"]),
        email=doc["email"],
        full_name=doc.get("full_name"),
        whatsapp_number=doc.get("whatsapp_number"),
        is_active=doc.get("is_active", True),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
    )


class UserService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["users"]

    async def get_by_email(self, email: str | EmailStr) -> dict | None:
        """Find a user by email address (case-insensitive)."""
        return await self.collection.find_one({"email": str(email).lower()})

    async def get_by_id(self, user_id: str) -> dict | None:
        """Find a user by MongoDB ObjectId."""
        if not ObjectId.is_valid(user_id):
            return None
        return await self.collection.find_one({"_id": ObjectId(user_id)})

    async def create_user(self, payload: UserRegister) -> dict:
        """Create a new user document in MongoDB with a hashed password."""
        now = datetime.now(timezone.utc)
        user_dict = {
            "email": payload.email.lower(),
            "hashed_password": hash_password(payload.password),
            "full_name": payload.full_name,
            "whatsapp_number": payload.whatsapp_number,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        return user_dict

    async def authenticate(self, email: str, password: str) -> dict | None:
        """Authenticate user credentials."""
        user = await self.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.get("hashed_password", "")):
            return None
        return user
