# CloudContextGuard

**Context-Aware Cloud Access Control Using IAM and Trusted VPC Boundaries**

## 1. Project Overview

CloudContextGuard is a local, fully working simulation of a context-aware
cloud authorization system. It demonstrates that a cloud access-control
decision should never rest on identity permission alone: every request is
evaluated against identity (IAM), network origin (VPC trust boundary),
multi-factor authentication, a per-resource policy, and a deterministic
risk score, and only then is a final ALLOW/DENY decision produced. The
system consists of a FastAPI backend (the authorization authority), a
SQLite database (the single source of truth for identities, resources,
policies and audit history), and a React dashboard for observing and
driving the system, including a live policy editor and an attack
simulation lab.

No real AWS account, IAM credential, VPC, or cloud resource is used or
contacted anywhere in this project. Every "resource," "VPC," and
"identity" is a row in a local SQLite database created for the purpose of
this simulation.

## 2. Problem Statement

Conventional cloud identity and access management answers one question:
*does this identity have permission to perform this action on this
resource?* A single valid IAM permission is often treated as sufficient
justification for access, regardless of where the request originates,
whether multi-factor authentication was used, or how risky the request
looks in context. This is the exact gap exploited by stolen-credential
attacks: an attacker with a leaked API key or session token inherits
every permission that identity has, from any network, with no additional
friction.

## 3. Research Objective

To design and implement a working authorization model that treats IAM
permission as necessary but not sufficient, and to demonstrate, with a
real, running system rather than a diagram, that:

- a valid IAM permission does not by itself guarantee access;
- network origin (VPC trust boundary) can independently deny an
  otherwise-permitted request;
- MFA and a deterministic, explainable risk score are additional,
  independent gates; and
- authorization policy is administrator-configurable at runtime, from a
  database, without any application code change, and takes effect on the
  very next request.

## 4. Key Idea

```
IDENTITY + IAM PERMISSION + NETWORK CONTEXT + RESOURCE POLICY + MFA + RISK
                                    =
                            FINAL DECISION
```

Every one of these six inputs is evaluated independently and explicitly
on every request. None of them can be skipped, and a client cannot submit
a decision, a risk score, or any other server-controlled field and have
it accepted - the backend recomputes everything from the database on
every call.

## 5. Security Architecture

```
React Frontend
      |
FastAPI API (app.main)
      |
Access Service (app.services.access_service)
      |
+-----------------------------------------------+
| IAM Engine | VPC Engine | Policy Engine (+MFA) |
| Risk Engine                                    |
+-----------------------------------------------+
      |
Decision Engine (central authority - the only place
                  that produces ALLOW / DENY)
      |
SQLite Database (AccessRequest, SecurityEvent, Alert)
      |
Dashboard / Security Events / Alerts / Policies UI
```

Each engine is a pure function: it takes plain, already-resolved inputs
and returns a structured, explainable result (never a bare boolean). All
database resolution and orchestration happens in the access service; no
engine ever queries the database, and no engine ever decides the final
ALLOW/DENY outcome except the decision engine.

## 6. Core Components

| Component | Location | Responsibility |
|---|---|---|
| IAM Engine | `backend/app/engine/iam_engine.py` | Does the identity's role hold a permission matching this action/resource? |
| VPC Engine | `backend/app/engine/vpc_engine.py` | Did the request originate from the resource's trusted network boundary? |
| Policy Engine | `backend/app/engine/policy_engine.py` | Is the resource's policy enabled, is a required role satisfied, and was MFA satisfied? |
| Risk Engine | `backend/app/engine/risk_engine.py` | Deterministic 0-100 risk score from named, explainable factors. |
| Decision Engine | `backend/app/engine/decision_engine.py` | Combines every result above into the final ALLOW/DENY. |
| Access Service | `backend/app/services/access_service.py` | Resolves the database, calls every engine in order, persists the outcome. |
| Policy Service | `backend/app/services/policy_service.py` | Validates and applies administrator policy edits; writes the audit trail. |
| Seed Service | `backend/app/services/seed_service.py` | Idempotent baseline catalog and demonstration-identity seeding. |

## 7. Technology Stack

