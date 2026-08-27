from __future__ import annotations

import html
import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Annotated, cast

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    admin_user,
    current_user,
    current_user_optional,
    require_csrf,
    verified_user,
)
from app.api.schemas import (
    AttributionInput,
    BacktestInput,
    DeleteAccountInput,
    FeedbackInput,
    FeedbackUpdate,
    NoteInput,
    OnboardingInput,
    PreferencesInput,
    ResetPortfolioInput,
    SettingsInput,
    TradeInput,
    WatchlistInput,
)
from app.backtests.engine import run_walk_forward
from app.core.config import Settings, get_settings
from app.core.security import signed_token, verify_password, verify_signed_token
from app.db.models import (
    Attribution,
    AuditEvent,
    BacktestRun,
    DailyPrice,
    EmailDelivery,
    Feedback,
    ProductEvent,
    Recommendation,
    RefreshSession,
    Stock,
    SyncRun,
    User,
    WatchlistItem,
)
from app.db.session import SessionLocal, get_db
from app.portfolios.service import execute_trade, portfolio_snapshot, reset_portfolio
from app.providers.demo import DEMO_AS_OF, DemoFundamentalsProvider
from app.providers.interfaces import PriceBar
from app.recommendations.engine import Contributor, market_regime
from app.services.analytics import DatabaseAnalytics
from app.services.demo_seed import seed_demo
from app.services.email import email_provider

router = APIRouter()
DISCLOSURE = (
    "For education and research only. Not investment advice. "
    "Past or simulated performance does not guarantee future results."
)
CONFIDENCE_HELP = "Confidence measures data completeness and freshness, not predictive certainty."
UTM_PATTERN = re.compile(r"[^a-zA-Z0-9_.~ -]")


def serialize_recommendation(stock: Stock, recommendation: Recommendation) -> dict[str, object]:
    return {
        "symbol": stock.symbol,
        "company_name": stock.company_name,
        "exchange": stock.exchange,
        "sector": stock.sector,
        "as_of_date": recommendation.as_of_date.isoformat(),
        "model_version": recommendation.model_version,
        "score": recommendation.score,
        "band": recommendation.band,
        "confidence": recommendation.confidence,
        "confidence_label": recommendation.confidence_label,
        "confidence_help": CONFIDENCE_HELP,
        "factor_scores": recommendation.factor_scores,
        "raw_features": recommendation.raw_features,
        "percentiles": recommendation.percentiles,
        "contributors": recommendation.contributors,
        "warnings": recommendation.warnings,
        "freshness": recommendation.freshness,
    }


async def latest_recommendation_date(session: AsyncSession) -> date:
    value = await session.scalar(select(func.max(Recommendation.as_of_date)))
    if not value:
        raise HTTPException(status_code=503, detail="Research snapshots are not available")
    return value


