# CloudContextGuard - API Documentation

Base URL (local development): `http://127.0.0.1:8000`

All endpoints are documented directly from the implementation in
`backend/app/api/` and `backend/app/schemas/`. Interactive documentation
is also available at `/api/docs` (Swagger UI) and `/api/redoc` while the
backend is running.

All list endpoints accept an optional `limit` query parameter
(`default=50`, `minimum=1`, `maximum=500`); a value outside that range
returns `422`.

---

## Health

### `GET /api/health`

Purpose: report API and database health. Used by the frontend's
ONLINE/OFFLINE indicator (polled, not on every request).

Request: none.

Response `200` (healthy) or `503` (database unavailable):

```json
{
  "status": "healthy",
  "service": "CloudContextGuard API",
  "database": "connected"
}
```

### `GET /health`

Identical to `GET /api/health` (kept for convenience/compatibility).

---

## Dashboard

### `GET /api/dashboard`

Purpose: aggregated, database-derived summary for the Dashboard page.
Nothing in this response is hardcoded; every value is computed live from
the `access_requests`, `security_events`, `alerts`, and `resources`
tables.

Response `200`:

```json
{
  "total_requests": 46,
  "allowed_requests": 19,
  "denied_requests": 27,
  "high_risk_requests": 27,
  "critical_events": 20,
  "open_alerts": 27,
  "protected_resources": 3,
  "decision_distribution": { "ALLOW": 19, "DENY": 27 },
  "risk_distribution": { "LOW": 10, "MEDIUM": 6, "HIGH": 3, "CRITICAL": 27 },
  "requests_by_vpc": { "vpc-development": 20, "external": 26 },
  "requests_by_user": { "developer01": 30, "finance01": 16 },
  "recent_events": [ /* up to 10 SecurityEventOut, newest first */ ]
}
```

---

## Access Control

### `POST /api/access/request`

