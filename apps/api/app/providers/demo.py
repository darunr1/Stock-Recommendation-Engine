from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime

import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.providers.interfaces import (
    FundamentalSnapshot,
    FundamentalsProvider,
    MarketDataProvider,
    PriceBar,
)

DEMO_AS_OF = date(2026, 8, 18)


def symbol_seed(symbol: str) -> int:
    digest = hashlib.sha256(symbol.encode("ascii")).digest()
    return int.from_bytes(digest[:4], "big") ^ get_settings().demo_seed


class DemoMarketDataProvider(MarketDataProvider):
    async def daily_bars(self, symbols: list[str], start: date, end: date) -> list[PriceBar]:
        output: list[PriceBar] = []
        effective_end = min(end, DEMO_AS_OF)
        dates = pd.bdate_range(start=start, end=effective_end)
        for symbol in sorted(symbols):
            symbol_dates = dates[:-6] if symbol == "DIS" and len(dates) > 6 else dates
            price_rng = np.random.default_rng(symbol_seed(symbol))
            microstructure_rng = np.random.default_rng(symbol_seed(symbol) + 10_000_019)
            base = 35.0 + float(symbol_seed(symbol) % 250)
            drift = 0.00028 + ((symbol_seed(symbol) % 17) - 8) * 0.000025
            volatility = 0.013 + (symbol_seed(symbol) % 11) * 0.0007
            if symbol == "AMD":
                drift, volatility = 0.00105, 0.036
            elif symbol in {"KO", "PG"}:
                drift, volatility = 0.0002, 0.009
            elif symbol == "SPY":
                drift, volatility, base = 0.00035, 0.0105, 390.0
            shocks = price_rng.normal(drift, volatility, len(symbol_dates))
            closes = base * np.exp(np.cumsum(shocks))
            volume_base = 8_000_000 + symbol_seed(symbol) % 45_000_000
            for index, session in enumerate(symbol_dates):
                close = float(closes[index])
                overnight = float(microstructure_rng.normal(0, volatility / 3))
                open_price = close * (1 + overnight)
                spread = abs(float(microstructure_rng.normal(volatility / 2, volatility / 5)))
                high = max(open_price, close) * (1 + spread)
                low = min(open_price, close) * max(0.01, 1 - spread)
                volume = max(
                    0,
                    int(volume_base * (1 + microstructure_rng.normal(0, 0.18))),
                )
                valid = (
                    low <= min(open_price, close) <= max(open_price, close) <= high and volume >= 0
                )
                output.append(
                    PriceBar(
                        symbol=symbol,
                        trading_date=session.date(),
                        open=round(open_price, 6),
                        high=round(high, 6),
                        low=round(low, 6),
                        close=round(close, 6),
                        adjusted_close=round(close, 6),
                        volume=volume,
                        provider="demo",
                        feed="deterministic-synthetic",
                        adjustment="all",
                        fetched_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
                        valid=valid,
                    )
                )
        return output


class DemoFundamentalsProvider(FundamentalsProvider):
    async def snapshots(self, symbols: list[str], as_of: date) -> dict[str, FundamentalSnapshot]:
        output: dict[str, FundamentalSnapshot] = {}
        for symbol in sorted(symbols):
            rng = np.random.default_rng(symbol_seed(symbol) + as_of.year)
            revenue = float(28_000_000_000 + symbol_seed(symbol) % 320_000_000_000)
            margin = float(0.055 + rng.random() * 0.27)
            assets = revenue * float(0.8 + rng.random() * 1.4)
            equity = assets * float(0.25 + rng.random() * 0.48)
            debt = assets * float(0.08 + rng.random() * 0.37)
            operating_cash = revenue * (margin + float(rng.random() * 0.08))
            metrics: dict[str, float | None] = {
                "revenue_ttm": revenue,
                "net_income_ttm": revenue * margin,
                "total_assets": assets,
                "average_total_assets": assets * 0.97,
                "equity": equity,
                "operating_cash_flow_ttm": operating_cash,
                "capex_ttm": operating_cash * float(0.12 + rng.random() * 0.28),
                "debt": debt,
                "revenue_growth": float(-0.03 + rng.random() * 0.26),
                "shares_outstanding": float(500_000_000 + symbol_seed(symbol) % 8_000_000_000),
            }
            warnings: tuple[str, ...] = ()
            coverage = 1.0
            if symbol == "ADBE":
                for key in ("operating_cash_flow_ttm", "capex_ttm", "equity", "debt"):
                    metrics[key] = None
                warnings = ("Demo fixture intentionally omits selected fundamental concepts.",)
                coverage = 0.56
            filed_at = date(as_of.year, 6, 30)
            if filed_at > as_of:
                filed_at = date(as_of.year - 1, 12, 31)
            output[symbol] = FundamentalSnapshot(
                symbol=symbol,
                as_of_date=as_of,
                filed_at=filed_at,
                metrics=metrics,
                coverage=coverage,
                warnings=warnings,
            )
        return output
