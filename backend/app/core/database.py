import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """Create the global Mongo client. Does not crash the app if Mongo is down."""
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    if await ping_mongo():
        logger.info("MongoDB connected (db=%s)", settings.mongodb_db_name)
    else:
        logger.warning("MongoDB not reachable at startup")


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping_mongo() -> bool:
    if _client is None:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001 - never leak details to users
        logger.warning("Mongo ping failed: %s", type(exc).__name__)
        return False


def get_database() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialised")
    return _client[get_settings().mongodb_db_name]