Purpose: the single authorization entry point. Evaluates a simulated
access request through the IAM, VPC, resource-policy, MFA, and risk
engines and returns the full explainable result. This is the only
endpoint that produces an authorization decision - the backend is
authoritative; the request body has no field that can set or influence
`decision`, `risk_score`, or any other computed value (unrecognized
fields are silently ignored, per Pydantic's default behavior).

Request body (`AccessRequestIn`):

```json
{
  "user": "contractor01",
  "action": "GetObject",
  "resource": "financial-records",
  "source_ip": "185.22.91.11",
  "source_vpc": "external",
  "mfa": false,
  "request_type": "SUSPICIOUS"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `user` | string | yes | Username; `404` if it does not exist. |
| `action` | string | yes | e.g. `GetObject`, `PutObject`, `ListBucket`, `DeleteObject`. |
| `resource` | string | yes | Resource name; `404` if it does not exist. |
| `source_ip` | string \| null | no | Free-form, stored for audit only. |
| `source_vpc` | string | yes | VPC name; an unrecognized value is treated as untrusted, not a validation error. |
| `mfa` | boolean | no (default `false`) | Whether MFA was provided. |
| `request_type` | `"NORMAL"` \| `"SUSPICIOUS"` \| `"AUTOMATED"` \| `"UNKNOWN"` | no (default `"NORMAL"`) | Contributes to risk when `SUSPICIOUS`. |

Response `200` (`AccessDecisionResponse`):

```json
{
  "request_id": 291,
  "timestamp": "2026-09-23T20:45:50",
  "decision": "DENY",
  "reason": "IAM authorization succeeded, but the request originated outside the trusted VPC and the request was assessed as CRITICAL risk (score 80).",
  "risk_score": 80,
  "risk_level": "CRITICAL",
  "iam_result": { "allowed": true, "result": "PASS", "reason": "...", "matched_permission": "GetObject:financial-records" },
  "vpc_result": { "allowed": false, "result": "FAIL", "reason": "...", "expected_vpc": "vpc-finance", "actual_vpc": "vpc-development" },
  "resource_result": { "allowed": true, "result": "PASS", "reason": "...", "is_enabled": true, "required_role": null, "trusted_vpc_required": true, "mfa_required": true, "external_access_allowed": false, "max_risk_score": 59 },
  "mfa_result": { "required": true, "provided": true, "result": "PASS", "reason": "..." },
  "risk_factors": [ { "name": "External network", "points": 40, "reason": "..." } ]
}
```

Errors:

| Status | Cause |
|---|---|
| `404` | `user` does not exist, or `resource` does not exist. |
| `422` | Missing/invalid field (e.g. missing `user`, non-boolean `mfa`, invalid `request_type`). |

### `GET /api/access/requests`

Purpose: audit log of stored access requests, newest first, with
resolved user/role/resource names.

Query: `limit` (see above).

Response `200`: array of `AccessRequestOut` -
`id, timestamp, user, role, action, resource, source_ip, source_vpc,
mfa, request_type, iam_result, vpc_result, resource_result,
mfa_required, mfa_result, risk_score, risk_level, risk_factors,
final_decision, decision_reason`.

---

## Security Events

### `GET /api/security/events`

Purpose: the security event log. An event is created for every denied
access request and for every applied policy change.

Query: `limit` (see above).

Response `200`: array of `SecurityEventOut` -
`id, access_request_id, timestamp, severity, event_type, user,
source_ip, source_vpc, resource, risk_score, description,
action_taken`. `access_request_id` is `null` for policy-change events.

---

## Alerts

### `GET /api/alerts`

Purpose: alerts raised for any request (allowed or denied) assessed as
`HIGH` or `CRITICAL` risk.

Query: `limit` (see above).

Response `200`: array of `AlertOut` -
`id, access_request_id, timestamp, severity, title, description,
status`. `access_request_id` is unique per alert (never duplicated for
the same request).

---

## Catalog (read-only)

### `GET /api/users`

Response `200`: array of `UserOut` -
`id, username, display_name, role, is_active, created_at`.

### `GET /api/roles`

Response `200`: array of `RoleOut` - `id, name, description`.

### `GET /api/permissions`

Response `200`: array of `PermissionOut` -
`id, role, action, resource_pattern`.

### `GET /api/resources`

Response `200`: array of `ResourceOut` -
`id, name, resource_type, classification, required_role, trusted_vpc,
trusted_vpc_name, mfa_required, external_access_allowed, description`.

### `GET /api/vpcs`

Response `200`: array of `VPCOut` -
`id, name, cidr, trust_level, description, is_trusted`.

---

## Policies

### `GET /api/policies`

Response `200`: array of `PolicyOut` -
`id, name, description, resource, required_role, trusted_vpc,
mfa_required, max_risk_score, external_access_allowed, is_enabled,
created_at, updated_at`. `trusted_vpc` is the resolved VPC name (or
`null`), not a boolean.

### `GET /api/policies/{policy_id}`

Response `200`: a single `PolicyOut`.

Errors: `404` if `policy_id` does not exist.

### `PUT /api/policies/{policy_id}`

Purpose: the only way to change a policy. Validates references, applies
the change, and records a `POLICY_CHANGED` security event
(`severity="HIGH"`, `action_taken="POLICY_UPDATED"`) describing exactly
which fields changed. Takes effect on the very next access evaluation -
nothing is cached.

Request body (`PolicyUpdate`):

```json
{
  "name": "financial-records-policy",
  "description": "...",
  "required_role": null,
  "trusted_vpc": "vpc-development",
  "mfa_required": true,
  "max_risk_score": 59,
  "external_access_allowed": false,
  "is_enabled": true
}
```

| Field | Type | Required | Validation |
|---|---|---|---|
| `name` | string | yes | 1-150 characters. |
| `description` | string \| null | no | Max 255 characters. |
| `required_role` | string \| null | no | Must be an existing role name, or `null` to clear. |
| `trusted_vpc` | string \| null | no | Must be an existing VPC name, or `null` to clear. |
| `mfa_required` | boolean | yes | |
| `max_risk_score` | integer \| null | no | `0`-`100`. |
| `external_access_allowed` | boolean | yes | |
| `is_enabled` | boolean | yes | |

`id`, `resource_id`, `created_at`, and `updated_at` are never accepted
from the client - they are not fields on this schema, so they are
silently ignored if submitted; `updated_at` is always the real server
timestamp of the change.

Response `200`: the updated `PolicyOut`.

Errors:

| Status | Cause |
|---|---|
| `404` | `policy_id` does not exist. |
| `422` | `max_risk_score` out of range, or `required_role`/`trusted_vpc` names a role/VPC that does not exist, or a required field is missing/invalid type. |

---

## Database

### `POST /api/database/seed`

Purpose: seed the baseline reference catalog (roles, users, resources,
VPCs, policies) if the database is empty, and ensure the `contractor01`
demonstration identity exists. Both operations are idempotent and
additive-only - they never delete existing data, never duplicate
existing rows, and never overwrite an administrator's policy
customization.

Request: none.

Response `200`:

```json
{
  "seeded": false,
  "contractor_identity_ensured": false,
  "message": "Database already contains data; seed skipped"
}
```
