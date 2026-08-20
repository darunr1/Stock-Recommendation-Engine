from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


def new_id() -> str:
    return str(uuid.uuid4())


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    onboarding_version: Mapped[str | None] = mapped_column(String(30))
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    onboarding_skipped: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    interests: Mapped[list[str]] = mapped_column(JSON, default=list)
    theme: Mapped[str] = mapped_column(String(20), default="system")
    weekly_digest: Mapped[bool] = mapped_column(Boolean, default=False)
    analytics_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    referral_code: Mapped[str | None] = mapped_column(String(40), unique=True)
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    family_id: Mapped[str] = mapped_column(String(36), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EmailActionToken(Base):
    __tablename__ = "email_action_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(30), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_email_action_user_purpose", "user_id", "purpose"),)


class Stock(TimestampMixin, Base):
    __tablename__ = "stocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    symbol: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(200))
    exchange: Mapped[str] = mapped_column(String(40))
    sector: Mapped[str | None] = mapped_column(String(80), index=True)
    cik: Mapped[str | None] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    stock_id: Mapped[str] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    trading_date: Mapped[date] = mapped_column(Date, index=True)
    open: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    high: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    low: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    close: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    adjusted_close: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    volume: Mapped[int] = mapped_column()
    provider: Mapped[str] = mapped_column(String(30), default="demo")
    feed: Mapped[str] = mapped_column(String(30), default="synthetic")
    adjustment: Mapped[str] = mapped_column(String(20), default="all")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint(
            "stock_id", "trading_date", "provider", "feed", "adjustment", name="uq_daily_price"
        ),
        Index("ix_daily_price_stock_date", "stock_id", "trading_date"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    stock_id: Mapped[str] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    model_version: Mapped[str] = mapped_column(String(50), index=True)
    score: Mapped[float | None] = mapped_column()
    band: Mapped[str] = mapped_column(String(40), index=True)
    confidence: Mapped[float] = mapped_column()
    confidence_label: Mapped[str] = mapped_column(String(20))
    factor_scores: Mapped[dict[str, float | None]] = mapped_column(JSON)
    raw_features: Mapped[dict[str, float | None]] = mapped_column(JSON)
    percentiles: Mapped[dict[str, float | None]] = mapped_column(JSON)
    contributors: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    freshness: Mapped[dict[str, object]] = mapped_column(JSON)
    canonical_payload: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("stock_id", "as_of_date", "model_version", name="uq_recommendation"),
        Index("ix_recommendation_screen", "as_of_date", "score", "confidence"),
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    stock_id: Mapped[str] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    note: Mapped[str] = mapped_column(String(500), default="")
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("user_id", "stock_id", name="uq_watchlist_item"),)


class BacktestRun(TimestampMixin, Base):
    __tablename__ = "backtest_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    progress: Mapped[int] = mapped_column(default=0)
    config: Mapped[dict[str, object]] = mapped_column(JSON)
    model_version: Mapped[str] = mapped_column(String(50))
    result: Mapped[dict[str, object] | None] = mapped_column(JSON)
    error_summary: Mapped[str | None] = mapped_column(String(300))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaperPortfolio(TimestampMixin, Base):
    __tablename__ = "paper_portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(80), default="Research portfolio")
    starting_cash: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    cash: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    realized_pl: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD")


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("paper_portfolios.id", ondelete="CASCADE"), index=True
    )
    stock_id: Mapped[str] = mapped_column(ForeignKey("stocks.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 6))

    __table_args__ = (UniqueConstraint("portfolio_id", "stock_id", name="uq_paper_position"),)


class PaperTransaction(Base):
    __tablename__ = "paper_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("paper_portfolios.id", ondelete="CASCADE"), index=True
    )
    stock_id: Mapped[str] = mapped_column(ForeignKey("stocks.id"), index=True)
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    execution_date: Mapped[date] = mapped_column(Date)
    fees: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    realized_pl: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Feedback(TimestampMixin, Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(40), index=True)
    rating: Mapped[int | None] = mapped_column()
    message: Mapped[str] = mapped_column(String(2000))
    page_path: Mapped[str | None] = mapped_column(String(300))
    symbol: Mapped[str | None] = mapped_column(String(12))
    data_version: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    admin_note: Mapped[str] = mapped_column(String(1000), default="")


class ProductEvent(Base):
    __tablename__ = "product_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    anonymous_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(60), index=True)
    properties: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Attribution(TimestampMixin, Base):
    __tablename__ = "attributions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    anonymous_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    first_touch: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    last_touch: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    referral_code: Mapped[str | None] = mapped_column(String(40))


class EmailDelivery(Base):
    __tablename__ = "email_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    kind: Mapped[str] = mapped_column(String(40), index=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    safe_error_code: Mapped[str | None] = mapped_column(String(80))


class SyncRun(Base):
    __tablename__ = "sync_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_type: Mapped[str] = mapped_column(String(40), index=True)
    provider: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), index=True)
    requested_count: Mapped[int] = mapped_column(default=0)
    written_count: Mapped[int] = mapped_column(default=0)
    coverage: Mapped[float] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    error_summary: Mapped[str | None] = mapped_column(String(300))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[str | None] = mapped_column(String(50))
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
