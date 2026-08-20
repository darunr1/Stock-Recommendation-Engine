"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useMemo } from "react";
import { ScoreBadge } from "@/components/ResearchUI";
import { api } from "@/lib/api";
import type { Recommendation } from "@/lib/types";
import { PageHead, QueryState } from "./Shared";

type Results = {
  items: Recommendation[];
  page: number;
  page_size: number;
  total: number;
  as_of_date: string;
};

export default function Screener() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const queryString = searchParams.toString();
  const results = useQuery({
    queryKey: ["screener", queryString],
    queryFn: () => api<Results>(`/recommendations?${queryString}`),
  });
  const values = useMemo(
    () => ({
      search: searchParams.get("search") ?? "",
      sector: searchParams.get("sector") ?? "",
      minimum_score: searchParams.get("minimum_score") ?? "0",
      minimum_confidence: searchParams.get("minimum_confidence") ?? "65",
      sort: searchParams.get("sort") ?? "score",
      direction: searchParams.get("direction") ?? "desc",
    }),
    [searchParams],
  );
  function update(name: string, value: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (value) params.set(name, value);
    else params.delete(name);
    params.delete("page");
    router.replace(`${pathname}?${params}`);
  }
  return (
    <>
      <PageHead
        eyebrow="Cross-sectional explorer"
        title="Stock screener"
        copy="Every filter and sort lives in the URL, ready to refresh or share."
      />
      <section className="filter-bar" aria-label="Screener filters">
        <label>
          Search
          <input
            value={values.search}
            onChange={(event) => update("search", event.target.value)}
            placeholder="Symbol or company"
          />
        </label>
        <label>
          Sector
          <select
            value={values.sector}
            onChange={(event) => update("sector", event.target.value)}
          >
            <option value="">All sectors</option>
            <option>Technology</option>
            <option>Financials</option>
            <option>Health Care</option>
            <option>Consumer Staples</option>
            <option>Communication Services</option>
            <option>Energy</option>
          </select>
        </label>
        <label>
          Minimum score
          <input
            type="number"
            min="0"
            max="100"
            value={values.minimum_score}
            onChange={(event) => update("minimum_score", event.target.value)}
          />
        </label>
        <label>
          Minimum confidence
          <input
            type="number"
            min="0"
            max="100"
            value={values.minimum_confidence}
            onChange={(event) =>
              update("minimum_confidence", event.target.value)
            }
          />
        </label>
      </section>
      <div className="inline-actions" style={{ marginBottom: "1rem" }}>
        <label style={{ display: "flex", alignItems: "center" }}>
          Sort
          <select
            value={values.sort}
            onChange={(event) => update("sort", event.target.value)}
          >
            <option value="score">Composite</option>
            <option value="confidence">Confidence</option>
            <option value="momentum">Momentum</option>
            <option value="quality">Quality</option>
            <option value="value">Value</option>
            <option value="risk">Risk</option>
            <option value="symbol">Symbol</option>
          </select>
        </label>
        <button
          className="button secondary"
          onClick={() =>
            update("direction", values.direction === "desc" ? "asc" : "desc")
          }
        >
          {values.direction === "desc" ? "High to low" : "Low to high"}
        </button>
      </div>
      <QueryState
        loading={results.isLoading}
        error={results.error}
        empty={results.data?.items.length === 0}
        onRetry={() => void results.refetch()}
      />
      {results.data && results.data.items.length > 0 && (
        <section className="card">
          <div className="card-head">
            <h2>{results.data.total} matching stocks</h2>
            <span className="status-badge">
              As of {results.data.as_of_date}
            </span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Composite</th>
                  <th>Confidence</th>
                  <th>Momentum</th>
                  <th>Quality</th>
                  <th>Value</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {results.data.items.map((item) => (
                  <tr key={item.symbol}>
                    <td>
                      <Link href={`/stocks/${item.symbol}`}>
                        <strong>{item.symbol}</strong>
                        <span
                          className="muted"
                          style={{ display: "block", fontSize: ".72rem" }}
                        >
                          {item.sector}
                        </span>
                      </Link>
                    </td>
                    <td>
                      <ScoreBadge score={item.score} band={item.band} />
                    </td>
                    <td title={item.confidence_help}>
                      {item.confidence.toFixed(1)}%
                    </td>
                    {["momentum", "quality", "value", "risk"].map((factor) => (
                      <td key={factor}>
                        {item.factor_scores[factor]?.toFixed(1) ?? "—"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </>
  );
}
