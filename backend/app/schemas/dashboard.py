"""Aggregated, database-derived schema for the dashboard summary endpoint."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.security import SecurityEventOut


class DashboardResponse(BaseModel):
    total_requests: int
    allowed_requests: int
    denied_requests: int
    high_risk_requests: int
    critical_events: int
    open_alerts: int
    protected_resources: int
    decision_distribution: dict[str, int]
    risk_distribution: dict[str, int]
    requests_by_vpc: dict[str, int]
    requests_by_user: dict[str, int]
    recent_events: list[SecurityEventOut]
