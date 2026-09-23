# CloudContextGuard - Project Documentation

**Context-Aware Cloud Access Control Using IAM and Trusted VPC Boundaries**

## 1. Abstract

CloudContextGuard is a working, locally-run simulation of a context-aware
cloud authorization system. It demonstrates, through a fully implemented
FastAPI backend, SQLite database, and React frontend, that a cloud
authorization decision should combine identity permission (IAM), network
origin (VPC trust boundary), multi-factor authentication, resource
policy, and a deterministic risk score, rather than relying on IAM
permission alone. The system supports live administrator-driven policy
changes that take effect immediately, without any code deployment, and
includes a full audit trail (access requests, security events, alerts)
and an attack simulation lab that exercises the real authorization
pipeline rather than a mock. The project is validated by 82 automated
backend tests and a 17-point portability check.

## 2. Introduction

Cloud storage breaches are frequently not the result of a broken
permission model but of a permission model that is trusted too much: a
single leaked credential, used from anywhere, is treated as sufficient
proof of authorization. CloudContextGuard implements and demonstrates an
alternative: IAM permission is necessary but never sufficient, and every
access decision is the product of several independent, explainable
checks.

## 3. Problem Statement

Given a valid IAM permission, most authorization systems grant access
unconditionally. This project asks: what additional, independently
enforced controls are needed so that a valid IAM permission, used from an
untrusted network or without MFA, is still denied - and how can those
controls be made administrator-configurable at runtime without weakening
the guarantee that the server (never the client) is authoritative?

## 4. Motivation

Stolen-credential and unexpected-network access are among the most
common real-world cloud storage attack patterns. A system that can
concretely show "this identity had a genuine, valid permission, and was
still denied because of where the request came from" is a stronger
teaching and research artifact than a diagram, because every claim it
makes can be independently re-run and re-verified against a live API.

## 5. Research Objective

To design, implement, and empirically verify a rule-based, explainable,
dynamically-configurable authorization model satisfying:

1. Authorization decisions are enforced server-side; a client cannot
   submit or influence the decision, risk score, or any other
   server-controlled field.
2. IAM permission alone does not guarantee access.
3. Network context (VPC trust boundary) can independently deny an
   otherwise-permitted request.
4. MFA requirements are enforced independently of IAM and network.
5. A deterministic, explainable risk score can independently deny a
   request above a documented threshold.
6. Resource policy (enabled state, required role, VPC, MFA, external
   access, maximum risk) is enforced.
7. Policy changes made by an administrator at runtime affect the very
   next authorization decision, with no code or deployment change.
8. Every decision is captured in an accurate, tamper-resistant audit
   trail.

## 6. Scope

In scope: a simulated IAM/VPC/MFA/risk/policy authorization pipeline; a
SQLite-backed catalog of synthetic users, roles, resources, and network
boundaries; a REST API; a React administrative and demonstration
frontend; an attack simulation lab exercising the real pipeline; and an
automated test suite validating all of the above.

Out of scope: any connection to a real cloud provider, any real
credential or identity provider, real network traffic or packet capture,
machine-learning-based risk scoring, and production-grade operational
concerns (rate limiting, horizontal scaling, a distributed database).
These are explicitly documented as limitations (Section 28) and future
work (Section 29), not implemented or claimed.

## 7. Proposed System

CloudContextGuard: a FastAPI service exposing `POST /api/access/request`
as the single authorization entry point, backed by five pure-function
"engines" (IAM, VPC, Policy, MFA, Risk) orchestrated by an access service
and combined by a central decision engine; a SQLite database holding
both the reference catalog and the full audit trail; and a React
frontend that is a real client of this API - it never computes a
security decision itself.

## 8. Existing Problem

Conventional access-control demonstrations either (a) describe a policy
model in the abstract without a running implementation, or (b) implement
IAM-only permission checks without contextual (network, MFA, risk)
enforcement, or (c) hardcode policy in source code such that a policy
change requires a redeploy. CloudContextGuard addresses all three: it is
a running system, it enforces context independently of IAM, and its
policy is live, database-backed, and administrator-editable at runtime.

