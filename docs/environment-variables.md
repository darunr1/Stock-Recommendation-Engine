# Environment variables

| Variable | Purpose | Sensitive | Environments | Source |
|---|---|---:|---|---|
| `APP_ENV` | `local`, `test`, `preview`, or `production` behavior | No | All | Deployment config |
| `APP_BASE_URL` | Canonical HTTPS web origin and email-link base | No | All | Vercel/domain |
| `API_BASE_URL` | API origin for smoke tooling | No | All | Railway/local |
| `API_UPSTREAM_URL` | Server-only same-origin rewrite target | No | Web | Railway API URL |
| `NEXT_PUBLIC_APP_BASE_URL` | Browser-visible canonical web origin | No | Web | Vercel/domain |
| `DATABASE_URL` | Async SQLAlchemy PostgreSQL/SQLite connection | Yes | API/jobs | Railway PostgreSQL |
| `REDIS_URL` | Celery broker/result and cache endpoint | Yes | API/jobs | Railway Redis |
| `REQUIRE_REDIS` | Make API readiness fail when Redis is unavailable | No | Preview/production | Deployment config |
| `DATA_MODE` | `demo` or `live` provider selection | No | API/jobs | Owner decision |
| `PUBLIC_MARKET_DATA_MODE` | `demo`, `restricted`, or `licensed` public shape | No | API/web | Licensing review |
| `PUBLIC_MARKET_DATA_LICENSE_ACKNOWLEDGED` | Owner attestation gate for licensed mode | No | Production | Owner review |
| `ALPACA_API_KEY`, `ALPACA_API_SECRET` | Server-only live market-data authentication | Yes | Live API/jobs | Alpaca dashboard |
| `SEC_USER_AGENT` | Identifying organization/contact for SEC requests | No | Live API/jobs | Owner contact |
| `SECRET_KEY`, `CSRF_SECRET` | Token signing and CSRF entropy | Yes | API | Password manager/host generator |
| `CORS_ORIGINS` | Explicit comma-separated web origins | No | API | Canonical URLs |
| `EMAIL_PROVIDER` | `capture` locally; `resend` after production gate | No | API/jobs | Owner decision |
| `EMAIL_CAPTURE_DIR` | Local safe email-capture directory | No | Local/test | Filesystem |
| `EMAIL_FROM` | Verified From identity | No | Production | Resend domain |
| `RESEND_API_KEY` | Transactional email API credential | Yes | Production | Resend dashboard |
| `SENDER_DOMAIN_VERIFIED` | Blocks Resend use before DNS verification | No | Production | Owner verification |
| `SENDER_POSTAL_ADDRESS` | Configurable lifecycle-email legal footer | Sensitive | Production | Owner/legal review |
| `POSTHOG_API_KEY`, `NEXT_PUBLIC_POSTHOG_KEY` | Server/browser analytics adapters | Yes/No | Production | PostHog project |
| `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN` | PII-filtered error reporting | Yes/No | Preview/production | Sentry project |
| `RELEASE_SHA` | Immutable source revision in logs/errors | No | Preview/production | CI provider |
| `DEMO_TASKS_EAGER` | Execute selected long jobs inline for tests/demo | No | Local/test | Config |

Production startup validates secrets, email verification state, live provider credentials, and the market-data licensing acknowledgement. Never paste secrets into source, issues, screenshots, logs, or chat.
