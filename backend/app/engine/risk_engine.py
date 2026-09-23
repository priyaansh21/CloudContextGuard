"""
Risk engine.

A transparent, deterministic, rule-based score. No machine learning, no
unexplained weights - every point added to the score is attached to a named,
human-readable factor.
"""

from __future__ import annotations

from app.schemas.engine_results import RiskFactor, RiskResult

MAX_SCORE = 100

POINTS_EXTERNAL_NETWORK = 40
POINTS_CONFIDENTIAL_RESOURCE = 30
POINTS_RESTRICTED_RESOURCE = 40
POINTS_MISSING_MFA = 30
POINTS_UNTRUSTED_SOURCE = 20
POINTS_REPEATED_FAILURES = 10
POINTS_SUSPICIOUS_REQUEST = 20

REPEATED_FAILURE_THRESHOLD = 2  # "multiple" recent denials

LEVEL_THRESHOLDS = (
    (80, "CRITICAL"),
    (60, "HIGH"),
    (30, "MEDIUM"),
    (0, "LOW"),
)


def _risk_level(score: int) -> str:
    for threshold, level in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return "LOW"  # pragma: no cover - unreachable, thresholds cover [0, 100]


def calculate_risk(
    *,
    vpc_check_failed: bool,
    resource_classification: str | None,
    mfa_required: bool,
    mfa_provided: bool,
    source_vpc_trusted: bool,
    repeated_failed_count: int,
    request_type: str,
    username: str,
) -> RiskResult:
    """Compute a deterministic 0-100 risk score from named, explainable factors."""
    factors: list[RiskFactor] = []

    if vpc_check_failed:
        factors.append(
            RiskFactor(
                name="External network",
                points=POINTS_EXTERNAL_NETWORK,
                reason="Request failed the trusted VPC boundary check for this resource",
            )
        )

    classification = (resource_classification or "").upper()
    if classification == "CONFIDENTIAL":
        factors.append(
            RiskFactor(
                name="CONFIDENTIAL resource",
                points=POINTS_CONFIDENTIAL_RESOURCE,
                reason="Requested resource is classified CONFIDENTIAL",
            )
        )
    elif classification == "RESTRICTED":
        factors.append(
            RiskFactor(
                name="RESTRICTED resource",
                points=POINTS_RESTRICTED_RESOURCE,
                reason="Requested resource is classified RESTRICTED",
            )
        )

    if mfa_required and not mfa_provided:
        factors.append(
            RiskFactor(
                name="Missing MFA",
                points=POINTS_MISSING_MFA,
                reason="MFA is required for this resource but was not provided",
            )
        )

    if not source_vpc_trusted:
        factors.append(
            RiskFactor(
                name="Unknown/untrusted source",
                points=POINTS_UNTRUSTED_SOURCE,
                reason="Source network is not a known, trusted VPC",
            )
        )

    if repeated_failed_count >= REPEATED_FAILURE_THRESHOLD:
        factors.append(
            RiskFactor(
                name="Repeated failed requests",
                points=POINTS_REPEATED_FAILURES,
                reason=f"{repeated_failed_count} denied requests by {username} in the last 15 minutes",
            )
        )

    if request_type == "SUSPICIOUS":
        factors.append(
            RiskFactor(
                name="Suspicious request",
                points=POINTS_SUSPICIOUS_REQUEST,
                reason="Request was flagged with request_type=SUSPICIOUS",
            )
        )

    raw_score = sum(factor.points for factor in factors)
    score = min(raw_score, MAX_SCORE)

    return RiskResult(score=score, level=_risk_level(score), factors=factors)
