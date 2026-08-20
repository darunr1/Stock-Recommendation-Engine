import Link from "next/link";
import {
  ArrowRight,
  DatabaseZap,
  Eye,
  FlaskConical,
  ShieldCheck,
} from "lucide-react";
import Disclosure from "@/components/Disclosure";
import Footer from "@/components/Footer";
import { serverApi } from "@/lib/api";

type Preview = {
  as_of_date: string;
  data_mode: string;
  items: {
    symbol: string;
    company_name: string;
    score: number;
    band: string;
    confidence: number;
  }[];
};

export const dynamic = "force-dynamic";

export default async function Home() {
  const preview = await serverApi<Preview>("/public/market-preview");
  return (
    <>
      <main>
        <section className="container hero">
          <div className="hero-copy">
            <span className="eyebrow">Explainable equity research</span>
            <h1>See the signal. Inspect the reason.</h1>
            <p className="lead">
              EquityLens ranks a focused U.S. stock universe with transparent
              momentum, trend, quality, value, and risk factors—then shows every
              input behind the score.
            </p>
            <div className="inline-actions">
              <Link className="button" href="/register">
                Build my watchlist <ArrowRight size={17} />
              </Link>
              <Link className="button secondary" href="/stocks/AAPL">
                Inspect a public snapshot
              </Link>
            </div>
            <p className="hero-note">
              No brokerage connection. No opaque prediction. Demo data works
              without API keys.
            </p>
          </div>
          <aside className="terminal-card" aria-label="Latest demo candidates">
            <div className="terminal-head">
              <span>Research shortlist</span>
              <span>
                {preview ? `As of ${preview.as_of_date}` : "API offline"}
              </span>
            </div>
            <div className="terminal-body">
              {(preview?.items ?? []).map((item) => (
                <Link
                  href={`/stocks/${item.symbol}`}
                  className="candidate-row"
                  key={item.symbol}
                >
                  <span className="candidate-symbol">{item.symbol}</span>
                  <span>
                    <span className="candidate-company">
                      {item.company_name}
                    </span>
                    <span
                      style={{
                        display: "block",
                        color: "#c9d8d0",
                        fontSize: ".76rem",
                        marginTop: ".22rem",
                      }}
                    >
                      {item.band} · {item.confidence.toFixed(0)}% confidence
                    </span>
                  </span>
                  <span className="candidate-score">
                    {item.score.toFixed(0)}
                  </span>
                </Link>
              ))}
              {!preview && (
                <div
                  className="empty-state"
                  style={{ minHeight: 320, color: "#a8bcb3" }}
                >
                  <p>
                    Start the API to load the deterministic research preview.
                  </p>
                </div>
              )}
            </div>
          </aside>
        </section>
        <section className="proof-strip" aria-label="Product principles">
          <div className="proof-item">
            <span className="proof-number">5</span>
            <span className="muted">transparent factor families</span>
          </div>
          <div className="proof-item">
            <span className="proof-number">100%</span>
            <span className="muted">scores with freshness and coverage</span>
          </div>
          <div className="proof-item">
            <span className="proof-number">0</span>
            <span className="muted">live trades or return promises</span>
          </div>
        </section>
        <section className="container section">
          <div className="section-head">
            <div>
              <span className="eyebrow">Research integrity</span>
              <h2>Built to be questioned.</h2>
            </div>
            <p className="lead">
              A useful rank should survive inspection. Every surface keeps the
              assumptions close.
            </p>
          </div>
          <div className="grid-3">
            <article className="feature-card">
              <div className="feature-icon">
                <Eye size={21} />
              </div>
              <h3>Explain every score</h3>
              <p>
                See raw values, cross-sectional percentiles, effective weights,
                and the strongest positive and negative contributors.
              </p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">
                <FlaskConical size={21} />
              </div>
              <h3>Backtest without peeking</h3>
              <p>
                Signals form on prior-session information and execute on the
                next session with explicit costs, slippage, and coverage
                warnings.
              </p>
            </article>
            <article className="feature-card">
              <div className="feature-icon">
                <DatabaseZap size={21} />
              </div>
              <h3>Know the data state</h3>
              <p>
                Demo, stale, missing, and license-restricted fields stay
                labeled. Provider failure never masquerades as a fresh score.
              </p>
            </article>
          </div>
        </section>
        <section className="container section" style={{ paddingTop: 0 }}>
          <div className="card" style={{ padding: "clamp(1.5rem, 6vw, 4rem)" }}>
            <div className="content-grid">
              <div>
                <span className="eyebrow">Transparent by construction</span>
                <h2>Confidence is data quality—not certainty.</h2>
                <p className="lead">
                  It combines weighted feature coverage, filing and price
                  freshness, and price-history continuity. It never claims the
                  probability that a stock rises.
                </p>
                <Link className="button ghost" href="/methodology">
                  Read the complete methodology <ArrowRight size={16} />
                </Link>
              </div>
              <div>
                <ShieldCheck
                  size={44}
                  aria-hidden="true"
                  style={{ marginBottom: "1rem", color: "var(--forest-2)" }}
                />
                <Disclosure />
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