## 9. System Architecture

```
React Frontend  --HTTP-->  FastAPI API  -->  Access Service
                                                    |
                        +---------------------------+---------------------------+
                        |            |              |            |             |
                    IAM Engine   VPC Engine   Policy Engine   MFA Eval     Risk Engine
                        |            |              |            |             |
                        +---------------------------+---------------------------+
                                                    |
                                           Decision Engine
                                                    |
                                          SQLite Database
                              (roles, users, permissions, resources, vpcs,
                               policies, access_requests, security_events,
                               alerts, schema_version)
```

See [`docs/diagrams/system-architecture.md`](docs/diagrams/system-architecture.md)
for the Mermaid rendering.

## 10. Component Description

| Component | File(s) | Role |
|---|---|---|
| API layer | `backend/app/api/*.py` | HTTP routing, request/response schema validation, no business logic |
| Access service | `backend/app/services/access_service.py` | Orchestrates a single access request through every engine; persists the outcome |
| Policy service | `backend/app/services/policy_service.py` | Validates and applies policy edits; writes the `POLICY_CHANGED` audit event |
| Seed service | `backend/app/services/seed_service.py` | Idempotent baseline catalog and `contractor01` demonstration-identity seeding |
| Engines | `backend/app/engine/*.py` | Pure functions: IAM, VPC, Policy (+MFA), Risk, Decision |
| Schemas | `backend/app/schemas/*.py` | Pydantic request/response and engine-result models |
| Models | `backend/app/db/models.py` | SQLAlchemy ORM tables |
| Database setup | `backend/app/db/database.py` | Engine/session setup, schema-version safety mechanism |
| Frontend pages | `frontend/src/pages/*.jsx` | Dashboard, Access Requests, IAM, VPC Security, Storage, Security Events, Alerts, Policies, Attack Simulator |

## 11. IAM Architecture

Implemented in `backend/app/engine/iam_engine.py`. Given a user's role and
its set of permissions (each a plain `action` / `resource_pattern` pair),
`evaluate_iam` checks: does the user exist, is the user active, does the
user have a role, and does that role hold a permission whose action and
resource pattern (matched with `fnmatch`, supporting `*` wildcards) match
the requested action and resource? The result is a structured `IAMResult`
(`allowed`, `result`, `reason`, `matched_permission`) - never a bare
boolean. The engine has no knowledge of network, MFA, or risk.

## 12. VPC Boundary Architecture

Implemented in `backend/app/engine/vpc_engine.py`. `evaluate_vpc` takes
whether the resource's active policy requires a trusted VPC at all, the
specific VPC name that policy currently designates as trusted (resolved
by the access service from the `Policy.trusted_vpc_id` foreign key, with
the resource's own `trusted_vpc_id` as a fallback when no policy row
exists), the request's actual source VPC name, and whether that source
VPC is a known, trusted network. A resource with no VPC requirement
always passes. A protected resource requires an exact match against its
policy's configured VPC - not merely "any trusted VPC."

## 13. MFA Architecture

