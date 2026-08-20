# EquityLens evidence snapshot

Generated from the local implementation on 2026-08-19. This file records measured repository evidence only; it does not claim a public deployment or real user activity.

## Running product evidence

- Dashboard screenshot: [`docs/screenshots/dashboard.png`](docs/screenshots/dashboard.png), captured by the demo-login Playwright flow.
- Anonymous browser flow: landing page to complete methodology.
- Authenticated browser flow: one-click demo login to a populated market overview, with the research disclosure visible.
- API smoke: liveness, readiness, public market preview, and public AAPL snapshot returned HTTP 200.

## Automated evidence

| Check | Result |
|---|---|
| Web/API lint | Passed |
| TypeScript + Python type analysis | Passed, zero reported errors |
| API tests | 11 passed |
| Web unit/integration tests | 3 passed |
| Playwright end-to-end tests | 2 passed |
| Next.js production build + Python compile | Passed |
| Alembic migration from empty SQLite schema | Revision `20260819_0001`; 18 tables |
| Deterministic demo seed | 35 symbols including SPY, 46,404 daily-price rows, 34 latest candidate recommendations |

## Truthful limits

- Docker is not installed on this workstation, so the Compose topology was statically reviewed but not executed here.
- Vercel, Railway, Resend DNS, PostHog, Sentry project settings, uptime monitoring, backups/PITR, and a restore drill are external account-bound launch gates.
- Live Alpaca/SEC ingestion requires owner credentials and identifying SEC contact information. Public price display remains controlled by the `demo|restricted|licensed` runtime gate.
- There is no live URL and no fabricated usage, conversion, performance, reliability, or cost claim.
