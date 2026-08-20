from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import ProductEvent

ALLOWED_EVENTS = {
    "landing_viewed",
    "public_stock_viewed",
    "signup_started",
    "signup_completed",
    "email_verified",
    "onboarding_completed",
    "user_activated",
    "stock_viewed",
    "watchlist_item_added",
    "screener_used",
    "backtest_started",
    "backtest_completed",
    "paper_trade_recorded",
    "share_clicked",
    "referral_landed",
    "feedback_submitted",
    "digest_opted_in",
    "digest_clicked",
    "account_deleted",
}
BLOCKED_PROPERTIES = {"email", "name", "token", "note", "message", "password"}


def safe_properties(properties: dict[str, object] | None) -> dict[str, object]:
    return {
        str(key)[:60]: value
        for key, value in (properties or {}).items()
        if key not in BLOCKED_PROPERTIES and isinstance(value, (str, int, float, bool, type(None)))
    }


class ProductAnalytics(ABC):
    @abstractmethod
    async def capture(
        self,
        name: str,
        *,
        user_id: str | None,
        anonymous_id: str | None = None,
        properties: dict[str, object] | None = None,
    ) -> None:
        pass


class PostHogAnalytics(ProductAnalytics):
    def __init__(self, api_key: str, host: str) -> None:
        self.api_key = api_key
        self.host = host.rstrip("/")

    async def capture(
        self,
        name: str,
        *,
        user_id: str | None,
        anonymous_id: str | None = None,
        properties: dict[str, object] | None = None,
    ) -> None:
        if name not in ALLOWED_EVENTS:
            return
        distinct_id = user_id or anonymous_id
        if not distinct_id:
            return
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                await client.post(
                    f"{self.host}/capture/",
                    json={
                        "api_key": self.api_key,
                        "event": name,
                        "distinct_id": distinct_id,
                        "properties": {
                            **safe_properties(properties),
                            "$process_person_profile": False,
                        },
                    },
                )
        except httpx.HTTPError:
            return


class DatabaseAnalytics(ProductAnalytics):
    """Persist an auditable event and mirror to PostHog when configured."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def capture(
        self,
        name: str,
        *,
        user_id: str | None,
        anonymous_id: str | None = None,
        properties: dict[str, object] | None = None,
    ) -> None:
        if name not in ALLOWED_EVENTS:
            return
        sanitized = safe_properties(properties)
        self.session.add(
            ProductEvent(
                user_id=user_id,
                anonymous_id=anonymous_id[:64] if anonymous_id else None,
                name=name,
                properties=sanitized,
                occurred_at=datetime.now(UTC),
            )
        )
        settings = get_settings()
        if settings.posthog_api_key and settings.app_env in {"preview", "production"}:
            await PostHogAnalytics(settings.posthog_api_key, settings.posthog_host).capture(
                name,
                user_id=user_id,
                anonymous_id=anonymous_id,
                properties=sanitized,
            )


class NoopAnalytics(ProductAnalytics):
    async def capture(
        self,
        name: str,
        *,
        user_id: str | None,
        anonymous_id: str | None = None,
        properties: dict[str, object] | None = None,
    ) -> None:
        return None
