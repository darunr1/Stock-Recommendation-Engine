"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Disclosure from "@/components/Disclosure";
import { FactorBars, ScoreBadge } from "@/components/ResearchUI";
import { api } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { Metric, PageHead, QueryState } from "./Shared";

type Summary = {
  as_of_date: string;
  data_health: string;
  data_mode: string;
  top_candidates: Recommendation[];
  band_counts: Record<string, number>;
  market_regime: {
    label: string;
    formula: string;
    as_of: string;
    context_only: boolean;
  };
};

export default function Dashboard() {
  const query = useQuery({
    queryKey: ["market-summary"],
    queryFn: () => api<Summary>("/market/summary"),
  });
  return (
    <>
      <PageHead
        eyebrow="Daily research desk"
        title="Market overview"
        copy="Stored, versioned snapshots—not a rank recalculated in your browser."
        action={
          <Link className="button" href="/screener">
            Open screener
          </Link>
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
              label="Model date"
              value={query.data.as_of_date.slice(5)}
              detail="Latest completed snapshot"
            />
            <Metric
              label="Candidates"
              value={
                (query.data.band_counts.Candidate ?? 0) +
                (query.data.band_counts["Strong Candidate"] ?? 0)
              }
              detail="Before your filters"
            />
            <Metric
              label="Market regime"
              value={query.data.market_regime.label}
              detail="SPY context only"
            />
            <Metric
              label="Data state"
              value={query.data.data_health}
              detail={`${query.data.data_mode} provider mode`}
            />
          </div>
          <div className="content-grid">
            <section className="card">
              <div className="card-head">
                <h2>Top research candidates</h2>
                <span className="status-badge">
                  As of {query.data.as_of_date}
                </span>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Symbol</th>
                      <th>Score</th>
                      <th>Confidence</th>
                      <th>Strongest contributor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.top_candidates.map((item) => (
                      <tr key={item.symbol}>
                        <td>
                          <Link href={`/stocks/${item.symbol}`}>
                            <strong>{item.symbol}</strong>
                            <span
                              className="muted"
                              style={{ display: "block", fontSize: ".75rem" }}
                            >
                              {item.company_name}
                            </span>
                          </Link>
                        </td>
                        <td>
                          <ScoreBadge band={item.band} score={item.score} />
                        </td>
                        <td title={item.confidence_help}>
                          {item.confidence.toFixed(0)}%
                          <span
                            className="muted"
                            style={{ display: "block", fontSize: ".7rem" }}
                          >
                            data quality
                          </span>
                        </td>
                        <td>
                          {item.contributors[0]?.label ?? "No contributor"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
            <aside className="form-grid">
              <section className="card">
                <div className="card-head">
                  <h2>Regime context</h2>
                  <span className="status-badge">Context only</span>
                </div>
                <div className="metric-value">
                  {query.data.market_regime.label}
                </div>
                <p className="muted">{query.data.market_regime.formula}</p>
                <p className="muted">
                  Inputs through {query.data.market_regime.as_of}. The regime
                  never modifies V1 scores.
                </p>
              </section>
              <section className="card">
                <div className="card-head">
                  <h2>Band distribution</h2>
                </div>
                <FactorBars
                  values={Object.fromEntries(
                    Object.entries(query.data.band_counts).map(
                      ([key, value]) => [
                        key,
                        (value /
                          Math.max(1, query.data.top_candidates.length * 3.4)) *
                          100,
                      ],
                    ),
                  )}
                />
              </section>
            </aside>
          </div>
          <div style={{ marginTop: "1rem" }}>
            <Disclosure />
          </div>
        </>
      )}
    </>
  );
}
