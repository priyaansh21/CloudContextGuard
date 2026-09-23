"""Schemas for the reference/catalog data (users, roles, resources, policies, ...).

Most of this module is read-only output schemas. ``PolicyUpdate`` is the one
exception - policies are the one piece of catalog data an administrator can
mutate at runtime (see ``app.api.policies``).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RoleOut(BaseModel):
    id: int
    name: str
    description: str | None = None


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str | None = None
    role: str | None = None
    is_active: bool
    created_at: datetime


class PermissionOut(BaseModel):
    id: int
    role: str | None = None
    action: str
    resource_pattern: str


class ResourceOut(BaseModel):
    id: int
    name: str
    resource_type: str
    classification: str | None = None
    required_role: str | None = None
    trusted_vpc: bool
    trusted_vpc_name: str | None = None
    mfa_required: bool
    external_access_allowed: bool
    description: str | None = None


class VPCOut(BaseModel):
    id: int
    name: str
    cidr: str
    trust_level: str | None = None
    description: str | None = None
    is_trusted: bool


class PolicyOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    resource: str | None = None
    required_role: str | None = None
    trusted_vpc: str | None = None
    mfa_required: bool
    max_risk_score: int | None = None
    external_access_allowed: bool
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


class PolicyUpdate(BaseModel):
    """Administrator-editable fields for a resource policy (PUT payload).

    ``id``, ``resource_id``, ``created_at`` and ``updated_at`` are always
    backend-managed and are never accepted here. ``required_role`` and
    ``trusted_vpc`` take names (not ids); ``null`` clears that restriction.
    """

    name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    required_role: str | None = None
    trusted_vpc: str | None = None
    mfa_required: bool
    max_risk_score: int | None = Field(default=None, ge=0, le=100)
    external_access_allowed: bool
    is_enabled: bool
