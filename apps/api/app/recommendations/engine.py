from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd

from app.providers.interfaces import FundamentalSnapshot, PriceBar

MODEL_CONFIG: dict[str, Any] = {
    "version": "equitylens-v1",
    "minimum_price": 5.0,
    "minimum_median_dollar_volume": 10_000_000.0,
    "stale_after_sessions": 2,
    "factor_weights": {
        "momentum": 0.30,
        "trend": 0.15,
        "quality": 0.25,
        "value": 0.15,
        "risk": 0.15,
    },
    "feature_weights": {
        "momentum": {"return_21d": 0.20, "return_63d": 0.35, "return_126d": 0.45},
        "trend": {
            "distance_sma20": 0.15,
            "distance_sma50": 0.25,
            "distance_sma200": 0.35,
            "sma50_above_sma200": 0.15,
            "rsi14_health": 0.10,
        },
        "quality": {
            "net_margin": 0.20,
            "return_on_assets": 0.20,
            "operating_cash_flow_margin": 0.20,
            "accrual_quality": 0.15,
            "debt_to_assets": 0.15,
            "revenue_growth": 0.10,
        },
        "value": {
            "earnings_yield": 0.30,
            "sales_yield": 0.20,
            "fcf_yield": 0.30,
            "book_to_market": 0.20,
        },
        "risk": {
            "volatility_63d": 0.30,
            "max_drawdown_252d": 0.25,
            "downside_deviation_252d": 0.20,
            "beta_distance": 0.10,
            "illiquidity_20d": 0.15,
        },
    },
}

LOWER_IS_BETTER = {
    "debt_to_assets",
    "volatility_63d",
    "max_drawdown_252d",
    "downside_deviation_252d",
    "beta_distance",
    "illiquidity_20d",
}

FEATURE_LABELS = {
    "return_21d": "One-month momentum",
    "return_63d": "Three-month momentum",
    "return_126d": "Six-month momentum",
    "distance_sma20": "Distance above the 20-day average",
    "distance_sma50": "Distance above the 50-day average",
    "distance_sma200": "Distance above the 200-day average",
    "sma50_above_sma200": "Long-term trend alignment",
    "rsi14_health": "RSI momentum balance",
    "net_margin": "Net margin",
    "return_on_assets": "Return on assets",
    "operating_cash_flow_margin": "Operating cash-flow margin",
    "accrual_quality": "Cash conversion",
    "debt_to_assets": "Debt to assets",
    "revenue_growth": "Revenue growth",
    "earnings_yield": "Earnings yield",
    "sales_yield": "Sales yield",
    "fcf_yield": "Free-cash-flow yield",
    "book_to_market": "Book to market",
    "volatility_63d": "63-day volatility",
    "max_drawdown_252d": "One-year drawdown",
    "downside_deviation_252d": "Downside deviation",
    "beta_distance": "Beta stability",
    "illiquidity_20d": "Trading liquidity",
}


class Contributor(TypedDict):
    feature: str
    label: str
    factor: str
    percentile: float
    contribution: float
    explanation: str


@dataclass(frozen=True)
class ScoredRecommendation:
    symbol: str
    as_of_date: date
    score: float | None
    band: str
    confidence: float
    confidence_label: str
    factor_scores: dict[str, float | None]
    raw_features: dict[str, float | None]
    percentiles: dict[str, float | None]
    contributors: list[Contributor]
    warnings: list[str]
    freshness: dict[str, object]
    canonical_payload: str


def safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    if (
        numerator is None
        or denominator is None
        or not math.isfinite(denominator)
        or denominator <= 0
    ):
        return None
    result = numerator / denominator
    return result if math.isfinite(result) else None


