from __future__ import annotations

import asyncio
import random
from datetime import UTC, date, datetime

import httpx

from app.providers.interfaces import MarketDataProvider, PriceBar


class AlpacaMarketDataProvider(MarketDataProvider):
    def __init__(self, api_key: str, api_secret: str, feed: str | None = None) -> None:
        self.headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }
        self.feed = feed

    async def daily_bars(self, symbols: list[str], start: date, end: date) -> list[PriceBar]:
        params: dict[str, str | int] = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "adjustment": "all",
            "limit": 10000,
        }
        if self.feed:
            params["feed"] = self.feed
        token: str | None = None
        output: list[PriceBar] = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5)) as client:
            for attempt in range(6):
                if token:
                    params["page_token"] = token
                response = await client.get(
                    "https://data.alpaca.markets/v2/stocks/bars",
                    params=params,
                    headers=self.headers,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt == 5:
                        response.raise_for_status()
                    await asyncio.sleep(min(8, 0.35 * (2**attempt)) + random.random() * 0.2)
                    continue
                response.raise_for_status()
                payload = response.json()
                fetched = datetime.now(UTC)
                for symbol, bars in payload.get("bars", {}).items():
                    for bar in bars:
                        opened, high, low, close = map(
                            float, (bar["o"], bar["h"], bar["l"], bar["c"])
                        )
                        volume = int(bar["v"])
                        valid = (
                            low <= min(opened, close) <= max(opened, close) <= high and volume >= 0
                        )
                        output.append(
                            PriceBar(
                                symbol=symbol,
                                trading_date=date.fromisoformat(bar["t"][:10]),
                                open=opened,
                                high=high,
                                low=low,
                                close=close,
                                adjusted_close=close,
                                volume=volume,
                                provider="alpaca",
                                feed=payload.get("feed") or self.feed or "entitled-default",
                                adjustment="all",
                                fetched_at=fetched,
                                valid=valid,
                            )
                        )
                token = payload.get("next_page_token")
                if not token:
                    return output
            return output
