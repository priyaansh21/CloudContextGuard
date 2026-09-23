# CloudContextGuard - Threat Model

All threats below are realized and tested entirely within
CloudContextGuard's own local simulation: a synthetic user submits a
request to `POST /api/access/request`, and the real IAM, VPC, MFA,
policy, and risk engines evaluate it. No real network, no real cloud
account, and no real credential is ever involved. Where a threat is
exercised by the Attack Simulator, the corresponding scenario ID from
`frontend/src/data/simulationScenarios.js` is noted.

## T1: Compromised Developer Credentials

| | |
|---|---|
| **Threat** | An attacker has obtained a valid developer identity's username (in this simulation, no password/token exists to steal - the identity itself is treated as compromised) and attempts to use it from an unexpected location. |
| **Attack condition** | `developer01` (a real, valid identity with real IAM permissions) issues a request for a resource it does have permission for, but from an untrusted external network without MFA. |
| **Affected control** | VPC boundary, MFA. |
| **Detection** | `VPCResult.result == "FAIL"`; `MFAResult.result == "FAIL"`; risk factors `External network` (+40) and `Unknown/untrusted source` (+20) are recorded. |
| **Response** | `AccessRequest` persisted with `final_decision="DENY"`; `SecurityEvent` created (`action_taken="BLOCKED"`); `Alert` created if risk reaches HIGH/CRITICAL. |
| **Expected result** | DENY. Simulator scenario: `stolen-credential` ("Stolen Credential Attack"). |

## T2: Access From Outside the Trusted VPC

| | |
|---|---|
| **Threat** | A request for a genuinely IAM-permitted, CONFIDENTIAL resource originates from a network the resource's policy does not trust. |
| **Attack condition** | `contractor01` (a role with real `GetObject` permission on `financial-records`) requests it from `external` or from a VPC other than the one the policy currently designates. |
| **Affected control** | VPC boundary (`vpc_engine.evaluate_vpc`), independent of IAM. |
| **Detection** | `IAMResult.result == "PASS"` but `VPCResult.result == "FAIL"`, `expected_vpc` != `actual_vpc`. |
| **Response** | DENY regardless of IAM outcome; `SecurityEvent` created. |
| **Expected result** | DENY. This is the project's central demonstration: valid IAM permission is not sufficient. Simulator scenario: `trusted-identity-untrusted-network` ("Trusted Identity, Untrusted Network") and `external-confidential-storage`. |

## T3: Missing MFA

| | |
|---|---|
| **Threat** | A request for an MFA-required resource is made without MFA, even from a network the policy does trust. |
| **Attack condition** | `finance01` requests `financial-records` from `vpc-finance` (the correct trusted VPC) with `mfa=false`. |
| **Affected control** | MFA evaluation (`policy_engine.evaluate_mfa`), independent of VPC. |
| **Detection** | `MFAResult.required == True`, `MFAResult.provided == False`, `MFAResult.result == "FAIL"`. |
| **Response** | DENY even though IAM and VPC both passed; `SecurityEvent` created. |
| **Expected result** | DENY. |

## T4: Unauthorized Resource Access

| | |
|---|---|
| **Threat** | A valid, active identity attempts an action on a resource its role was never granted permission for. |
| **Attack condition** | `developer01` (`DeveloperRole`, permissioned only for `project-data` and `public-assets`) requests `GetObject` on `credentials-vault`. |
| **Affected control** | IAM (`iam_engine.evaluate_iam`). |
| **Detection** | `IAMResult.result == "FAIL"`, `matched_permission == null`. |
| **Response** | DENY at the earliest evaluation stage (decision engine's first rule); `SecurityEvent` created. |
| **Expected result** | DENY. |

## T5: Privilege Escalation Attempt

| | |
|---|---|
| **Threat** | A low-privilege identity attempts an administrative-style action its role does not permit, on a RESTRICTED resource. |
| **Attack condition** | `developer01` requests `DeleteObject` on `credentials-vault` (a `RESTRICTED` resource whose policy additionally requires `AdminRole`). |
| **Affected control** | IAM (action not permitted) and, redundantly, resource policy (`required_role` gate). |
| **Detection** | `IAMResult.result == "FAIL"`; `resource_result.result == "FAIL"` (`Resource policy requires the 'AdminRole' role`). |
| **Response** | DENY; `SecurityEvent` created; risk assessed CRITICAL (RESTRICTED classification `+40`, plus network/MFA factors). |
| **Expected result** | DENY. Simulator scenario: `privilege-escalation` ("Privilege Escalation Attempt"). |

## T6: Repeated Unauthorized Requests

| | |
|---|---|
| **Threat** | The same identity repeatedly submits denied requests against a resource in a short window - a pattern consistent with automated probing or brute-force-style access attempts. |
| **Attack condition** | `developer01` submits three or more sequential denied requests against `credentials-vault` within 15 minutes. |
| **Affected control** | Risk engine's repeated-failure factor (`risk_engine.calculate_risk`, `repeated_failed_count`), computed from real `AccessRequest` history (`access_service.py`, 15-minute window, `final_decision == "DENY"`). |
| **Detection** | From the second denied attempt onward, risk factor `Repeated failed requests` (+10) appears, with a factor reason naming the exact count observed (for example, `"3 denied requests by developer01 in the last 15 minutes"`). |
| **Response** | Risk score escalates with each additional failure; DENY persists across all attempts (IAM already fails independently in this scenario). |
| **Expected result** | Escalating risk score across repeated attempts; DENY throughout. Simulator scenario: `repeated-unauthorized` ("Repeated Unauthorized Requests", 3 sequential real API calls). |

## T7: Sensitive Storage Exposure

| | |
|---|---|
| **Threat** | A resource's policy is misconfigured to allow external access on a CONFIDENTIAL or RESTRICTED resource, creating a latent exposure risk even before any specific attack request is made. |
| **Attack condition** | An administrator sets `external_access_allowed=true` on a policy whose resource classification is `CONFIDENTIAL` or `RESTRICTED` (via `PUT /api/policies/{id}`). |
| **Affected control** | Policy configuration review (the Policies page cross-references live resource classification against the policy's `external_access_allowed` field). |
| **Detection** | The Policies page (`frontend/src/pages/Policies.jsx`) displays a visible warning, "External access enabled on sensitive resource," and counts the policy in the "High-Risk" summary tile - computed from real, live policy and resource data. |
| **Response** | This is a configuration warning, not an automatic denial - the actual access decision still follows the ordinary decision-engine rules on the next real request; CloudContextGuard does not introduce undocumented automatic-denial behavior for this case. |
| **Expected result** | Visible administrative warning; no fabricated denial. |

## Scope Statement

Every threat above is demonstrated by submitting a real, structurally
valid HTTP request to the running FastAPI application and observing the
genuine response, database state, and (where applicable) frontend
rendering. No destructive testing, no real network scanning, no real
credential attack, and no interaction with any system outside this
project's own local database was performed or is supported.
