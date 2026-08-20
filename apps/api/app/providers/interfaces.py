from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class PriceBar:
    symbol: str
    trading_date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float
    volume: int
    provider: str
    feed: str
    adjustment: str
    fetched_at: datetime
    valid: bool = True


@dataclass(frozen=True)
class FundamentalSnapshot:
    symbol: str
    as_of_date: date
    filed_at: date
    metrics: dict[str, float | None]
    coverage: float
    warnings: tuple[str, ...] = ()


class MarketDataProvider(ABC):
    @abstractmethod
    async def daily_bars(self, symbols: list[str], start: date, end: date) -> list[PriceBar]:
        """Return adjusted daily bars without leaking provider SDK objects."""


class FundamentalsProvider(ABC):
    @abstractmethod
    async def snapshots(self, symbols: list[str], as_of: date) -> dict[str, FundamentalSnapshot]:
        """Return the latest fundamentals known on or before ``as_of``."""
