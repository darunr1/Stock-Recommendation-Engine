from __future__ import annotations

import json
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.core.config import Settings


class EmailProvider(ABC):
    @abstractmethod
    async def send(self, *, to: str, subject: str, text: str, kind: str) -> str:
        """Send a message and return a safe provider message identifier."""


class CaptureEmailProvider(EmailProvider):
    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)

    async def send(self, *, to: str, subject: str, text: str, kind: str) -> str:
        self.directory.mkdir(parents=True, exist_ok=True)
        message_id = f"capture-{uuid.uuid4()}"
        payload = {
            "id": message_id,
            "to": to,
            "subject": subject,
            "text": text,
            "kind": kind,
            "captured_at": datetime.now(UTC).isoformat(),
        }
        path = self.directory / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%S')}-{message_id}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return message_id


class ResendEmailProvider(EmailProvider):
    def __init__(self, api_key: str, sender: str) -> None:
        self.api_key = api_key
        self.sender = sender

    async def send(self, *, to: str, subject: str, text: str, kind: str) -> str:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"from": self.sender, "to": [to], "subject": subject, "text": text},
            )
            response.raise_for_status()
            return str(response.json()["id"])


def email_provider(settings: Settings) -> EmailProvider:
    if settings.email_provider == "resend":
        if not settings.resend_api_key or not settings.sender_domain_verified:
            raise RuntimeError("Resend email is blocked until the sender domain is verified")
        return ResendEmailProvider(settings.resend_api_key, settings.email_from)
    return CaptureEmailProvider(settings.email_capture_dir)


def verification_email(base_url: str, token: str) -> tuple[str, str]:
    return (
        "Verify your EquityLens email",
        f"Verify your email: {base_url}/verify-email?token={token}\n\n"
        "This link expires and can be used once. EquityLens is for education and research only.",
    )


def reset_email(base_url: str, token: str) -> tuple[str, str]:
    return (
        "Reset your EquityLens password",
        f"Reset your password: {base_url}/reset-password?token={token}\n\n"
        "If you did not request this, you can ignore it.",
    )
