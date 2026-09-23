"""Schemas for security events and alerts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SecurityEventOut(BaseModel):
    id: int
    access_request_id: int | None = None
    timestamp: datetime
    severity: str
    event_type: str
    user: str | None = None
    source_ip: str | None = None
    source_vpc: str | None = None
    resource: str | None = None
    risk_score: int | None = None
    description: str | None = None
    action_taken: str | None = None


class AlertOut(BaseModel):
    id: int
    access_request_id: int | None = None
    timestamp: datetime
    severity: str
    title: str
    description: str
    status: str
