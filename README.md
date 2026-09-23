# CloudContextGuard

**Context-Aware Cloud Access Control Using IAM and Trusted VPC Boundaries**

CloudContextGuard is an academic cybersecurity project that will simulate
context-aware access control for cloud resources: access decisions combine
IAM-style identity permissions with contextual signals such as whether a
request originates from a trusted VPC boundary. Everything runs locally as a
simulation. No real cloud accounts, credentials or resources are used.

## Current development stage

**Step 1 - Portable Project Foundation**

Only the project skeleton, central path utility, startup script stubs and a
portability check exist so far. The API, engines, database and dashboard are
built in later steps.

## Portability

The project is designed to be moved freely:

- All paths are resolved dynamically at runtime from the location of the
  source files (`backend/app/core/paths.py`), not from the terminal's working
  directory.
- The project can be moved to another drive or folder (for example,
  `E:\Projects\CloudContextGuard`) without any source-code changes.
- The current development location is not hardcoded anywhere in the
  application, configuration or startup scripts. The `.bat` scripts locate the
  project from their own folder (`%~dp0`).
- Backend modules must import paths such as `PROJECT_ROOT`, `DATA_DIR` and
  `DATABASE_PATH` from `app.core.paths` instead of building their own.

## Layout

```
backend/app/core/   central path utility (paths.py)
frontend/           dashboard (later step)
data/               runtime data, e.g. cloud_security.db (git-ignored)
logs/               runtime logs (git-ignored)
policies/           access-control policies (later step)
simulator/          request/attack simulation (later step)
docs/               documentation
config/             configuration files
tests/              verification scripts
```

## Getting started (Windows)

```bat
setup.bat
python tests\verify_portability.py
```

`setup.bat` creates any missing runtime directories. `start_backend.bat`,
`start_frontend.bat` and `start_all.bat` currently only report the detected
project root, since those components are not implemented yet.

Configuration: copy `.env.example` to `.env` for local overrides. `.env` is
git-ignored and must never contain secrets or cloud credentials.
