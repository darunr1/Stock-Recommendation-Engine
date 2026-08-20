import Footer from "@/components/Footer";

export const metadata = { title: "Changelog" };
export default function Changelog() {
  return (
    <>
      <main className="article">
        <span className="eyebrow">Product changelog</span>
        <h1>What changed, and why.</h1>
        <div className="card">
          <span className="status-badge">August 19, 2026</span>
          <h2>Public beta foundation</h2>
          <p>
            Added transparent research snapshots, credential-free deterministic
            demo data, secure account flows, onboarding, server-verified
            activation, screener and stock research views, watchlists,
            point-in-time price-factor backtests, a simulated portfolio,
            referrals, email preferences, feedback, data health, and operational
            launch gates.
          </p>
        </div>
      </main>
      <Footer />
    </>
  );
}
