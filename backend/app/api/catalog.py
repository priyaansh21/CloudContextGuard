"""Read-only catalog API routes (users, roles, permissions, resources, VPCs).

Policies are handled by app.api.policies - they are the one piece of
catalog data that can be mutated at runtime.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Permission, Resource, Role, User, VPC
from app.schemas.catalog import PermissionOut, ResourceOut, RoleOut, UserOut, VPCOut

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/users", response_model=list[UserOut])
def get_users(db: Session = Depends(get_db)) -> list[UserOut]:
    roles = {r.id: r.name for r in db.query(Role).all()}
    return [
        UserOut(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            role=roles.get(u.role_id),
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in db.query(User).all()
    ]


@router.get("/roles", response_model=list[RoleOut])
def get_roles(db: Session = Depends(get_db)) -> list[RoleOut]:
    return [RoleOut(id=r.id, name=r.name, description=r.description) for r in db.query(Role).all()]


@router.get("/permissions", response_model=list[PermissionOut])
def get_permissions(db: Session = Depends(get_db)) -> list[PermissionOut]:
    roles = {r.id: r.name for r in db.query(Role).all()}
    return [
        PermissionOut(id=p.id, role=roles.get(p.role_id), action=p.action, resource_pattern=p.resource_pattern)
        for p in db.query(Permission).all()
    ]


@router.get("/resources", response_model=list[ResourceOut])
def get_resources(db: Session = Depends(get_db)) -> list[ResourceOut]:
    roles = {r.id: r.name for r in db.query(Role).all()}
    vpcs = {v.id: v.name for v in db.query(VPC).all()}
    return [
        ResourceOut(
            id=r.id,
            name=r.name,
            resource_type=r.resource_type,
            classification=r.classification,
            required_role=roles.get(r.required_role),
            trusted_vpc=r.trusted_vpc,
            trusted_vpc_name=vpcs.get(r.trusted_vpc_id),
            mfa_required=r.mfa_required,
            external_access_allowed=r.external_access_allowed,
            description=r.description,
        )
        for r in db.query(Resource).all()
    ]


@router.get("/vpcs", response_model=list[VPCOut])
def get_vpcs(db: Session = Depends(get_db)) -> list[VPCOut]:
    return [
        VPCOut(
            id=v.id,
            name=v.name,
            cidr=v.cidr,
            trust_level=v.trust_level,
            description=v.description,
            is_trusted=v.is_trusted,
        )
        for v in db.query(VPC).all()
    ]