**Backend:** Python, FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2.10,
pydantic-settings, Uvicorn, pytest, httpx (via FastAPI's `TestClient`).

**Frontend:** React 19, Vite 8, React Router 7, Tailwind CSS 4, Recharts,
Lucide React icons.

**Database:** SQLite (file-based, portable, part of the project's own
`data/` directory).

## 8. Security Decision Flow

```
Access Request
      |
User / Resource Resolution  (404 if either does not exist)
      |
IAM Evaluation
      |
VPC Evaluation
      |
Resource Policy Evaluation
      |
MFA Evaluation
      |
Repeated-Failure Lookup (15-minute window)
      |
Risk Calculation
      |
Decision Engine  ->  ALLOW or DENY
      |
Persist AccessRequest
      |
DENY?  -> SecurityEvent          (always, only on DENY)
HIGH/CRITICAL risk? -> Alert     (regardless of ALLOW/DENY)
      |
API Response
```

## 9. IAM Engine

Answers exactly one question: does the requesting user's role hold a
permission whose action and resource pattern match this request? Matching
supports exact strings and shell-style wildcards (`fnmatch`), so a single
permission such as `action="*", resource_pattern="*"` grants broad
(administrator) access. The IAM engine never looks at network, MFA, or
risk - a valid IAM PASS is only ever the first of six required checks.

## 10. VPC Engine

Answers exactly one question: did the request originate from the network
the resource's active policy currently trusts? A resource whose policy
does not require a trusted VPC (for example a `PUBLIC` resource) always
passes this check. For a protected resource, the source VPC must match
the specific VPC configured on that resource's policy - not merely "any
trusted VPC." This is deliberately sourced from the database `Policy`
row (with the resource's own configuration as a fallback when no policy
row exists), so that an administrator's live policy edit changes VPC
evaluation on the very next request, with no code change.

## 11. MFA Evaluation

A resource whose policy does not require MFA always passes. A resource
that does require MFA fails this check, and is denied, if the request
did not provide it - independently of whether IAM or VPC passed.

## 12. Risk Engine

A transparent, deterministic, rule-based score - no machine learning, no
hidden weights. See [`docs/research/SECURITY_DECISION_MODEL.md`](docs/research/SECURITY_DECISION_MODEL.md)
for the full formula and worked examples.

## 13. Dynamic Policy Engine

Resource policies (`Policy` rows) are the authoritative, administrator
-editable source of a resource's trusted VPC, MFA requirement, external
-access setting, maximum risk score, required role, and enabled state.
They are read from the database fresh on every single access evaluation
- nothing is cached. An administrator can edit a policy through the
Policy Management page (`PUT /api/policies/{id}`), and the very next
access request is evaluated against the new value. See
[`docs/research/DYNAMIC_POLICY_EVALUATION.md`](docs/research/DYNAMIC_POLICY_EVALUATION.md)
for the full worked demonstration.

## 14. Security Events

Every denied access request creates exactly one `SecurityEvent` row
(`event_type`, e.g. `BLOCKED_DATABASE_ACCESS`; `severity` = the request's
risk level; `action_taken="BLOCKED"`; full context: user, source IP,
source VPC, resource, risk score, and a human-readable description).
Every policy change also creates a `SecurityEvent`
(`event_type="POLICY_CHANGED"`, `severity="HIGH"`,
`action_taken="POLICY_UPDATED"`) describing exactly which field changed,
from what value, to what value.

## 15. Alerts

Any request assessed as `HIGH` or `CRITICAL` risk - allowed or denied -
creates exactly one `Alert` (severity matches the risk level, status
starts `OPEN`). Alerts are linked to their originating request via
`access_request_id`, which is how the frontend can definitively confirm
an alert was created rather than merely assuming it.

## 16. Attack Simulator

A dedicated page (`/simulator`) with five real, backend-verified
scenarios plus a dedicated sixth ("Trusted Identity, Untrusted Network")
demonstrating that IAM permission alone is not sufficient. Every scenario
submits a real `POST /api/access/request`; the frontend never computes or
fakes a decision, a risk score, or a PASS/FAIL result - every value shown
is the live API response.

## 17. Database

SQLite, at `data/cloud_security.db`, resolved dynamically from
`backend/app/core/paths.py` (never a hardcoded path). Tables: `roles`,
`users`, `permissions`, `resources`, `vpcs`, `policies`,
`access_requests`, `security_events`, `alerts`, `schema_version`. A
lightweight schema-version mechanism (`app/db/database.py`) guarantees
that normal startup never drops a table or deletes data, and that an
incompatible on-disk schema fails startup loudly instead of being
silently recreated. See [`docs/architecture/PROJECT_STRUCTURE.md`](docs/architecture/PROJECT_STRUCTURE.md).

## 18. API

A full REST API under `/api` - access evaluation, catalog (users, roles,
permissions, resources, VPCs, policies), security events, alerts, a
dashboard summary, and policy management. See
[`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) for every endpoint.

## 19. Frontend

A React single-page application: Dashboard, Access Requests (with a
detail modal and the full decision pipeline visualized), IAM, VPC
Security, Storage, Security Events, Alerts, Policies (live editor with a
confirm-before-save safety step for sensitive fields), and the Attack
Simulator.

## 20. Testing

**82 backend tests** (`pytest`, run from `backend/`), covering IAM, VPC,
MFA, risk, policy, dynamic policy evaluation, audit and alert integrity,
input validation, injection resistance, mass-assignment resistance,
database integrity, and database-safety/persistence behavior. See
[`docs/research/RESULTS.md`](docs/research/RESULTS.md).

## 21. Portability

The project can be moved to a different drive or folder without any
source change: every path is resolved dynamically from
`backend/app/core/paths.py`, never from the terminal's working directory
or a hardcoded string. `python tests/verify_portability.py` runs 17
checks (project-root detection, cwd-independence, a simulated moved
project, every named path, and a scan of every source/config file for
hardcoded machine-specific paths) - currently **17/17 PASS**.

## 22. Project Structure

See [`docs/architecture/PROJECT_STRUCTURE.md`](docs/architecture/PROJECT_STRUCTURE.md)
for the full annotated directory tree.

## 23. Installation

Requires Python 3.10+ and Node.js.

```bat
setup.bat
```

Then, from `backend/`:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

And from `frontend/`:

```bash
npm install
```

Copy `.env.example` to `.env` (root and/or `frontend/`) for local
overrides if needed. `.env` is git-ignored and must never contain real
secrets or cloud credentials - this project does not use any.

## 24. Running the Project

```bat
start_all.bat
```

or individually:

```bat
start_backend.bat
start_frontend.bat
```

The backend serves on `http://127.0.0.1:8000` (interactive API docs at
`/api/docs`); the frontend dev server on `http://127.0.0.1:5173`. The
database and reference catalog (roles, users, resources, VPCs, policies,
including the `contractor01` demonstration identity) are created and
seeded automatically on first startup, and preserved on every subsequent
startup.

## 25. Example Scenarios

**Legitimate access (ALLOW):** `developer01` requests `GetObject` on
`project-data` from `vpc-development` with MFA - IAM PASS, VPC PASS, MFA
PASS, low risk, **ALLOW**.

**Contextual denial despite valid IAM (DENY):** `contractor01` (a role
with genuine, real `GetObject` permission on `financial-records`)
requests it from an external network without MFA - **IAM PASS**, VPC
FAIL, MFA FAIL, CRITICAL risk, **DENY**. This is the project's central
research demonstration: a valid IAM permission alone did not grant
access.

**Dynamic policy change:** the administrator changes
`financial-records-policy`'s trusted VPC from `vpc-finance` to
`vpc-development` through the Policy Management page; the very next
request from `vpc-development` is evaluated against the new value with
no code change, then the policy is restored.

## 26. Security Limitations

This is a controlled local simulation, not a production system. See
[`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md#28-limitations)
and [`THREAT_MODEL.md`](THREAT_MODEL.md) for the full, explicit list -
in summary: no real AWS integration, no real cloud credentials,
rule-based (not ML-based) risk scoring, no production-grade rate
limiting, SQLite rather than a production distributed database, no
production identity provider, and no real cloud telemetry.

## 27. Future Work

AWS IAM/VPC-endpoint integration, S3 integration, CloudTrail ingestion,
real-time event streaming, ML-based anomaly detection, production rate
limiting, a distributed database, identity-provider integration,
policy-as-code, and Terraform/IaC integration. See
[`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md#29-future-improvements).

## 28. Research Relevance

CloudContextGuard operationalizes a core zero-trust principle - "never
trust, always verify," applied specifically to cloud storage access - as
a working, testable system rather than a slide. It gives a concrete,
reproducible answer to "what happens to a request with a stolen but
genuinely valid credential, from an unexpected network, without MFA?"
and demonstrates that dynamic, database-driven policy is a viable
mechanism for enforcing contextual IAM restrictions without redeploying
code.

## Documentation Index

- [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) - full project report
- [`THREAT_MODEL.md`](THREAT_MODEL.md) - the seven simulated threats
- [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md) - every endpoint
- [`docs/architecture/PROJECT_STRUCTURE.md`](docs/architecture/PROJECT_STRUCTURE.md)
- [`docs/diagrams/`](docs/diagrams/) - architecture, authorization-flow, threat-model diagrams
- [`docs/research/`](docs/research/) - decision model, dynamic policy evaluation, methodology, results
- [`docs/presentation/`](docs/presentation/) - presentation guide, demo script, viva questions
