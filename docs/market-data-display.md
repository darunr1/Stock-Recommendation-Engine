# Public market-data display gate

Current default: deterministic synthetic demo data.

| Field | Current value |
|---|---|
| Provider/plan | Demo generator; no vendor entitlement claimed |
| Feed/latency | Deterministic synthetic daily series; visibly labeled |
| Adjustment | `all` semantics in fixture metadata |
| Public fields | Symbol, company, dated demo score/band/confidence, factor summary, limited synthetic history |
| Audience | Public beta visitors and registered researchers |
| Attribution requirement | EquityLens demo-data label |
| Owner permission verification date | Not yet verified for any live provider |

Runtime behavior:

- `demo`: serves visibly labeled deterministic demo values.
- `restricted`: withholds public prices/history and adds a license-restricted warning; only the versioned public allowlist remains.
- `licensed`: production refuses startup unless `PUBLIC_MARKET_DATA_LICENSE_ACKNOWLEDGED=true`.

Before changing to `licensed`, the owner must document the exact provider, subscription plan, feed, delay, adjustment, displayed fields, audience, redistribution/attribution requirements, and verification date. Recheck when monetizing, expanding audience, changing feeds, or adding real-time fields. This is an operational gate, not legal advice.
