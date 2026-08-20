"use client";

import { useQuery } from "@tanstack/react-query";
import { BookmarkPlus, Copy, ExternalLink, Share2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import Disclosure from "./Disclosure";
import { FactorBars, ScoreBadge, Sparkline } from "./ResearchUI";
import { captureBrowserEvent } from "@/components/AnalyticsBeacon";
import { api } from "@/lib/api";
import type { Recommendation } from "@/lib/types";

export default function StockExperience({
  initial,
}: {
  initial: Recommendation;
}) {
  const [shareMessage, setShareMessage] = useState("");
  const [watchMessage, setWatchMessage] = useState("");
  const full = useQuery({
    queryKey: ["full-stock", initial.symbol],
    queryFn: () => api<Recommendation>(`/recommendations/${initial.symbol}`),
    retry: false,
  });
  const data = full.data ?? initial;

  async function share() {
    const url = window.location.href.split("?")[0];
    let mechanism = "clipboard";
    try {
      if (navigator.share) {
        mechanism = "native";
        await navigator.share({
          title: `${data.symbol} research snapshot · EquityLens`,
          url,
        });
        setShareMessage("Shared");
      } else {
        await navigator.clipboard.writeText(url);
        setShareMessage("Link copied");
      }
      await captureBrowserEvent("share_clicked", {
        symbol: data.symbol,
        mechanism,
      });
    } catch {
      setShareMessage("Sharing cancelled");
    }
  }

  async function addWatchlist() {
    try {
      await api("/watchlist/items", {
        method: "POST",
        body: JSON.stringify({ symbol: data.symbol, note: "" }),
      });
      setWatchMessage("Added to watchlist");
    } catch {
      setWatchMessage("Sign in and verify your email to add this stock");
    }
  }

  return (
    <main className="container">
      <section className="stock-hero">
        <div>
          <span className="eyebrow">
            {data.data_mode ?? "Authenticated research"} · as of{" "}
            {data.as_of_date}
          </span>
          <h1 style={{ marginBottom: ".55rem" }}>{data.symbol}</h1>
          <p className="lead">
            {data.company_name} · {data.sector ?? "Sector unavailable"}
          </p>
          <div className="inline-actions">
            <ScoreBadge band={data.band} />
            <span className="status-badge" title={data.confidence_help}>
              {data.confidence.toFixed(0)}% confidence
            </span>
            {data.demo && (
              <span className="status-badge warning">Synthetic demo data</span>
            )}
          </div>
        </div>
        <div>
          <div className="stock-score">{data.score?.toFixed(0) ?? "—"}</div>
          <span className="muted">Composite / 100</span>
        </div>
      </section>
      <div
        className="inline-actions"
        style={{ marginBottom: "1rem", flexWrap: "wrap" }}
      >
        <button className="button" onClick={addWatchlist}>
          <BookmarkPlus size={17} /> Add to watchlist
        </button>
        <button className="button secondary" onClick={share}>
          <Share2 size={17} /> Share snapshot
        </button>
        <Link className="button ghost" href="/methodology">
          <ExternalLink size={16} /> Methodology
        </Link>
        {(shareMessage || watchMessage) && (
          <span className="muted" role="status">
            <Copy size={14} style={{ display: "inline" }} />{" "}
            {shareMessage || watchMessage}
          </span>
        )}
      </div>
      {data.warnings?.length > 0 && (
        <div className="disclosure" style={{ marginBottom: "1rem" }}>
          <strong>Data notes:</strong> {data.warnings.join(" ")}
        </div>
      )}
      <section className="content-grid" style={{ marginBottom: "1rem" }}>
        <article className="card chart-card">
          <div className="card-head">
            <h2>Adjusted price history</h2>
            <span className="status-badge">
              {data.price_date ?? data.as_of_date}
            </span>
          </div>
          {data.history?.length ? (
            <Sparkline
              values={data.history.map((item) => item.close)}
              label={`${data.symbol} limited public adjusted-close history`}
            />
          ) : (
            <div className="empty-state">
              <p>
                Price history is withheld in the configured public display mode.
              </p>
            </div>
          )}
        </article>
        <article className="card">
          <div className="card-head">
            <h2>Factor scorecard</h2>
            <span className="muted">0–100 rank</span>
          </div>
          <FactorBars values={data.factor_scores} />
        </article>
      </section>
      <section className="content-grid" style={{ marginBottom: "1rem" }}>
        <article className="card">
          <div className="card-head">
            <h2>What drives the score</h2>
            <span className="status-badge">Deterministic</span>
          </div>
          <div className="form-grid">
            {data.contributors?.map((item) => (
              <div
                key={item.feature}
                style={{
                  borderTop: "1px solid var(--line)",
                  paddingTop: ".8rem",
                }}
              >
                <strong
                  className={item.contribution >= 0 ? "positive" : "negative"}
                >
                  {item.contribution >= 0 ? "↑ Positive" : "↓ Negative"} ·{" "}
                  {item.label}
                </strong>
                <p className="muted" style={{ margin: ".35rem 0 0" }}>
                  {item.explanation}
                </p>
              </div>
            ))}
          </div>
        </article>
        <article className="card">
          <div className="card-head">
            <h2>Data confidence</h2>
          </div>
          <div className="metric-value">{data.confidence.toFixed(1)}%</div>
          <p className="muted">{data.confidence_help}</p>
          {full.isError && (
            <p className="muted">
              Public view shown. Sign in for raw metrics, risks, and full
              history.
            </p>
          )}
          {full.data?.what_could_change && (
            <>
              <h3>What could change this score?</h3>
              <ul>
                {full.data.what_could_change.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}
          {!full.data && (
            <Link className="button" href="/register">
              See full analysis
            </Link>
          )}
        </article>
      </section>
      <Disclosure />
      <div style={{ height: "5rem" }} />
    </main>
  );
}
