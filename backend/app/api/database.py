"""Database maintenance API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.seed_service import ensure_contractor_identity, seed_if_empty

router = APIRouter(prefix="/api", tags=["database"])


@router.post("/database/seed")
def seed_database(db: Session = Depends(get_db)) -> dict[str, object]:
    """Seed the reference catalog and ensure demonstration identities exist.

    The base catalog seed only runs against an empty database. The
    contractor demonstration identity check is additive/idempotent and runs
    regardless, without touching existing audit history.
    """
    seeded = seed_if_empty(db)
    contractor_ensured = ensure_contractor_identity(db)
    return {
        "seeded": seeded,
        "contractor_identity_ensured": contractor_ensured,
        "message": "Database seeded" if seeded else "Database already contains data; seed skipped",
    }
