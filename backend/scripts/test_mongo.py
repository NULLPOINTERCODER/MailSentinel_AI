"""Run from backend/: python -m scripts.test_mongo"""
import asyncio

from app.core.database import close_mongo, connect_to_mongo, ping_mongo


async def main() -> None:
    await connect_to_mongo()
    ok = await ping_mongo()
    print("MongoDB connection:", "OK" if ok else "FAILED")
    await close_mongo()


asyncio.run(main())
