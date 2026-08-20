import Link from "next/link";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <span>© 2026 EquityLens · Explainable research, never a promise.</span>
        <span className="inline-actions">
          <Link href="/privacy">Privacy</Link>
          <Link href="/terms">Terms</Link>
          <Link href="/methodology">Methodology</Link>
        </span>
      </div>
    </footer>
  );
}
