# ADR 0001: Demo-first production-shaped monorepo

## Decision

Use a pnpm workspace containing a Next.js web application and a Python FastAPI service. The API uses SQLAlchemy with SQLite for zero-credential local/test execution and PostgreSQL in Compose/production. Redis-backed Celery processes scheduled and long-running work, while tests can execute tasks eagerly. Demo fixtures are deterministic and regenerated from a fixed algorithm.

## Rationale

This preserves the PRD's production topology without making credentials or local infrastructure prerequisites for inspecting the product. Business logic remains provider- and database-vendor-neutral. Stored analytic snapshots prevent page requests from recomputing rankings.

## Consequences

- PostgreSQL-specific migration and locking behavior requires separate integration coverage.
- Docker is the canonical full-stack verification path; host-only development is an additional convenience.
- Account-bound hosting, email DNS, monitoring projects, and market-data licensing remain explicit launch gates.
