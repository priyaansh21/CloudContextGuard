"""
Access service - orchestrates a single access request through every
security engine and persists the outcome.

This module resolves database records into the plain inputs each engine
expects, calls the engines in a fixed order, and stores the result. No
authorization decision is made here - that is the decision engine's job.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.models import AccessRequest, Alert, Permission, Policy, Resource, Role, SecurityEvent, User, VPC
from app.engine.decision_engine import decide
from app.engine.iam_engine import PermissionSpec, evaluate_iam
from app.engine.policy_engine import evaluate_mfa, evaluate_policy
from app.engine.risk_engine import calculate_risk
from app.engine.vpc_engine import evaluate_vpc
from app.schemas.access import AccessDecisionResponse, AccessRequestIn

logger = get_logger()

REPEATED_FAILURE_WINDOW_MINUTES = 15
HIGH_RISK_LEVELS = ("HIGH", "CRITICAL")


class UserNotFoundError(LookupError):
    """Raised when the requesting user does not exist."""


class ResourceNotFoundError(LookupError):
    """Raised when the requested resource does not exist."""


def evaluate_access_request(db: Session, request_in: AccessRequestIn) -> AccessDecisionResponse:
    """Evaluate one access request end-to-end and persist the result.

    Order: resolve identity/resource -> IAM -> VPC -> resource policy -> MFA
    -> repeated-failure context -> risk -> central decision -> persist.
    """
    user = db.query(User).filter_by(username=request_in.user).first()
    if user is None:
        raise UserNotFoundError(f"User '{request_in.user}' does not exist")

    resource = db.query(Resource).filter_by(name=request_in.resource).first()
    if resource is None:
        raise ResourceNotFoundError(f"Resource '{request_in.resource}' does not exist")

    role = db.get(Role, user.role_id) if user.role_id else None
    role_name = role.name if role else None

    permissions: list[PermissionSpec] = []
    if role is not None:
        permissions = [
            PermissionSpec(action=perm.action, resource_pattern=perm.resource_pattern)
            for perm in db.query(Permission).filter_by(role_id=role.id).all()
        ]

    iam_result = evaluate_iam(
        user_exists=True,
        user_is_active=user.is_active,
        role_name=role_name,
        action=request_in.action,
        resource_name=resource.name,
        permissions=permissions,
    )

    # The policy is the authoritative source for which VPC is trusted; the
    # resource's own trusted_vpc_id is only used as a fallback when no
    # policy row exists for it. Fetched here (before VPC evaluation) so an
    # admin's policy edit is reflected on this very request.
    policy = db.query(Policy).filter_by(resource_id=resource.id).first()
    policy_trusted_vpc_id = policy.trusted_vpc_id if policy else resource.trusted_vpc_id
    requires_trusted_vpc = bool(policy_trusted_vpc_id) if policy else resource.trusted_vpc

    source_vpc_record = db.query(VPC).filter_by(name=request_in.source_vpc).first()
    source_vpc_trusted = bool(source_vpc_record and source_vpc_record.is_trusted)
    expected_vpc_record = db.get(VPC, policy_trusted_vpc_id) if policy_trusted_vpc_id else None

    vpc_result = evaluate_vpc(
        requires_trusted_vpc=requires_trusted_vpc,
        expected_vpc_name=expected_vpc_record.name if expected_vpc_record else None,
        source_vpc_name=request_in.source_vpc,
        source_vpc_trusted=source_vpc_trusted,
    )

    required_role_record = db.get(Role, policy.required_role) if policy and policy.required_role else None

    policy_result = evaluate_policy(
        policy_exists=policy is not None,
        policy_name=policy.name if policy else None,
        is_enabled=bool(policy.is_enabled) if policy else False,
        required_role_name=required_role_record.name if required_role_record else None,
        actual_role_name=role_name,
        trusted_vpc_required=requires_trusted_vpc,
        mfa_required=bool(policy.mfa_required) if policy else resource.mfa_required,
        external_access_allowed=bool(policy.external_access_allowed) if policy else resource.external_access_allowed,
        max_risk_score=policy.max_risk_score if policy else None,
    )

    mfa_result = evaluate_mfa(required=policy_result.mfa_required, provided=request_in.mfa)

    # Naive UTC to match SQLite's naive CURRENT_TIMESTAMP-derived columns.
    window_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
        minutes=REPEATED_FAILURE_WINDOW_MINUTES
    )
    repeated_failed_count = (
        db.query(AccessRequest)
        .filter(
            AccessRequest.user_id == user.id,
            AccessRequest.final_decision == "DENY",
            AccessRequest.timestamp >= window_start,
        )
        .count()
    )

    risk_result = calculate_risk(
        vpc_check_failed=not vpc_result.allowed,
        resource_classification=resource.classification,
        mfa_required=mfa_result.required,
        mfa_provided=request_in.mfa,
        source_vpc_trusted=source_vpc_trusted,
        repeated_failed_count=repeated_failed_count,
        request_type=request_in.request_type,
        username=user.username,
    )

    decision_result = decide(
        iam_result=iam_result,
        vpc_result=vpc_result,
        policy_result=policy_result,
        mfa_result=mfa_result,
        risk_result=risk_result,
        source_is_external=not source_vpc_trusted,
    )

    # Security log line: timestamp is added by the logging formatter itself.
    # No secrets are logged - there are none in this request shape (no
    # passwords/tokens; MFA is a plain boolean).
    logger.info(
        "access_decision event=ACCESS_EVALUATED user=%s resource=%s action=%s source=%s "
        "decision=%s risk=%s/%s reason=%s",
        user.username,
        resource.name,
        request_in.action,
        request_in.source_vpc or "external",
        decision_result.decision,
        risk_result.score,
        risk_result.level,
        decision_result.reason,
    )

    access_request = AccessRequest(
        user_id=user.id,
        role_id=role.id if role else None,
        action=request_in.action,
        resource_id=resource.id,
        source_ip=request_in.source_ip,
        source_vpc=request_in.source_vpc,
        mfa=request_in.mfa,
        request_type=request_in.request_type,
        iam_result=iam_result.result,
        vpc_result=vpc_result.result,
        resource_result=policy_result.result,
        mfa_required=mfa_result.required,
        mfa_result=mfa_result.result,
        risk_score=risk_result.score,
        risk_level=risk_result.level,
        risk_factors=json.dumps([factor.model_dump() for factor in risk_result.factors]),
        final_decision=decision_result.decision,
        decision_reason=decision_result.reason,
    )
    db.add(access_request)
    db.flush()

    if decision_result.decision == "DENY":
        db.add(_build_security_event(access_request, user, resource, request_in, risk_result, decision_result))

    if risk_result.level in HIGH_RISK_LEVELS:
        db.add(_build_alert(access_request, user, resource, request_in, risk_result, decision_result))

    db.commit()
    db.refresh(access_request)

    return AccessDecisionResponse(
        request_id=access_request.id,
        timestamp=access_request.timestamp,
        decision=decision_result.decision,
        reason=decision_result.reason,
        risk_score=risk_result.score,
        risk_level=risk_result.level,
        iam_result=iam_result,
        vpc_result=vpc_result,
        resource_result=policy_result,
        mfa_result=mfa_result,
        risk_factors=risk_result.factors,
    )


def _build_security_event(
    access_request: AccessRequest,
    user: User,
    resource: Resource,
    request_in: AccessRequestIn,
    risk_result,
    decision_result,
) -> SecurityEvent:
    resource_family = resource.resource_type.split("-")[0].upper()
    return SecurityEvent(
        access_request_id=access_request.id,
        severity=risk_result.level,
        event_type=f"BLOCKED_{resource_family}_ACCESS",
        user=user.username,
        source_ip=request_in.source_ip,
        source_vpc=request_in.source_vpc,
        resource=resource.name,
        risk_score=risk_result.score,
        description=decision_result.reason,
        action_taken="BLOCKED",
    )


def _build_alert(
    access_request: AccessRequest,
    user: User,
    resource: Resource,
    request_in: AccessRequestIn,
    risk_result,
    decision_result,
) -> Alert:
    verb = "Blocked" if decision_result.decision == "DENY" else "Allowed high-risk"
    return Alert(
        access_request_id=access_request.id,
        severity=risk_result.level,
        title=f"{verb} access to {resource.name}",
        description=(
            f"{user.username} attempted {request_in.action} on {resource.name} "
            f"from {request_in.source_vpc or 'external'} network "
            f"(risk {risk_result.score}/{risk_result.level}, decision {decision_result.decision})."
        ),
        status="OPEN",
    )


def list_access_requests(db: Session, limit: int = 50) -> list[AccessRequest]:
    """Return the most recent access requests, newest first."""
    return (
        db.query(AccessRequest)
        .order_by(AccessRequest.timestamp.desc(), AccessRequest.id.desc())
        .limit(limit)
        .all()
    )
