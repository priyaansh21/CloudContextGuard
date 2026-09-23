# Dynamic Policy Evaluation

This document records a real, executed experiment demonstrating that
CloudContextGuard's authorization policy is read from the database on
every request - not compiled into, or cached by, the application code -
so that an administrator's live policy change takes effect on the very
next access evaluation with no code change and no restart.

## Mechanism

`backend/app/services/access_service.py::evaluate_access_request` queries
the `Policy` table (`db.query(Policy).filter_by(resource_id=resource.id)`)
at the start of every single evaluation, and derives the VPC boundary
(`policy.trusted_vpc_id`), the MFA requirement, the external-access
setting, and the maximum risk score directly from that row. Nothing in
the request path caches a policy value between requests. An
administrator's edit, applied through `PUT /api/policies/{id}`
(`backend/app/api/policies.py`, validated and persisted by
`backend/app/services/policy_service.py`), is committed to the database
immediately and is visible to the very next call into
`evaluate_access_request` - there is no reload, restart, or cache
-invalidation step involved.

## Experiment

Resource under test: `financial-records` (classification `CONFIDENTIAL`).
Identity under test: `contractor01` (`ContractorRole`), which holds a
genuine, real `GetObject` permission on `financial-records`.

### Step 1 - Baseline policy

`financial-records-policy`: `trusted_vpc = "vpc-finance"`,
`mfa_required = true`, `external_access_allowed = false`,
`is_enabled = true`.

### Step 2 - Baseline request (external network)

Request: `contractor01`, `GetObject`, `financial-records`, source VPC
`external`, MFA provided.

Actual verified result:

```json
"iam_result": { "result": "PASS" },
"vpc_result": { "result": "FAIL", "expected_vpc": "vpc-finance", "actual_vpc": "external" },
"decision": "DENY"
```

IAM passed - the identity genuinely has the permission - but VPC failed,
because the request did not originate from `vpc-finance`. Final decision:
**DENY**.

### Step 3 - Policy changed

`PUT /api/policies/{id}` with `trusted_vpc = "vpc-development"` (all
other fields unchanged). Verified response: `"trusted_vpc":
"vpc-development"`. This also recorded a `SecurityEvent`
(`event_type="POLICY_CHANGED"`, `severity="HIGH"`,
`action_taken="POLICY_UPDATED"`, description: `"Policy
'financial-records-policy' updated: Trusted VPC: vpc-finance ->
vpc-development"`).

### Step 4 - Request from the newly trusted VPC

Request: `contractor01`, `GetObject`, `financial-records`, source VPC
`vpc-development`, MFA provided - submitted immediately after Step 3,
with no application restart.

Actual verified result:

```json
"iam_result": { "result": "PASS" },
"vpc_result": { "result": "PASS", "expected_vpc": "vpc-development", "actual_vpc": "vpc-development" },
"risk_score": 40,
"risk_level": "MEDIUM",
"decision": "ALLOW",
"reason": "IAM, network context, resource policy, MFA and risk checks all passed."
```

The VPC engine's `expected_vpc` field itself now reads
`"vpc-development"` - direct evidence that the evaluation used the
updated database value, not a stale or compiled-in one. With IAM and VPC
both passing, the remaining policy and risk controls determined the
final decision: risk reached 40 (MEDIUM: the `CONFIDENTIAL` classification
factor plus a repeated-failed-requests factor from prior denied attempts
in this same session), which is below the 60-point deny threshold, so
the request was **ALLOWED**. This final ALLOW was a genuine outcome of
the remaining controls, not a predetermined result.

### Step 5 - Policy restored

`PUT /api/policies/{id}` with `trusted_vpc = "vpc-finance"` (restoring
the original value). Verified response: `"trusted_vpc": "vpc-finance"`.

### Step 6 - Re-verification

Request: `contractor01`, `GetObject`, `financial-records`, source VPC
`external`, MFA provided.

Actual verified result:

```json
"vpc_result": { "result": "FAIL", "expected_vpc": "vpc-finance", "actual_vpc": "external" },
"decision": "DENY"
```

External access is denied again, exactly as in Step 2. All other policy
fields were independently confirmed unchanged
(`mfa_required=true`, `external_access_allowed=false`, `is_enabled=true`,
`required_role=null`, `max_risk_score=59`).

## Conclusion

The experiment directly demonstrates the required property: a policy
change made through the API is read from the database and applied to
the very next access evaluation, with no source-code change and no
restart, and the system can be returned to its original, secure
configuration by the same mechanism.
