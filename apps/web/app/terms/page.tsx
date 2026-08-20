import Disclosure from "@/components/Disclosure";
import Footer from "@/components/Footer";

export const metadata = { title: "Terms" };
export default function Terms() {
  return (
    <>
      <main className="article">
        <span className="eyebrow">Terms of use</span>
        <h1>Research tooling, not financial advice.</h1>
        <Disclosure />
        <h2>Acceptable use</h2>
        <p>
          Use EquityLens to study transparent quantitative signals and simulated
          decisions. Do not attempt to evade access controls, extract restricted
          provider data, overload services, or present product outputs as
          guaranteed outcomes.
        </p>
        <h2>Data and models</h2>
        <p>
          Inputs may be delayed, incomplete, synthetic, or subject to display
          restrictions. Scores are reproducible ranks under a documented model
          version, not price targets or individualized recommendations.
        </p>
        <h2>Simulations</h2>
        <p>
          Backtests and paper portfolios simplify execution and can differ
          materially from live conditions. Modeled costs, data coverage,
          universe construction, and other assumptions remain visible with
          results.
        </p>
        <h2>No brokerage service</h2>
        <p>
          V1 never connects to a live trading endpoint, accepts brokerage
          credentials, or executes orders.
        </p>
      </main>
      <Footer />
    </>
  );
}
