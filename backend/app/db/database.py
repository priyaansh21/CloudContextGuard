"""
SQLAlchemy database setup for CloudContextGuard.

The SQLite file lives at ``app.core.paths.DATABASE_PATH``
(``PROJECT_ROOT/data/cloud_security.db``), resolved dynamically so the
database follows the project if it is moved.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

from sqlalchemy import DateTime, Integer, create_engine, event, func, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import get_settings
from app.core.paths import ensure_directories

settings = get_settings()

# check_same_thread=False: FastAPI may use the session from a different
# thread than the one that created it; SQLAlchemy's session handling keeps
# this safe for our per-request session usage.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    """Enable SQLite foreign-key constraint enforcement on every connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


class SchemaVersion(Base):
    """Tracks which application schema version this database was built for.

    Deliberately minimal - a single stamped value, not a migration history
    or an Alembic-style ledger. When a change to app.db.models is NOT
    safely representable by SQLAlchemy's additive-only ``create_all()``
    (a column type change, rename or removal on an existing table - as
    happened when ``Policy.trusted_vpc`` became ``Policy.trusted_vpc_id``),
    bump CURRENT_SCHEMA_VERSION below. A mismatch between that constant and
    the value stamped here stops the application from starting instead of
    silently running against - or automatically recreating - an
    incompatible schema. See ``init_db()``.
    """

    __tablename__ = "schema_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


# Bump this only when a model change is incompatible with data already on
# disk. Purely additive changes (a new table, or a new nullable column with
# no data-shape conflict) don't need a bump - create_all() already handles
# those safely without any version check.
CURRENT_SCHEMA_VERSION = 1


class SchemaVersionMismatchError(RuntimeError):
    """Raised when the on-disk database was built for a schema version the
    application no longer expects.

    Deliberately not auto-resolved: the application refuses to start rather
    than risk running against a stale schema or silently destroying audit
    history by recreating the database. For a local development database,
    discard and recreate it explicitly and only when you mean to, with:

        python -m app.cli reset-demo-db
    """


def init_db() -> None:
    """Ensure the data directory and schema exist. Safe to call repeatedly.

    Never drops a table or deletes the database file.

    - Brand-new database (no tables at all): create the full schema and
      stamp it with CURRENT_SCHEMA_VERSION.
    - Existing database predating this versioning mechanism (tables exist,
      but no schema_version table): adopted in place - only the new
      schema_version table is added and stamped; every other table and all
      of its data is left untouched (create_all() only creates tables that
      don't yet exist).
    - Existing, already-versioned database: the stamped version must match
      CURRENT_SCHEMA_VERSION exactly, or SchemaVersionMismatchError is
      raised and nothing is modified.
    """
    ensure_directories()
    # Import models so they register on Base.metadata before create_all runs.
    from app.db import models  # noqa: F401

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    if not existing_tables:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            db.add(SchemaVersion(version=CURRENT_SCHEMA_VERSION))
            db.commit()
        return

    if SchemaVersion.__tablename__ not in existing_tables:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            db.add(SchemaVersion(version=CURRENT_SCHEMA_VERSION))
            db.commit()
        return

    with SessionLocal() as db:
        stamped = db.query(SchemaVersion).order_by(SchemaVersion.id.desc()).first()
    stamped_version = stamped.version if stamped else None

    if stamped_version != CURRENT_SCHEMA_VERSION:
        raise SchemaVersionMismatchError(
            f"Database schema version {stamped_version!r} does not match the application's "
            f"expected version {CURRENT_SCHEMA_VERSION}. Refusing to start to avoid running "
            "against an incompatible schema or silently destroying data. If this is a local "
            "development database, discard and recreate it explicitly with: "
            "python -m app.cli reset-demo-db"
        )

    # Versions match. Still safe (and necessary after adding a new model)
    # to run create_all() here - it only creates missing tables and never
    # alters or drops ones that already exist.
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_database_connected() -> bool:
    """Lightweight connectivity check used by the health endpoint."""
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False
