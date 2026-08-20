"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import Disclosure from "@/components/Disclosure";
import { Sparkline } from "@/components/ResearchUI";
import { api } from "@/lib/api";
import { Metric, PageHead, QueryState } from "./Shared";

type Run = {
  id: string;
  status: string;
  progress: number;
  config: Record<string, unknown>;
  metrics: Record<string, number | null> | null;
  created_at: string;
  completed_at?: string;
  error_summary?: string;
};
type Detail = {
  id: string;
  status: string;
  progress: number;
  config: Record<string, unknown>;
  model_version: string;
  result: null | {
    series: {
      date: string;
      strategy_value: number;
      benchmark_value: number;
      drawdown: number;
    }[];
    metrics: Record<string, number | null>;
    assumptions: Record<string, string | number>;
    warnings: string[];
    coverage: number;
  };
  error_summary?: string;
};

export default function Backtests() {
  const client = useQueryClient();
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    start_date: "2022-01-03",
    end_date: "2026-07-31",
    top_n: 10,
    transaction_cost_bps: 10,
    slippage_bps: 5,
  });
  const runs = useQuery({
    queryKey: ["backtests"],
    queryFn: () => api<{ items: Run[] }>("/backtests"),
    refetchInterval: 4000,
  });
  const detail = useQuery({
    queryKey: ["backtest", selected],
    queryFn: () => api<Detail>(`/backtests/${selected}`),
    enabled: Boolean(selected),
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 2000 : false,
  });
  const create = useMutation({
    mutationFn: () =>
      api<{ id: string }>("/backtests", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          rebalance_frequency: "monthly",
          minimum_confidence: 65,
          factor_weights: {
            momentum: 0.3,
            trend: 0.15,
            quality: 0.25,
            value: 0.15,
            risk: 0.15,
          },
          initial_capital: 100000,
          benchmark: "SPY",
        }),
      }),
    onSuccess: (data) => {
      setSelected(data.id);
      setError("");
      void client.invalidateQueries({ queryKey: ["backtests"] });
    },
    onError: (reason) => setError(reason.message),
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    create.mutate();
  }
  const result = detail.data?.result;
  return (
    <>
      <PageHead
        eyebrow="Walk-forward laboratory"
        title="Backtests"
        copy="Signals form on the prior session; modeled execution starts on the next session."
      />
      <div className="content-grid">
        <section className="card">
          <div className="card-head">
            <h2>Configure a run</h2>
            <span className="status-badge">Immutable on save</span>
          </div>
          <form className="form-grid" onSubmit={submit}>
            <div className="form-row">
              <label>
                Start date
                <input
                  type="date"
                  value={form.start_date}
                  onChange={(event) =>
                    setForm({ ...form, start_date: event.target.value })
                  }
                />
              </label>
              <label>
                End date
                <input
                  type="date"
                  value={form.end_date}
                  onChange={(event) =>
                    setForm({ ...form, end_date: event.target.value })
                  }
                />
              </label>
            </div>
            <div className="form-row">
              <label>
                Top N
                <input
                  type="number"
                  min="3"
                  max="20"
                  value={form.top_n}
                  onChange={(event) =>
                    setForm({ ...form, top_n: Number(event.target.value) })
                  }
                />
              </label>
              <label>
                One-way cost (bps)
                <input
                  type="number"
                  min="0"
                  max="100"
                  value={form.transaction_cost_bps}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      transaction_cost_bps: Number(event.target.value),
                    })
                  }
                />
              </label>
            </div>
            <label>
              Slippage (bps)
              <input
                type="number"
                min="0"
                max="100"
                value={form.slippage_bps}
                onChange={(event) =>
                  setForm({ ...form, slippage_bps: Number(event.target.value) })
                }
              />
            </label>
            {error && <p className="form-message error">{error}</p>}
            <button className="button" disabled={create.isPending}>
              {create.isPending ? "Queueing…" : "Queue walk-forward run"}
            </button>
            <Disclosure />
          </form>
        </section>
        <section className="card">
          <div className="card-head">
            <h2>Saved runs</h2>
            <span className="status-badge">{runs.data?.items.length ?? 0}</span>
          </div>
          <QueryState
            loading={runs.isLoading}
            error={runs.error}
            empty={runs.data?.items.length === 0}
          />
          {runs.data?.items.map((run) => (
            <button
              key={run.id}
              className="button secondary"
              onClick={() => setSelected(run.id)}
              style={{
                width: "100%",
                justifyContent: "space-between",
                marginBottom: ".55rem",
              }}
            >
              <span>{run.created_at.slice(0, 10)}</span>
              <span>
                {run.status} · {run.progress}%
              </span>
            </button>
          ))}
        </section>
      </div>
      {selected && (
        <section style={{ marginTop: "1rem" }}>
          <QueryState loading={detail.isLoading} error={detail.error} />
          {detail.data && !result && (
            <div className="card loading-state">
              <div>
                <h2>{detail.data.status}</h2>
                <p>{detail.data.progress}% complete</p>
                {detail.data.error_summary && (
                  <p className="negative">{detail.data.error_summary}</p>
                )}
              </div>
            </div>
          )}
          {result && (
            <>
              <div className="metric-grid">
                <Metric
                  label="Total return"
                  value={
                    result.metrics.total_return == null
                      ? "—"
                      : `${(result.metrics.total_return * 100).toFixed(1)}%`
                  }
                />
                <Metric
                  label="CAGR"
                  value={
                    result.metrics.cagr == null
                      ? "—"
                      : `${(result.metrics.cagr * 100).toFixed(1)}%`
                  }
                />
                <Metric
                  label="Max drawdown"
                  value={
                    result.metrics.max_drawdown == null
                      ? "—"
                      : `${(result.metrics.max_drawdown * 100).toFixed(1)}%`
                  }
                />
                <Metric
                  label="Sharpe"
                  value={result.metrics.sharpe?.toFixed(2) ?? "—"}
                />
              </div>
              <div className="content-grid">
                <article className="card">
                  <div className="card-head">
                    <h2>Equity curve</h2>
                    <span className="status-badge">
                      Coverage {(result.coverage * 100).toFixed(0)}%
                    </span>
                  </div>
                  <Sparkline
                    values={result.series.map((point) => point.strategy_value)}
                    label="Strategy portfolio value over the selected walk-forward period"
                  />
                </article>
                <aside className="card">
                  <div className="card-head">
                    <h2>Assumptions</h2>
                  </div>
                  <dl>
                    {Object.entries(result.assumptions).map(([key, value]) => (
                      <div
                        key={key}
                        style={{
                          borderTop: "1px solid var(--line)",
                          padding: ".7rem 0",
                        }}
                      >
                        <dt className="metric-label">
                          {key.replaceAll("_", " ")}
                        </dt>
                        <dd style={{ margin: 0 }}>{value}</dd>
                      </div>
                    ))}
                  </dl>
                  {result.warnings.map((warning) => (
                    <p className="muted" key={warning}>
                      {warning}
                    </p>
                  ))}
                </aside>
              </div>
            </>
          )}
        </section>
      )}
    </>
  );
}
