"""Security event and alert API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Alert, SecurityEvent
from app.schemas.security import AlertOut, SecurityEventOut

router = APIRouter(prefix="/api", tags=["security"])


@router.get("/security/events", response_model=list[SecurityEventOut])
def get_security_events(
    limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)
) -> list[SecurityEventOut]:
    rows = db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc(), SecurityEvent.id.desc()).limit(limit).all()
    return [SecurityEventOut.model_validate(row, from_attributes=True) for row in rows]


@router.get("/alerts", response_model=list[AlertOut])
def get_alerts(limit: int = Query(default=50, ge=1, le=500), db: Session = Depends(get_db)) -> list[AlertOut]:
    rows = db.query(Alert).order_by(Alert.timestamp.desc(), Alert.id.desc()).limit(limit).all()
    return [AlertOut.model_validate(row, from_attributes=True) for row in rows]
