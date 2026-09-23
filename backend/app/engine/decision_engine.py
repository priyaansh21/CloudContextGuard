"""
Central decision engine.

The final authorization authority. Combines the IAM, VPC, resource policy,
MFA and risk results into a single ALLOW/DENY decision with a human-readable
explanation. This is the only place a final decision is made - no other
engine or the access service should decide ALLOW/DENY on its own.

Core principle demonstrated here: a valid identity with a valid IAM
permission (AUTHENTICATION/IDENTITY) does not automatically receive access -
network context, resource policy, MFA and risk (AUTHORIZATION/CONTEXT) can
still deny it.

Priority order:
    1. IAM fails                                           -> DENY
    2. Resource policy fails (disabled or role gate)        -> DENY
    3. Protected resource requires trusted VPC and VPC fails -> DENY
    4. MFA required and MFA fails                           -> DENY
    5. External access prohibited and source is external    -> DENY
    6. Risk score >= 80 (CRITICAL)                           -> DENY
    7. Risk score >= 60 (HIGH)                               -> DENY
    8. Otherwise                                             -> ALLOW

A policy-specific risk threshold (``max_risk_score``), when configured, is
enforced as an additional safeguard after the fixed thresholds above.
"""

from __future__ import annotations

from app.schemas.engine_results import DecisionResult, IAMResult, MFAResult, PolicyResult, RiskResult, VPCResult


def decide(
    *,
    iam_result: IAMResult,
    vpc_result: VPCResult,
    policy_result: PolicyResult,
    mfa_result: MFAResult,
    risk_result: RiskResult,
    source_is_external: bool,
) -> DecisionResult:
    """Combine every component result into the final ALLOW/DENY decision."""
    if not iam_result.allowed:
        return DecisionResult(decision="DENY", reason=f"Access denied: {iam_result.reason}.")

    failures: list[str] = []

    if not policy_result.allowed:
        failures.append(policy_result.reason.lower())

    if policy_result.trusted_vpc_required and not vpc_result.allowed:
        failures.append("the request originated outside the trusted VPC")

    if mfa_result.required and not mfa_result.allowed:
        failures.append("the protected resource requires MFA")

    if not policy_result.external_access_allowed and source_is_external:
        failures.append("external access is not permitted for this resource")

    risk_blocked = False
    if risk_result.score >= 80:
        failures.append(f"the request was assessed as CRITICAL risk (score {risk_result.score})")
        risk_blocked = True
    elif risk_result.score >= 60:
        failures.append(f"the request was assessed as HIGH risk (score {risk_result.score})")
        risk_blocked = True

    if not risk_blocked and policy_result.max_risk_score is not None and risk_result.score > policy_result.max_risk_score:
        failures.append(
            f"the risk score ({risk_result.score}) exceeds this resource's policy threshold "
            f"({policy_result.max_risk_score})"
        )

    if failures:
        reason = "IAM authorization succeeded, but " + " and ".join(failures) + "."
        return DecisionResult(decision="DENY", reason=reason)

    return DecisionResult(
        decision="ALLOW",
        reason="IAM, network context, resource policy, MFA and risk checks all passed.",
    )
