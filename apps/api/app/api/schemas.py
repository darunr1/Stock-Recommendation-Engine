from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RegisterInput(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=12, max_length=128)
    anonymous_id: str | None = Field(default=None, max_length=64)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Enter a valid email address")
        return value


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class DemoLoginInput(BaseModel):
    role: Literal["user", "admin"] = "user"


class TokenInput(BaseModel):
    token: str = Field(min_length=20, max_length=300)


class EmailInput(BaseModel):
    email: str = Field(min_length=5, max_length=320)


class ResetPasswordInput(TokenInput):
    password: str = Field(min_length=12, max_length=128)


class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    verified: bool
    onboarding_completed: bool
    activated: bool
    is_demo: bool
    theme: str
    referral_code: str | None


class WatchlistInput(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    note: str = Field(default="", max_length=500)

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, value: str) -> str:
        return value.strip().upper()


class NoteInput(BaseModel):
    note: str = Field(max_length=500)


class OnboardingInput(BaseModel):
    symbols: list[str] = Field(default_factory=list, max_length=10)
    interests: list[str] = Field(default_factory=list, max_length=10)
    skipped: bool = False


class BacktestInput(BaseModel):
    start_date: date = date(2022, 1, 3)
    end_date: date = date(2026, 7, 31)
    rebalance_frequency: Literal["monthly", "quarterly"] = "monthly"
    top_n: int = Field(default=10, ge=3, le=20)
    minimum_confidence: float = Field(default=65, ge=0, le=100)
    factor_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "momentum": 0.30,
            "trend": 0.15,
            "quality": 0.25,
            "value": 0.15,
            "risk": 0.15,
        }
    )
    initial_capital: float = Field(default=100_000, gt=0, le=10_000_000)
    transaction_cost_bps: float = Field(default=10, ge=0, le=100)
    slippage_bps: float = Field(default=5, ge=0, le=100)
    benchmark: Literal["SPY"] = "SPY"

    @model_validator(mode="after")
    def validate_configuration(self) -> BacktestInput:
        if (self.end_date - self.start_date).days < 365:
            raise ValueError("Backtests require at least one year")
        if (self.end_date - self.start_date).days > 365 * 10:
            raise ValueError("Backtests are capped at ten years")
        if abs(sum(self.factor_weights.values()) - 1.0) > 0.0001:
            raise ValueError("Factor weights must sum to 1")
        if set(self.factor_weights) != {"momentum", "trend", "quality", "value", "risk"}:
            raise ValueError("All five factor weights are required")
        return self


class TradeInput(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    side: Literal["buy", "sell"]
    quantity: float = Field(gt=0, le=1_000_000)
    execution_date: date | None = None
    price: float | None = Field(default=None, gt=0)

    @field_validator("symbol")
    @classmethod
    def uppercase_trade_symbol(cls, value: str) -> str:
        return value.strip().upper()


class ResetPortfolioInput(BaseModel):
    starting_cash: float = Field(default=100_000, gt=0, le=10_000_000)


class AttributionInput(BaseModel):
    anonymous_id: str = Field(min_length=8, max_length=64)
    utm_source: str | None = Field(default=None, max_length=80)
    utm_medium: str | None = Field(default=None, max_length=80)
    utm_campaign: str | None = Field(default=None, max_length=120)
    utm_content: str | None = Field(default=None, max_length=120)
    referrer: str | None = Field(default=None, max_length=300)
    landing_path: str = Field(default="/", max_length=300)
    referral_code: str | None = Field(default=None, max_length=40)


class FeedbackInput(BaseModel):
    category: Literal["general", "feature", "usability", "data_issue"]
    rating: int | None = Field(default=None, ge=1, le=5)
    message: str = Field(min_length=3, max_length=2000)
    page_path: str | None = Field(default=None, max_length=300)
    symbol: str | None = Field(default=None, max_length=12)


class FeedbackUpdate(BaseModel):
    status: Literal["open", "reviewing", "resolved", "closed"]
    admin_note: str = Field(default="", max_length=1000)


class PreferencesInput(BaseModel):
    weekly_digest: bool
    analytics_enabled: bool = True


class SettingsInput(BaseModel):
    theme: Literal["light", "dark", "system"]


class DeleteAccountInput(BaseModel):
    password: str = Field(min_length=1, max_length=128)
