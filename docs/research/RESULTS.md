# Results

All figures below are directly reproducible: run `pytest` from
`backend/`, `python tests/verify_portability.py` from the project root,
and `npm run build` from `frontend/`, or re-submit the two demonstration
requests described below to a running instance of the application.

## Automated Test Suite

| Suite | File | Tests |
|---|---|---|
| Health/liveness | `backend/tests/test_health.py` | 5 |
| Access control (IAM/VPC/MFA/risk/policy, contractor01) | `backend/tests/test_access_control.py` | 17 |
| Policy management (CRUD, validation, dynamic policy) | `backend/tests/test_policy_management.py` | 10 |
| Database safety (schema-version, persistence, reset) | `backend/tests/test_database_safety.py` | 9 |
| Security validation (Step 7 comprehensive pass) | `backend/tests/test_security_validation.py` | 41 |
| **Total** | | **82 passed, 0 failed** |

## Portability

`python tests/verify_portability.py`: **17/17 checks passed**, including
project-root detection independent of the working directory, a
simulated moved project folder, every named project path, and a scan of
every source/configuration file for hardcoded machine-specific paths.

## Frontend Build

`npm run build` (Vite): **passed**, no errors.

## Primary Contextual-Denial Demonstration

Request: `contractor01`, `GetObject`, `financial-records`, source VPC
`external`, MFA not provided, `request_type="SUSPICIOUS"`.

Verified result:

| Check | Result |
|---|---|
| IAM | **PASS** |
| VPC | **FAIL** |
| MFA | **FAIL** |
| Risk | **100 / CRITICAL** |
| Final decision | **DENY** |

This is the project's central finding: a genuinely valid IAM permission
(`ContractorRole` does hold `GetObject:financial-records`) was not
sufficient to grant access once network context and MFA were evaluated.
A `SecurityEvent` (`event_type="BLOCKED_DATABASE_ACCESS"`,
`action_taken="BLOCKED"`) and an `Alert` (`severity="CRITICAL"`,
`status="OPEN"`) were both created and confirmed via the API.

## Dynamic-Policy Demonstration

After changing `financial-records-policy`'s trusted VPC from
`vpc-finance` to `vpc-development`, request: `contractor01`,
`GetObject`, `financial-records`, source VPC `vpc-development`, MFA
provided.

Verified result:

| Check | Result |
|---|---|
| IAM | **PASS** |
| VPC | **PASS** |
| Risk | **40 / MEDIUM** |
| Final decision | **ALLOW** (determined by the remaining policy/risk controls, not predetermined) |

Full experiment, including the before/after/restore sequence, is
documented in
[`DYNAMIC_POLICY_EVALUATION.md`](DYNAMIC_POLICY_EVALUATION.md).

## Scope of These Results

These results describe the behavior of a local, controlled simulation
only. No finding here should be read as a claim about the security
properties of any real AWS deployment or any production system.
