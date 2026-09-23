"""Response schema for the health endpoints."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Reported service and database status."""

    status: str
    service: str
    database: str
