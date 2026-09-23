"""
CloudContextGuard - portability verification.

Run from anywhere:

    python tests/verify_portability.py

Checks that every project path is derived dynamically from the source tree,
that required directories exist, and that no source file, configuration file
or startup script contains a hardcoded absolute or machine-specific path.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Locate the backend package relative to this file (not the working directory).
_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND_DIR))

from app.core import paths  # noqa: E402

LINE = "=" * 40

# Files that must never contain absolute or machine-specific paths.
# Documentation (README.md, docs/) may show example locations and is excluded.
SCANNED_SUFFIXES = {".py", ".bat", ".cmd", ".ps1", ".json", ".toml", ".ini", ".cfg", ".yaml", ".yml"}
SCANNED_NAMES = {".env.example", ".gitignore"}
SKIPPED_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "dist", "build", "docs"}

# Generic absolute-path patterns: any drive letter root, or a Users folder.
GENERIC_PATTERNS = [
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"Users[\\/]", re.IGNORECASE),
]

# Ancestor folder names too generic to indicate a leaked location.
GENERIC_FOLDER_NAMES = {"users", "home", "desktop", "documents", "downloads", "projects", "src", "code"}


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, ok: bool, message: str, detail: str = "") -> None:
        print(f"[{'PASS' if ok else 'FAIL'}] {message}")
        if not ok:
            if detail:
                print(f"       {detail}")
            self.failures.append(message)


def machine_specific_markers() -> list[str]:
    """Strings that identify THIS machine/location, computed at runtime."""
    root = paths.PROJECT_ROOT
    markers = {str(root), root.as_posix()}
    for ancestor in root.parents:
        if ancestor == Path(ancestor.anchor):
            continue
        name = ancestor.name
        if len(name) >= 4 and name.lower() not in GENERIC_FOLDER_NAMES:
            markers.add(name)
    username = Path.home().name
    if len(username) >= 3:
        markers.add(username)
    return sorted(markers, key=len, reverse=True)


def iter_scanned_files() -> list[Path]:
    files = []
    for path in paths.PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(paths.PROJECT_ROOT).parts
        if any(part in SKIPPED_DIRS for part in rel_parts[:-1]):
            continue
        if path.suffix.lower() in SCANNED_SUFFIXES or path.name in SCANNED_NAMES:
            files.append(path)
    return files


def find_path_leaks(files: list[Path]) -> list[str]:
    markers = [m.lower() for m in machine_specific_markers()]
    leaks = []
    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            hit = next((m for m in markers if m in lowered), None)
            if hit is None:
                pattern = next((p for p in GENERIC_PATTERNS if p.search(line)), None)
                hit = pattern.pattern if pattern else None
            if hit is not None:
                rel = file.relative_to(paths.PROJECT_ROOT)
                leaks.append(f"{rel}:{lineno}: {line.strip()}")
    return leaks


def root_independent_of_cwd() -> tuple[bool, str]:
    """Import paths.py from an unrelated working directory; root must not change."""
    code = "from app.core import paths; print(paths.PROJECT_ROOT)"
    with tempfile.TemporaryDirectory() as other_cwd:
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=other_cwd,
            env={**_minimal_env(), "PYTHONPATH": str(_BACKEND_DIR)},
            capture_output=True,
            text=True,
        )
    reported = Path(result.stdout.strip()) if result.returncode == 0 else None
    ok = reported is not None and reported.resolve() == paths.PROJECT_ROOT
    return ok, f"got {reported!r}, stderr: {result.stderr.strip()}"


def root_follows_moved_project() -> tuple[bool, str]:
    """Copy paths.py into a fake relocated project; root must follow the copy."""
    with tempfile.TemporaryDirectory() as tmp:
        moved_root = Path(tmp) / "Moved Folder (copy)" / "CloudContextGuard"
        target = moved_root / "backend" / "app" / "core" / "paths.py"
        target.parent.mkdir(parents=True)
        shutil.copy2(Path(paths.__file__), target)
        result = subprocess.run(
            [sys.executable, "-c", "import runpy, sys; "
             "ns = runpy.run_path(sys.argv[1]); print(ns['PROJECT_ROOT']); print(ns['DATABASE_PATH'])",
             str(target)],
            cwd=tmp,
            env=_minimal_env(),
            capture_output=True,
            text=True,
        )
        lines = result.stdout.strip().splitlines()
        if result.returncode != 0 or len(lines) != 2:
            return False, result.stderr.strip()
        root, db = Path(lines[0]).resolve(), Path(lines[1]).resolve()
        expected = moved_root.resolve()
        ok = root == expected and db == expected / "data" / "cloud_security.db"
        return ok, f"root={root}, db={db}"


def _minimal_env() -> dict[str, str]:
    import os
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    return env


def main() -> int:
    print(LINE)
    print("CloudContextGuard")
    print("PORTABILITY VERIFICATION")
    print(LINE)
    print(f"Detected project root: {paths.PROJECT_ROOT}")
    print()

    report = Report()
    root = paths.PROJECT_ROOT

    # 1-2. Root is derived from the module's own location and exists.
    expected_root = Path(paths.__file__).resolve().parents[3]
    report.check(
        root == expected_root and root.is_dir() and (root / "backend" / "app" / "core" / "paths.py").is_file(),
        "Project root detected dynamically",
        f"PROJECT_ROOT={root}, expected={expected_root}",
    )
    ok, detail = root_independent_of_cwd()
    report.check(ok, "Project root independent of working directory", detail)
    ok, detail = root_follows_moved_project()
    report.check(ok, "Project root follows a moved project folder", detail)

    # 3-12. Every named path lives inside the project root.
    labels = [
        ("BACKEND_DIR", "Backend"),
        ("FRONTEND_DIR", "Frontend"),
        ("DATA_DIR", "Data"),
        ("LOG_DIR", "Log"),
        ("POLICY_DIR", "Policy"),
        ("SIMULATOR_DIR", "Simulator"),
        ("DOCS_DIR", "Documentation"),
        ("CONFIG_DIR", "Config"),
        ("TESTS_DIR", "Tests"),
        ("DATABASE_PATH", "Database"),
    ]
    for attr, label in labels:
        value = getattr(paths, attr)
        report.check(
            paths.is_inside_project(value) and value != root,
            f"{label} path is project-relative",
            f"{attr}={value}",
        )
    report.check(
        paths.DATABASE_PATH == root / "data" / "cloud_security.db",
        "Database path derived as data/cloud_security.db",
        f"DATABASE_PATH={paths.DATABASE_PATH}",
    )

    # 13. Required directories exist (or can be created).
    paths.ensure_directories()
    missing = [str(d.relative_to(root)) for d in paths.REQUIRED_DIRS if not d.is_dir()]
    report.check(not missing, "Required directories exist", f"missing: {missing}")

    # 14. No hardcoded absolute / machine-specific paths in source or config.
    scanned = iter_scanned_files()
    non_bat_leaks = find_path_leaks([f for f in scanned if f.suffix.lower() != ".bat"])
    report.check(
        not non_bat_leaks,
        f"No hardcoded Windows paths detected ({len(scanned)} files scanned)",
        "\n       ".join(non_bat_leaks),
    )

    # 15. Startup scripts locate the project from their own location.
    bat_files = sorted(root.glob("*.bat"))
    expected_bats = {"setup.bat", "start_backend.bat", "start_frontend.bat", "start_all.bat"}
    missing_bats = sorted(expected_bats - {b.name for b in bat_files})
    bat_leaks = find_path_leaks(bat_files)
    not_self_locating = [b.name for b in bat_files if "%~dp0" not in b.read_text(encoding="utf-8", errors="replace")]
    report.check(
        not missing_bats and not bat_leaks and not not_self_locating,
        "Startup scripts are portable",
        "\n       ".join(bat_leaks
                        + [f"{n}: does not use %~dp0" for n in not_self_locating]
                        + [f"missing script: {n}" for n in missing_bats]),
    )

    print()
    print(LINE)
    print(f"RESULT: {'PASS' if not report.failures else 'FAIL'}")
    print(LINE)
    return 0 if not report.failures else 1


if __name__ == "__main__":
    sys.exit(main())
