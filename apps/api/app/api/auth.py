from __future__ import annotations

import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import current_user, require_csrf, utc
from app.api.schemas import (
    DemoLoginInput,
    EmailInput,
    LoginInput,
    RegisterInput,
    ResetPasswordInput,
    TokenInput,
)
from app.core.config import Settings, get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    random_token,
    verify_password,
)
from app.db.models import (
    Attribution,
    AuditEvent,
    EmailActionToken,
    EmailDelivery,
    PaperPortfolio,
    RefreshSession,
    User,
)
from app.db.session import get_db
from app.services.analytics import DatabaseAnalytics
from app.services.email import email_provider, reset_email, verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
rate_windows: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request, action: str, maximum: int = 10, window_seconds: int = 60) -> None:
    key = f"{action}:{request.client.host if request.client else 'unknown'}"
    now = time.monotonic()
    bucket = rate_windows[key]
    while bucket and bucket[0] < now - window_seconds:
        bucket.popleft()
    if len(bucket) >= maximum:
        raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")
    bucket.append(now)


def user_payload(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "verified": bool(user.email_verified_at),
        "onboarding_completed": bool(user.onboarding_completed_at),
        "activated": bool(user.activated_at),
        "is_demo": user.is_demo,
        "deletion_requested": bool(user.deletion_requested_at),
        "theme": user.theme,
        "referral_code": user.referral_code,
    }


async def set_session(
    response: Response,
    user: User,
    session: AsyncSession,
    settings: Settings,
    family_id: str | None = None,
) -> None:
    now = datetime.now(UTC)
    raw_refresh = random_token(48)
    family = family_id or str(uuid.uuid4())
    session.add(
        RefreshSession(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            family_id=family,
            expires_at=now + timedelta(days=settings.refresh_token_days),
            created_at=now,
        )
    )
    await session.flush()
    access = create_access_token(user.id, user.role, bool(user.email_verified_at), settings)
    csrf = secrets.token_urlsafe(24)
    cookie = {"secure": settings.is_production, "samesite": "lax", "path": "/"}
    response.set_cookie(
        "access_token", access, httponly=True, max_age=settings.access_token_minutes * 60, **cookie
    )
    response.set_cookie(
        "refresh_token",
        raw_refresh,
        httponly=True,
        max_age=settings.refresh_token_days * 86400,
        **cookie,
    )
    response.set_cookie(
        "csrf_token", csrf, httponly=False, max_age=settings.refresh_token_days * 86400, **cookie
    )


