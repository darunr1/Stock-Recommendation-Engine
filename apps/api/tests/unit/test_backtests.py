from __future__ import annotations

import numpy as np
import pandas as pd

from app.backtests.engine import backtest_metrics, run_walk_forward


def frames() -> dict[str, pd.DataFrame]:
    dates = pd.bdate_range("2021-01-01", "2024-12-31")
    output: dict[str, pd.DataFrame] = {}
    for index, symbol in enumerate(["SPY", "AAA", "BBB", "CCC", "DDD"]):
        close = 80 * np.exp(np.cumsum(np.full(len(dates), 0.0002 + index * 0.00003)))
        output[symbol] = pd.DataFrame(
            {"open": close, "close": close, "volume": np.full(len(dates), 30_000_000)},
            index=dates,
        )
    return output


def config(cost: float) -> dict[str, object]:
    return {
        "start_date": "2022-01-03",
        "end_date": "2024-12-31",
        "rebalance_frequency": "monthly",
        "top_n": 3,
        "initial_capital": 100_000,
        "transaction_cost_bps": cost,
        "slippage_bps": 5,
    }


def test_costs_reduce_walk_forward_results_and_execution_is_next_session() -> None:
    no_cost = run_walk_forward(frames(), config(0))
    with_cost = run_walk_forward(frames(), config(50))
    assert with_cost["series"][-1]["strategy_value"] < no_cost["series"][-1]["strategy_value"]
    assert all(item["execution_date"] > item["signal_date"] for item in with_cost["rebalances"])
    assert with_cost["metrics"]["modeled_costs"] > no_cost["metrics"]["modeled_costs"]


def test_undefined_metrics_are_null_not_infinity() -> None:
    index = pd.to_datetime(["2024-01-01"])
    series = pd.Series([100_000.0], index=index)
    metrics = backtest_metrics(
        series,
        series,
        initial_capital=100_000,
        turnover=0,
        modeled_costs=0,
        rebalances=0,
    )
    assert metrics["cagr"] is None
    assert metrics["sharpe"] is None
