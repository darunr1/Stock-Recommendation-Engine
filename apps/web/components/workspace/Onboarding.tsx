"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Disclosure from "@/components/Disclosure";
import { api } from "@/lib/api";
import { PageHead } from "./Shared";
const choices = [
  "AAPL",
  "MSFT",
  "NVDA",
  "AMZN",
  "GOOGL",
  "META",
  "JPM",
  "KO",
  "XOM",
];
export default function Onboarding() {
  const router = useRouter();
  const [selected, setSelected] = useState<string[]>([]);
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  async function finish(skipped = false) {
    try {
      await api("/onboarding", {
        method: "PUT",
        body: JSON.stringify({
          symbols: selected,
          interests: ["factor research", "backtesting"],
          skipped,
        }),
      });
      router.push("/dashboard");
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not finish onboarding",
      );
    }
  }
  return (
    <>
      <PageHead
        eyebrow={`Getting started · ${step}/2`}
        title={
          step === 1
            ? "Score and confidence answer different questions."
            : "Choose three stocks to follow."
        }
        copy={
          step === 1
            ? "The score is a relative factor rank. Confidence only describes completeness, freshness, and continuity."
            : "This makes the dashboard useful immediately; you can remove them any time."
        }
      />
      {step === 1 ? (
        <section className="card" style={{ maxWidth: 760 }}>
          <div className="grid-3">
            <div>
              <span className="metric-value">82</span>
              <h3>Composite score</h3>
              <p className="muted">
                A cross-sectional rank produced from five factor families.
              </p>
            </div>
            <div>
              <span className="metric-value">91%</span>
              <h3>Confidence</h3>
              <p className="muted">
                Coverage and freshness, never prediction accuracy.
              </p>
            </div>
            <div>
              <span className="metric-value">v1</span>
              <h3>Version</h3>
              <p className="muted">
                Old results remain tied to the rules that produced them.
              </p>
            </div>
          </div>
          <Disclosure />
          <button
            className="button"
            onClick={() => setStep(2)}
            style={{ marginTop: "1rem" }}
          >
            Choose my watchlist
          </button>
        </section>
      ) : (
        <section className="card" style={{ maxWidth: 760 }}>
          <div className="grid-3">
            {choices.map((symbol) => (
              <button
                key={symbol}
                className={
                  selected.includes(symbol) ? "button" : "button secondary"
                }
                onClick={() =>
                  setSelected((current) =>
                    current.includes(symbol)
                      ? current.filter((item) => item !== symbol)
                      : [...current, symbol],
                  )
                }
              >
                {symbol}
              </button>
            ))}
          </div>
          <p className="muted">{selected.length}/3 minimum selected</p>
          {error && <p className="form-message error">{error}</p>}
          <div className="inline-actions">
            <button
              className="button"
              disabled={selected.length < 3}
              onClick={() => void finish(false)}
            >
              Finish onboarding
            </button>
            <button className="button ghost" onClick={() => void finish(true)}>
              Skip for now
            </button>
          </div>
        </section>
      )}
    </>
  );
}
