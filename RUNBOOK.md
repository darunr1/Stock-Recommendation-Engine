# EquityLens operations runbook

Never include passwords, tokens, cookies, email bodies, provider payloads, or user notes in incident tickets or logs.

## Provider outage or stale coverage

1. Check `/api/v1/data-health` and `sync_runs` for safe error summary, coverage, timestamps, feed, and adjustment.
2. Stop duplicate retries; one job type may be active at a time.
3. Keep the last valid snapshot. Set/retain stale or restricted labels and publish a status banner.
4. Validate provider status/entitlement/rate headers outside end-user logs, then retry the idempotent sync.
5. If live public rights are uncertain, switch to `restricted`; do not silently fall back to unlabeled values.

## Failed nightly score

1. Confirm daily bars completed and expected-session coverage is sufficient.
2. Inspect model version, invalid-bar count, missing factor families, and canonical-payload errors.
3. Rerun the same date/version idempotently. Never overwrite prior successful model versions.
4. If scoring remains incomplete, surface stale/insufficient status and notify the owner.

## Failed migration

1. Pre-deploy failure stops the release; do not start mixed-schema application replicas.
2. Preserve logs after redaction, check advisory-lock holder, and confirm the exact release SHA.
3. Prefer a forward fix compatible with both old/new code. Destructive change requires expand/migrate/contract and a verified backup.
4. Roll back the application revision only when the prior code remains schema compatible.

## Email incident

1. Set `EMAIL_PROVIDER=capture` or pause lifecycle job; revoke the exposed key in Resend if relevant.
2. Keep verification/reset behavior unavailable rather than using an unverified sender.
3. Review safe delivery status and suppression counts, not bodies or secret links.
4. Correct DNS/template/link base, rotate credentials, test external inbox and unsubscribe, then restore gradually.

## Leaked secret

1. Revoke/rotate at the provider immediately; rotate signing secrets if token integrity may be affected and revoke sessions.
2. Remove secret from current files and Git history with owner approval; invalidate affected builds/caches.
3. Search logs, screenshots, CI artifacts, captured emails, and error tools for exposure without echoing the value.
4. Record scope/timeline and add prevention. Never paste the secret into the incident record.

## Bad recommendation-data release

1. Disable affected job and mark snapshots stale/invalid through a new auditable state; never rewrite historic analytic payloads.
2. Identify data/model version, affected symbols/dates, and whether public/share metadata needs a status banner.
3. Restore the last-known-good code/data source, recompute as a new model version if formula behavior changed, and run determinism/anti-leakage tests.
4. Publish a concise changelog/incident notice without investment-performance claims.

## Backup restore

Restore into a new/scratch database or Railway PITR sibling, compare critical row counts and recent records, run readiness/smoke, then plan a controlled connection-string cutover. Never overwrite the only production database during a drill.
