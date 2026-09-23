"""
Structured result schemas returned by each security engine.

Every engine returns one of these models instead of a bare boolean, so every
authorization decision remains explainable end-to-end.
"""

from __future__ import annotations

from pydantic import BaseModel


class IAMResult(BaseModel):
    """Outcome of identity/permission evaluation."""

    allowed: bool
    result: str  # "PASS" | "FAIL"
    reason: str
    matched_permission: str | None = None


class VPCResult(BaseModel):
    """Outcome of network-context (trusted VPC boundary) evaluation."""

    allowed: bool
    result: str  # "PASS" | "FAIL"
    reason: str
    expected_vpc: str | None = None
    actual_vpc: str | None = None


class PolicyResult(BaseModel):
    """Outcome of resource policy evaluation (role gate, enablement, thresholds)."""

    allowed: bool
    result: str  # "PASS" | "FAIL"
    reason: str
    is_enabled: bool
    required_role: str | None = None
    trusted_vpc_required: bool
    mfa_required: bool
    external_access_allowed: bool
    max_risk_score: int | None = None


class MFAResult(BaseModel):
    """Outcome of multi-factor authentication evaluation."""

    required: bool
    provided: bool
    result: str  # "PASS" | "FAIL"
    reason: str

    @property
    def allowed(self) -> bool:
        return self.result == "PASS"


class RiskFactor(BaseModel):
    """A single, explainable contributor to the overall risk score."""

    name: str
    points: int
    reason: str


class RiskResult(BaseModel):
    """Deterministic, rule-based risk assessment."""

    score: int
    level: str  # LOW | MEDIUM | HIGH | CRITICAL
    factors: list[RiskFactor]


class DecisionResult(BaseModel):
    """Final authorization outcome produced by the decision engine."""

    decision: str  # "ALLOW" | "DENY"
    reason: str