Implemented as `evaluate_mfa` in `backend/app/engine/policy_engine.py`
(grouped with policy evaluation, since the MFA requirement is a property
of the resource's policy). A resource whose policy does not require MFA
always passes this check regardless of whether MFA was provided. A
resource that does require MFA fails, and denies the request, if MFA was
not provided.

## 14. Risk Model

Implemented in `backend/app/engine/risk_engine.py`. See
[`docs/research/SECURITY_DECISION_MODEL.md`](docs/research/SECURITY_DECISION_MODEL.md)
for the full formula, per-factor point values, and level thresholds.
Deterministic and rule-based; no machine learning is used anywhere in
this project.

## 15. Dynamic Policy Model

`Policy` rows (`backend/app/db/models.py`) are the authoritative,
administrator-editable configuration for each resource: `required_role`,
`trusted_vpc_id`, `mfa_required`, `max_risk_score`,
`external_access_allowed`, `is_enabled`. `access_service.py` queries the
`Policy` table fresh on every single access evaluation - there is no
cache anywhere in the request path. `PUT /api/policies/{id}`
(`backend/app/api/policies.py`, validated and applied by
`policy_service.py`) is the only way to change a policy; every change is
recorded as a `SecurityEvent`. See
[`docs/research/DYNAMIC_POLICY_EVALUATION.md`](docs/research/DYNAMIC_POLICY_EVALUATION.md)
for the full worked experiment.

## 16. Decision Engine

Implemented in `backend/app/engine/decision_engine.py`. The sole place a
final ALLOW/DENY is produced. Priority order: IAM failure denies
immediately; otherwise, resource-policy failure, a failed VPC check on a
policy that requires one, a failed MFA check where required, and
external access being prohibited for an external request are each
collected as failure reasons; risk score `>= 80` or `>= 60` also denies;
a configured `max_risk_score` on the policy is enforced as an additional
safeguard; if nothing failed, the decision is ALLOW. The reason string
returned is composed from the actual results of each check, never a
fixed template unrelated to what happened.

## 17. Database Design

SQLite via SQLAlchemy 2.0. Tables: `roles`, `users`, `permissions`,
`resources`, `vpcs`, `policies`, `access_requests`, `security_events`,
`alerts`, `schema_version`. Full schema documented in
[`docs/architecture/PROJECT_STRUCTURE.md`](docs/architecture/PROJECT_STRUCTURE.md).
Foreign keys are enforced (`PRAGMA foreign_keys=ON` on every connection).
The database file path is resolved dynamically
(`backend/app/core/paths.py`), never hardcoded.

## 18. API Architecture

A FastAPI application (`backend/app/main.py`) composed of six routers
(`access`, `catalog`, `policies`, `security`, `dashboard`, `database`),
each in its own module under `backend/app/api/`. Every endpoint is
documented in [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md). CORS is an
explicit origin allowlist (never a wildcard with credentials); baseline
security response headers (`X-Content-Type-Options`, `X-Frame-Options`,
`Referrer-Policy`) are attached to every response by a lightweight
middleware.

## 19. Frontend Architecture

A React 19 single-page application built with Vite, styled with Tailwind
CSS, routed with React Router, and charted with Recharts. Organized into
`pages/` (one per route), `components/` (`common/`, `layout/`,
`dashboard/`, `security/`, `tables/`), `services/api.js` (the single
centralized API client - no component builds a fetch URL directly), and
`hooks/useApi.js` (data-fetching and health-polling hooks). The frontend
holds no authorization logic: every decision, risk score, and PASS/FAIL
value displayed is read directly from an API response.

## 20. Attack Simulation

`frontend/src/pages/Simulator.jsx` and
`frontend/src/data/simulationScenarios.js` define six scenarios as pure
request inputs (user, action, resource, source IP/VPC, MFA, request
type) - no expected outcome is stored client-side. Running a scenario
submits a real `POST /api/access/request` and renders whatever the API
actually returns, including confirming, via `GET /api/security/events`
and `GET /api/alerts` filtered by `access_request_id`, whether a security
event or alert was genuinely created before claiming so in the UI.

## 21. Security Event Model

`SecurityEvent` rows are created in exactly two circumstances, both in
`backend/app/services/access_service.py` and `policy_service.py`: every
denied access request (never an allowed one), and every applied policy
change. Fields: `timestamp`, `severity`, `event_type`, `user`,
`source_ip`, `source_vpc`, `resource`, `risk_score`, `description`,
`action_taken`, and `access_request_id` (nullable - `null` for
policy-change events).

## 22. Alert Model

`Alert` rows are created for any request (allowed or denied) whose risk
level is `HIGH` or `CRITICAL`, linked to the originating request via a
unique `access_request_id` (guaranteeing at most one alert per request).
Severity mirrors the risk level; status starts `OPEN`.

## 23. Auditability

Every access decision is persisted as an `AccessRequest` row capturing
the full request (`user`, `role`, `action`, `resource`, `source_ip`,
`source_vpc`, `mfa`, `request_type`) and the full outcome
(`iam_result`, `vpc_result`, `resource_result`, `mfa_result`,
`risk_score`, `risk_level`, `risk_factors` as JSON, `final_decision`,
`decision_reason`), independently verified by automated tests
(`backend/tests/test_security_validation.py::test_audit_record_fields_match_the_actual_request`)
to match the actual request and response.

## 24. Portability

Every filesystem path used anywhere in the application is derived from
`backend/app/core/paths.py`'s own file location at import time, never
from the current working directory or a hardcoded string.
`tests/verify_portability.py` independently verifies this with 17
checks, including spawning a subprocess from an unrelated working
directory and simulating a moved project folder. Current result:
**17/17 PASS**.

## 25. Testing Methodology

82 automated tests (`pytest`, `backend/tests/`), organized by concern:
`test_health.py` (5, basic liveness), `test_access_control.py` (17, IAM
/VPC/MFA/risk/policy behavior and the `contractor01` scenarios),
`test_policy_management.py` (10, policy CRUD, validation, and the
dynamic-policy-change demonstration), `test_database_safety.py` (9,
schema-version safety and persistence), `test_security_validation.py`
(41, the Step 7 comprehensive security validation pass: server-side
authorization, IAM/VPC/MFA/risk edge cases, engine-level risk-factor and
decision-threshold unit tests, audit/alert integrity, input validation,
injection resistance, mass-assignment resistance, and database
integrity). All tests run against the project's real database and API
(via FastAPI's `TestClient`) - no mocked paths, no mocked data.

## 26. Security Validation

A dedicated hardening pass (Step 7) independently verified: authorization
cannot be forced by a client-supplied `decision` field; extra fields
(`role`, `is_admin`, `risk_score`, `severity`, etc.) submitted in either
an access request or a policy update are ignored, never applied; SQL
-like, script-like, and path-traversal-like input strings are treated as
inert data (no raw SQL interpolation exists anywhere in the codebase);
foreign-key integrity holds with zero orphaned rows; error responses
(404/422) contain no stack traces, file paths, or environment data; CORS
is a specific origin allowlist; and baseline security response headers
are present on every response.

## 27. Results

See [`docs/research/RESULTS.md`](docs/research/RESULTS.md) for the full,
verified results, including the exact IAM/VPC/MFA/risk values produced
by the two central demonstration scenarios.

## 28. Limitations

- Local simulation only; no connection to a real cloud provider.
- No real AWS integration and no real cloud credentials are used or
  supported anywhere in this project.
- Risk scoring is rule-based (fixed, named point values), not
  machine-learning-based.
- No production-grade rate limiting is implemented.
- SQLite is used rather than a production distributed database.
- Schema-change safety uses a lightweight, manually-maintained
  schema-version number, not a full migration framework such as
  Alembic.
- No production identity provider (OAuth/OIDC/SAML) is integrated;
  identities are rows in the local database with no authentication of
  their own.
- No real cloud telemetry (e.g. AWS CloudTrail) is ingested; all audit
  data originates from this application's own simulated requests.

## 29. Future Improvements

- AWS IAM integration (map simulated roles/permissions onto real IAM
  policy evaluation).
- AWS VPC endpoint context (real network-origin verification via VPC
  endpoints or PrivateLink).
- S3 integration (apply the same context-aware model to real S3 bucket
  policies).
- CloudTrail ingestion (replace simulated audit data with real AWS
  event data).
- Real-time event streaming (push security events/alerts to the
  frontend rather than polling).
- ML-based anomaly detection, as a complement to (not replacement for)
  the current rule-based risk engine.
- Production-grade rate limiting.
- A distributed database for production-scale audit volume.
- Identity-provider integration (OAuth/OIDC/SAML).
- Policy-as-code and Terraform/IaC integration for managing policies
  outside the application database.

## 30. Conclusion

CloudContextGuard demonstrates, with a fully working and independently
testable system, that context-aware cloud authorization - IAM, network,
MFA, policy, and risk evaluated together rather than IAM alone - is
implementable, explainable, and dynamically configurable without
sacrificing server-side authority. Its central finding, reproduced by
both automated tests and live demonstration, is direct: a genuinely
valid IAM permission, exercised from an untrusted network without MFA,
is still denied.
