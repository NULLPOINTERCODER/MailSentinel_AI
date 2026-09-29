import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai, auth, emails, gmail, health, notifications, rag, settings, webhook
from app.core.config import get_settings
from app.core.database import close_mongo, connect_to_mongo
from app.core.logging_config import setup_logging

setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Initializing MailSentinel AI services...")
    await connect_to_mongo()
    yield
    logger.info("Shutting down MailSentinel AI services...")
    await close_mongo()


def create_app() -> FastAPI:
    settings_cfg = get_settings()
    app = FastAPI(
        title=settings_cfg.app_name,
        version="1.0.0",
        description="Production-grade AI Email Intelligence and WhatsApp Notification Platform",
        lifespan=lifespan,
    )

    # Security Headers & Request Correlation Middleware
    @app.middleware("http")
    async def security_and_telemetry_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled server exception on %s %s: %s",
                request.method,
                request.url.path,
                str(exc),
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred. Please try again later.",
                    "request_id": request_id,
                },
            )

        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"
        # Security hardening headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings_cfg.frontend_url,
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time-Ms"],
    )

    # API Routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(gmail.router)
    app.include_router(emails.router)
    app.include_router(ai.router)
    app.include_router(rag.router)
    app.include_router(notifications.router)
    app.include_router(settings.router)
    app.include_router(webhook.router)

    return app


app = create_app()
