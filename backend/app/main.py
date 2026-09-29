import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, auth, emails, gmail, health, notifications, rag, settings
from app.core.config import get_settings
from app.core.database import close_mongo, connect_to_mongo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo()


def create_app() -> FastAPI:
    settings_cfg = get_settings()
    app = FastAPI(title=settings_cfg.app_name, version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings_cfg.frontend_url, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(gmail.router)
    app.include_router(emails.router)
    app.include_router(ai.router)
    app.include_router(rag.router)
    app.include_router(notifications.router)
    app.include_router(settings.router)
    return app


app = create_app()
