from __future__ import annotations

import asyncio
from datetime import date, timedelta

from app.providers.demo import DEMO_AS_OF, DemoFundamentalsProvider, DemoMarketDataProvider
from app.recommendations.engine import score_universe, winsorized_percentiles


def test_percentiles_reverse_lower_is_better() -> None:
    normal = winsorized_percentiles({"a": 1.0, "b": 2.0, "c": 3.0})
    reverse = winsorized_percentiles({"a": 1.0, "b": 2.0, "c": 3.0}, reverse=True)
    assert normal["a"] < normal["c"]
    assert reverse["a"] > reverse["c"]
    assert winsorized_percentiles({"missing": None})["missing"] is None


def test_scoring_is_deterministic_explainable_and_handles_stale_data() -> None:
    symbols = ["AAPL", "MSFT", "AMD", "KO", "ADBE", "DIS", "SPY"]

    async def calculate():
        bars = await DemoMarketDataProvider().daily_bars(
            symbols, DEMO_AS_OF - timedelta(days=365 * 3), DEMO_AS_OF
        )
        grouped = {symbol: [] for symbol in symbols}
        for bar in bars:
            grouped[bar.symbol].append(bar)
        fundamentals = await DemoFundamentalsProvider().snapshots(symbols, DEMO_AS_OF)
        return score_universe(grouped, fundamentals, DEMO_AS_OF)

    first = asyncio.run(calculate())
    second = asyncio.run(calculate())
    assert [item.canonical_payload for item in first] == [item.canonical_payload for item in second]
    by_symbol = {item.symbol: item for item in first}
    assert by_symbol["DIS"].band == "STALE_DATA"
    assert by_symbol["AAPL"].contributors
    assert all("percentile" in item for item in by_symbol["AAPL"].contributors)
    assert by_symbol["ADBE"].confidence < by_symbol["AAPL"].confidence
    assert 0 <= (by_symbol["AMD"].score or 0) <= 100


def test_future_bars_do_not_change_an_earlier_score() -> None:
    symbols = ["AAPL", "MSFT", "AMD", "KO", "SPY"]
    signal_date = date(2025, 12, 31)

    async def calculate(end: date):
        bars = await DemoMarketDataProvider().daily_bars(
            symbols, signal_date - timedelta(days=365 * 3), end
        )
        grouped = {
            symbol: [
                bar for bar in bars if bar.symbol == symbol and bar.trading_date <= signal_date
            ]
            for symbol in symbols
        }
        fundamentals = await DemoFundamentalsProvider().snapshots(symbols, signal_date)
        return score_universe(grouped, fundamentals, signal_date)

    baseline = asyncio.run(calculate(signal_date))
    with_future = asyncio.run(calculate(DEMO_AS_OF))
    assert [item.canonical_payload for item in baseline] == [
        item.canonical_payload for item in with_future
    ]
