"""
Database safety hardening tests for CloudContextGuard (Step 6.1).

Covers:
- init_db()'s first-run / normal-startup / schema-mismatch behavior, using
  an isolated temporary SQLite database so these tests never touch the
  shared project database.
- Seed idempotency, and that dynamically modified policies and audit
  history survive a normal application restart - against the real, shared
  project database, exactly like the rest of this test suite.
- The explicit, deliberately-invoked developer reset CLI, and that the
  running application never triggers it on its own.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

import app.cli as cli_module
import app.db.database as database_module
from app.core.paths import BACKEND_DIR
from app.db.database import CURRENT_SCHEMA_VERSION, SchemaVersion, SchemaVersionMismatchError, SessionLocal, init_db
from app.db.models import Role
from app.main import app
from app.services.seed_service import ensure_contractor_identity, seed_if_empty

EDITABLE_POLICY_FIELDS = (
    "name",
    "description",
    "required_role",
    "trusted_vpc",
    "mfa_required",
    "max_risk_score",
    "external_access_allowed",
    "is_enabled",
)


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Point app.db.database (and app.cli) at a throwaway SQLite file for
    the duration of one test. Restored automatically by monkeypatch
    afterwards. Never touches the shared project database."""
    db_path = tmp_path / "isolated_test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "SessionLocal", session_local)
    monkeypatch.setattr(cli_module, "DATABASE_PATH", db_path)
    monkeypatch.setattr(cli_module, "SessionLocal", session_local)
    monkeypatch.setattr(cli_module, "engine", engine)

    yield db_path

    engine.dispose()


def _update_payload(policy: dict, **overrides) -> dict:
    payload = {field: policy[field] for field in EDITABLE_POLICY_FIELDS}
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# TEST 1: first initialization creates schema
# ---------------------------------------------------------------------------


def test_1_first_initialization_creates_schema(isolated_db) -> None:
    assert not isolated_db.exists()

    init_db()

    assert isolated_db.exists()
    tables = set(sa_inspect(database_module.engine).get_table_names())
    assert {"schema_version", "users", "roles", "resources", "policies", "vpcs"}.issubset(tables)

    with database_module.SessionLocal() as db:
        stamped = db.query(SchemaVersion).first()
    assert stamped is not None
    assert stamped.version == CURRENT_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# TEST 2: second initialization preserves existing records
# ---------------------------------------------------------------------------


def test_2_second_initialization_preserves_existing_records(isolated_db) -> None:
    init_db()
    with database_module.SessionLocal() as db:
        db.add(Role(name="TemporaryRole", description="Created before the second init_db() call"))
        db.commit()

    init_db()  # second call must not touch existing data

    with database_module.SessionLocal() as db:
        role = db.query(Role).filter_by(name="TemporaryRole").first()
    assert role is not None


# ---------------------------------------------------------------------------
# TEST 3: seed operation idempotent
# ---------------------------------------------------------------------------


def test_3_seed_operation_idempotent() -> None:
    from app.db.models import User

    db = SessionLocal()
    try:
        seed_if_empty(db)  # ensures the shared dev database is seeded
        before_count = db.query(User).count()

        ran_again = seed_if_empty(db)
        after_count = db.query(User).count()
    finally:
        db.close()

    assert ran_again is False
    assert after_count == before_count


# ---------------------------------------------------------------------------
# TEST 4: existing policy modifications survive normal initialization
# ---------------------------------------------------------------------------


def test_4_policy_modifications_survive_normal_initialization() -> None:
    with TestClient(app) as client:
        assert client.post("/api/database/seed").status_code == 200

        policies = client.get("/api/policies").json()
        policy = next(p for p in policies if p["resource"] == "financial-records")
        original_required_role = policy["required_role"]

        update_response = client.put(
            f"/api/policies/{policy['id']}", json=_update_payload(policy, required_role="FinanceRole")
        )
        assert update_response.status_code == 200
        assert update_response.json()["required_role"] == "FinanceRole"

        try:
            # Simulate a normal application restart's startup sequence.
            # It must NOT revert the administrator's change above.
            init_db()
            db = SessionLocal()
            try:
                seed_if_empty(db)
                ensure_contractor_identity(db)
            finally:
                db.close()

            reloaded = client.get(f"/api/policies/{policy['id']}").json()
            assert reloaded["required_role"] == "FinanceRole"
        finally:
            client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy, required_role=original_required_role))