async def stock_and_latest(session: AsyncSession, symbol: str) -> tuple[Stock, Recommendation]:
    row = (
        await session.execute(
            select(Stock, Recommendation)
            .join(Recommendation, Recommendation.stock_id == Stock.id)
            .where(Stock.symbol == symbol.upper(), Stock.active.is_(True))
            .order_by(Recommendation.as_of_date.desc())
            .limit(1)
        )
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Supported symbol not found")
    return row[0], row[1]


async def latest_close(session: AsyncSession, stock_id: str) -> DailyPrice:
    row = await session.scalar(
        select(DailyPrice)
        .where(DailyPrice.stock_id == stock_id, DailyPrice.valid.is_(True))
        .order_by(DailyPrice.trading_date.desc())
        .limit(1)
    )
    if not row:
        raise HTTPException(status_code=503, detail="Price history is unavailable")
    return row


async def record_stock_view(session: AsyncSession, user: User | None, symbol: str) -> None:
    if not user:
        return
    await DatabaseAnalytics(session).capture(
        "stock_viewed", user_id=user.id, properties={"symbol": symbol}
    )
    if user.onboarding_completed_at and not user.activated_at:
        distinct_stocks = await session.scalar(
            select(func.count(func.distinct(ProductEvent.properties["symbol"]))).where(
                ProductEvent.user_id == user.id, ProductEvent.name == "stock_viewed"
            )
        )
        watch_count = await session.scalar(
            select(func.count()).select_from(WatchlistItem).where(WatchlistItem.user_id == user.id)
        )
        completed_backtest = await session.scalar(
            select(func.count())
            .select_from(BacktestRun)
            .where(BacktestRun.user_id == user.id, BacktestRun.status == "completed")
        )
        if int(distinct_stocks or 0) >= 2 and (int(watch_count or 0) >= 3 or completed_backtest):
            user.activated_at = datetime.now(UTC)
            await DatabaseAnalytics(session).capture("user_activated", user_id=user.id)


@router.get("/public/market-preview", tags=["public"])
async def public_market_preview(session: AsyncSession = Depends(get_db)) -> dict[str, object]:
    as_of = await latest_recommendation_date(session)
    rows = (
        await session.execute(
            select(Stock, Recommendation)
            .join(Recommendation, Recommendation.stock_id == Stock.id)
            .where(
                Recommendation.as_of_date == as_of,
                Stock.symbol != "SPY",
                Recommendation.score.is_not(None),
            )
            .order_by(Recommendation.score.desc())
            .limit(5)
        )
    ).all()
    return {
        "as_of_date": as_of.isoformat(),
        "data_mode": "demo",
        "items": [
            {
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "band": recommendation.band,
                "score": recommendation.score,
                "confidence": recommendation.confidence,
            }
            for stock, recommendation in rows
        ],
        "disclosure": DISCLOSURE,
    }


@router.get("/public/stocks/{symbol}", tags=["public"])
async def public_stock(
    symbol: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    stock, recommendation = await stock_and_latest(session, symbol)
    price = await latest_close(session, stock.id)
    history = (
        await session.scalars(
            select(DailyPrice)
            .where(DailyPrice.stock_id == stock.id, DailyPrice.valid.is_(True))
            .order_by(DailyPrice.trading_date.desc())
            .limit(40)
        )
    ).all()
    anonymous_id = request.headers.get("X-Anonymous-Id")
    await DatabaseAnalytics(session).capture(
        "public_stock_viewed",
        user_id=None,
        anonymous_id=anonymous_id,
        properties={"symbol": stock.symbol, "data_mode": settings.public_market_data_mode},
    )
    await session.commit()
    base = serialize_recommendation(stock, recommendation)
    public_shape = {
        "symbol": base["symbol"],
        "company_name": base["company_name"],
        "sector": base["sector"],
        "as_of_date": base["as_of_date"],
        "score": base["score"],
        "band": base["band"],
        "confidence": base["confidence"],
        "confidence_help": CONFIDENCE_HELP,
        "factor_scores": base["factor_scores"],
        "contributors": recommendation.contributors[:4],
        "warnings": recommendation.warnings,
        "latest_price": float(price.adjusted_close),
        "price_date": price.trading_date.isoformat(),
        "history": [
            {"date": item.trading_date.isoformat(), "close": float(item.adjusted_close)}
            for item in reversed(history)
        ],
        "data_mode": settings.public_market_data_mode,
        "demo": settings.public_market_data_mode == "demo",
        "canonical_url": f"{settings.app_base_url}/stocks/{stock.symbol}",
        "disclosure": DISCLOSURE,
    }
    if settings.public_market_data_mode == "restricted":
        public_shape["latest_price"] = None
        public_shape["history"] = []
        public_shape["warnings"] = [
            *recommendation.warnings,
            "Public price display is license restricted.",
        ]
    return public_shape


@router.get("/market/summary", tags=["research"])
async def market_summary(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    as_of = await latest_recommendation_date(session)
    rows = (
        await session.execute(
            select(Stock, Recommendation)
            .join(Recommendation, Recommendation.stock_id == Stock.id)
            .where(Recommendation.as_of_date == as_of, Stock.symbol != "SPY")
        )
    ).all()
    top = sorted(
        ((stock, rec) for stock, rec in rows if rec.score is not None),
        key=lambda item: (-float(item[1].score or 0), item[0].symbol),
    )[:10]
    band_counts: dict[str, int] = {}
    for _, rec in rows:
        band_counts[rec.band] = band_counts.get(rec.band, 0) + 1
    spy = await session.scalar(select(Stock).where(Stock.symbol == "SPY"))
    if spy is None:
        raise HTTPException(status_code=503, detail="Benchmark history is unavailable")
    spy_rows = (
        await session.scalars(
            select(DailyPrice)
            .where(DailyPrice.stock_id == spy.id, DailyPrice.valid.is_(True))
            .order_by(DailyPrice.trading_date)
        )
    ).all()
    spy_bars = [
        PriceBar(
            symbol="SPY",
            trading_date=item.trading_date,
            open=float(item.open),
            high=float(item.high),
            low=float(item.low),
            close=float(item.close),
            adjusted_close=float(item.adjusted_close),
            volume=item.volume,
            provider=item.provider,
            feed=item.feed,
            adjustment=item.adjustment,
            fetched_at=item.fetched_at,
            valid=item.valid,
        )
        for item in spy_rows
    ]
    return {
        "as_of_date": as_of.isoformat(),
        "data_health": "healthy" if all(rec.band != "STALE_DATA" for _, rec in top) else "partial",
        "data_mode": "demo",
        "top_candidates": [serialize_recommendation(stock, rec) for stock, rec in top],
        "band_counts": band_counts,
        "market_regime": market_regime(spy_bars),
        "disclosure": DISCLOSURE,
    }


@router.get("/recommendations", tags=["research"])
async def recommendations(
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=5, le=100)] = 25,
    search: Annotated[str | None, Query(max_length=60)] = None,
    sector: Annotated[str | None, Query(max_length=80)] = None,
    band: Annotated[str | None, Query(max_length=40)] = None,
    minimum_score: Annotated[float, Query(ge=0, le=100)] = 0,
    minimum_confidence: Annotated[float, Query(ge=0, le=100)] = 0,
    sort: Annotated[str, Query()] = "score",
    direction: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> dict[str, object]:
    as_of = await latest_recommendation_date(session)
    filters = [Recommendation.as_of_date == as_of, Stock.symbol != "SPY"]
    if search:
        term = f"%{search.strip()}%"
        filters.append(or_(Stock.symbol.ilike(term), Stock.company_name.ilike(term)))
    if sector:
        filters.append(Stock.sector == sector)
    if band:
        filters.append(Recommendation.band == band)
    filters.extend(
        [Recommendation.score >= minimum_score, Recommendation.confidence >= minimum_confidence]
    )
    sort_map = {
        "symbol": Stock.symbol,
        "score": Recommendation.score,
        "confidence": Recommendation.confidence,
        "momentum": Recommendation.factor_scores["momentum"],
        "trend": Recommendation.factor_scores["trend"],
        "quality": Recommendation.factor_scores["quality"],
        "value": Recommendation.factor_scores["value"],
        "risk": Recommendation.factor_scores["risk"],
    }
    order = sort_map.get(sort, Recommendation.score)
    order = order.asc() if direction == "asc" else order.desc()
    count = await session.scalar(
        select(func.count()).select_from(Recommendation).join(Stock).where(*filters)
    )
    rows = (
        await session.execute(
            select(Stock, Recommendation)
            .join(Stock, Stock.id == Recommendation.stock_id)
            .where(*filters)
            .order_by(order, Stock.symbol)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    await DatabaseAnalytics(session).capture(
        "screener_used",
        user_id=user.id,
        properties={"has_search": bool(search), "sector": sector or "all", "sort": sort},
    )
    await session.commit()
    return {
        "items": [serialize_recommendation(stock, rec) for stock, rec in rows],
        "page": page,
        "page_size": page_size,
        "total": int(count or 0),
        "as_of_date": as_of.isoformat(),
    }


@router.get("/recommendations/{symbol}", tags=["research"])
async def recommendation_detail(
    symbol: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    stock, rec = await stock_and_latest(session, symbol)
    price = await latest_close(session, stock.id)
    await record_stock_view(session, user, stock.symbol)
    await session.commit()
    contributors = cast(list[Contributor], rec.contributors)
    result = serialize_recommendation(stock, rec)
    result.update(
        {
            "latest_price": float(price.adjusted_close),
            "price_date": price.trading_date.isoformat(),
            "risk_metrics": {
                "annualized_volatility": rec.raw_features.get("volatility_63d"),
                "maximum_drawdown": rec.raw_features.get("max_drawdown_252d"),
                "downside_deviation": rec.raw_features.get("downside_deviation_252d"),
                "beta_distance_from_one": rec.raw_features.get("beta_distance"),
                "liquidity_proxy": rec.raw_features.get("illiquidity_20d"),
            },
            "what_could_change": [
                f"A material change in {item['label'].lower()} could move the score."
                for item in sorted(
                    contributors,
                    key=lambda value: abs(float(value["contribution"])),
                    reverse=True,
                )[:3]
            ],
            "disclosure": DISCLOSURE,
        }
    )
    return result


@router.get("/recommendations/{symbol}/history", tags=["research"])
async def recommendation_history(
    symbol: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    stock = await session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if not stock:
        raise HTTPException(status_code=404, detail="Supported symbol not found")
    rows = (
        await session.scalars(
            select(Recommendation)
            .where(Recommendation.stock_id == stock.id)
            .order_by(Recommendation.as_of_date)
        )
    ).all()
    return {
        "symbol": stock.symbol,
        "items": [
            {
                "date": item.as_of_date.isoformat(),
                "score": item.score,
                "band": item.band,
                "confidence": item.confidence,
            }
            for item in rows
        ],
    }


@router.get("/stocks/search", tags=["research"])
async def stock_search(
    q: Annotated[str, Query(min_length=1, max_length=60)],
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    term = f"%{q.strip()}%"
    stocks = (
        await session.scalars(
            select(Stock)
            .where(
                Stock.active.is_(True),
                or_(Stock.symbol.ilike(term), Stock.company_name.ilike(term)),
            )
            .order_by(Stock.symbol)
            .limit(10)
        )
    ).all()
    return {
        "items": [
            {"symbol": stock.symbol, "company_name": stock.company_name, "sector": stock.sector}
            for stock in stocks
        ]
    }


@router.get("/stocks/{symbol}", tags=["research"])
async def stock_detail(
    symbol: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    return await recommendation_detail(symbol, user, session)


@router.get("/stocks/{symbol}/prices", tags=["research"])
async def stock_prices(
    symbol: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
    range: Annotated[str, Query(pattern="^(1M|3M|6M|1Y|3Y|5Y)$")] = "1Y",
) -> dict[str, object]:
    stock = await session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if not stock:
        raise HTTPException(status_code=404, detail="Supported symbol not found")
    days = {"1M": 31, "3M": 93, "6M": 186, "1Y": 366, "3Y": 1096, "5Y": 1830}[range]
    cutoff = DEMO_AS_OF - timedelta(days=days)
    rows = (
        await session.scalars(
            select(DailyPrice)
            .where(
                DailyPrice.stock_id == stock.id,
                DailyPrice.trading_date >= cutoff,
                DailyPrice.valid.is_(True),
            )
            .order_by(DailyPrice.trading_date)
        )
    ).all()
    closes = pd.Series([float(row.adjusted_close) for row in rows])
    return {
        "symbol": stock.symbol,
        "range": range,
        "items": [
            {
                "date": row.trading_date.isoformat(),
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": row.volume,
                "sma20": round(float(closes.iloc[: index + 1].tail(20).mean()), 4),
                "sma50": round(float(closes.iloc[: index + 1].tail(50).mean()), 4),
                "sma200": round(float(closes.iloc[: index + 1].tail(200).mean()), 4),
            }
            for index, row in enumerate(rows)
        ],
        "accessible_summary": f"{len(rows)} daily adjusted OHLC observations for {stock.symbol}.",
    }


@router.get("/stocks/{symbol}/fundamentals", tags=["research"])
async def stock_fundamentals(
    symbol: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    stock = await session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if not stock:
        raise HTTPException(status_code=404, detail="Supported symbol not found")
    snapshot = (await DemoFundamentalsProvider().snapshots([stock.symbol], DEMO_AS_OF))[
        stock.symbol
    ]
    return {
        "symbol": stock.symbol,
        "as_of_date": snapshot.as_of_date.isoformat(),
        "filed_at": snapshot.filed_at.isoformat(),
        "metrics": snapshot.metrics,
        "coverage": snapshot.coverage,
        "warnings": snapshot.warnings,
        "source": "deterministic demo fundamentals",
    }


@router.get("/watchlist", tags=["watchlist"])
async def get_watchlist(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    as_of = await latest_recommendation_date(session)
    rows = (
        await session.execute(
            select(WatchlistItem, Stock, Recommendation)
            .join(Stock, Stock.id == WatchlistItem.stock_id)
            .join(
                Recommendation,
                and_(Recommendation.stock_id == Stock.id, Recommendation.as_of_date == as_of),
            )
            .where(WatchlistItem.user_id == user.id)
            .order_by(Stock.symbol)
        )
    ).all()
    return {
        "items": [
            {
                **serialize_recommendation(stock, recommendation),
                "note": item.note,
                "added_at": item.added_at.isoformat(),
            }
            for item, stock, recommendation in rows
        ]
    }


@router.post("/watchlist/items", dependencies=[Depends(require_csrf)], tags=["watchlist"])
async def add_watchlist(
    payload: WatchlistInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    stock = await session.scalar(
        select(Stock).where(Stock.symbol == payload.symbol, Stock.active.is_(True))
    )
    if not stock or stock.symbol == "SPY":
        raise HTTPException(status_code=404, detail="Active candidate symbol not found")
    item = await session.scalar(
        select(WatchlistItem).where(
            WatchlistItem.user_id == user.id, WatchlistItem.stock_id == stock.id
        )
    )
    created = item is None
    if not item:
        item = WatchlistItem(
            user_id=user.id,
            stock_id=stock.id,
            note=payload.note,
            added_at=datetime.now(UTC),
        )
        session.add(item)
    else:
        item.note = payload.note
    if created:
        await DatabaseAnalytics(session).capture(
            "watchlist_item_added", user_id=user.id, properties={"symbol": stock.symbol}
        )
    await session.commit()
    return {"symbol": stock.symbol, "note": item.note, "created": created}


@router.patch("/watchlist/items/{symbol}", dependencies=[Depends(require_csrf)], tags=["watchlist"])
async def update_watchlist(
    symbol: str,
    payload: NoteInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    item = await session.scalar(
        select(WatchlistItem)
        .join(Stock)
        .where(WatchlistItem.user_id == user.id, Stock.symbol == symbol.upper())
    )
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    item.note = payload.note
    await session.commit()
    return {"symbol": symbol.upper(), "note": item.note}


@router.delete(
    "/watchlist/items/{symbol}", dependencies=[Depends(require_csrf)], tags=["watchlist"]
)
async def delete_watchlist(
    symbol: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    stock = await session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if stock:
        await session.execute(
            delete(WatchlistItem).where(
                WatchlistItem.user_id == user.id, WatchlistItem.stock_id == stock.id
            )
        )
        await session.commit()
    return {"message": "Removed from watchlist"}


@router.get("/onboarding", tags=["account"])
async def get_onboarding(user: User = Depends(verified_user)) -> dict[str, object]:
    return {
        "version": "v1",
        "completed": bool(user.onboarding_completed_at),
        "skipped": user.onboarding_skipped,
        "interests": user.interests,
        "score_explanation": "The composite is a cross-sectional research rank from five factors.",
        "confidence_explanation": CONFIDENCE_HELP,
        "disclosure": DISCLOSURE,
    }


@router.put("/onboarding", dependencies=[Depends(require_csrf)], tags=["account"])
async def put_onboarding(
    payload: OnboardingInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    if not payload.skipped and len(set(payload.symbols)) < 3:
        raise HTTPException(
            status_code=422, detail="Select at least three symbols or skip onboarding"
        )
    for symbol in sorted(set(value.upper() for value in payload.symbols)):
        stock = await session.scalar(
            select(Stock).where(Stock.symbol == symbol, Stock.active.is_(True))
        )
        if not stock or stock.symbol == "SPY":
            continue
        existing = await session.scalar(
            select(WatchlistItem).where(
                WatchlistItem.user_id == user.id, WatchlistItem.stock_id == stock.id
            )
        )
        if not existing:
            session.add(
                WatchlistItem(
                    user_id=user.id, stock_id=stock.id, note="", added_at=datetime.now(UTC)
                )
            )
    user.onboarding_version = "v1"
    user.onboarding_completed_at = datetime.now(UTC)
    user.onboarding_skipped = payload.skipped
    user.interests = payload.interests
    await DatabaseAnalytics(session).capture(
        "onboarding_completed", user_id=user.id, properties={"skipped": payload.skipped}
    )
    await session.commit()
    return {"completed": True, "next": "/dashboard"}


async def process_backtest(run_id: str) -> None:
    async with SessionLocal() as session:
        run = await session.get(BacktestRun, run_id)
        if not run:
            return
        run.status = "running"
        run.progress = 10
        run.started_at = datetime.now(UTC)
        await session.commit()
        try:
            rows = (
                await session.execute(
                    select(Stock.symbol, DailyPrice)
                    .join(Stock, Stock.id == DailyPrice.stock_id)
                    .where(DailyPrice.valid.is_(True))
                    .order_by(DailyPrice.trading_date)
                )
            ).all()
            records: dict[str, list[dict[str, object]]] = {}
            for symbol, price in rows:
                records.setdefault(symbol, []).append(
                    {
                        "date": price.trading_date,
                        "open": float(price.open),
                        "close": float(price.adjusted_close),
                        "volume": price.volume,
                    }
                )
            prices = {
                symbol: pd.DataFrame(values).set_index(
                    pd.to_datetime([row["date"] for row in values])
                )
                for symbol, values in records.items()
            }
            config = {**run.config}
            result = run_walk_forward(prices, config)
            run.result = result
            run.status = "completed"
            run.progress = 100
            run.completed_at = datetime.now(UTC)
            await DatabaseAnalytics(session).capture("backtest_completed", user_id=run.user_id)
        except Exception as exc:
            run.status = "failed"
            run.error_summary = str(exc)[:300]
            run.completed_at = datetime.now(UTC)
        await session.commit()


@router.post(
    "/backtests", status_code=202, dependencies=[Depends(require_csrf)], tags=["backtests"]
)
async def create_backtest(
    payload: BacktestInput,
    background: BackgroundTasks,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    active = await session.scalar(
        select(func.count())
        .select_from(BacktestRun)
        .where(BacktestRun.user_id == user.id, BacktestRun.status.in_(["queued", "running"]))
    )
    if active:
        raise HTTPException(status_code=409, detail="A backtest is already active")
    config = payload.model_dump(mode="json")
    run = BacktestRun(
        user_id=user.id,
        status="queued",
        progress=0,
        config=config,
        model_version=settings.model_version,
    )
    session.add(run)
    await DatabaseAnalytics(session).capture("backtest_started", user_id=user.id)
    await session.commit()
    if settings.demo_tasks_eager:
        await process_backtest(run.id)
    else:
        background.add_task(process_backtest, run.id)
    return {"id": run.id, "status": "queued", "poll_url": f"/api/v1/backtests/{run.id}"}


@router.get("/backtests", tags=["backtests"])
async def list_backtests(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    runs = (
        await session.scalars(
            select(BacktestRun)
            .where(BacktestRun.user_id == user.id)
            .order_by(BacktestRun.created_at.desc())
        )
    ).all()
    return {
        "items": [
            {
                "id": run.id,
                "status": run.status,
                "progress": run.progress,
                "config": run.config,
                "metrics": run.result.get("metrics") if run.result else None,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_summary": run.error_summary,
            }
            for run in runs
        ]
    }


@router.get("/backtests/{run_id}", tags=["backtests"])
async def get_backtest(
    run_id: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    run = await session.scalar(
        select(BacktestRun).where(BacktestRun.id == run_id, BacktestRun.user_id == user.id)
    )
    if not run:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return {
        "id": run.id,
        "status": run.status,
        "progress": run.progress,
        "config": run.config,
        "model_version": run.model_version,
        "result": run.result,
        "error_summary": run.error_summary,
    }


@router.get("/backtests/{run_id}/series", tags=["backtests"])
async def get_backtest_series(
    run_id: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    result = await get_backtest(run_id, user, session)
    payload = result.get("result")
    series = payload.get("series", []) if isinstance(payload, dict) else []
    return {"id": run_id, "series": series}


@router.get("/paper/portfolio", tags=["paper"])
@router.get("/paper/positions", tags=["paper"])
@router.get("/paper/transactions", tags=["paper"])
@router.get("/paper/performance", tags=["paper"])
async def get_paper_portfolio(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    try:
        return await portfolio_snapshot(session, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/paper/transactions", dependencies=[Depends(require_csrf)], tags=["paper"])
async def post_paper_transaction(
    payload: TradeInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        transaction = await execute_trade(
            session,
            user_id=user.id,
            symbol=payload.symbol,
            side=payload.side,
            quantity=Decimal(str(payload.quantity)),
            execution_date=payload.execution_date,
            explicit_price=Decimal(str(payload.price)) if payload.price else None,
        )
        session.add(
            AuditEvent(
                actor_user_id=user.id,
                action="paper.trade",
                target_type="paper_transaction",
                target_id=transaction.id,
                metadata_json={"symbol": payload.symbol, "side": payload.side},
                created_at=datetime.now(UTC),
            )
        )
        await DatabaseAnalytics(session).capture(
            "paper_trade_recorded",
            user_id=user.id,
            properties={"symbol": payload.symbol, "side": payload.side},
        )
        await session.commit()
        return await portfolio_snapshot(session, user.id)
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/paper/portfolio/reset", dependencies=[Depends(require_csrf)], tags=["paper"])
async def reset_paper(
    payload: ResetPortfolioInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    try:
        await reset_portfolio(session, user.id, Decimal(str(payload.starting_cash)))
        session.add(
            AuditEvent(
                actor_user_id=user.id,
                action="paper.reset",
                target_type="paper_portfolio",
                target_id=user.id,
                metadata_json={},
                created_at=datetime.now(UTC),
            )
        )
        await session.commit()
        return await portfolio_snapshot(session, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def sanitize_touch(payload: AttributionInput) -> dict[str, str]:
    raw = payload.model_dump(exclude_none=True)
    return {
        key: UTM_PATTERN.sub("", str(value))[:300]
        for key, value in raw.items()
        if key not in {"anonymous_id", "referral_code"}
    }


@router.post("/attribution/landing", tags=["growth"])
async def attribution_landing(
    payload: AttributionInput, session: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    touch = sanitize_touch(payload)
    attribution = await session.scalar(
        select(Attribution).where(Attribution.anonymous_id == payload.anonymous_id)
    )
    if not attribution:
        attribution = Attribution(
            anonymous_id=payload.anonymous_id,
            first_touch=touch,
            last_touch=touch,
            referral_code=payload.referral_code,
        )
        session.add(attribution)
    else:
        attribution.last_touch = touch
        attribution.referral_code = attribution.referral_code or payload.referral_code
    if payload.referral_code:
        inviter = await session.scalar(
            select(User).where(User.referral_code == payload.referral_code)
        )
        if inviter:
            await DatabaseAnalytics(session).capture(
                "referral_landed", user_id=inviter.id, anonymous_id=payload.anonymous_id
            )
    await session.commit()
    return {"message": "Attribution recorded"}


@router.get("/referrals/me", tags=["growth"])
async def referrals_me(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    count = await session.scalar(
        select(func.count())
        .select_from(Attribution)
        .where(Attribution.referral_code == user.referral_code, Attribution.user_id.is_not(None))
    )
    return {"code": user.referral_code, "converted_count": int(count or 0)}


@router.post("/referrals/convert", dependencies=[Depends(require_csrf)], tags=["growth"])
async def referrals_convert(
    anonymous_id: str,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    attribution = await session.scalar(
        select(Attribution).where(Attribution.anonymous_id == anonymous_id[:64])
    )
    if attribution:
        inviter = await session.scalar(
            select(User).where(User.referral_code == attribution.referral_code)
        )
        if inviter and inviter.id == user.id:
            raise HTTPException(status_code=422, detail="Self-referral is not allowed")
        attribution.user_id = user.id
        await session.commit()
    return {"message": "Referral attribution evaluated"}


@router.get("/email/preferences", tags=["account"])
async def get_email_preferences(user: User = Depends(verified_user)) -> dict[str, object]:
    return {"weekly_digest": user.weekly_digest, "analytics_enabled": user.analytics_enabled}


@router.put("/email/preferences", dependencies=[Depends(require_csrf)], tags=["account"])
async def put_email_preferences(
    payload: PreferencesInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    opted_in = payload.weekly_digest and not user.weekly_digest
    user.weekly_digest = payload.weekly_digest
    user.analytics_enabled = payload.analytics_enabled
    if opted_in:
        await DatabaseAnalytics(session).capture("digest_opted_in", user_id=user.id)
    await session.commit()
    return {"weekly_digest": user.weekly_digest, "analytics_enabled": user.analytics_enabled}


@router.post("/email/unsubscribe", tags=["account"])
async def unsubscribe(
    token: str,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    raw = verify_signed_token(token, settings)
    if not raw:
        raise HTTPException(status_code=400, detail="Unsubscribe link is invalid")
    user = await session.get(User, raw)
    if user:
        user.weekly_digest = False
        await session.commit()
    return {"message": "Weekly digest unsubscribed"}


async def run_digest_job(session: AsyncSession, settings: Settings) -> int:
    users = (
        await session.scalars(
            select(User).where(
                User.weekly_digest.is_(True),
                User.email_verified_at.is_not(None),
                User.is_active.is_(True),
                User.deletion_requested_at.is_(None),
            )
        )
    ).all()
    provider = email_provider(settings)
    sent = 0
    week_key = datetime.now(UTC).strftime("%G-W%V")
    for user in users:
        has_item = await session.scalar(
            select(func.count()).select_from(WatchlistItem).where(WatchlistItem.user_id == user.id)
        )
        prior = await session.scalar(
            select(EmailDelivery).where(
                EmailDelivery.user_id == user.id,
                EmailDelivery.kind == f"weekly_digest:{week_key}",
            )
        )
        if not has_item or prior:
            continue
        token = signed_token(user.id, settings)
        text = (
            f"Your EquityLens watchlist research digest is ready: {settings.app_base_url}/watchlist\n\n"
            f"Unsubscribe: {settings.app_base_url}/unsubscribe?token={token}\n\n{DISCLOSURE}"
        )
        message_id = await provider.send(
            to=user.email,
            subject="Your weekly EquityLens research digest",
            text=text,
            kind="weekly_digest",
        )
        session.add(
            EmailDelivery(
                user_id=user.id,
                kind=f"weekly_digest:{week_key}",
                provider_message_id=message_id,
                status="captured" if settings.email_provider == "capture" else "sent",
                sent_at=datetime.now(UTC),
            )
        )
        sent += 1
    await session.commit()
    return sent


@router.post("/feedback", dependencies=[Depends(require_csrf)], tags=["growth"])
async def submit_feedback(
    payload: FeedbackInput,
    user: User | None = Depends(current_user_optional),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    clean_message = html.escape(payload.message.strip())
    item = Feedback(
        user_id=user.id if user else None,
        category=payload.category,
        rating=payload.rating,
        message=clean_message,
        page_path=payload.page_path,
        symbol=payload.symbol.upper() if payload.symbol else None,
        data_version=settings.model_version if payload.category == "data_issue" else None,
    )
    session.add(item)
    await DatabaseAnalytics(session).capture(
        "feedback_submitted",
        user_id=user.id if user else None,
        properties={"category": payload.category},
    )
    await session.commit()
    return {"id": item.id, "status": item.status, "message": "Feedback received. Thank you."}


@router.get("/settings", tags=["account"])
async def get_settings_route(user: User = Depends(verified_user)) -> dict[str, object]:
    return {
        "theme": user.theme,
        "model_version": "equitylens-v1",
        "email": user.email,
        "verified": bool(user.email_verified_at),
        "disclosure": DISCLOSURE,
    }


@router.put("/settings", dependencies=[Depends(require_csrf)], tags=["account"])
async def put_settings_route(
    payload: SettingsInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user.theme = payload.theme
    await session.commit()
    return {"theme": user.theme}


@router.get("/account/export", tags=["account"])
async def account_export(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    watchlist = await get_watchlist(user, session)
    runs = await list_backtests(user, session)
    paper = await portfolio_snapshot(session, user.id)
    feedback_items = (
        await session.scalars(select(Feedback).where(Feedback.user_id == user.id))
    ).all()
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "profile": {
            "email": user.email,
            "role": user.role,
            "verified": bool(user.email_verified_at),
            "interests": user.interests,
        },
        "watchlist": watchlist,
        "backtests": runs,
        "paper_portfolio": paper,
        "email_preferences": {
            "weekly_digest": user.weekly_digest,
            "analytics_enabled": user.analytics_enabled,
        },
        "feedback": [
            {"category": item.category, "message": item.message, "status": item.status}
            for item in feedback_items
        ],
    }


@router.post("/account/delete-request", dependencies=[Depends(require_csrf)], tags=["account"])
async def delete_request(
    payload: DeleteAccountInput,
    user: User = Depends(verified_user),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password is incorrect")
    user.deletion_requested_at = datetime.now(UTC)
    user.weekly_digest = False
    await session.execute(delete(RefreshSession).where(RefreshSession.user_id == user.id))
    await DatabaseAnalytics(session).capture("account_deleted", user_id=user.id)
    await session.commit()
    return {"scheduled": True, "grace_days": settings.deletion_grace_days}


@router.post("/account/delete-cancel", dependencies=[Depends(require_csrf)], tags=["account"])
async def delete_cancel(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    user.deletion_requested_at = None
    await session.commit()
    return {"scheduled": False}


@router.get("/data-health", tags=["health"])
async def data_health(
    user: User = Depends(verified_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    runs = (
        await session.scalars(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(20))
    ).all()
    stale = await session.scalar(
        select(func.count()).select_from(Recommendation).where(Recommendation.band == "STALE_DATA")
    )
    return {
        "provider_mode": "demo",
        "status": "partial" if stale else "healthy",
        "stale_symbols": int(stale or 0),
        "runs": [
            {
                "id": run.id,
                "job_type": run.job_type,
                "provider": run.provider,
                "status": run.status,
                "requested_count": run.requested_count,
                "written_count": run.written_count,
                "coverage": run.coverage,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "warnings": run.warnings,
                "error_summary": run.error_summary,
            }
            for run in runs
        ],
    }


@router.get("/admin/jobs", tags=["admin"])
async def admin_jobs(
    user: User = Depends(admin_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    return await data_health(user, session)


@router.post("/admin/jobs/{job_type}", dependencies=[Depends(require_csrf)], tags=["admin"])
async def admin_trigger_job(
    job_type: str,
    user: User = Depends(admin_user),
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    allowed = {"price_sync", "fundamentals_sync", "scoring", "demo_reset", "weekly_digest"}
    if job_type not in allowed:
        raise HTTPException(status_code=404, detail="Allowed job not found")
    active = await session.scalar(
        select(SyncRun).where(
            SyncRun.job_type == job_type, SyncRun.status.in_(["queued", "running"])
        )
    )
    if active:
        raise HTTPException(status_code=409, detail="This job is already active")
    run = SyncRun(
        job_type=job_type,
        provider="demo",
        status="running",
        started_at=datetime.now(UTC),
    )
    session.add(run)
    session.add(
        AuditEvent(
            actor_user_id=user.id,
            action="admin.job.trigger",
            target_type="sync_run",
            target_id=run.id,
            metadata_json={"job_type": job_type},
            created_at=datetime.now(UTC),
        )
    )
    await session.flush()
    if job_type == "weekly_digest":
        run.written_count = await run_digest_job(session, settings)
    elif job_type == "demo_reset":
        counts = await seed_demo(session, settings, reset=True)
        run.written_count = sum(counts.values())
    else:
        counts = await seed_demo(session, settings)
        run.written_count = sum(counts.values())
    run.status = "completed"
    run.coverage = 100
    run.completed_at = datetime.now(UTC)
    await session.commit()
    return {"id": run.id, "job_type": job_type, "status": run.status}


@router.get("/admin/product-metrics", tags=["admin"])
async def product_metrics(
    user: User = Depends(admin_user), session: AsyncSession = Depends(get_db)
) -> dict[str, object]:
    cutoff_day = datetime.now(UTC) - timedelta(days=1)
    cutoff_week = datetime.now(UTC) - timedelta(days=7)
    legitimate = and_(User.is_demo.is_(False), User.role != "admin")
    registered = await session.scalar(select(func.count()).select_from(User).where(legitimate))
    verified = await session.scalar(
        select(func.count())
        .select_from(User)
        .where(legitimate, User.email_verified_at.is_not(None))
    )
    activated = await session.scalar(
        select(func.count()).select_from(User).where(legitimate, User.activated_at.is_not(None))
    )
    dau = await session.scalar(
        select(func.count(func.distinct(ProductEvent.user_id)))
        .join(User, User.id == ProductEvent.user_id)
        .where(legitimate, ProductEvent.occurred_at >= cutoff_day)
    )
    wau = await session.scalar(
        select(func.count(func.distinct(ProductEvent.user_id)))
        .join(User, User.id == ProductEvent.user_id)
        .where(legitimate, ProductEvent.occurred_at >= cutoff_week)
    )
    referrals = await session.scalar(
        select(func.count()).select_from(Attribution).where(Attribution.user_id.is_not(None))
    )
    feedback_count = await session.scalar(select(func.count()).select_from(Feedback))
    return {
        "registered": int(registered or 0),
        "verified": int(verified or 0),
        "activated": int(activated or 0),
        "daily_active": int(dau or 0),
        "weekly_active": int(wau or 0),
        "referral_conversions": int(referrals or 0),
        "feedback": int(feedback_count or 0),
        "exclusions": "demo users, administrators, tests, health checks",
        "note": "Counts are shown without misleading percentages when the sample is small.",
    }


@router.get("/admin/feedback", tags=["admin"])
async def admin_feedback(
    status_filter: str | None = None,
    user: User = Depends(admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    query = select(Feedback).order_by(Feedback.created_at.desc())
    if status_filter:
        query = query.where(Feedback.status == status_filter)
    items = (await session.scalars(query)).all()
    return {
        "items": [
            {
                "id": item.id,
                "category": item.category,
                "rating": item.rating,
                "message": item.message,
                "page_path": item.page_path,
                "symbol": item.symbol,
                "data_version": item.data_version,
                "status": item.status,
                "admin_note": item.admin_note,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ]
    }


@router.patch("/admin/feedback/{feedback_id}", dependencies=[Depends(require_csrf)], tags=["admin"])
async def update_feedback(
    feedback_id: str,
    payload: FeedbackUpdate,
    user: User = Depends(admin_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    item = await session.get(Feedback, feedback_id)
    if not item:
        raise HTTPException(status_code=404, detail="Feedback not found")
    item.status = payload.status
    item.admin_note = html.escape(payload.admin_note.strip())
    await session.commit()
    return {"id": item.id, "status": item.status}
