"""Access-control API routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Resource, Role, User
from app.schemas.access import AccessDecisionResponse, AccessRequestIn, AccessRequestOut
from app.services.access_service import (
    ResourceNotFoundError,
    UserNotFoundError,
    evaluate_access_request,
    list_access_requests,
)

router = APIRouter(prefix="/api", tags=["access"])


@router.post("/access/request", response_model=AccessDecisionResponse)
def submit_access_request(request_in: AccessRequestIn, db: Session = Depends(get_db)) -> AccessDecisionResponse:
    """Evaluate a simulated access request through every security engine."""
    try:
        return evaluate_access_request(db, request_in)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/access/requests", response_model=list[AccessRequestOut])
def get_access_requests(
    limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)
) -> list[AccessRequestOut]:
    """Return the most recent access requests with resolved identity/resource names."""
    rows = list_access_requests(db, limit=limit)
    users = {u.id: u.username for u in db.query(User).all()}
    roles = {r.id: r.name for r in db.query(Role).all()}
    resources = {r.id: r.name for r in db.query(Resource).all()}
    return [
        AccessRequestOut(
            id=row.id,
            timestamp=row.timestamp,
            user=users.get(row.user_id),
            role=roles.get(row.role_id),
            action=row.action,
            resource=resources.get(row.resource_id),
            source_ip=row.source_ip,
            source_vpc=row.source_vpc,
            mfa=row.mfa,
            request_type=row.request_type,
            iam_result=row.iam_result,
            vpc_result=row.vpc_result,
            resource_result=row.resource_result,
            mfa_required=row.mfa_required,
            mfa_result=row.mfa_result,
            risk_score=row.risk_score,
            risk_level=row.risk_level,
            risk_factors=json.loads(row.risk_factors) if row.risk_factors else [],
            final_decision=row.final_decision,
            decision_reason=row.decision_reason,
        )
        for row in rows
    ]
