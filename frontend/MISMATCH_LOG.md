# Mismatch Log

| Endpoint | Field | Expected Shape (`docs/openapi.json`) | Actual Response Shape | Resolution |
|---|---|---|---|---|
| POST /auth/signup | — | `AuthTokenResponse` | Matches exactly (201 Created) | Resolved — Backend & Frontend in sync |
| POST /auth/login | — | `AuthTokenResponse` | Matches exactly (200 OK) | Resolved — Backend & Frontend in sync |
| GET /auth/me | — | `UserProfileResponse` | Matches exactly (200 OK) | Resolved — Backend & Frontend in sync |
| GET /tickers | — | `TickerListResponse` | Matches exactly (200 OK) | Resolved — Backend & Frontend in sync |
| GET /ticker/{symbol} | — | `TickerAdvancedResponse` (all 5 indices with `{ label, score, available, coverage_note }`) | Matches exactly (200 OK) | Resolved — Backend & Frontend in sync |
| GET /ticker/{symbol}/simple | — | `TickerSimpleResponse` | Matches exactly (200 OK) | Resolved — Backend & Frontend in sync |
| GET /ticker/{symbol}/reasoning | — | `ReasoningTraceResponse` | Matches exactly (200 OK) | Resolved — Backend & Frontend in sync |

### Edge Case Confirmations
- **Protected route 401 unauthenticated check**: Calling `GET /ticker/{symbol}` without `Authorization` header returns HTTP `401 Unauthorized`. Frontend `apiFetch` catches 401, resets session, and initiates redirect to `/login`.
- **Protected route 401 invalid/expired token**: Returns HTTP `401 Unauthorized` and cleanly redirects to `/login`.
- **Public endpoint access**: `GET /tickers` and `GET /ticker/{symbol}/simple` return HTTP `200` without requiring an `Authorization` header.
- **Unavailable index handling**: `IndexCard` component explicitly checks `!metric.available` and renders `CoverageNote` with `{label}: not yet computable — {coverage_note}`.
