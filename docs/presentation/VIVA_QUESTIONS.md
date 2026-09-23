# Viva Questions

Concise, technically accurate answers grounded in the actual
implementation. Where a number or field name is cited, it matches the
real source code.

## Project Basics

**1. What is CloudContextGuard?**
A locally-run simulation of a context-aware cloud authorization system:
a FastAPI backend, SQLite database, and React frontend that together
demonstrate that IAM permission alone should not grant cloud resource
access.

**2. What problem does it solve?**
It demonstrates and tests an authorization model where network origin,
MFA, and risk are enforced independently of IAM permission, so a stolen
or misused-but-genuinely-valid credential can still be denied.

**3. Is this connected to real AWS?**
No. No real cloud account, credential, or network is used anywhere in
the project. Every user, resource, VPC, and policy is a row in a local
SQLite database.

**4. What technologies were used?**
Python/FastAPI/SQLAlchemy/Pydantic on the backend; React/Vite/Tailwind
CSS/Recharts on the frontend; SQLite as the database.

**5. How is the project validated?**
82 automated `pytest` tests, a 17-point portability check, and live
demonstration against the running application.

## Cloud Security

**6. Why is IAM-only authorization insufficient?**
Because it grants access based solely on possessing a credential,
regardless of where the request came from or whether an additional
factor was verified - exactly the gap a stolen credential exploits.

**7. What is "context-aware" access control?**
Authorization that considers request context (network origin, MFA,
computed risk) in addition to identity permission, rather than
permission alone.

**8. What is the principle of least privilege, and is it demonstrated
here?**
Granting only the permissions needed for a role's function. Demonstrated
by the seeded roles: `DeveloperRole` can only act on `project-data` and
`public-assets`, `FinanceRole` only on `financial-records`, etc.

**9. How does this project relate to defense in depth?**
Each of IAM, VPC, MFA, and risk is an independent layer; a failure of
any single layer can still deny access even if every other layer
passed.

## IAM

**10. How does the IAM engine work?**
`iam_engine.evaluate_iam` checks the user exists and is active, has a
role, and that role holds a permission whose action and resource pattern
(matched with `fnmatch`, supporting `*` wildcards) match the request.

**11. What does the IAM engine return?**
A structured `IAMResult` - `allowed`, `result` (`PASS`/`FAIL`), `reason`,
`matched_permission` - never a bare boolean.

**12. Can an inactive user ever pass IAM?**
No - `user_is_active` is checked explicitly and inactive users always
fail IAM, independent of their permissions.

**13. How are wildcard permissions implemented?**
Via Python's `fnmatch`, so `action="*", resource_pattern="*"` (used for
`AdminRole`) matches anything.

## VPC

