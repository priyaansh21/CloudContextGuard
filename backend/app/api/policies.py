"""
Policy management API routes.

GET is read-only reference data, exactly like the rest of the catalog
endpoints. PUT is the one mutation point in the whole catalog: it updates
the actual database row, validates references, and records a
POLICY_CHANGED security event. The database policy remains authoritative -
nothing here bypasses or short-circuits the access-evaluation pipeline in
app.services.access_service.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Policy, Resource, Role, VPC
from app.schemas.catalog import PolicyOut, PolicyUpdate
from app.services.policy_service import PolicyNotFoundError, PolicyValidationError, get_policy, update_policy

router = APIRouter(prefix="/api", tags=["policies"])


def _to_policy_out(db: Session, policy: Policy) -> PolicyOut:
    role = db.get(Role, policy.required_role) if policy.required_role else None
    vpc = db.get(VPC, policy.trusted_vpc_id) if policy.trusted_vpc_id else None
    resource = db.get(Resource, policy.resource_id) if policy.resource_id else None
    return PolicyOut(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        resource=resource.name if resource else None,
        required_role=role.name if role else None,
        trusted_vpc=vpc.name if vpc else None,
        mfa_required=policy.mfa_required,
        max_risk_score=policy.max_risk_score,
        external_access_allowed=policy.external_access_allowed,
        is_enabled=policy.is_enabled,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@router.get("/policies", response_model=list[PolicyOut])
def list_policies(db: Session = Depends(get_db)) -> list[PolicyOut]:
    return [_to_policy_out(db, policy) for policy in db.query(Policy).all()]


@router.get("/policies/{policy_id}", response_model=PolicyOut)
def get_policy_detail(policy_id: int, db: Session = Depends(get_db)) -> PolicyOut:
    try:
        policy = get_policy(db, policy_id)
    except PolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_policy_out(db, policy)


@router.put("/policies/{policy_id}", response_model=PolicyOut)
def put_policy(policy_id: int, payload: PolicyUpdate, db: Session = Depends(get_db)) -> PolicyOut:
    """Update a policy. Takes effect on the very next access evaluation -
    there is no cache to invalidate."""
    try:
        policy, _changes = update_policy(db, policy_id, payload)
    except PolicyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PolicyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _to_policy_out(db, policy)
