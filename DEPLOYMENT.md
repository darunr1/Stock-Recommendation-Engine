# EquityLens deployment guide

Status: configuration is complete; no public deployment is claimed. The owner must authorize hosting, DNS, email, analytics, monitoring, and market-data terms.

## Target topology

- Vercel: `apps/web`, Git-connected previews and production.
- Railway: FastAPI service, Celery worker, exactly one Celery Beat scheduler, managed PostgreSQL, and managed Redis.
- Resend: verified owner-controlled sending subdomain.
- PostHog: product analytics through the server adapter and browser-safe key.
- Sentry: API/web errors with PII filtering and release SHA.
- External HTTPS monitor: landing page and `/api/v1/health/ready`.

The browser always calls `/api/v1/*` on the Vercel origin. `apps/web/next.config.ts` proxies that path to server-only `API_UPSTREAM_URL`, avoiding cross-origin cookies.

## 1. Prepare Git and protected production

1. Push this repository to an owner-controlled GitHub repository.
2. In GitHub, open **Settings → Branches → Add branch protection rule** for `main`.
3. Require the `CI / verify` status, pull requests, and approval before merging. Disable force pushes.
4. Confirm Actions runs `format:check`, lint, types, all unit/integration tests, the production build, migration from empty PostgreSQL, and browser smoke.

## 2. Railway data services

1. In Railway, choose **New Project → Empty project**.
2. From **+ Create → Database**, add PostgreSQL and Redis managed services.
3. Open PostgreSQL **Backups**, enable daily and weekly volume backups; enable point-in-time recovery if the plan supports it.
4. Create three empty source services named `api`, `worker`, and `scheduler`; connect the same GitHub repository and protected branch.
5. Keep repository root as build context and set Dockerfile path to `apps/api/Dockerfile` on all three.
6. Select `/railway.toml` for API, `/deploy/railway/worker.toml` for worker, and `/deploy/railway/scheduler.toml` for scheduler where Config as Code is configured. Confirm scheduler replicas equal exactly one.
7. Add reference variables to each service: `DATABASE_URL=${{Postgres.DATABASE_URL}}` and `REDIS_URL=${{Redis.REDIS_URL}}`. Convert the Postgres scheme to `postgresql+asyncpg://` if Railway supplies a generic `postgresql://` URL.
8. Add every production API/job value documented in `docs/environment-variables.md`. Generate `SECRET_KEY` and `CSRF_SECRET` in a password manager; do not paste them into source or chat.
9. On API only, open **Settings → Networking → Generate Domain**. Worker and scheduler remain private.
10. Confirm API pre-deploy command is `python scripts/release.py`; it takes a PostgreSQL advisory lock before Alembic so replicas cannot race migrations.

