"""
Resource policy engine.

Evaluates the resource's own configured security requirements - enablement
and the (optional) additional role gate - and exposes the rest of its
configuration (trusted-VPC requirement, MFA requirement, max risk score,
external access policy) for the decision engine and risk engine to consume.
This intentionally does not re-check the requesting user's granular
action/resource permission - that is the IAM engine's job.

MFA evaluation also lives here: MFA is a property of the resource's policy,
not a separate subsystem.
"""

from __future__ import annotations

from app.schemas.engine_results import MFAResult, PolicyResult


def evaluate_policy(
    *,
    policy_exists: bool,
    policy_name: str | None,
    is_enabled: bool,
    required_role_name: str | None,
    actual_role_name: str | None,
    trusted_vpc_required: bool,
    mfa_required: bool,
    external_access_allowed: bool,
    max_risk_score: int | None,
) -> PolicyResult:
    """Evaluate the resource's policy: is it enabled, and does the role gate pass?"""
    if not policy_exists:
        return PolicyResult(
            allowed=False,
            result="FAIL",
            reason="No policy is configured for this resource",
            is_enabled=False,
            required_role=required_role_name,
            trusted_vpc_required=trusted_vpc_required,
            mfa_required=mfa_required,
            external_access_allowed=external_access_allowed,
            max_risk_score=max_risk_score,
        )

    if not is_enabled:
        return PolicyResult(
            allowed=False,
            result="FAIL",
            reason=f"Policy '{policy_name}' is disabled",
            is_enabled=False,
            required_role=required_role_name,
            trusted_vpc_required=trusted_vpc_required,
            mfa_required=mfa_required,
            external_access_allowed=external_access_allowed,
            max_risk_score=max_risk_score,
        )

    if required_role_name and actual_role_name != required_role_name:
        return PolicyResult(
            allowed=False,
            result="FAIL",
            reason=f"Resource policy requires the '{required_role_name}' role",
            is_enabled=True,
            required_role=required_role_name,
            trusted_vpc_required=trusted_vpc_required,
            mfa_required=mfa_required,
            external_access_allowed=external_access_allowed,
            max_risk_score=max_risk_score,
        )

    return PolicyResult(
        allowed=True,
        result="PASS",
        reason="Resource policy requirements satisfied",
        is_enabled=True,
        required_role=required_role_name,
        trusted_vpc_required=trusted_vpc_required,
        mfa_required=mfa_required,
        external_access_allowed=external_access_allowed,
        max_risk_score=max_risk_score,
    )


def evaluate_mfa(*, required: bool, provided: bool) -> MFAResult:
    """Evaluate multi-factor authentication against the resource's requirement."""
    if not required:
        return MFAResult(
            required=False,
            provided=provided,
            result="PASS",
            reason="MFA is not required for this resource",
        )

    if provided:
        return MFAResult(
            required=True,
            provided=True,
            result="PASS",
            reason="MFA was required and provided",
        )

    return MFAResult(
        required=True,
        provided=False,
        result="FAIL",
        reason="MFA is required for this resource but was not provided",
    )
