from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import Settings

password_hasher = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return password_hasher.verify(encoded, password)
    except VerifyMismatchError:
        return False


def random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: str, role: str, verified: bool, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "verified": verified,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def signed_token(value: str, settings: Settings) -> str:
    signature = hmac.new(settings.csrf_secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def verify_signed_token(value: str, settings: Settings) -> str | None:
    try:
        raw, signature = value.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(settings.csrf_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return raw if hmac.compare_digest(signature, expected) else None
