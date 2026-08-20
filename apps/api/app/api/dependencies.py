from __future__ import annotations

from datetime import UTC, datetime

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db


async def current_user_optional(
    access_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    if not access_token:
        return None
    try:
        payload = decode_access_token(access_token, settings)
    except jwt.PyJWTError:
        return None
    user = await session.get(User, str(payload["sub"]))
    if not user or not user.is_active:
        return None
    return user


async def current_user(user: User | None = Depends(current_user_optional)) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    return user


async def verified_user(user: User = Depends(current_user)) -> User:
    if user.deletion_requested_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deletion is pending; cancel the request to continue",
        )
    if not user.email_verified_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required"
        )
    return user


async def admin_user(user: User = Depends(verified_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required"
        )
    return user


async def require_csrf(
    request: Request,
    access_token: str | None = Cookie(default=None),
    csrf_cookie: str | None = Cookie(default=None, alias="csrf_token"),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.app_env == "test" or not access_token:
        return
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")


def utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)
