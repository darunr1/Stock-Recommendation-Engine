# EquityLens implementation plan

Status legend: `[x]` implemented and locally verified, `[!]` external/account-bound gate.

## Phase 0 — repository orientation

- [x] Inspect the source PRD and establish repository instructions, commands, ADR, architecture, and requirement map.

## Phase 1 — monorepo and local infrastructure

- [x] Add strict Next.js and FastAPI applications, pnpm workspace tooling, PostgreSQL/Redis/API/worker/scheduler/web Compose services, environment validation, health endpoints, CI, formatting, linting, and types.

## Phase 2 — persistence and authentication

- [x] Add versioned SQLAlchemy/Alembic persistence for users, sessions, tokens, research, jobs, user resources, analytics, email, and audit records.
- [x] Implement Argon2id auth, rotating refresh cookies, CSRF, roles, rate limits, verification/reset, captured/Resend email, export, and reversible deletion.

## Phase 3 — providers and ingestion

- [x] Add a 34-candidate versioned universe plus SPY, deterministic five-year demo data, vendor-neutral provider contracts, Alpaca/SEC adapters, validation, caching, sync records, and schedules.

## Phase 4 — recommendation engine

- [x] Implement deterministic momentum/trend/quality/value/risk formulas, eligibility, winsorized cross-sectional ranks, missing-data renormalization, confidence, bands, contributors, warnings, SPY context, canonical snapshots, and focused tests.

## Phase 5 — research product

- [x] Implement typed public/authenticated/admin APIs and landing, methodology, legal, auth, onboarding, dashboard, screener, stock, watchlist, settings, deletion recovery, data-health, and admin routes.
- [x] Add metadata/share images, sitemap/robots, URL filters, chart alternatives, responsive design, and honest loading/empty/stale/error states.

## Phase 6 — backtesting

- [x] Implement immutable runs, lifecycle polling, monthly next-session execution, point-in-time inputs, costs/slippage, strategy/benchmark/drawdown series, metrics, assumptions, coverage, UI, and future-information/accounting tests.

## Phase 7 — paper portfolio

- [x] Implement transactional simulated buys/sells/resets, cash, positions, basis, realized/unrealized P&L, performance history, validation, API, and UI.

## Phase 8 — growth, email, analytics, and feedback

- [x] Add privacy-safe allow-listed analytics, attribution/referrals, server-verified activation, native/copy sharing, email preferences/digest/unsubscribe, safe delivery metadata, feedback/data issues, admin triage, and aggregate metrics excluding demo/admin/test traffic.

## Phase 9 — hardening and observability

- [x] Add job locks/audits, singleton scheduler definitions, request IDs, secure headers/CSP/CORS, consistent redacted errors, dependency-aware readiness, PostHog server mirroring, and Sentry API capture.

## Phase 10 — deployment readiness

- [x] Add Vercel/Railway manifests, same-origin proxy, advisory-locked migrations, environment reference, licensing gate, rollback/backup/runbook, smoke workflows, launch plan, cost guardrails, and checklists.
- [!] Owner connects GitHub/Vercel/Railway, provisions services, verifies Resend DNS, configures production analytics/error monitoring, confirms data-display rights, runs a backup restore drill, and supplies the final HTTPS URL.

## Phase 11 — verification and evidence

- [x] Pass formatting, lint, TypeScript/Python types, 11 API tests, 3 web tests, 2 Playwright flows, production build, empty-schema migration, API smoke, and screenshot capture.
- [!] Run the production-shaped Compose smoke on a Docker host; Docker is not installed on this workstation.

## Deliberate decisions

- Local/test demo mode uses SQLite and deterministic synthetic data; Compose/production use PostgreSQL and Redis.
- Celery eager execution is allowed for test/demo interactions; deployed topology uses separate worker and exactly one Beat scheduler.
- Public data display is a runtime `demo|restricted|licensed` choice. Licensed mode requires explicit owner acknowledgement.
- Live-demo links and usage/reliability metrics stay absent until an owner-authorized deployment passes post-deploy checks.
