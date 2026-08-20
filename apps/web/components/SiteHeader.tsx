import Link from "next/link";
import { ScanSearch } from "lucide-react";

export default function SiteHeader() {
  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <Link className="brand" href="/" aria-label="EquityLens home">
          <span className="brand-mark" aria-hidden="true">
            <ScanSearch size={20} strokeWidth={2.4} />
          </span>
          EquityLens
        </Link>
        <nav className="site-nav" aria-label="Public navigation">
          <Link href="/methodology">Methodology</Link>
          <Link href="/stocks/AAPL">Stock snapshot</Link>
          <Link href="/changelog">Changelog</Link>
        </nav>
        <div className="header-actions">
          <Link className="button secondary" href="/login">
            Sign in
          </Link>
          <Link className="button" href="/register">
            Build a watchlist
          </Link>
        </div>
      </div>
    </header>
  );
}
