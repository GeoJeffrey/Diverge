# Diverge API Contract Notes & Frozen Schema Documentation

> **Status: FROZEN**  
> **Backend Contract: Antigravity**  
> **Frontend Contract: Cursor**  
> **Frozen Specification File:** [`docs/openapi.json`](openapi.json)

---

## 1. Frozen Scope & Rule Guarantees

As required by Step 1 of the architecture contract freeze:
1. **Pipeline Isolation**: No pipeline internals, calculation engines, or DB ingestion routines have been modified.
2. **Explicit Models**: Every field has an explicit type and name. Loose unshaped dictionaries have been completely eliminated.
3. **Strict Null-Handling Envelopes**: Every financial index metric (`rn`, `cirg`, `cli`, `cassi`, `vdi`, and `coordination`) strictly adheres to the standard schema:
   ```json
   {
     "label": "Contagion Core",
     "score": 1.34,
     "available": true,
     "coverage_note": null
   }
   ```
   When unavailable (e.g. data requirements not yet satisfied):
   ```json
   {
     "label": "Cross-Market Spillover",
     "score": null,
     "available": false,
     "coverage_note": "Needs 30+ days of overlapping multi-ticker data, currently at 12 days"
   }
   ```
4. **Approved Human-Readable Labels**: Short codes remain as standard JSON field keys, but each carries its mandatory approved label string:
   - `rn` -> **Contagion Core**
   - `cirg` -> **Reality Check**
   - `cli` -> **Capitulation Signal**
   - `cassi` -> **Cross-Market Spillover**
   - `vdi` -> **Language Divergence**
   - `coordination_score` / `confidence_flag` -> **Trust Score**

---

## 2. Frozen Endpoints Overview

| Method | Path | Summary | Description & Shape |
|---|---|---|---|
| `GET` | `/health` | Service Health Check | Operational status, DB connectivity status, version, and server timestamp. |
| `GET` | `/tickers` | Tracked Ticker Universe | List of all monitored equities with metadata (`id`, `symbol`, `name`, `sector`) and latest high-level verdict. |
| `GET` | `/ticker/{symbol}` | Advanced Mode Detail | Full technical diagnosis with all 5 indices, coordination trust score, composite rating, and phylogeny transitions. |
| `GET` | `/ticker/{symbol}/simple` | Simple Mode Summary | Non-technical consumer payload with plain-language `why_sentence`, `verdict_label`, and `trust_label`. No raw index values. |
| `GET` | `/ticker/{symbol}/reasoning` | Why this Score Panel | Post-level audit trail grouping raw source evidence posts by audit driver category with 140-char previews. |
| `POST` | `/auth/signup` | User Registration | Creates account; returns `access_token`, `refresh_token`, `token_type`, and `expires_in`. |
| `POST` | `/auth/login` | User Authentication | Validates credentials; returns `access_token` and `refresh_token`. |
| `POST` | `/auth/refresh` | Token Refresh | Exchanges refresh token for newly issued access token. |
| `GET` | `/auth/me` | User Profile Session | Returns authenticated user details (`id`, `email`, `full_name`, `role`, `created_at`) via `BearerAuth`. |

---

## 3. Deliberate Ambiguities & Open Design Decisions

The following items are deliberately noted for frontend (Cursor) alignment:

1. **Window Resolution Fallback**:
   - The `/ticker/{symbol}` and `/ticker/{symbol}/simple` endpoints accept an optional `?window=` query parameter (ISO 8601 UTC). When omitted or null, the backend automatically defaults to the most recent window with computed metrics.
2. **Auth Token Lifetime**:
   - `expires_in` is specified in seconds (default `3600` = 1 hour). Access tokens are JWTs formatted for standard `Authorization: Bearer <access_token>` headers.
3. **Phylogeny History Depth**:
   - In `/ticker/{symbol}`, `phylogeny_context` provides up to 3 recent transition events preceding the requested window to render recent directionality without loading the full historical tree.
4. **Sector Groupings**:
   - Tracked symbols are grouped into standard sector taxonomy (`Information Technology`, `Energy`, `Financial Services`, `Consumer Goods`, `Basic Materials`, `Automotive`, `Consumer Discretionary`, `Conglomerate`).

---

## 4. Deliverable Confirmation

> **"This schema is frozen. Any future change to field names, types, or nesting must be called out explicitly, not made silently."**
