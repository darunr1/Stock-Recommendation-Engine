# Product analytics events

Analytics uses opaque account/anonymous identifiers and bounded, allowlisted properties. Email addresses, names, tokens, notes, feedback text, and raw financial selections are prohibited.

| Event | Owner | Server/client trigger | Safe properties | Privacy |
|---|---|---|---|---|
| `landing_viewed` | Growth | Public landing view | campaign class | Anonymous |
| `public_stock_viewed` | Product | Public snapshot API | symbol, data mode | Anonymous |
| `signup_started` / `signup_completed` | Growth | Form/API | attribution state | Anonymous/account |
| `email_verified` | Security | Token consumption | none | Account |
| `onboarding_completed` | Product | Server persistence | skipped boolean | Account |
| `user_activated` | Product | Server conditions only | none | Account |
| `stock_viewed` | Research | Authenticated detail API | symbol | Account |
| `watchlist_item_added` | Research | Successful insert | symbol | Account |
| `screener_used` | Research | Results request | broad filter flags, sort | Account |
| `backtest_started` / `backtest_completed` | Research | Job persistence | engine version | Account |
| `paper_trade_recorded` | Research | Committed ledger transaction | symbol, side | Account |
| `share_clicked` | Growth | Share action | symbol, mechanism | Anonymous/account |
| `referral_landed` | Growth | Sanitized landing attribution | campaign class | Anonymous |
| `feedback_submitted` | Product | Accepted report | category only | Anonymous/account |
| `digest_opted_in` / `digest_clicked` | Lifecycle | Preference/link | campaign kind | Account |
| `account_deleted` | Privacy | Deletion state transition | none | Account |

The signup-to-activation funnel is `signup_completed → email_verified → onboarding_completed → user_activated`. Activation requires server evidence: verification, onboarding, two distinct stock views, and either three watchlist stocks or one completed backtest. Retention uses distinct non-demo, non-admin account events over D1/D7/D30 windows. Analytics failure never blocks product behavior.
