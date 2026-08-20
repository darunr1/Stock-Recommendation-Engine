# API guide

Interactive OpenAPI is available at `/api/docs`; the schema is `/api/openapi.json`. All product routes use `/api/v1`.

## Authentication

The API sets short-lived `access_token`, rotating `refresh_token`, and readable `csrf_token` cookies. Browser state changes copy `csrf_token` into `X-CSRF-Token`. Production cookies are secure and `SameSite=Lax`. Passwords use Argon2id; only refresh/action-token hashes are stored.

Core auth routes: register, login/demo-login (non-production), refresh, logout, revoke-all, current user, verification/resend, forgot/reset password. Forgot/resend replies do not reveal account existence.

## Public shape

`GET /public/market-preview` and `GET /public/stocks/{symbol}` are anonymous and separately shaped. They never expose raw feature inputs, user/admin fields, credentials, or unrestricted payloads. Runtime licensing mode may withhold price/history.

## Research and user resources

- Market/recommendations: summary, pageable/filterable/sortable screener, detail/history, search, prices, fundamentals.
- Watchlist: get, idempotent add/update/delete.
- Backtests: queue/list/detail/series; saved configuration/result is immutable.
- Paper portfolio: snapshot/positions/transactions/performance, validated transaction, and audited reset.
- Growth/privacy: attribution, referrals, onboarding, preferences/unsubscribe, feedback, export, deletion state.
- Operations: liveness/readiness, data health, admin job controls, real product aggregates, feedback triage.

## Error envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [],
    "request_id": "uuid"
  }
}
```

Stack traces, SQL, raw provider errors, tokens, and secrets never appear in the envelope.
