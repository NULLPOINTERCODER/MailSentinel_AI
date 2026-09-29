from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env."""

    app_name: str = "MailSentinel AI"
    environment: str = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "mailsentinel"

    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    # Authentication & Security
    jwt_secret: str = "mailsentinel-super-secret-change-in-production-key-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
