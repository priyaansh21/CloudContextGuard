"""
CloudContextGuard developer CLI.

This module is intentionally NOT imported by the web application
(app.main) or exposed through any HTTP route - the running application
never deletes or recreates its own database. It exists solely for
deliberate, command-line-invoked developer operations.

Usage (from the backend/ directory, with the virtualenv active):

    python -m app.cli reset-demo-db [--yes]

reset-demo-db is destructive: it permanently discards the local SQLite
database - every access request, security event, alert and any policy
customization - and recreates it from the baseline seed data. It requires
either an interactive "reset" confirmation or the explicit --yes flag; it
never runs on its own.
"""

from __future__ import annotations

import argparse
import sys

from app.core.paths import DATABASE_PATH
from app.db.database import SessionLocal, engine, init_db
from app.services.seed_service import ensure_contractor_identity, seed_if_empty


def reset_demo_db(skip_confirmation: bool = False) -> None:
    """Delete the local SQLite database and recreate it from scratch.

    Only ever runs when this module is invoked directly - see the module
    docstring. Nothing in the FastAPI application calls this function.
    """
    if DATABASE_PATH.exists():
        if not skip_confirmation:
            print(f"This will permanently delete {DATABASE_PATH} and all audit history it contains.")
            answer = input("Type 'reset' to confirm: ").strip()
            if answer != "reset":
                print("Aborted - database was not modified.")
                return
        # Release any open SQLite file handles held by the connection pool
        # before deleting the file (required on Windows; harmless elsewhere).
        engine.dispose()
        DATABASE_PATH.unlink()
        print(f"Deleted {DATABASE_PATH}")

    init_db()
    print("Recreated schema.")

    db = SessionLocal()
    try:
        seed_if_empty(db)
        ensure_contractor_identity(db)
    finally:
        db.close()
    print("Reseeded reference catalog and demonstration identities.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="CloudContextGuard developer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    reset_parser = subparsers.add_parser(
        "reset-demo-db",
        help="DESTRUCTIVE: delete and recreate the local demo database. Development use only.",
    )
    reset_parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt.")

    args = parser.parse_args(argv)

    if args.command == "reset-demo-db":
        reset_demo_db(skip_confirmation=args.yes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