def rsi(values: np.ndarray, period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    changes = np.diff(values[-(period + 1) :])
    gains = np.clip(changes, 0, None).mean()
    losses = -np.clip(changes, None, 0).mean()
    if losses == 0:
        return 100.0
    strength = gains / losses
    return float(100 - (100 / (1 + strength)))


def max_drawdown(values: np.ndarray) -> float | None:
    if not len(values):
        return None
    peaks = np.maximum.accumulate(values)
    drawdowns = 1 - values / peaks
    return float(np.max(drawdowns))


def business_session_gap(last: date, as_of: date) -> int:
    if last >= as_of:
        return 0
    return max(0, len(pd.bdate_range(last, as_of)) - 1)


def _raw_features(
    symbol: str,
    bars: list[PriceBar],
    fundamentals: FundamentalSnapshot | None,
    spy_returns: pd.Series,
) -> dict[str, float | None]:
    valid = [bar for bar in sorted(bars, key=lambda value: value.trading_date) if bar.valid]
    closes = np.array([bar.adjusted_close for bar in valid], dtype=float)
    volumes = np.array([bar.volume for bar in valid], dtype=float)
    returns = pd.Series(closes).pct_change().dropna()
    latest = closes[-1]
    sma20, sma50, sma200 = (float(np.mean(closes[-window:])) for window in (20, 50, 200))
    rsi_value = rsi(closes)
    health = None if rsi_value is None else max(0.0, 1 - abs(rsi_value - 60.0) / 60.0)
    aligned = returns.iloc[-252:].reset_index(drop=True)
    spy_aligned = spy_returns.iloc[-len(aligned) :].reset_index(drop=True)
    beta = None
    if len(aligned) > 20 and float(spy_aligned.var()) > 0:
        beta = float(np.cov(aligned, spy_aligned, ddof=1)[0, 1] / spy_aligned.var())
    metrics = fundamentals.metrics if fundamentals else {}
    shares = metrics.get("shares_outstanding")
    market_cap = latest * shares if shares else None
    net_income = metrics.get("net_income_ttm")
    revenue = metrics.get("revenue_ttm")
    assets = metrics.get("total_assets")
    avg_assets = metrics.get("average_total_assets")
    operating_cash = metrics.get("operating_cash_flow_ttm")
    capex = metrics.get("capex_ttm")
    equity = metrics.get("equity")
    debt = metrics.get("debt")
    downside = returns.iloc[-252:][returns.iloc[-252:] < 0]
    dollar_volume = closes[-20:] * volumes[-20:]
    amihud_returns = np.abs(returns.iloc[-20:].to_numpy())
    amihud_dollars = dollar_volume[-len(amihud_returns) :]
    return {
        "return_21d": latest / closes[-22] - 1,
        "return_63d": latest / closes[-64] - 1,
        "return_126d": latest / closes[-127] - 1,
        "distance_sma20": latest / sma20 - 1,
        "distance_sma50": latest / sma50 - 1,
        "distance_sma200": latest / sma200 - 1,
        "sma50_above_sma200": 1.0 if sma50 > sma200 else 0.0,
        "rsi14_health": health,
        "net_margin": safe_divide(net_income, revenue),
        "return_on_assets": safe_divide(net_income, avg_assets),
        "operating_cash_flow_margin": safe_divide(operating_cash, revenue),
        "accrual_quality": safe_divide(operating_cash, net_income),
        "debt_to_assets": safe_divide(debt, assets),
        "revenue_growth": metrics.get("revenue_growth"),
        "earnings_yield": safe_divide(net_income, market_cap),
        "sales_yield": safe_divide(revenue, market_cap),
        "fcf_yield": safe_divide(
            operating_cash - capex if operating_cash is not None and capex is not None else None,
            market_cap,
        ),
        "book_to_market": safe_divide(equity, market_cap),
        "volatility_63d": float(returns.iloc[-63:].std(ddof=1) * math.sqrt(252)),
        "max_drawdown_252d": max_drawdown(closes[-252:]),
        "downside_deviation_252d": (
            float(downside.std(ddof=1) * math.sqrt(252)) if len(downside) > 1 else None
        ),
        "beta_distance": abs(beta - 1.0) if beta is not None else None,
        "illiquidity_20d": (
            float(np.mean(amihud_returns / amihud_dollars)) if np.all(amihud_dollars > 0) else None
        ),
    }


def winsorized_percentiles(
    values: dict[str, float | None], reverse: bool = False
) -> dict[str, float | None]:
    available = pd.Series(
        {key: value for key, value in values.items() if value is not None}, dtype=float
    )
    result: dict[str, float | None] = dict.fromkeys(values)
    if available.empty:
        return result
    low, high = available.quantile([0.05, 0.95])
    clipped = available.clip(float(low), float(high))
    ranked = cast(pd.Series, clipped.rank(method="average", pct=True) * 100)
    if reverse:
        ranked = 100 - ranked + (100 / len(ranked))
    for key, value in ranked.items():
        result[str(key)] = round(float(value), 6)
    return result


def _factor_score(
    factor: str, percentiles: dict[str, float | None]
) -> tuple[float | None, dict[str, float]]:
    weights: dict[str, float] = MODEL_CONFIG["feature_weights"][factor]
    present = {
        feature: weight
        for feature, weight in weights.items()
        if percentiles.get(feature) is not None
    }
    coverage = sum(present.values())
    if coverage < 0.5:
        return None, {}
    effective = {feature: weight / coverage for feature, weight in present.items()}
    score = sum(
        value * weight
        for feature, weight in effective.items()
        if (value := percentiles.get(feature)) is not None
    )
    return round(score, 6), effective


def _band(score: float | None, confidence: float, stale: bool, factor_count: int) -> str:
    if stale:
        return "STALE_DATA"
    if score is None or factor_count < 3:
        return "INSUFFICIENT_DATA"
    if score >= 80:
        band = "Strong Candidate"
    elif score >= 65:
        band = "Candidate"
    elif score >= 45:
        band = "Watch"
    else:
        band = "Low Score"
    if confidence < 65 and band in {"Strong Candidate", "Candidate"}:
        return "Watch"
    return band


def _confidence_label(confidence: float) -> str:
    return "High" if confidence >= 85 else "Medium" if confidence >= 65 else "Low"


def score_universe(
    bars_by_symbol: dict[str, list[PriceBar]],
    fundamentals: dict[str, FundamentalSnapshot],
    as_of: date,
) -> list[ScoredRecommendation]:
    spy_bars = sorted(bars_by_symbol.get("SPY", []), key=lambda value: value.trading_date)
    spy_returns = (
        pd.Series([bar.adjusted_close for bar in spy_bars], dtype=float).pct_change().dropna()
    )
    eligible: dict[str, bool] = {}
    stale_flags: dict[str, bool] = {}
    gaps: dict[str, int] = {}
    raw_by_symbol: dict[str, dict[str, float | None]] = {}
    for symbol, bars in sorted(bars_by_symbol.items()):
        if symbol == "SPY":
            continue
        valid = [bar for bar in sorted(bars, key=lambda value: value.trading_date) if bar.valid]
        if len(valid) < 252:
            eligible[symbol] = False
            stale_flags[symbol] = False
            gaps[symbol] = 999
            raw_by_symbol[symbol] = {}
            continue
        gap = business_session_gap(valid[-1].trading_date, as_of)
        gaps[symbol] = gap
        stale_flags[symbol] = gap > MODEL_CONFIG["stale_after_sessions"]
        median_dollar_volume = float(
            np.median([bar.adjusted_close * bar.volume for bar in valid[-20:]])
        )
        eligible[symbol] = (
            not stale_flags[symbol]
            and valid[-1].adjusted_close >= MODEL_CONFIG["minimum_price"]
            and median_dollar_volume >= MODEL_CONFIG["minimum_median_dollar_volume"]
        )
        raw_by_symbol[symbol] = _raw_features(symbol, valid, fundamentals.get(symbol), spy_returns)

    all_features = [
        feature
        for factor_features in MODEL_CONFIG["feature_weights"].values()
        for feature in factor_features
    ]
    percentiles_by_symbol: dict[str, dict[str, float | None]] = {
        symbol: dict.fromkeys(all_features) for symbol in raw_by_symbol
    }
    for feature in all_features:
        values = {
            symbol: raw.get(feature)
            for symbol, raw in raw_by_symbol.items()
            if eligible.get(symbol, False)
        }
        ranked = winsorized_percentiles(values, feature in LOWER_IS_BETTER)
        for symbol, value in ranked.items():
            percentiles_by_symbol[symbol][feature] = value

    output: list[ScoredRecommendation] = []
    for symbol in sorted(raw_by_symbol):
        raw = raw_by_symbol[symbol]
        percentiles = percentiles_by_symbol[symbol]
        factors: dict[str, float | None] = {}
        effective_features: dict[str, dict[str, float]] = {}
        for factor in MODEL_CONFIG["factor_weights"]:
            factors[factor], effective_features[factor] = _factor_score(factor, percentiles)
        present_factors = {name: value for name, value in factors.items() if value is not None}
        required_present = factors.get("momentum") is not None and factors.get("risk") is not None
        factor_weight_sum = sum(MODEL_CONFIG["factor_weights"][name] for name in present_factors)
        score = None
        if len(present_factors) >= 3 and required_present and factor_weight_sum:
            score = round(
                sum(
                    float(value) * MODEL_CONFIG["factor_weights"][name] / factor_weight_sum
                    for name, value in present_factors.items()
                ),
                6,
            )
        weighted_coverage = 0.0
        for factor, factor_weight in MODEL_CONFIG["factor_weights"].items():
            internal = MODEL_CONFIG["feature_weights"][factor]
            weighted_coverage += factor_weight * sum(
                weight for feature, weight in internal.items() if raw.get(feature) is not None
            )
        price_freshness = max(0.0, 1 - gaps[symbol] / 3) if gaps[symbol] < 999 else 0.0
        snapshot = fundamentals.get(symbol)
        fundamental_age = (as_of - snapshot.filed_at).days if snapshot else 9999
        if fundamental_age <= 120:
            fundamentals_freshness = 1.0
        else:
            fundamentals_freshness = max(0.0, 1 - (fundamental_age - 120) / 430)
        freshness_score = 0.6 * price_freshness + 0.4 * fundamentals_freshness
        valid_bars = [bar for bar in bars_by_symbol[symbol] if bar.valid]
        recent_dates = [bar.trading_date for bar in valid_bars[-252:]]
        continuity = min(1.0, len(recent_dates) / 252)
        confidence = round(
            min(100.0, 100 * (0.7 * weighted_coverage + 0.2 * freshness_score + 0.1 * continuity)),
            6,
        )
        warnings = list(snapshot.warnings if snapshot else ("Fundamentals are unavailable.",))
        if stale_flags[symbol]:
            warnings.append("Latest price is older than two expected trading sessions.")
        if len(present_factors) < 3:
            warnings.append("Fewer than three factor families have sufficient coverage.")
        contributors: list[Contributor] = []
        for factor, feature_weights in effective_features.items():
            global_weight = MODEL_CONFIG["factor_weights"][factor]
            for feature, internal_weight in feature_weights.items():
                percentile = percentiles.get(feature)
                if percentile is None:
                    continue
                contribution = (percentile - 50) / 50 * global_weight * internal_weight * 100
                direction = "positively" if contribution >= 0 else "negatively"
                contributors.append(
                    {
                        "feature": feature,
                        "label": FEATURE_LABELS[feature],
                        "factor": factor,
                        "percentile": round(percentile, 2),
                        "contribution": round(contribution, 4),
                        "explanation": (
                            f"{FEATURE_LABELS[feature]} ranks in the {percentile:.0f}th percentile "
                            f"and contributes {direction} to the composite."
                        ),
                    }
                )
        positives = sorted(
            (item for item in contributors if float(item["contribution"]) >= 0),
            key=lambda item: (-float(item["contribution"]), str(item["feature"])),
        )[:3]
        negatives = sorted(
            (item for item in contributors if float(item["contribution"]) < 0),
            key=lambda item: (float(item["contribution"]), str(item["feature"])),
        )[:3]
        top_contributors = positives + negatives
        band = _band(score, confidence, stale_flags[symbol], len(present_factors))
        analytic_payload = {
            "as_of_date": as_of.isoformat(),
            "band": band,
            "confidence": confidence,
            "confidence_label": _confidence_label(confidence),
            "contributors": top_contributors,
            "factor_scores": factors,
            "model_version": MODEL_CONFIG["version"],
            "percentiles": percentiles,
            "raw_features": raw,
            "score": score,
            "symbol": symbol,
            "warnings": warnings,
        }
        canonical = json.dumps(
            analytic_payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        output.append(
            ScoredRecommendation(
                symbol=symbol,
                as_of_date=as_of,
                score=score,
                band=band,
                confidence=confidence,
                confidence_label=_confidence_label(confidence),
                factor_scores=factors,
                raw_features=raw,
                percentiles=percentiles,
                contributors=top_contributors,
                warnings=warnings,
                freshness={
                    "price_date": max(
                        bar.trading_date for bar in bars_by_symbol[symbol]
                    ).isoformat(),
                    "price_session_gap": gaps[symbol],
                    "fundamentals_filed_at": snapshot.filed_at.isoformat() if snapshot else None,
                    "coverage": round(weighted_coverage, 6),
                },
                canonical_payload=canonical,
            )
        )
    return output


def market_regime(spy_bars: list[PriceBar]) -> dict[str, object]:
    valid = sorted((bar for bar in spy_bars if bar.valid), key=lambda bar: bar.trading_date)
    closes = np.array([bar.adjusted_close for bar in valid], dtype=float)
    latest = closes[-1]
    sma50, sma200 = float(np.mean(closes[-50:])), float(np.mean(closes[-200:]))
    conditions = [latest > sma200, sma50 > sma200]
    label = "Risk-on" if all(conditions) else "Risk-off" if not any(conditions) else "Mixed"
    return {
        "label": label,
        "as_of": valid[-1].trading_date.isoformat(),
        "close": round(latest, 2),
        "sma50": round(sma50, 2),
        "sma200": round(sma200, 2),
        "formula": "SPY close > SMA200 and SMA50 > SMA200",
        "context_only": True,
    }
