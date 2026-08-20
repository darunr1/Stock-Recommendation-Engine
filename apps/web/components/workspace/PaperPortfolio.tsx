"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import Disclosure from "@/components/Disclosure";
import { api } from "@/lib/api";
import { Metric, PageHead, QueryState } from "./Shared";

type Portfolio = {
  starting_cash: number;
  cash: number;
  market_value: number;
  total_value: number;
  total_return: number;
  realized_pl: number;
  unrealized_pl: number;
  disclosure: string;
  positions: {
    symbol: string;
    company_name: string;
    quantity: number;
    average_cost: number;
    latest_price: number;
    market_value: number;
    unrealized_pl: number;
  }[];
  transactions: {
    id: string;
    symbol: string;
    side: string;
    quantity: number;
    price: number;
    execution_date: string;
    realized_pl: number;
  }[];
};

export default function PaperPortfolioPage() {
  const client = useQueryClient();
  const [trade, setTrade] = useState({
    symbol: "AAPL",
    side: "buy",
    quantity: 10,
  });
  const [message, setMessage] = useState("");
  const query = useQuery({
    queryKey: ["paper"],
    queryFn: () => api<Portfolio>("/paper/portfolio"),
  });
  const submitTrade = useMutation({
    mutationFn: () =>
      api<Portfolio>("/paper/transactions", {
        method: "POST",
        body: JSON.stringify(trade),
      }),
    onSuccess: () => {
      setMessage("Simulated transaction recorded.");
      void client.invalidateQueries({ queryKey: ["paper"] });
    },
    onError: (error) => setMessage(error.message),
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    submitTrade.mutate();
  }
  async function reset() {
    if (!window.confirm("Reset the simulated ledger and positions?")) return;
    await api("/paper/portfolio/reset", {
      method: "POST",
      body: JSON.stringify({ starting_cash: 100000 }),
    });
    setMessage("Paper portfolio reset.");
    void client.invalidateQueries({ queryKey: ["paper"] });
  }
  return (
    <>
      <PageHead
        eyebrow="Decision tracker"
        title="Paper portfolio"
        copy="A simplified close-price simulation with no broker connection."
        action={
          <button className="button secondary" onClick={reset}>
            Reset simulation
          </button>
        }
      />
      <QueryState
        loading={query.isLoading}
        error={query.error}
        onRetry={() => void query.refetch()}
      />
      {query.data && (
        <>
          <div className="metric-grid">
            <Metric
              label="Total value"
              value={query.data.total_value.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            />
            <Metric
              label="Cash"
              value={query.data.cash.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            />
            <Metric
              label="Unrealized P/L"
              value={query.data.unrealized_pl.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            />
            <Metric
              label="Total return"
              value={`${(query.data.total_return * 100).toFixed(2)}%`}
            />
          </div>
          <div className="content-grid">
            <section className="card">
              <div className="card-head">
                <h2>Positions</h2>
                <span className="status-badge">
                  {query.data.positions.length}
                </span>
              </div>
              {query.data.positions.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Symbol</th>
                        <th>Quantity</th>
                        <th>Avg. cost</th>
                        <th>Latest</th>
                        <th>Market value</th>
                        <th>Unrealized</th>
                      </tr>
                    </thead>
                    <tbody>
                      {query.data.positions.map((position) => (
                        <tr key={position.symbol}>
                          <td>
                            <strong>{position.symbol}</strong>
                          </td>
                          <td>{position.quantity}</td>
                          <td>${position.average_cost.toFixed(2)}</td>
                          <td>${position.latest_price.toFixed(2)}</td>
                          <td>${position.market_value.toFixed(2)}</td>
                          <td
                            className={
                              position.unrealized_pl >= 0
                                ? "positive"
                                : "negative"
                            }
                          >
                            {position.unrealized_pl >= 0 ? "▲" : "▼"} $
                            {position.unrealized_pl.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <p>No simulated positions yet.</p>
                </div>
              )}
            </section>
            <aside className="card">
              <div className="card-head">
                <h2>Record a trade</h2>
                <span className="status-badge">Daily close</span>
              </div>
              <form className="form-grid" onSubmit={submit}>
                <label>
                  Symbol
                  <input
                    value={trade.symbol}
                    onChange={(event) =>
                      setTrade({
                        ...trade,
                        symbol: event.target.value.toUpperCase(),
                      })
                    }
                  />
                </label>
                <label>
                  Side
                  <select
                    value={trade.side}
                    onChange={(event) =>
                      setTrade({ ...trade, side: event.target.value })
                    }
                  >
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                  </select>
                </label>
                <label>
                  Shares
                  <input
                    type="number"
                    min="0.000001"
                    step="any"
                    value={trade.quantity}
                    onChange={(event) =>
                      setTrade({
                        ...trade,
                        quantity: Number(event.target.value),
                      })
                    }
                  />
                </label>
                {message && (
                  <p
                    className={
                      message.includes("recorded") || message.includes("reset")
                        ? "form-message"
                        : "form-message error"
                    }
                  >
                    {message}
                  </p>
                )}
                <button className="button" disabled={submitTrade.isPending}>
                  {submitTrade.isPending
                    ? "Validating…"
                    : `Record simulated ${trade.side}`}
                </button>
              </form>
            </aside>
          </div>
          <section className="card" style={{ marginTop: "1rem" }}>
            <div className="card-head">
              <h2>Transaction ledger</h2>
              <span className="status-badge">
                Realized P/L ${query.data.realized_pl.toFixed(2)}
              </span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Realized P/L</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.transactions.map((item) => (
                    <tr key={item.id}>
                      <td>{item.execution_date}</td>
                      <td>{item.symbol}</td>
                      <td>{item.side}</td>
                      <td>{item.quantity}</td>
                      <td>${item.price.toFixed(2)}</td>
                      <td>${item.realized_pl.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <div style={{ marginTop: "1rem" }}>
            <Disclosure>
              {query.data.disclosure} For education and research only. Not
              investment advice.
            </Disclosure>
          </div>
        </>
      )}
    </>
  );
}
