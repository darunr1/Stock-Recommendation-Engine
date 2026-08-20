from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx

from app.providers.interfaces import FundamentalSnapshot, FundamentalsProvider

TAG_MAP: dict[str, tuple[str, ...]] = {
    "revenue_ttm": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"),
    "net_income_ttm": ("NetIncomeLoss",),
    "total_assets": ("Assets",),
    "equity": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
    "operating_cash_flow_ttm": ("NetCashProvidedByUsedInOperatingActivities",),
    "capex_ttm": ("PaymentsToAcquirePropertyPlantAndEquipment",),
    "debt": (
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "LongTermDebtCurrent",
        "LongTermDebt",
    ),
    "shares_outstanding": (
        "CommonStocksIncludingAdditionalPaidInCapital",
        "EntityCommonStockSharesOutstanding",
    ),
}


def latest_fact_as_of(facts: list[dict[str, Any]], as_of: date) -> dict[str, Any] | None:
    allowed = [
        fact
        for fact in facts
        if fact.get("form", "").replace("/A", "") in {"10-K", "10-Q"}
        and fact.get("filed")
        and date.fromisoformat(fact["filed"]) <= as_of
    ]
    if not allowed:
        return None
    return max(allowed, key=lambda item: (item.get("end", ""), item["filed"], item.get("accn", "")))


class SecCompanyFactsProvider(FundamentalsProvider):
    def __init__(
        self, user_agent: str, cik_by_symbol: dict[str, str], cache_dir: str = "var/sec-cache"
    ) -> None:
        self.user_agent = user_agent
        self.cik_by_symbol = cik_by_symbol
        self.cache_dir = Path(cache_dir)

    async def snapshots(self, symbols: list[str], as_of: date) -> dict[str, FundamentalSnapshot]:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        output: dict[str, FundamentalSnapshot] = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5)) as client:
            for symbol in symbols:
                cik = self.cik_by_symbol.get(symbol)
                if not cik:
                    continue
                response = await client.get(
                    f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
                    headers={"User-Agent": self.user_agent, "Accept-Encoding": "gzip, deflate"},
                )
                response.raise_for_status()
                raw = response.content
                checksum = hashlib.sha256(raw).hexdigest()
                (self.cache_dir / f"{int(cik):010d}-{checksum[:12]}.json").write_bytes(raw)
                payload = json.loads(raw)
                us_gaap = payload.get("facts", {}).get("us-gaap", {})
                metrics: dict[str, float | None] = {}
                filed_dates: list[date] = []
                warnings: list[str] = []
                for metric, tags in TAG_MAP.items():
                    selected = None
                    for tag in tags:
                        units = us_gaap.get(tag, {}).get("units", {})
                        candidates = units.get("USD") or units.get("shares") or []
                        selected = latest_fact_as_of(candidates, as_of)
                        if selected:
                            break
                    metrics[metric] = float(selected["val"]) if selected else None
                    if selected:
                        filed_dates.append(date.fromisoformat(selected["filed"]))
                    else:
                        warnings.append(
                            f"No reliable {metric} fact available as of {as_of.isoformat()}."
                        )
                coverage = sum(value is not None for value in metrics.values()) / max(
                    1, len(metrics)
                )
                output[symbol] = FundamentalSnapshot(
                    symbol=symbol,
                    as_of_date=as_of,
                    filed_at=max(filed_dates) if filed_dates else as_of,
                    metrics=metrics,
                    coverage=coverage,
                    warnings=tuple(warnings),
                )
        return output