Railway’s current deployment guidance supports separate monorepo service commands/config paths, managed PostgreSQL/Redis reference variables, and a pre-deploy migration command. See [monorepo deployments](https://docs.railway.com/deployments/monorepo), [Compose-to-Railway mapping](https://docs.railway.com/guides/docker-compose), and [pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command).

## 3. Resend and email DNS

1. Use an owner-controlled subdomain such as `updates.example.com` to isolate sending reputation.
2. In Resend, open **Domains → Add Domain**, enter the sending subdomain, and copy the generated SPF/MX and DKIM records to the DNS provider exactly.
3. Add an initial monitoring DMARC TXT record after reviewing the owner’s existing domain mail policy.
4. Wait until Resend reports `verified`. Resend’s current domain guide requires SPF and DKIM and recommends a subdomain; DMARC is optional but trust-enhancing. See [Resend domain verification](https://resend.com/docs/dashboard/domains/introduction).
5. Create a sending-only API key. Set Railway `RESEND_API_KEY`, `EMAIL_PROVIDER=resend`, `EMAIL_FROM`, `SENDER_DOMAIN_VERIFIED=true`, `SENDER_POSTAL_ADDRESS`, and the canonical `APP_BASE_URL`.
6. Deploy and send verification/reset/digest messages to a real external inbox. Confirm links use HTTPS, reset and verification tokens are single use, and unsubscribe suppresses later digests.

Public registration is not launch-ready before this inbox test passes.

## 4. Product analytics and error monitoring

1. In PostHog, create a production project; copy its project API key into Railway `POSTHOG_API_KEY` and Vercel `NEXT_PUBLIC_POSTHOG_KEY`.
2. Create a funnel `signup_completed → email_verified → onboarding_completed → user_activated` and retention insight based on eligible authenticated events. Apply exclusions from `docs/analytics-events.md`.
3. In Sentry, create Python/FastAPI and JavaScript/Next.js projects. Put DSNs only in host environment variables.
4. Set `RELEASE_SHA` to the exact tested commit. Enable source-map upload in the Vercel integration and configure inbound filters/scrubbing for email, cookies, authorization headers, tokens, and request bodies.

## 5. Market-data launch mode

1. Start production with `PUBLIC_MARKET_DATA_MODE=restricted` and `PUBLIC_MARKET_DATA_LICENSE_ACKNOWLEDGED=false`.
2. Complete `docs/market-data-display.md` with provider, plan, feed, delay, adjustment, exact fields, audience, attribution, and verification date.
3. Only after the owner confirms public redistribution rights set mode to `licensed` and acknowledgement to `true`. Production refuses licensed startup otherwise.
4. A beta may launch in visibly labeled demo mode only by deliberately allowing that mode in the production configuration policy; current API validation expects `restricted` or licensed production.

## 6. Vercel web project

1. In Vercel choose **Add New… → Project**, import the Git repository, and set Root Directory to `apps/web`. Ensure source outside the root is included for the pnpm workspace.
2. Keep the Next.js framework preset and `apps/web/vercel.json` commands.
3. Add `API_UPSTREAM_URL=https://<railway-api-domain>`, `NEXT_PUBLIC_APP_BASE_URL=https://<vercel-production-domain>`, and the optional browser PostHog/Sentry keys for the appropriate Preview/Production environments.
4. Under **Settings → Environments → Production → Branch Tracking**, confirm the protected production branch. Vercel’s current Git deployment flow creates previews for non-production branches and production deployments from the selected production branch. See [Vercel Git deployments](https://vercel.com/docs/git) and [monorepo setup](https://vercel.com/docs/monorepos).
5. Deploy the tested commit SHA. Check deployment details show that exact SHA.
6. Under **Settings → Domains**, add an owner-controlled domain if available; enforce canonical HTTPS and redirect alternate hosts. Keep previews out of indexing.

## 7. Post-deploy verification

Run from the tested checkout:

```bash
BASE_URL=https://your-verified-host.example pnpm post-deploy-smoke
```

Then manually verify:

1. Anonymous landing and one supported public snapshot, including Open Graph image.
2. Real registration → external verification email → onboarding → two stock views → three watchlist items or one backtest → activated dashboard.
3. Password reset, session rotation/logout/revoke-all, weekly digest opt-in/unsubscribe, feedback, export, and deletion grace flow.
4. Admin job lock/audit, product metrics exclusions, feedback resolution, worker heartbeat, scheduler heartbeat, and data-health freshness.
5. External monitor checks `/` and `/api/v1/health/ready`; alert owner on repeated failure.

Only after this passes: put `Live Demo: https://...` in `README.md`, refresh `RESUME_EVIDENCE.md`, and record the production smoke timestamp.

## Backups and restore drill

Enable native schedules before beta. Take a portable `pg_dump --format=custom --no-owner`, restore to a scratch database with `pg_restore --exit-on-error`, compare important row counts, record duration/backup age, then delete the scratch database. Railway’s current guide explicitly recommends native volume backups, PITR, and portable logical dumps and treats an untested backup as unverified; see [Railway backup and restore](https://docs.railway.com/guides/postgres-backups-restores).

## Rollback

- Web: Vercel **Deployments** → select the last healthy exact-SHA deployment → promote/rollback; verify same-origin API and smoke again.
- API/worker/scheduler: Railway service **Deployments** → redeploy the prior image/source revision for all three. Keep worker/API on the same revision.
- Database: application migrations must be backward-compatible expand/migrate/contract changes. Roll back code first. Restore a backup/PITR fork only after preserving the current database and documenting the incident.

## Cost guardrail

Target below $25/month for fewer than 1,000 beta MAU, excluding the domain and any market-data display license. Start with one small API, one small worker, one scheduler, low-volume managed data services, free/entry analytics and monitoring tiers, retention limits, and provider billing alerts. Never reduce backup durability, security, disclosures, or licensing compliance to reach the target.
