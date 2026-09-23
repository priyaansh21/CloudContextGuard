"""
ORM models for CloudContextGuard.

These tables are the data foundation for later steps (IAM evaluation, VPC
trust evaluation, risk scoring, decision engine, attack simulation). Step 2
only defines the schema; no evaluation logic lives here.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Role(Base):
    """A named role, e.g. admin, developer, auditor."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


class User(Base):
    """A simulated identity used to generate access requests."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(150))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Permission(Base):
    """An action a role is allowed to perform on a resource pattern."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_pattern: Mapped[str] = mapped_column(String(255), nullable=False)


class Resource(Base):
    """A simulated cloud resource protected by context-aware access control."""

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    classification: Mapped[str | None] = mapped_column(String(50))
    required_role: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    # Whether this resource is bound to a specific network boundary at all
    # (False for PUBLIC resources with no VPC restriction).
    trusted_vpc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # The specific VPC a request must originate from when trusted_vpc is True.
    trusted_vpc_id: Mapped[int | None] = mapped_column(ForeignKey("vpcs.id"))
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    external_access_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


class VPC(Base):
    """A simulated virtual network boundary with an associated trust level."""

    __tablename__ = "vpcs"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    cidr: Mapped[str] = mapped_column(String(50), nullable=False)
    trust_level: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(String(255))
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Policy(Base):
    """A context-aware access rule evaluated against incoming requests."""

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    resource_id: Mapped[int | None] = mapped_column(ForeignKey("resources.id"))
    required_role: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    # The specific VPC a request must originate from for this policy's
    # resource. None means no VPC boundary is enforced. This is the
    # authoritative source for VPC evaluation - access_service.py reads it
    # fresh on every request, so an admin's policy edit takes effect
    # immediately on the next access evaluation.
    trusted_vpc_id: Mapped[int | None] = mapped_column(ForeignKey("vpcs.id"))
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_risk_score: Mapped[int | None] = mapped_column(Integer)
    external_access_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AccessRequest(Base):
    """A logged (simulated) access attempt and its evaluation outcome.

    Result/score/decision fields are nullable because the evaluation engines
    that populate them (IAM, VPC, resource, risk, decision) are built in
    later steps; Step 2 only defines the schema.
    """

    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(ForeignKey("resources.id"))
    source_ip: Mapped[str | None] = mapped_column(String(45))
    source_vpc: Mapped[str | None] = mapped_column(String(100))
    mfa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    request_type: Mapped[str | None] = mapped_column(String(50))
    iam_result: Mapped[str | None] = mapped_column(String(20))
    vpc_result: Mapped[str | None] = mapped_column(String(20))
    resource_result: Mapped[str | None] = mapped_column(String(20))
    mfa_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_result: Mapped[str | None] = mapped_column(String(20))
    risk_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[str | None] = mapped_column(String(20))
    # JSON-encoded list of {name, points, reason} - the risk engine's factor
    # breakdown at evaluation time, persisted so the UI can show it later.
    risk_factors: Mapped[str | None] = mapped_column(Text)
    final_decision: Mapped[str | None] = mapped_column(String(20))
    decision_reason: Mapped[str | None] = mapped_column(Text)


class SecurityEvent(Base):
    """A security-relevant event derived from access request evaluation.

    ``user``, ``source_ip``, ``source_vpc`` and ``resource`` are stored as
    plain strings (a denormalized snapshot) rather than foreign keys, so the
    security log remains accurate even if the referenced user or resource is
    later renamed or removed.
    """

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Links this event back to the request that produced it, so a client
    # holding a request_id can confirm whether an event was actually
    # created for it (mirrors Alert.access_request_id below).
    access_request_id: Mapped[int | None] = mapped_column(ForeignKey("access_requests.id"), unique=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    user: Mapped[str | None] = mapped_column(String(100))
    source_ip: Mapped[str | None] = mapped_column(String(45))
    source_vpc: Mapped[str | None] = mapped_column(String(100))
    resource: Mapped[str | None] = mapped_column(String(150))
    risk_score: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    action_taken: Mapped[str | None] = mapped_column(String(50))


class Alert(Base):
    """A raised alert for a high or critical risk access request.

    One alert is created per qualifying access request (never duplicated for
    the same request), so ``access_request_id`` is unique.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    access_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("access_requests.id"), unique=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
