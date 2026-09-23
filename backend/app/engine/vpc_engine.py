"""
VPC (network context) engine.

Answers one question only: did this request originate from a network
location the resource trusts? A resource that does not require a trusted
VPC boundary (e.g. a PUBLIC resource) always passes this check; whether
external access is actually *allowed* for it is a resource-policy concern,
evaluated separately.
"""

from __future__ import annotations

from app.schemas.engine_results import VPCResult


def evaluate_vpc(
    *,
    requires_trusted_vpc: bool,
    expected_vpc_name: str | None,
    source_vpc_name: str | None,
    source_vpc_trusted: bool,
) -> VPCResult:
    """Evaluate whether the request's source VPC satisfies the resource's boundary."""
    actual_vpc = source_vpc_name or "external"

    if not requires_trusted_vpc:
        return VPCResult(
            allowed=True,
            result="PASS",
            reason="Resource does not enforce a trusted VPC boundary",
            expected_vpc=None,
            actual_vpc=actual_vpc,
        )

    if not expected_vpc_name:
        return VPCResult(
            allowed=False,
            result="FAIL",
            reason="Resource requires a trusted VPC but none is configured",
            expected_vpc=None,
            actual_vpc=actual_vpc,
        )

    if source_vpc_name == expected_vpc_name and source_vpc_trusted:
        return VPCResult(
            allowed=True,
            result="PASS",
            reason=f"Request originated from the trusted VPC '{expected_vpc_name}'",
            expected_vpc=expected_vpc_name,
            actual_vpc=actual_vpc,
        )

    return VPCResult(
        allowed=False,
        result="FAIL",
        reason="Request originated outside the trusted VPC",
        expected_vpc=expected_vpc_name,
        actual_vpc=actual_vpc,
    )
