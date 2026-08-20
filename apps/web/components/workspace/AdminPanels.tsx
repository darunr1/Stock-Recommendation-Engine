"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Metric, PageHead, QueryState } from "./Shared";

type Kind = "jobs" | "metrics" | "feedback";
type Health = {
  runs: {
    id: string;
    job_type: string;
    status: string;
    started_at: string;
    written_count: number;
  }[];
};
type Metrics = {
  registered: number;
  verified: number;
  activated: number;
  daily_active: number;
  weekly_active: number;
  referral_conversions: number;
  feedback: number;
  exclusions: string;
  note: string;
};
type Feedback = {
  items: {
    id: string;
    category: string;
    rating: number | null;
    message: string;
    symbol?: string;
    data_version?: string;
    status: string;
    admin_note: string;
    created_at: string;
  }[];
};

export default function AdminPanels({ kind }: { kind: Kind }) {
  const client = useQueryClient();
  const path =
    kind === "jobs"
      ? "/admin/jobs"
      : kind === "metrics"
        ? "/admin/product-metrics"
        : "/admin/feedback";
  const query = useQuery({
    queryKey: ["admin", kind],
    queryFn: () => api<Health | Metrics | Feedback>(path),
  });
  const trigger = useMutation({
    mutationFn: (job: string) => api(`/admin/jobs/${job}`, { method: "POST" }),
    onSuccess: () =>
      void client.invalidateQueries({ queryKey: ["admin", "jobs"] }),
  });
  async function resolve(id: string) {
    await api(`/admin/feedback/${id}`, {
      method: "PATCH",
      body: JSON.stringify({
        status: "resolved",
        admin_note: "Reviewed in the administrator queue.",
      }),
    });
    void client.invalidateQueries({ queryKey: ["admin", "feedback"] });
  }
  if (kind === "jobs") {
    const data = query.data as Health | undefined;
    return (
      <>
        <PageHead
          eyebrow="Operations"
          title="Job controls"
          copy="Manual triggers are allowlisted, locked against duplicates, and audited."
          action={
            <div className="inline-actions">
              {[
                "price_sync",
                "fundamentals_sync",
                "scoring",
                "weekly_digest",
              ].map((job) => (
                <button
                  key={job}
                  className="button secondary"
                  disabled={trigger.isPending}
                  onClick={() => trigger.mutate(job)}
                >
                  {job.replace("_", " ")}
                </button>
              ))}
            </div>
          }
        />
        <QueryState loading={query.isLoading} error={query.error} />
        <section className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Started</th>
                  <th>Job</th>
                  <th>Status</th>
                  <th>Records</th>
                </tr>
              </thead>
              <tbody>
                {data?.runs.map((run) => (
                  <tr key={run.id}>
                    <td>{run.started_at.slice(0, 19)}</td>
                    <td>{run.job_type}</td>
                    <td>{run.status}</td>
                    <td>{run.written_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </>
    );
  }
  if (kind === "metrics") {
    const data = query.data as Metrics | undefined;
    return (
      <>
        <PageHead
          eyebrow="Privacy-conscious analytics"
          title="Product metrics"
          copy="Real counts only. Demo users, administrators, tests, and health checks stay excluded."
        />
        <QueryState loading={query.isLoading} error={query.error} />
        {data && (
          <>
            <div className="metric-grid">
              <Metric label="Registered" value={data.registered} />
              <Metric label="Verified" value={data.verified} />
              <Metric label="Activated" value={data.activated} />
              <Metric
                label="DAU / WAU"
                value={`${data.daily_active} / ${data.weekly_active}`}
              />
            </div>
            <div className="metric-grid">
              <Metric label="Referrals" value={data.referral_conversions} />
              <Metric label="Feedback" value={data.feedback} />
            </div>
            <div className="disclosure">
              <strong>Exclusions:</strong> {data.exclusions}. {data.note}
            </div>
          </>
        )}
      </>
    );
  }
  const data = query.data as Feedback | undefined;
  return (
    <>
      <PageHead
        eyebrow="User evidence"
        title="Feedback queue"
        copy="Review product and data-quality reports without exposing unrelated account data."
      />
      <QueryState
        loading={query.isLoading}
        error={query.error}
        empty={data?.items.length === 0}
      />
      {data?.items.map((item) => (
        <article
          className="card"
          key={item.id}
          style={{ marginBottom: ".75rem" }}
        >
          <div className="card-head">
            <div>
              <span className="status-badge">{item.category}</span>{" "}
              {item.symbol && (
                <span className="status-badge warning">
                  {item.symbol} · {item.data_version}
                </span>
              )}
              <h2 style={{ marginTop: ".8rem" }}>{item.message}</h2>
            </div>
            <span className="status-badge">{item.status}</span>
          </div>
          <p className="muted">
            Submitted {item.created_at.slice(0, 19)} · Rating{" "}
            {item.rating ?? "not provided"}
          </p>
          {item.status !== "resolved" && (
            <button className="button" onClick={() => void resolve(item.id)}>
              Mark resolved
            </button>
          )}
        </article>
      ))}
    </>
  );
}
