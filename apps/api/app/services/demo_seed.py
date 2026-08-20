from __future__ import annotations

import csv
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password
from app.db.models import (
    DailyPrice,
    PaperPortfolio,
    Recommendation,
    Stock,
    SyncRun,
    User,
)
from app.providers.demo import DEMO_AS_OF, DemoFundamentalsProvider, DemoMarketDataProvider
from app.recommendations.engine import score_universe


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


async def seed_demo(
    session: AsyncSession, settings: Settings, *, reset: bool = False
) -> dict[str, int]:
    if reset:
        await session.execute(delete(Recommendation))
        await session.execute(delete(DailyPrice))
        await session.execute(delete(Stock))
        await session.commit()

    stock_count = await session.scalar(select(func.count()).select_from(Stock)) or 0
    stock_by_symbol: dict[str, Stock] = {}
    if stock_count == 0:
        universe_path = repo_root() / "config" / "universe.csv"
        with universe_path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                stock = Stock(
                    symbol=row["symbol"],
                    company_name=row["company_name"],
                    exchange=row["exchange"],
                    sector=row["sector"] or None,
                    cik=row["cik"] or None,
                    active=row["active"].lower() == "true",
                    effective_from=date.fromisoformat(row["effective_from"]),
                    effective_to=date.fromisoformat(row["effective_to"])
                    if row["effective_to"]
                    else None,
                )
                session.add(stock)
                stock_by_symbol[stock.symbol] = stock
        await session.flush()
    else:
        stocks = (await session.scalars(select(Stock))).all()
        stock_by_symbol = {stock.symbol: stock for stock in stocks}

    for email, password, role, is_demo in (
        (settings.demo_user_email, settings.demo_user_password, "user", True),
        (settings.demo_admin_email, settings.demo_admin_password, "admin", True),
    ):
        user = await session.scalar(select(User).where(User.email == email.lower()))
        if not user and not settings.is_production:
            user = User(
                email=email.lower(),
                password_hash=hash_password(password),
                role=role,
                is_demo=is_demo,
                email_verified_at=datetime.now(UTC),
                onboarding_version="v1",
                onboarding_completed_at=datetime.now(UTC),
                referral_code=f"demo-{role}-ref",
            )
            session.add(user)
            await session.flush()
            session.add(
                PaperPortfolio(
                    user_id=user.id,
                    starting_cash=Decimal(str(settings.starting_cash)),
                    cash=Decimal(str(settings.starting_cash)),
                )
            )
    await session.commit()

    price_count = await session.scalar(select(func.count()).select_from(DailyPrice)) or 0
    recommendation_count = (
        await session.scalar(select(func.count()).select_from(Recommendation)) or 0
    )
    if price_count == 0 or recommendation_count == 0:
        symbols = sorted(stock_by_symbol)
        start = DEMO_AS_OF - timedelta(days=365 * 5 + 30)
        bars = await DemoMarketDataProvider().daily_bars(symbols, start, DEMO_AS_OF)
        if price_count == 0:
            for offset in range(0, len(bars), 2000):
                session.add_all(
                    [
                        DailyPrice(
                            stock_id=stock_by_symbol[bar.symbol].id,
                            trading_date=bar.trading_date,
                            open=Decimal(str(bar.open)),
                            high=Decimal(str(bar.high)),
                            low=Decimal(str(bar.low)),
                            close=Decimal(str(bar.close)),
                            adjusted_close=Decimal(str(bar.adjusted_close)),
                            volume=bar.volume,
                            provider=bar.provider,
                            feed=bar.feed,
                            adjustment=bar.adjustment,
                            fetched_at=bar.fetched_at,
                            valid=bar.valid,
                        )
                        for bar in bars[offset : offset + 2000]
                    ]
                )
                await session.flush()
            await session.commit()
        bars_by_symbol = {symbol: [] for symbol in symbols}
        for bar in bars:
            bars_by_symbol[bar.symbol].append(bar)
        fundamentals = await DemoFundamentalsProvider().snapshots(symbols, DEMO_AS_OF)
        scored = score_universe(bars_by_symbol, fundamentals, DEMO_AS_OF)
        if recommendation_count == 0:
            for result in scored:
                session.add(
                    Recommendation(
                        stock_id=stock_by_symbol[result.symbol].id,
                        as_of_date=result.as_of_date,
                        model_version=settings.model_version,
                        score=result.score,
                        band=result.band,
                        confidence=result.confidence,
                        confidence_label=result.confidence_label,
                        factor_scores=result.factor_scores,
                        raw_features=result.raw_features,
                        percentiles=result.percentiles,
                        contributors=result.contributors,
                        warnings=result.warnings,
                        freshness=result.freshness,
                        canonical_payload=result.canonical_payload,
                    )
                )
            session.add(
                SyncRun(
                    job_type="demo_seed",
                    provider="demo",
                    status="completed",
                    requested_count=len(symbols),
                    written_count=len(bars) + len(scored),
                    coverage=100.0,
                    started_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                    warnings=["Deterministic synthetic demo data; not market observations."],
                )
            )
            await session.commit()
    return {
        "stocks": int(await session.scalar(select(func.count()).select_from(Stock)) or 0),
        "prices": int(await session.scalar(select(func.count()).select_from(DailyPrice)) or 0),
        "recommendations": int(
            await session.scalar(select(func.count()).select_from(Recommendation)) or 0
        ),
    }