async def issue_action_token(session: AsyncSession, user: User, purpose: str, minutes: int) -> str:
    now = datetime.now(UTC)
    await session.execute(
        update(EmailActionToken)
        .where(
            EmailActionToken.user_id == user.id,
            EmailActionToken.purpose == purpose,
            EmailActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    raw = random_token(36)
    session.add(
        EmailActionToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=hash_token(raw),
            expires_at=now + timedelta(minutes=minutes),
            created_at=now,
        )
    )
    return raw


async def send_action_email(
    session: AsyncSession, user: User, purpose: str, raw: str, settings: Settings
) -> None:
    subject, text = (
        verification_email(settings.app_base_url, raw)
        if purpose == "verify"
        else reset_email(settings.app_base_url, raw)
    )
    provider = email_provider(settings)
    message_id = await provider.send(to=user.email, subject=subject, text=text, kind=purpose)
    session.add(
        EmailDelivery(
            user_id=user.id,
            kind=purpose,
            provider_message_id=message_id,
            status="captured" if settings.email_provider == "capture" else "sent",
            sent_at=datetime.now(UTC),
        )
    )


@router.post("/register", status_code=201)
async def register(
    payload: RegisterInput,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    rate_limit(request, "register", 6, 60)
    if await session.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="user",
        referral_code=f"el-{secrets.token_urlsafe(9)}",
    )
    session.add(user)
    await session.flush()
    session.add(PaperPortfolio(user_id=user.id, starting_cash=100_000, cash=100_000))
    if payload.anonymous_id:
        attribution = await session.scalar(
            select(Attribution).where(Attribution.anonymous_id == payload.anonymous_id)
        )
        if attribution:
            attribution.user_id = user.id
    raw = await issue_action_token(session, user, "verify", settings.email_token_minutes)
    await send_action_email(session, user, "verify", raw, settings)
    await DatabaseAnalytics(session).capture("signup_completed", user_id=user.id)
    await set_session(response, user, session, settings)
    await session.commit()
    return {"user": user_payload(user), "message": "Check your email to verify your account."}


@router.post("/login")
async def login(
    payload: LoginInput,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    rate_limit(request, "login", 10, 60)
    user = await session.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if not user or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await set_session(response, user, session, settings)
    session.add(
        AuditEvent(
            actor_user_id=user.id,
            action="auth.login",
            target_type="user",
            target_id=user.id,
            metadata_json={},
            created_at=datetime.now(UTC),
        )
    )
    await session.commit()
    return {"user": user_payload(user)}


@router.post("/demo-login")
async def demo_login(
    payload: DemoLoginInput,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    if settings.is_production:
        raise HTTPException(status_code=404, detail="Not found")
    email = settings.demo_admin_email if payload.role == "admin" else settings.demo_user_email
    user = await session.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=503, detail="Run the demo seed command first")
    await set_session(response, user, session, settings)
    await session.commit()
    return {"user": user_payload(user)}


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    rate_limit(request, "refresh", 20, 60)
    raw = request.cookies.get("refresh_token")
    if not raw:
        raise HTTPException(status_code=401, detail="Refresh session missing")
    stored = await session.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == hash_token(raw))
    )
    if not stored or stored.revoked_at or utc(stored.expires_at) <= datetime.now(UTC):
        if stored:
            await session.execute(
                update(RefreshSession)
                .where(RefreshSession.family_id == stored.family_id)
                .values(revoked_at=datetime.now(UTC))
            )
            await session.commit()
        raise HTTPException(status_code=401, detail="Refresh session is invalid")
    stored.revoked_at = datetime.now(UTC)
    user = await session.get(User, stored.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Account unavailable")
    await set_session(response, user, session, settings, stored.family_id)
    await session.commit()
    return {"user": user_payload(user)}


@router.post("/logout", dependencies=[Depends(require_csrf)])
async def logout(
    request: Request, response: Response, session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    raw = request.cookies.get("refresh_token")
    if raw:
        stored = await session.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == hash_token(raw))
        )
        if stored:
            stored.revoked_at = datetime.now(UTC)
            await session.commit()
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(name, path="/")
    return {"message": "Logged out"}


@router.post("/revoke-all", dependencies=[Depends(require_csrf)])
async def revoke_all(
    response: Response,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await session.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(name, path="/")
    return {"message": "All sessions revoked"}


@router.get("/me")
async def me(user: User = Depends(current_user)) -> dict[str, object]:
    return {"user": user_payload(user)}


@router.post("/verify-email")
async def verify_email(
    payload: TokenInput,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    token = await session.scalar(
        select(EmailActionToken).where(
            EmailActionToken.token_hash == hash_token(payload.token),
            EmailActionToken.purpose == "verify",
        )
    )
    if not token or token.used_at or utc(token.expires_at) <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Verification link is invalid or expired")
    user = await session.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Verification link is invalid or expired")
    token.used_at = datetime.now(UTC)
    user.email_verified_at = user.email_verified_at or datetime.now(UTC)
    await DatabaseAnalytics(session).capture("email_verified", user_id=user.id)
    await session.commit()
    return {"message": "Email verified. You can continue to onboarding."}


@router.post("/resend-verification")
async def resend_verification(
    payload: EmailInput,
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    rate_limit(request, "resend", 5, 300)
    user = await session.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user and not user.email_verified_at:
        raw = await issue_action_token(session, user, "verify", settings.email_token_minutes)
        await send_action_email(session, user, "verify", raw, settings)
        await session.commit()
    return {"message": "If that account needs verification, a new message has been sent."}


@router.post("/forgot-password")
async def forgot_password(
    payload: EmailInput,
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    rate_limit(request, "forgot", 5, 300)
    user = await session.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user and user.is_active:
        raw = await issue_action_token(session, user, "reset", settings.reset_token_minutes)
        await send_action_email(session, user, "reset", raw, settings)
        await session.commit()
    return {"message": "If an account exists, password-reset instructions have been sent."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordInput,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    token = await session.scalar(
        select(EmailActionToken).where(
            EmailActionToken.token_hash == hash_token(payload.token),
            EmailActionToken.purpose == "reset",
        )
    )
    if not token or token.used_at or utc(token.expires_at) <= datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    user = await session.get(User, token.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    user.password_hash = hash_password(payload.password)
    token.used_at = datetime.now(UTC)
    await session.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await session.commit()
    return {"message": "Password updated. Sign in with your new password."}
