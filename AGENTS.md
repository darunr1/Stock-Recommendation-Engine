# EquityLens repository guide

## Scope

This repository implements the EquityLens public-beta PRD. Treat `IMPLEMENTATION_PLAN.md` as the delivery map and keep all financial language educational and non-personalized. Never add live brokerage execution.

## Architecture

- `apps/web`: Next.js App Router frontend. Browser calls use same-origin `/api/v1/*`.
- `apps/api`: FastAPI service. Route handlers stay thin; business rules live in service/domain modules.
- `config/universe.csv`: versioned universe membership. SPY is a benchmark, never a ranked candidate.
- `fixtures/demo`: deterministic, credential-free demo inputs.
- Analytic functions always accept an explicit `as_of` date and versioned configuration.
- Provider payloads and SDK types never cross provider adapters.
- Scores, backtests, and simulated trades are deterministic. Never use an LLM to create a score.
- Production public market data defaults to `restricted`; `licensed` requires an explicit acknowledgement flag.
- Do not claim deployment, usage, performance, or reliability metrics that were not measured.

## Commands

- `pnpm install`: install JavaScript workspace dependencies.
- `pnpm dev`: start web and API development processes.
- `pnpm format`: format supported files.
- `pnpm lint`: lint web and API.
- `pnpm typecheck`: TypeScript and Python type checks.
- `pnpm test`: run unit and integration tests.
- `pnpm build`: create production builds.
- `pnpm seed`: seed deterministic demo data.
- `pnpm smoke`: run local API smoke checks.
- `docker compose up --build`: run the full containerized demo stack when Docker is installed.

Equivalent Make targets are provided for Unix/CI environments.

## Verification

Before handing off a change, run the narrowest relevant tests, then `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build` for broad changes. For deployment work also run `pnpm deploy-check`. Docker smoke verification requires a Docker host and must be reported as unavailable—not passed—when Docker is absent.

## Coding rules

- Python: 3.12+, Ruff formatting/lint, strict-enough Pyright, Pydantic schemas at API boundaries.
- TypeScript: strict mode, accessible semantic UI, no `any` in product code without a documented boundary.
- Persist UTC timestamps; use ISO U.S. market-session dates for trading dates.
- State-changing cookie-auth routes require CSRF validation outside demo-test shortcuts.
- Error responses use `{ "error": { "code", "message", "details", "request_id" } }` and never expose internals.
- Preserve user changes and update `IMPLEMENTATION_PLAN.md` plus `COMPLETION_REPORT.md` when scope changes.
