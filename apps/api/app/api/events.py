from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user_optional
from app.db.models import User
from app.db.session import get_db
from app.services.analytics import DatabaseAnalytics

router = APIRouter()


class BrowserEvent(BaseModel):
    name: Literal[
        "landing_viewed",
        "signup_started",
        "share_clicked",
        "digest_clicked",
        "referral_landed",
    ]
    properties: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


@router.post("/events", status_code=status.HTTP_202_ACCEPTED, tags=["analytics"])
async def capture_browser_event(
    payload: BrowserEvent,
    anonymous_id: str | None = Header(default=None, alias="X-Anonymous-Id"),
    user: User | None = Depends(current_user_optional),
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Accept an allow-listed, privacy-minimized product event."""
    if user and not user.analytics_enabled:
        return {"accepted": True}
    await DatabaseAnalytics(session).capture(
        payload.name,
        user_id=user.id if user and user.analytics_enabled else None,
        anonymous_id=(anonymous_id or "")[:64] or None,
        properties=dict(payload.properties),
    )
    await session.commit()
    return {"accepted": True}