**14. How does the VPC engine determine the "trusted" VPC for a
resource?**
From the resource's active `Policy` row's `trusted_vpc_id` (with the
resource's own `trusted_vpc_id` as a fallback if no policy exists) -
resolved fresh from the database on every request.

**15. What happens if a resource requires no VPC boundary?**
The VPC check passes unconditionally (`requires_trusted_vpc=False`),
regardless of the source network - used for `PUBLIC` resources like
`public-assets`.

**16. Does "any trusted VPC" satisfy a resource's VPC requirement?**
No - the source VPC must match the *specific* VPC configured for that
resource's policy, not merely be trusted in general.

**17. What determines whether a VPC itself is "trusted"?**
The `vpcs.is_trusted` boolean, seeded per VPC (e.g. `vpc-finance` is
trusted; `external` is not).

## Zero Trust

**18. How does this project embody zero-trust principles?**
"Never trust, always verify": a valid identity is never treated as
sufficient; every request is independently re-evaluated against network,
MFA, and risk regardless of past requests or identity validity.

**19. What is the project's single clearest zero-trust demonstration?**
`contractor01`, holding a real IAM permission, denied access from an
untrusted network without MFA - IAM PASS, but overall DENY.

## MFA

**20. How is MFA enforced?**
`policy_engine.evaluate_mfa`: if the resource's policy requires MFA and
the request did not provide it, the check fails and denies the request,
independent of IAM or VPC outcome.

**21. Does MFA absence always cause a denial?**
No - only when the resource's policy requires MFA. A resource that does
not require MFA passes this check regardless of whether MFA was
provided.

**22. Where is the MFA requirement configured?**
On the resource's `Policy` row (`mfa_required`), administrator-editable
via `PUT /api/policies/{id}`.

## Risk Scoring

**23. What kind of risk scoring is used?**
Deterministic, rule-based, additive point values per named factor - not
machine learning.

**24. List the risk factors and their point values.**
External network +40, CONFIDENTIAL resource +30, RESTRICTED resource
+40, Missing required MFA +30, Untrusted source +20, Repeated failures
(2+ in 15 minutes) +10, Suspicious request +20.

**25. What is the maximum possible risk score?**
100 - the raw sum is capped with `min(score, 100)`.

**26. What are the risk level bands?**
0-29 LOW, 30-59 MEDIUM, 60-79 HIGH, 80-100 CRITICAL.

**27. At what risk score does the decision engine deny a request purely
on risk?**
60 or above (both the 60 and 80 thresholds independently deny; 80 is
called out separately in the reason text as CRITICAL).

## Dynamic Policies

**28. What makes a policy "dynamic" in this system?**
It is a database row, re-read on every single request; an administrator
can change it through the API/UI and the very next request is evaluated
against the new value, with no code change or restart.

**29. What fields of a policy are administrator-editable?**
`name`, `description`, `required_role`, `trusted_vpc`, `mfa_required`,
`max_risk_score`, `external_access_allowed`, `is_enabled`.

**30. What fields can never be set by the client?**
`id`, `resource_id`, `created_at`, `updated_at` - not present on the
`PolicyUpdate` schema at all, so any client-submitted value for them is
silently ignored.

**31. What happens when a policy is updated?**
`policy_service.update_policy` validates the referenced role/VPC exist,
applies the change, and records a `SecurityEvent`
(`event_type="POLICY_CHANGED"`) describing exactly which fields changed.

## FastAPI

**32. Why FastAPI?**
Automatic request/response validation via Pydantic, automatic OpenAPI
documentation, and async-capable routing, with minimal boilerplate.

**33. How is input validated?**
Pydantic schemas (`AccessRequestIn`, `PolicyUpdate`) declare exact,
typed fields; anything missing or mistyped returns `422` automatically;
unrecognized extra fields are silently ignored, not applied.

**34. How are errors handled?**
Domain-specific exceptions (e.g. `UserNotFoundError`,
`PolicyValidationError`) are caught at the route layer and mapped to
`404`/`422`; a global exception handler returns a generic `500` for
anything unhandled, without leaking stack traces.

## React

**35. Does the frontend ever make a security decision?**
No - every decision, risk score, and PASS/FAIL value shown is read
directly from an API response; the frontend has no authorization logic.

**36. How does the frontend know about a new security event or alert
after a simulation runs?**
It queries `GET /api/security/events` / `GET /api/alerts` and matches by
`access_request_id`, only claiming an event/alert exists if the API
confirms it.

**37. What state management approach is used?**
Local component state and a small set of custom hooks (`useApi`,
`useHealthStatus`) - no global state library; each page fetches its own
data.

## SQLite

**38. Why SQLite rather than a client-server database?**
It requires no separate server process, keeps the project fully
portable and self-contained, and is sufficient for this simulation's
scale; documented explicitly as a limitation for production use.

**39. How are foreign keys enforced?**
`PRAGMA foreign_keys=ON` is executed on every new connection via a
SQLAlchemy `connect` event listener.

**40. How does the project avoid destructive schema changes on
startup?**
A `schema_version` table and a `CURRENT_SCHEMA_VERSION` constant; normal
startup never drops a table or deletes data, and a version mismatch
raises an error and refuses to start rather than auto-recreating the
database.

## REST API

**41. What is the single authorization entry point?**
`POST /api/access/request`.

**42. Can a client force an ALLOW decision?**
No - `AccessRequestIn` has no `decision` field at all; any such field
submitted is ignored, and the backend always recomputes the decision
from the database.

**43. How is pagination/limiting handled on list endpoints?**
A `limit` query parameter, default 50, bounded 1-500 (`422` outside that
range).

## Threat Modeling

**44. Name the seven threats modeled.**
Compromised developer credentials, access from outside the trusted VPC,
missing MFA, unauthorized resource access, privilege escalation,
repeated unauthorized requests, sensitive storage exposure.

**45. How is "privilege escalation" demonstrated?**
`developer01` (`DeveloperRole`) attempting `DeleteObject` on
`credentials-vault` (`RESTRICTED`, requiring `AdminRole`) - denied by
IAM and, redundantly, by the resource policy's required-role gate.

## Security Events and Alerts

**46. When is a SecurityEvent created?**
On every denied access request, and on every applied policy change -
never on an allowed access request.

**47. When is an Alert created, and can it duplicate?**
For any request (allowed or denied) assessed HIGH or CRITICAL risk;
`access_request_id` is unique on the `alerts` table, guaranteeing at
most one alert per request.

## Testing

**48. How many backend tests exist, and what do they cover?**
82, covering health/liveness, IAM/VPC/MFA/risk/policy behavior, policy
management and dynamic-policy evaluation, database safety/persistence,
and a comprehensive security-validation pass (injection resistance,
mass-assignment resistance, audit/alert integrity, database integrity).

**49. Do the tests use a mocked database?**
No - they run against the project's real, portable SQLite database via
FastAPI's `TestClient`, matching the project's stated no-mocking
convention.

## Portability

**50. What makes the project portable?**
Every filesystem path is derived at runtime from
`backend/app/core/paths.py`'s own file location, never from a hardcoded
string or the terminal's working directory; `verify_portability.py`
independently verifies this with 17 checks.

## Limitations

**51. What is explicitly out of scope?**
Real AWS integration, real credentials, ML-based risk scoring,
production-grade rate limiting, a production distributed database, and a
real identity provider - all documented in
`PROJECT_DOCUMENTATION.md` and `THREAT_MODEL.md`.

## Future Work

**52. What would be the first step toward production readiness?**
Integrating with real AWS IAM and VPC-endpoint context so that policy
decisions here could be mapped onto real infrastructure, alongside
production-grade rate limiting and a real identity provider.
