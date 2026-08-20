"use client";

import Link from "next/link";

export function PageHead({
  eyebrow,
  title,
  copy,
  action,
}: {
  eyebrow: string;
  title: string;
  copy: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="page-head">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p className="muted" style={{ marginBottom: 0 }}>
          {copy}
        </p>
      </div>
      {action}
    </header>
  );
}

export function QueryState({
  loading,
  error,
  empty,
  onRetry,
}: {
  loading: boolean;
  error?: Error | null;
  empty?: boolean;
  onRetry?: () => void;
}) {
  if (loading)
    return (
      <div className="card loading-state" aria-live="polite">
        <div style={{ width: "min(420px, 90%)" }}>
          <div className="skeleton" />
          <div
            className="skeleton"
            style={{ marginTop: ".8rem", width: "72%" }}
          />
          <p className="muted">Loading current research…</p>
        </div>
      </div>
    );
  if (error)
    return (
      <div className="card error-state">
        <div>
          <h2>Research unavailable</h2>
          <p>{error.message}</p>
          {onRetry && (
            <button className="button secondary" onClick={onRetry}>
              Retry
            </button>
          )}
          <p>
            <Link href="/data-health">Inspect data health</Link>
          </p>
        </div>
      </div>
    );
  if (empty)
    return (
      <div className="card empty-state">
        <div>
          <h2>Nothing here yet</h2>
          <p className="muted">
            The next action on this page will create the first record.
          </p>
        </div>
      </div>
    );
  return null;
}

export function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: React.ReactNode;
  detail?: string;
}) {
  return (
    <div className="metric-card card">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
      {detail && (
        <p
          className="muted"
          style={{ margin: ".3rem 0 0", fontSize: ".78rem" }}
        >
          {detail}
        </p>
      )}
    </div>
  );
}
