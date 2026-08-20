from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_env: Literal["local", "test", "preview", "production"] = "local"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite+aiosqlite:///./var/equitylens.db"
    redis_url: str = "redis://localhost:6379/0"
    require_redis: bool = False
    data_mode: Literal["demo", "live"] = "demo"
    public_market_data_mode: Literal["demo", "licensed", "restricted"] = "demo"
    public_market_data_license_acknowledged: bool = False
    secret_key: str = "local-only-change-me-equitylens-secret-key"
    csrf_secret: str = "local-only-change-me-csrf-secret"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    email_token_minutes: int = 60
    reset_token_minutes: int = 30
    deletion_grace_days: int = 7
    email_provider: Literal["capture", "resend"] = "capture"
    email_capture_dir: str = "captured-emails"
    resend_api_key: str | None = None
    email_from: str = "EquityLens <noreply@localhost>"
    sender_domain_verified: bool = False
    sender_postal_address: str | None = None
    sec_user_agent: str | None = None
    alpaca_api_key: str | None = None
    alpaca_api_secret: str | None = None
    posthog_api_key: str | None = None
    posthog_host: str = "https://us.i.posthog.com"
    sentry_dsn: str | None = None
    cors_origins: str = "http://localhost:3000"
    demo_tasks_eager: bool = True
    model_version: str = "equitylens-v1"
    demo_seed: int = 20260819
    starting_cash: float = 100_000.0
    admin_emails: str = "admin@equitylens.demo"
    demo_user_email: str = "demo@equitylens.local"
    demo_user_password: str = "DemoResearch2026!"
    demo_admin_email: str = "admin@equitylens.demo"
    demo_admin_password: str = "DemoAdmin2026!"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def allowed_origins(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @model_validator(mode="after")
    def validate_production(self) -> Settings:
        if self.is_production:
            if self.secret_key.startswith("local-only") or self.csrf_secret.startswith(
                "local-only"
            ):
                raise ValueError("Production requires unique SECRET_KEY and CSRF_SECRET values")
            if (
                self.public_market_data_mode == "licensed"
                and not self.public_market_data_license_acknowledged
            ):
                raise ValueError(
                    "Licensed public data mode requires PUBLIC_MARKET_DATA_LICENSE_ACKNOWLEDGED=true"
                )
            if self.email_provider != "resend":
                raise ValueError("Production requires the verified Resend email provider")
            if not self.resend_api_key or not self.sender_domain_verified:
                raise ValueError(
                    "Resend production email requires an API key and verified sender domain"
                )
            if not self.sender_postal_address:
                raise ValueError("Production lifecycle email requires SENDER_POSTAL_ADDRESS")
            if not self.posthog_api_key or not self.sentry_dsn:
                raise ValueError("Production requires configured PostHog and Sentry projects")
            if self.data_mode == "live" and (
                not self.alpaca_api_key or not self.alpaca_api_secret or not self.sec_user_agent
            ):
                raise ValueError("Live data mode requires Alpaca credentials and SEC_USER_AGENT")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
