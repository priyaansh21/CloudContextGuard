# Security Decision Model

This document explains the exact, implemented decision model used by
CloudContextGuard. It documents what the code actually does
(`backend/app/engine/risk_engine.py`, `backend/app/engine/decision_engine.py`)
- no alternative or hypothetical formula is presented.

## The Combined Model

```
IDENTITY + IAM PERMISSION + NETWORK CONTEXT + RESOURCE POLICY + MFA + RISK
                                    =
                            FINAL DECISION
```

Each term is evaluated independently by its own engine
(`iam_engine.py`, `vpc_engine.py`, `policy_engine.py`, `risk_engine.py`),
and only the decision engine (`decision_engine.py`) combines the results
into a final `ALLOW` or `DENY`. No engine other than the decision engine
ever produces a final decision.

## Risk Formula (as implemented)

Each factor is independent and additive; a request can accumulate any
combination of the factors below, in this order of evaluation:

| Factor | Points | Trigger condition (`risk_engine.calculate_risk`) |
|---|---|---|
| External network | **+40** | The VPC check failed for this request (`vpc_check_failed=True`). |
| CONFIDENTIAL resource | **+30** | The resource's classification is `CONFIDENTIAL`. |
| RESTRICTED resource | **+40** | The resource's classification is `RESTRICTED`. (Mutually exclusive with CONFIDENTIAL - a resource has one classification.) |
| Missing MFA | **+30** | MFA is required for this resource and was not provided. |
| Unknown/untrusted source | **+20** | The source network is not a known, trusted VPC. |
| Repeated failed requests | **+10** | Two or more denied requests by the same user in the last 15 minutes. |
| Suspicious request | **+20** | `request_type == "SUSPICIOUS"`. |

```python
raw_score = sum(factor.points for factor in triggered_factors)
score = min(raw_score, 100)
```

The score is capped at 100 - it is never allowed to exceed 100 regardless
of how many factors are triggered simultaneously.

## Risk Levels

| Score range | Level |
|---|---|
| 0-29 | LOW |
| 30-59 | MEDIUM |
| 60-79 | HIGH |
| 80-100 | CRITICAL |

Implemented as `LEVEL_THRESHOLDS = ((80, "CRITICAL"), (60, "HIGH"),
(30, "MEDIUM"), (0, "LOW"))` in `risk_engine.py`, evaluated top-down (the
first threshold the score meets or exceeds determines the level).

## Decision Thresholds (as implemented)

Implemented in `decision_engine.py::decide`, in this exact priority
order:

1. **IAM fails** -> `DENY` immediately (no other check is consulted for
   the decision itself, though all other checks still run and are
   reported).
2. **Resource policy fails** (disabled, or a required role not
   satisfied) -> contributes to `DENY`.
3. **Protected resource requires a trusted VPC and the VPC check
   failed** -> contributes to `DENY`.
4. **MFA is required and failed** -> contributes to `DENY`.
5. **External access is not permitted and the source is external**
   -> contributes to `DENY`.
6. **Risk score >= 80** -> contributes to `DENY` (reason names it
   CRITICAL).
7. **Risk score >= 60** -> contributes to `DENY` (reason names it
   HIGH).
8. **A policy-specific `max_risk_score` is configured and the score
   exceeds it** (only checked if steps 6-7 did not already deny) ->
   contributes to `DENY` as an additional safeguard.
9. **None of the above** -> `ALLOW`.

If one or more of steps 2-8 apply, the final decision is `DENY` and the
response `reason` is composed from every failing check's own reason
(for example: *"IAM authorization succeeded, but the request originated
outside the trusted VPC and the protected resource requires MFA and the
request was assessed as CRITICAL risk (score 100)."*) - not a fixed
template disconnected from what actually happened.

## Worked Example

Request: `developer01`, `GetObject`, `financial-records`, source VPC
`external`, MFA not provided, `request_type="SUSPICIOUS"`.

| Factor | Triggered? | Points |
|---|---|---|
| External network | yes (VPC check fails: `financial-records` requires `vpc-finance`) | 40 |
| CONFIDENTIAL resource | yes (`financial-records` is CONFIDENTIAL) | 30 |
| Missing MFA | yes (required, not provided) | 30 |
| Unknown/untrusted source | yes (`external` is not a trusted VPC) | 20 |
| Suspicious request | yes | 20 |
| **Raw total** | | **140** |
| **Capped score** | | **100 (CRITICAL)** |

Decision: `developer01` also has no IAM permission on
`financial-records`, so IAM already fails independently (rule 1) - the
final decision is `DENY` regardless of the risk score. For the
project's central demonstration of risk alone reinforcing a contextual
denial where IAM does pass, see
[`DYNAMIC_POLICY_EVALUATION.md`](DYNAMIC_POLICY_EVALUATION.md) and
[`RESULTS.md`](RESULTS.md).
