import Footer from "@/components/Footer";

export const metadata = { title: "Privacy" };
export default function Privacy() {
  return (
    <>
      <main className="article">
        <span className="eyebrow">Privacy policy</span>
        <h1>Collect less. Explain what remains.</h1>
        <p>
          EquityLens stores account identity, security sessions, onboarding
          state, watchlists, simulated research decisions, saved backtest
          configurations, email preferences, referrals, and feedback required to
          operate the product.
        </p>
        <h2>Analytics</h2>
        <p>
          Product events use opaque internal IDs and bounded campaign
          attributes. Email addresses, tokens, portfolio notes, and feedback
          text are never analytics properties. Demo users, administrators in
          test mode, health checks, and obvious automation are excluded from
          production product metrics.
        </p>
        <h2>Email</h2>
        <p>
          Security messages support account verification and password reset.
          Weekly watchlist messages require explicit opt-in and include
          immediate one-click unsubscribe.
        </p>
        <h2>Your controls</h2>
        <p>
          Settings exposes analytics and lifecycle-email preferences. You may
          export your product data or request deletion. Deletion revokes
          sessions and scheduled email immediately, then enters a documented
          reversible grace period before deletion or irreversible anonymization.
        </p>
        <h2>Contact</h2>
        <p>
          The deployment owner must configure a real privacy contact and
          physical sender information before launch. No placeholder contact is
          represented here as monitored.
        </p>
      </main>
      <Footer />
    </>
  );
}