# ---------------------------------------------------------------------------
# TEST 5: existing audit records survive normal initialization
# ---------------------------------------------------------------------------


def test_5_audit_records_survive_normal_initialization() -> None:
    with TestClient(app) as client:
        client.post("/api/database/seed")
        client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            },
        )

        before_requests = len(client.get("/api/access/requests", params={"limit": 1000}).json())
        before_events = len(client.get("/api/security/events", params={"limit": 1000}).json())
        before_alerts = len(client.get("/api/alerts", params={"limit": 1000}).json())

        # Normal application restart's startup sequence.
        init_db()
        db = SessionLocal()
        try:
            seed_if_empty(db)
            ensure_contractor_identity(db)
        finally:
            db.close()

        after_requests = len(client.get("/api/access/requests", params={"limit": 1000}).json())
        after_events = len(client.get("/api/security/events", params={"limit": 1000}).json())
        after_alerts = len(client.get("/api/alerts", params={"limit": 1000}).json())

    assert after_requests == before_requests
    assert after_events == before_events
    assert after_alerts == before_alerts


# ---------------------------------------------------------------------------
# TEST 6: schema mismatch does NOT automatically delete the database
# ---------------------------------------------------------------------------


def test_6_schema_mismatch_does_not_delete_database(isolated_db) -> None:
    init_db()

    with database_module.SessionLocal() as db:
        db.add(Role(name="SurvivorRole", description="Must still exist after a rejected mismatched init"))
        db.commit()
        stamped = db.query(SchemaVersion).first()
        stamped.version = 999999  # simulate an on-disk schema the app no longer recognizes
        db.commit()

    assert isolated_db.exists()

    with pytest.raises(SchemaVersionMismatchError):
        init_db()

    # The database file, and everything in it, must be exactly as it was -
    # nothing was deleted, dropped or recreated by the failed init_db() call.
    assert isolated_db.exists()
    with database_module.SessionLocal() as db:
        role = db.query(Role).filter_by(name="SurvivorRole").first()
        version_row = db.query(SchemaVersion).first()
    assert role is not None
    assert version_row.version == 999999


# ---------------------------------------------------------------------------
# TEST 7: explicit development reset - implemented, only runs when invoked
# ---------------------------------------------------------------------------


def test_7_reset_is_never_referenced_by_the_running_application() -> None:
    main_source = (Path(BACKEND_DIR) / "app" / "main.py").read_text(encoding="utf-8")
    assert "app.cli" not in main_source
    assert "reset_demo_db" not in main_source

    for module_file in ("access.py", "catalog.py", "policies.py", "security.py", "dashboard.py", "database.py"):
        route_source = (Path(BACKEND_DIR) / "app" / "api" / module_file).read_text(encoding="utf-8")
        assert "reset_demo_db" not in route_source


def test_7b_explicit_reset_works_when_deliberately_invoked(isolated_db) -> None:
    init_db()
    with database_module.SessionLocal() as db:
        seed_if_empty(db)
        db.add(Role(name="ShouldBeWipedRole", description="Must not survive an explicit reset"))
        db.commit()

    cli_module.reset_demo_db(skip_confirmation=True)

    with database_module.SessionLocal() as db:
        wiped_role = db.query(Role).filter_by(name="ShouldBeWipedRole").first()
        reseeded_role = db.query(Role).filter_by(name="DeveloperRole").first()
    assert wiped_role is None
    assert reseeded_role is not None


def test_7c_explicit_reset_requires_confirmation_without_yes_flag(isolated_db, monkeypatch) -> None:
    init_db()
    with database_module.SessionLocal() as db:
        seed_if_empty(db)

    # Simulate a user declining the interactive confirmation prompt.
    monkeypatch.setattr("builtins.input", lambda _prompt: "no")
    cli_module.reset_demo_db(skip_confirmation=False)

    # Declining must leave the database completely untouched.
    assert isolated_db.exists()
    with database_module.SessionLocal() as db:
        role = db.query(Role).filter_by(name="DeveloperRole").first()
    assert role is not None
