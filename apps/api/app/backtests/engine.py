from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def _finite(value: float) -> float | None:
    return round(float(value), 6) if math.isfinite(value) else None


def backtest_metrics(
    strategy: pd.Series,
    benchmark: pd.Series,
    *,
    initial_capital: float,
    turnover: float,
    modeled_costs: float,
    rebalances: int,
) -> dict[str, float | int | None]:
    if len(strategy) < 2:
        return {
            "total_return": None,
            "cagr": None,
            "annualized_volatility": None,
            "sharpe": None,
            "sortino": None,
            "max_drawdown": None,
            "calmar": None,
            "monthly_hit_rate": None,
            "turnover": turnover,
            "rebalances": rebalances,
            "modeled_costs": modeled_costs,
        }
    returns = strategy.pct_change().dropna()
    total_return = strategy.iloc[-1] / initial_capital - 1
    years = max((strategy.index[-1] - strategy.index[0]).days / 365.25, 1 / 365.25)
    cagr = (strategy.iloc[-1] / strategy.iloc[0]) ** (1 / years) - 1
    volatility = returns.std(ddof=1) * math.sqrt(252)
    sharpe = (
        returns.mean() / returns.std(ddof=1) * math.sqrt(252) if returns.std(ddof=1) else math.nan
    )
    downside = returns[returns < 0]
    sortino = (
        returns.mean() / downside.std(ddof=1) * math.sqrt(252)
        if len(downside) > 1 and downside.std(ddof=1)
        else math.nan
    )
    drawdown = strategy / strategy.cummax() - 1
    max_dd = float(drawdown.min())
    calmar = cagr / abs(max_dd) if max_dd else math.nan
    monthly_strategy = strategy.resample("ME").last().pct_change().dropna()
    monthly_benchmark = benchmark.resample("ME").last().pct_change().dropna()
    aligned = pd.concat([monthly_strategy, monthly_benchmark], axis=1).dropna()
    hit_rate = float((aligned.iloc[:, 0] > aligned.iloc[:, 1]).mean()) if len(aligned) else math.nan
    return {
        "total_return": _finite(total_return),
        "cagr": _finite(cagr),
        "annualized_volatility": _finite(volatility),
        "sharpe": _finite(sharpe),
        "sortino": _finite(sortino),
        "max_drawdown": _finite(max_dd),
        "calmar": _finite(calmar),
        "monthly_hit_rate": _finite(hit_rate),
        "turnover": round(turnover, 6),
        "rebalances": rebalances,
        "modeled_costs": round(modeled_costs, 2),
    }


def run_walk_forward(prices: dict[str, pd.DataFrame], config: dict[str, Any]) -> dict[str, object]:
    """Run a deterministic next-session, price-factor walk-forward simulation.

    Each monthly signal uses only bars through the prior session. Selection combines
    contemporaneous momentum and inverse volatility. Demo fundamentals are not replayed;
    this limitation is surfaced in result warnings rather than silently using future facts.
    """

    start = pd.Timestamp(str(config["start_date"]))
    end = pd.Timestamp(str(config["end_date"]))
    spy = prices["SPY"].copy().sort_index().loc[start:end]
    if len(spy) < 252:
        raise ValueError("Insufficient SPY history for the selected period")
    sessions = spy.index
    cadence = "QS" if config.get("rebalance_frequency") == "quarterly" else "MS"
    period_keys = sessions.to_period("Q" if cadence == "QS" else "M")
    rebalance_indices = [
        index for index in range(1, len(sessions)) if period_keys[index] != period_keys[index - 1]
    ]
    initial = float(config["initial_capital"])
    value = initial
    benchmark_value = initial
    holdings: list[str] = []
    turnover_total = 0.0
    modeled_costs = 0.0
    rebalance_log: list[dict[str, object]] = []
    points: list[dict[str, object]] = []
    cost_rate = (float(config["transaction_cost_bps"]) + float(config["slippage_bps"])) / 10_000
    top_n = int(config["top_n"])
    rebalance_set = set(rebalance_indices)
    for index in range(1, len(sessions)):
        current = sessions[index]
        previous = sessions[index - 1]
        if index in rebalance_set:
            candidates: list[tuple[str, float]] = []
            for symbol, frame in prices.items():
                if symbol == "SPY":
                    continue
                history = frame.loc[:previous]
                if len(history) < 252:
                    continue
                closes = history["close"].astype(float)
                dollar_volume = (history["close"] * history["volume"]).iloc[-20:].median()
                if closes.iloc[-1] < 5 or dollar_volume < 10_000_000:
                    continue
                momentum = closes.iloc[-1] / closes.iloc[-127] - 1
                volatility = closes.pct_change().iloc[-63:].std(ddof=1) * math.sqrt(252)
                candidates.append((symbol, float(momentum - 0.35 * volatility)))
            selected = [
                symbol
                for symbol, _ in sorted(candidates, key=lambda item: (-item[1], item[0]))[:top_n]
            ]
            changed = len(set(selected).symmetric_difference(holdings))
            turnover = changed / max(1, top_n)
            charge = value * turnover * cost_rate
            value -= charge
            turnover_total += turnover
            modeled_costs += charge
            holdings = selected
            rebalance_log.append(
                {
                    "signal_date": previous.date().isoformat(),
                    "execution_date": current.date().isoformat(),
                    "symbols": selected,
                    "turnover": round(turnover, 4),
                    "modeled_cost": round(charge, 2),
                }
            )
        daily_returns: list[float] = []
        for symbol in holdings:
            frame = prices[symbol]
            if current in frame.index and previous in frame.index:
                daily_returns.append(
                    float(frame.loc[current, "close"] / frame.loc[previous, "close"] - 1)
                )
        if daily_returns:
            value *= 1 + float(np.mean(daily_returns))
        benchmark_value *= float(spy.loc[current, "close"] / spy.loc[previous, "close"])
        points.append(
            {
                "date": current.date().isoformat(),
                "strategy_value": round(value, 2),
                "benchmark_value": round(benchmark_value, 2),
            }
        )
    series_frame = pd.DataFrame(points)
    series_frame.index = pd.to_datetime(series_frame["date"])
    strategy_series = series_frame["strategy_value"]
    benchmark_series = series_frame["benchmark_value"]
    drawdown = strategy_series / strategy_series.cummax() - 1
    for point, draw in zip(points, drawdown, strict=True):
        point["drawdown"] = round(float(draw), 6)
    metrics = backtest_metrics(
        strategy_series,
        benchmark_series,
        initial_capital=initial,
        turnover=turnover_total,
        modeled_costs=modeled_costs,
        rebalances=len(rebalance_log),
    )
    yearly = strategy_series.resample("YE").last().pct_change()
    annual_returns = {
        str(index.year): round(float(value), 6)
        for index, value in yearly.items()
        if math.isfinite(value)
    }
    return {
        "series": points,
        "metrics": metrics,
        "annual_returns": annual_returns,
        "rebalances": rebalance_log,
        "assumptions": {
            "signal": "Prior session completed price-factor rank",
            "execution": "Next market session; costs and slippage charged one way",
            "holdings": f"Top {top_n}, equal weighted",
            "benchmark": "SPY buy and hold",
            "dividends": "Reflected only when present in adjusted demo price history",
            "risk_free_rate": 0,
        },
        "warnings": [
            "Demo mode uses deterministic synthetic prices, not observed market history.",
            "The replay uses point-in-time price factors; historical SEC filing fixtures are not included in this demo backtest.",
        ],
        "coverage": round(len(points) / max(1, len(sessions) - 1), 6),
    }
