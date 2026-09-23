"""Request/response schemas for the access-control API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.engine_results import IAMResult, MFAResult, PolicyResult, RiskFactor, VPCResult

RequestType = Literal["NORMAL", "SUSPICIOUS", "AUTOMATED", "UNKNOWN"]


class AccessRequestIn(BaseModel):
    """A simulated access attempt submitted for evaluation."""

    user: str
    action: str
    resource: str
    source_ip: str | None = None
    source_vpc: str
    mfa: bool = False
    request_type: RequestType = "NORMAL"


class AccessDecisionResponse(BaseModel):
    """The complete, explainable result of evaluating an access request."""

    request_id: int
    timestamp: datetime
    decision: Literal["ALLOW", "DENY"]
    reason: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    iam_result: IAMResult
    vpc_result: VPCResult
    resource_result: PolicyResult
    mfa_result: MFAResult
    risk_factors: list[RiskFactor]


class AccessRequestOut(BaseModel):
    """A stored access request, as returned by list endpoints."""

    id: int
    timestamp: datetime
    user: str | None = None
    role: str | None = None
    action: str
    resource: str | None = None
    source_ip: str | None = None
    source_vpc: str | None = None
    mfa: bool
    request_type: str | None = None
    iam_result: str | None = None
    vpc_result: str | None = None
    resource_result: str | None = None
    mfa_required: bool = False
    mfa_result: str | None = None
    risk_score: int | None = None
    risk_level: str | None = None
    risk_factors: list[RiskFactor] = []
    final_decision: str | None = None
    decision_reason: str | None = None
