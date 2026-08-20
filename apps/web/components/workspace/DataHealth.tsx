"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Metric, PageHead, QueryState } from "./Shared";
type Health = {
  provider_mode: string;
  status: string;
  stale_symbols: number;
  runs: {
    id: string;
    job_type: string;
    provider: string;
    status: string;
    requested_count: number;
    written_count: number;
    coverage: number;
    started_at: string;
    warnings: string[];
    error_summary?: string;
  }[];
};
export default function DataHealth() {
  const query = useQuery({
    queryKey: ["data-health"],
    queryFn: () => api<Health>("/data-health"),
    refetchInterval: 15000,
  });
  return (
    <>
      <PageHead
        eyebrow="Provider observability"
        title="Data health"
        copy="The last valid research stays available when a provider fails; stale state remains visible."
      />
      <QueryState
        loading={query.isLoading}
        error={query.error}
        onRetry={() => void query.refetch()}
      />
      {query.data && (
        <>
          <div className="metric-grid">
            <Metric label="Status" value={query.data.status} />
            <Metric label="Provider mode" value={query.data.provider_mode} />
            <Metric label="Stale symbols" value={query.data.stale_symbols} />
            <Metric label="Sync records" value={query.data.runs.length} />
          </div>
          <section className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Started</th>
                    <th>Job</th>
                    <th>Status</th>
                    <th>Provider</th>
                    <th>Written</th>
                    <th>Coverage</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.runs.map((run) => (
                    <tr key={run.id}>
                      <td>{run.started_at.slice(0, 19).replace("T", " ")}</td>
                      <td>{run.job_type}</td>
                      <td>
                        <span
                          className={`status-badge ${run.status !== "completed" ? "warning" : ""}`}
                        >
                          {run.status}
                        </span>
                      </td>
                      <td>{run.provider}</td>
                      <td>{run.written_count}</td>
                      <td>{run.coverage.toFixed(0)}%</td>
                      <td>
                        {run.error_summary ?? run.warnings.join(" ") ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  );
}
