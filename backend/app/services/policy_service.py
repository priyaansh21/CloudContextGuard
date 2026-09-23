"""
Policy service - validated, audited mutation of resource policies.

The Policy row in the database is the sole source of truth for a
resource's dynamic authorization requirements. access_service.py re-reads
the Policy table fresh on every access evaluation - nothing here or
anywhere else caches a policy decision, so an update applied through this
module is visible to the very next access request.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Policy, Resource, Role, SecurityEvent, VPC
from app.schemas.catalog import PolicyUpdate

_FIELD_LABELS = {
    "name": "Name",
    "description": "Description",
    "required_role": "Required role",
    "trusted_vpc": "Trusted VPC",
    "mfa_required": "MFA required",
    "max_risk_score": "Max risk score",
    "external_access_allowed": "External access allowed",
    "is_enabled": "Enabled",
}

# Pydantic field name -> ORM column name, where they differ (name/role/vpc
# fields resolve to id columns on the model).
_MODEL_FIELD = {
    "required_role": "required_role",
    "trusted_vpc": "trusted_vpc_id",
}


class PolicyNotFoundError(LookupError):
    """Raised when the requested policy does not exist."""


class PolicyValidationError(ValueError):
    """Raised when a policy update references a role or VPC that doesn't exist."""


def get_policy(db: Session, policy_id: int) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise PolicyNotFoundError(f"Policy {policy_id} does not exist")
    return policy


def update_policy(db: Session, policy_id: int, payload: PolicyUpdate) -> tuple[Policy, list[str]]:
    """Apply a validated update to a policy and record a security audit event.

    Returns the updated policy and a list of human-readable "Field: old -> new"
    change descriptions (empty if the payload matched the current values).
    """
    policy = get_policy(db, policy_id)

    required_role_id: int | None = None
    if payload.required_role is not None:
        role = db.query(Role).filter_by(name=payload.required_role).first()
        if role is None:
            raise PolicyValidationError(f"Role '{payload.required_role}' does not exist")
        required_role_id = role.id

    trusted_vpc_id: int | None = None
    if payload.trusted_vpc is not None:
        vpc = db.query(VPC).filter_by(name=payload.trusted_vpc).first()
        if vpc is None:
            raise PolicyValidationError(f"VPC '{payload.trusted_vpc}' does not exist")
        trusted_vpc_id = vpc.id

    new_values = {
        "name": payload.name,
        "description": payload.description,
        "required_role": required_role_id,
        "trusted_vpc": trusted_vpc_id,
        "mfa_required": payload.mfa_required,
        "max_risk_score": payload.max_risk_score,
        "external_access_allowed": payload.external_access_allowed,
        "is_enabled": payload.is_enabled,
    }

    role_names = {role.id: role.name for role in db.query(Role).all()}
    vpc_names = {vpc.id: vpc.name for vpc in db.query(VPC).all()}

    def _display(field: str, value: object) -> str:
        if field == "required_role":
            return role_names.get(value, "none") if value else "none"
        if field == "trusted_vpc":
            return vpc_names.get(value, "none") if value else "none"
        return str(value)

    changes: list[str] = []
    for field, new_value in new_values.items():
        model_field = _MODEL_FIELD.get(field, field)
        old_value = getattr(policy, model_field)
        if old_value != new_value:
            changes.append(f"{_FIELD_LABELS[field]}: {_display(field, old_value)} -> {_display(field, new_value)}")
        setattr(policy, model_field, new_value)

    if changes:
        resource = db.get(Resource, policy.resource_id) if policy.resource_id else None
        db.add(
            SecurityEvent(
                severity="HIGH",
                event_type="POLICY_CHANGED",
                resource=resource.name if resource else None,
                description=f"Policy '{policy.name}' updated: " + "; ".join(changes),
                action_taken="POLICY_UPDATED",
            )
        )

    db.commit()
    db.refresh(policy)
    return policy, changes
