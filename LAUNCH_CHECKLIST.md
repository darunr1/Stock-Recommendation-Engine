# Public-beta launch checklist

Unchecked account-bound items are real gates, not missing credentials to paste into this repository.

## Automated repository readiness

- [x] Credential-free deterministic demo provider and 30+ candidate universe plus SPY.
- [x] Production-shaped web/API/worker/scheduler/PostgreSQL/Redis Compose topology.
- [x] Vercel and Railway manifests, same-origin API proxy, locked migration release command.
- [x] Auth, verification/reset capture, onboarding, research, watchlist, backtest, paper portfolio, feedback, preferences, privacy controls, and admin APIs/UI.
- [x] Runtime `demo|restricted|licensed` public-data gate; production licensed mode requires explicit acknowledgement.
- [x] CI and post-deploy smoke workflows.
- [x] Security/financial disclosures and public legal pages.

## Owner authorization and launch gates

- [ ] Push repository to owner GitHub and protect `main` with required CI.
- [ ] Connect `apps/web` to Vercel and API/worker/scheduler to Railway at one tested commit SHA.
- [ ] Provision managed PostgreSQL and Redis, use service reference variables, and confirm private networking.
- [ ] Generate unique production signing/CSRF secrets in a password manager.
- [ ] Set canonical HTTPS `APP_BASE_URL`, API upstream, CORS allowlist, trusted proxy, and secure-cookie environment.
- [ ] Verify owner-controlled Resend sending subdomain (SPF/DKIM; reviewed DMARC), set real sender/postal details, and test an external inbox.
- [ ] Create PostHog project/funnel/retention views and validate event privacy/exclusions.
- [ ] Create Sentry projects, release tagging/source maps, and PII filters.
- [ ] Confirm exact public market-data fields and audience are licensed, or keep production restricted and visibly labeled.
- [ ] Enable database daily/weekly backups and PITR where supported; complete and timestamp a scratch restore drill.
- [ ] Configure external HTTPS monitoring for landing and API readiness plus owner alert channel.
- [ ] Confirm exactly one production scheduler and healthy worker heartbeat.
- [ ] Run `BASE_URL=https://... pnpm post-deploy-smoke` against the real URL.
- [ ] Verify real signup, email verification, onboarding, activation, reset, digest/unsubscribe, feedback, export, and deletion flows.
- [ ] Run desktop/mobile Lighthouse; reach 90+ for public desktop categories and document mobile exceptions.
- [ ] Confirm previews are not indexed and production has no demo login/admin credentials.
- [ ] Update README Live Demo/screenshots only after smoke passes.
- [ ] Run `pnpm evidence` against production-safe aggregate access and commit only measured claims.

## Launch-day operating checks

- [ ] Latest daily price/scoring run is successful with expected coverage and clear demo/restricted/licensed label.
- [ ] Transactional email delivery, bounce/suppression, and unsubscribe are healthy.
- [ ] Error rate, latency, worker/scheduler heartbeat, database capacity, Redis no-eviction behavior, and backup timestamp are visible.
- [ ] Incident banner path and owner escalation channel are ready.
- [ ] Five private-alpha sessions are scheduled before broad promotion.
