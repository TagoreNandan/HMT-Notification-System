from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Normalize provider-specific Postgres URLs for SQLAlchemy."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Product Availability Monitor"
    base_url: str = "http://localhost:8000"
    jwt_secret: str = "change-me-in-production"
    jwt_access_token_expire_days: int = 7
    database_url: str = "sqlite:///./data/monitor.db"
    poll_interval_seconds: int = 900
    request_timeout_seconds: int = 30
    max_products_per_user: int = 20
    email_verification_expire_hours: int = 24
    signup_rate_limit: str = "5/hour"
    notification_preference_rate_limit: str = "20/hour"
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Email via Resend (https://resend.com)
    resend_api_key: str = ""
    resend_from_email: str = ""

    # Legacy global notification setting (unused by per-user dispatcher)
    notification_channel: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_to: str = ""
    webhook_url: str = ""

    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_template_name: str = "product_update"
    whatsapp_api_version: str = "v23.0"

    @property
    def sqlalchemy_database_url(self) -> str:
        return normalize_database_url(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
