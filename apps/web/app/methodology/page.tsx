import Disclosure from "@/components/Disclosure";
import Footer from "@/components/Footer";

const factors = [
  [
    "Momentum · 30%",
    "One-, three-, and six-month adjusted returns, weighted toward the longer window.",
  ],
  [
    "Trend · 15%",
    "Distance from 20-, 50-, and 200-day averages, trend alignment, and balanced RSI.",
  ],
  [
    "Quality · 25%",
    "Margins, return on assets, cash conversion, leverage, and point-in-time revenue growth.",
  ],
  [
    "Value · 15%",
    "Earnings, sales, free-cash-flow, and book yields relative to market capitalization.",
  ],
  [
    "Risk · 15%",
    "Volatility, drawdown, downside deviation, beta stability, and trading liquidity.",
  ],
];

export const metadata = { title: "Methodology" };

export default function Methodology() {
  return (
    <>
      <main className="article">
        <span className="eyebrow">Methodology · equitylens-v1</span>
        <h1>Transparent enough to reproduce.</h1>
        <p className="lead">
          EquityLens produces a daily cross-sectional research rank. The score
          says where a stock sits relative to the eligible universe—not what
          must happen next.
        </p>
        <Disclosure />
        <h2>Eligibility</h2>
        <p>
          A candidate needs active universe membership, at least 252 valid daily
          bars, a $5 minimum close, at least $10 million of twenty-day median
          dollar volume, and no more than two missing expected sessions. SPY is
          context and benchmark only.
        </p>
        <h2>Factor model</h2>
        <div className="form-grid">
          {factors.map(([name, copy]) => (
            <div className="card" key={name}>
              <h3>{name}</h3>
              <p>{copy}</p>
            </div>
          ))}
        </div>
        <h2>Normalization and missing inputs</h2>
        <p>
          Each feature is winsorized at the contemporary 5th and 95th
          percentiles, then ranked from 0 to 100. Lower-is-better measures are
          reversed. Missing values are never filled with zero. A factor must
          retain at least half its configured feature weight; the composite
          needs three factors, including Momentum and Risk.
        </p>
        <h2>Score bands</h2>
        <p>
          80–100 is Strong Candidate, 65–79.99 Candidate, 45–64.99 Watch, and
          below 45 Low Score. Confidence below 65 caps the label at Watch. Stale
          prices produce STALE_DATA and inadequate factor coverage produces
          INSUFFICIENT_DATA.
        </p>
        <h2>Confidence</h2>
        <p>
          Confidence is 70% weighted feature coverage, 20% freshness, and 10%
          price-history continuity. It measures the fitness of the input
          record—not predictive accuracy.
        </p>
        <h2>Walk-forward testing</h2>
        <p>
          Historical signals use the prior completed session and execute no
          earlier than the following market session. Costs and slippage are
          deducted. The demo replay uses deterministic synthetic price factors
          and openly warns when historic filing fixtures are not part of that
          replay.
        </p>
        <h2>Limitations</h2>
        <p>
          A configured universe can introduce survivorship bias. Synthetic demo
          prices are not observed history. Public display rights vary by
          provider and audience, so production starts in restricted mode until
          the owner confirms exact permissions. Factor relationships can break
          down, and no rank is individualized advice.
        </p>
      </main>
      <Footer />
    </>
  );
}
