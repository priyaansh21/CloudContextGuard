"""Database-derived aggregation for the dashboard summary endpoint."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import AccessRequest, Alert, Resource, SecurityEvent
from app.schemas.dashboard import DashboardResponse
from app.schemas.security import SecurityEventOut

HIGH_RISK_LEVELS = ("HIGH", "CRITICAL")
RECENT_EVENTS_LIMIT = 10


def _count_by(db: Session, column) -> dict[str, int]:
    rows = db.query(column, func.count(AccessRequest.id)).group_by(column).all()
    return {(key or "unknown"): count for key, count in rows}


def build_dashboard(db: Session) -> DashboardResponse:
    """Build the full dashboard summary from live database state."""
    total_requests = db.query(func.count(AccessRequest.id)).scalar() or 0
    allowed_requests = (
        db.query(func.count(AccessRequest.id)).filter(AccessRequest.final_decision == "ALLOW").scalar() or 0
    )
    denied_requests = (
        db.query(func.count(AccessRequest.id)).filter(AccessRequest.final_decision == "DENY").scalar() or 0
    )
    high_risk_requests = (
        db.query(func.count(AccessRequest.id)).filter(AccessRequest.risk_level.in_(HIGH_RISK_LEVELS)).scalar() or 0
    )
    critical_events = (
        db.query(func.count(SecurityEvent.id)).filter(SecurityEvent.severity == "CRITICAL").scalar() or 0
    )
    open_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "OPEN").scalar() or 0
    protected_resources = db.query(func.count(Resource.id)).filter(Resource.trusted_vpc.is_(True)).scalar() or 0

    decision_distribution = _count_by(db, AccessRequest.final_decision)
    risk_distribution = _count_by(db, AccessRequest.risk_level)
    requests_by_vpc = _count_by(db, AccessRequest.source_vpc)
    requests_by_user = _count_by(db, AccessRequest.user_id)

    # requests_by_user is keyed by user_id above; resolve to usernames.
    if requests_by_user:
        from app.db.models import User

        id_to_username = {u.id: u.username for u in db.query(User).all()}
        requests_by_user = {
            id_to_username.get(int(user_id), f"user-{user_id}") if user_id != "unknown" else "unknown": count
            for user_id, count in requests_by_user.items()
        }

    recent_events = (
        db.query(SecurityEvent)
        .order_by(SecurityEvent.timestamp.desc(), SecurityEvent.id.desc())
        .limit(RECENT_EVENTS_LIMIT)
        .all()
    )

    return DashboardResponse(
        total_requests=total_requests,
        allowed_requests=allowed_requests,
        denied_requests=denied_requests,
        high_risk_requests=high_risk_requests,
        critical_events=critical_events,
        open_alerts=open_alerts,
        protected_resources=protected_resources,
        decision_distribution=decision_distribution,
        risk_distribution=risk_distribution,
        requests_by_vpc=requests_by_vpc,
        requests_by_user=requests_by_user,
        recent_events=[SecurityEventOut.model_validate(event, from_attributes=True) for event in recent_events],
    )
