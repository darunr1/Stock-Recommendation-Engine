"use client";

import { useMemo } from "react";

export function ScoreBadge({
  band,
  score,
}: {
  band: string;
  score?: number | null;
}) {
  return (
    <span className="score-badge">
      <span aria-hidden="true">●</span>{" "}
      {score == null ? band : `${score.toFixed(1)} · ${band}`}
    </span>
  );
}

export function FactorBars({
  values,
}: {
  values: Record<string, number | null>;
}) {
  return (
    <div
      className="factor-list"
      role="list"
      aria-label="Factor scores out of 100"
    >
      {Object.entries(values).map(([name, value]) => (
        <div key={name} role="listitem">
          <div className="factor-row-head">
            <span style={{ textTransform: "capitalize" }}>{name}</span>
            <strong>{value == null ? "Missing" : value.toFixed(1)}</strong>
          </div>
          <div className="factor-track" aria-hidden="true">
            <div
              className="factor-fill"
              style={{ width: `${Math.max(0, value ?? 0)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Sparkline({
  values,
  label,
}: {
  values: number[];
  label: string;
}) {
  const points = useMemo(() => {
    if (!values.length) return "";
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || 1;
    return values
      .map((value, index) => {
        const x = (index / Math.max(1, values.length - 1)) * 100;
        const y = 40 - ((value - min) / span) * 36;
        return `${x},${y}`;
      })
      .join(" ");
  }, [values]);
  return (
    <figure style={{ margin: 0 }}>
      <svg
        viewBox="0 0 100 42"
        role="img"
        aria-label={label}
        style={{ width: "100%", height: 220 }}
      >
        <polyline
          fill="none"
          stroke="var(--forest-2)"
          strokeWidth="1.7"
          vectorEffect="non-scaling-stroke"
          points={points}
        />
      </svg>
      <figcaption className="muted" style={{ fontSize: ".78rem" }}>
        {label}. First {values[0]?.toFixed(2) ?? "—"}; last{" "}
        {values.at(-1)?.toFixed(2) ?? "—"}.
      </figcaption>
    </figure>
  );
}
