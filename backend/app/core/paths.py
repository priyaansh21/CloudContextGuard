"""
Central path resolution for CloudContextGuard.

Every project path is derived from the location of THIS file, never from the
terminal's current working directory and never from a hardcoded absolute path.
Moving the project folder to another drive or parent directory therefore needs
no source-code changes.

Layout this module relies on:

    <PROJECT_ROOT>/backend/app/core/paths.py

All other backend modules must import their paths from here instead of
building their own.
"""

from pathlib import Path

# paths.py -> core -> app -> backend -> <PROJECT_ROOT>
_THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT: Path = _THIS_FILE.parents[3]

BACKEND_DIR: Path = PROJECT_ROOT / "backend"
FRONTEND_DIR: Path = PROJECT_ROOT / "frontend"
DATA_DIR: Path = PROJECT_ROOT / "data"
LOG_DIR: Path = PROJECT_ROOT / "logs"
POLICY_DIR: Path = PROJECT_ROOT / "policies"
SIMULATOR_DIR: Path = PROJECT_ROOT / "simulator"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
CONFIG_DIR: Path = PROJECT_ROOT / "config"
TESTS_DIR: Path = PROJECT_ROOT / "tests"

DATABASE_PATH: Path = DATA_DIR / "cloud_security.db"

# Directories the application needs at runtime; created on demand.
REQUIRED_DIRS: tuple[Path, ...] = (
    DATA_DIR,
    LOG_DIR,
    POLICY_DIR,
    SIMULATOR_DIR,
    DOCS_DIR,
    CONFIG_DIR,
)

# Every named project path, useful for diagnostics and verification.
ALL_PATHS: dict[str, Path] = {
    "PROJECT_ROOT": PROJECT_ROOT,
    "BACKEND_DIR": BACKEND_DIR,
    "FRONTEND_DIR": FRONTEND_DIR,
    "DATA_DIR": DATA_DIR,
    "LOG_DIR": LOG_DIR,
    "POLICY_DIR": POLICY_DIR,
    "SIMULATOR_DIR": SIMULATOR_DIR,
    "DOCS_DIR": DOCS_DIR,
    "CONFIG_DIR": CONFIG_DIR,
    "TESTS_DIR": TESTS_DIR,
    "DATABASE_PATH": DATABASE_PATH,
}


def is_inside_project(path: Path) -> bool:
    """Return True if ``path`` resolves to a location inside PROJECT_ROOT."""
    try:
        Path(path).resolve().relative_to(PROJECT_ROOT)
        return True
    except ValueError:
        return False


def ensure_directories() -> list[Path]:
    """Create any missing required directories. Returns the ones created."""
    created = []
    for directory in REQUIRED_DIRS:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(directory)
    return created


if __name__ == "__main__":
    # Used by setup.bat: create required directories and show resolved paths.
    new_dirs = ensure_directories()
    for name, value in ALL_PATHS.items():
        print(f"{name:<14} {value}")
    if new_dirs:
        print("\nCreated directories:")
        for directory in new_dirs:
            print(f"  {directory.relative_to(PROJECT_ROOT)}")
    else:
        print("\nAll required directories already exist.")
