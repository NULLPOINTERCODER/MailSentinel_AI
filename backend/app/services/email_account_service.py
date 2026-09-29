from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.encryption import encrypt_token
from app.schemas.email_account import EmailAccountResponse


def email_account_doc_to_response(doc: dict) -> EmailAccountResponse:
    """Convert an email_account MongoDB document to public response schema."""
    return EmailAccountResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        provider=doc.get("provider", "gmail"),
        email=doc["email"],
        is_active=doc.get("is_active", True),
        scopes=doc.get("scopes", []),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )


class EmailAccountService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db["email_accounts"]

    async def get_by_user_and_email(self, user_id: str, email: str) -> dict | None:
        return await self.collection.find_one({
            "user_id": user_id,
            "email": email.lower(),
        })

    async def get_by_id(self, account_id: str, user_id: str) -> dict | None:
        if not ObjectId.is_valid(account_id):
            return None
        return await self.collection.find_one({
            "_id": ObjectId(account_id),
            "user_id": user_id,
        })

    async def get_user_accounts(self, user_id: str) -> list[dict]:
        cursor = self.collection.find({"user_id": user_id, "is_active": True})
        return await cursor.to_list(length=100)

    async def upsert_account(
        self,
        user_id: str,
        email: str,
        access_token: str,
        refresh_token: str | None,
        token_expiry: datetime | None,
        scopes: list[str],
        provider: str = "gmail",
    ) -> dict:
        now = datetime.now(timezone.utc)
        encrypted_access = encrypt_token(access_token)
        encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

        existing = await self.get_by_user_and_email(user_id, email)

        update_data = {
            "provider": provider,
            "encrypted_access_token": encrypted_access,
            "token_expiry": token_expiry,
            "scopes": scopes,
            "is_active": True,
            "updated_at": now,
        }

        # Keep existing refresh token if Google didn't return a new one on re-auth
        if encrypted_refresh:
            update_data["encrypted_refresh_token"] = encrypted_refresh

        if existing:
            await self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": update_data},
            )
            return await self.collection.find_one({"_id": existing["_id"]})
        else:
            doc = {
                "user_id": user_id,
                "email": email.lower(),
                **update_data,
                "created_at": now,
            }
            res = await self.collection.insert_one(doc)
            doc["_id"] = res.inserted_id
            return doc

    async def delete_account(self, account_id: str, user_id: str) -> bool:
        if not ObjectId.is_valid(account_id):
            return False
        result = await self.collection.delete_one({
            "_id": ObjectId(account_id),
            "user_id": user_id,
        })
        return result.deleted_count > 0
