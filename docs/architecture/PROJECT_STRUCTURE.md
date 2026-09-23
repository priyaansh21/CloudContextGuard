# CloudContextGuard - Project Structure

This document reflects the actual repository layout. Generated/runtime
directories (`backend/.venv/`, `backend/**/__pycache__/`,
`frontend/node_modules/`, `frontend/dist/`, `data/*.db`,
`logs/*.log`) are git-ignored and omitted below; see the root
`.gitignore`.

## Top-Level Layout

```
CloudContextGuard/
├── backend/                  FastAPI application, engines, tests
├── frontend/                 React (Vite) single-page application
├── tests/
│   └── verify_portability.py Standalone portability verification script
├── data/                     Runtime SQLite database (git-ignored)
├── logs/                     Runtime application log (git-ignored)
├── docs/                     Documentation (this file and others)
├── config/                   Reserved for future configuration files
├── policies/                 Reserved for future file-based policy artifacts
├── simulator/                Reserved for future standalone simulator tooling
├── .env.example              Example environment configuration (no secrets)
├── .gitignore
├── README.md
├── PROJECT_DOCUMENTATION.md
├── THREAT_MODEL.md
├── API_DOCUMENTATION.md
├── setup.bat                 Creates required runtime directories
├── start_backend.bat         Launches the FastAPI backend (uvicorn)
├── start_frontend.bat        Launches the Vite frontend dev server
└── start_all.bat             Launches both, each in its own window
```

`config/`, `policies/`, and `simulator/` are directories the project's
own path utility (`backend/app/core/paths.py`) reserves and creates at
startup for potential future use; they are currently empty and not read
by any implemented feature.

## Backend (`backend/`)

```
backend/
├── requirements.txt
├── app/
│   ├── main.py                    FastAPI app, lifespan, routers, security headers
│   ├── cli.py                     Standalone developer CLI (reset-demo-db); never imported by main.py
│   ├── core/
│   │   ├── paths.py                Central, dynamically-resolved path utility
│   │   ├── config.py               Settings (env-driven, CORS origins, DB path)
│   │   └── logging_config.py       Rotating file + console logger setup
│   ├── db/
│   │   ├── database.py             Engine/session setup, schema-version safety
│   │   └── models.py                SQLAlchemy ORM models (see table list below)
│   ├── schemas/
│   │   ├── access.py                AccessRequestIn, AccessDecisionResponse, AccessRequestOut
│   │   ├── catalog.py               User/Role/Permission/Resource/VPC/Policy Out + PolicyUpdate
│   │   ├── security.py              SecurityEventOut, AlertOut
│   │   ├── dashboard.py             DashboardResponse
│   │   ├── engine_results.py        IAMResult, VPCResult, PolicyResult, MFAResult, RiskFactor, RiskResult, DecisionResult
│   │   └── health.py                HealthResponse
│   ├── engine/
│   │   ├── iam_engine.py            evaluate_iam()
│   │   ├── vpc_engine.py            evaluate_vpc()
│   │   ├── policy_engine.py         evaluate_policy(), evaluate_mfa()
│   │   ├── risk_engine.py           calculate_risk()
│   │   └── decision_engine.py       decide() - the sole ALLOW/DENY authority
│   ├── services/
│   │   ├── access_service.py        Orchestrates one request through every engine; persists outcome
│   │   ├── policy_service.py        Validated, audited policy updates
│   │   ├── dashboard_service.py     Live aggregation for the dashboard
│   │   └── seed_service.py          Idempotent baseline + contractor01 seeding
│   └── api/
│       ├── access.py                 POST /api/access/request, GET /api/access/requests
│       ├── catalog.py                 GET /api/users|roles|permissions|resources|vpcs
│       ├── policies.py                GET/PUT /api/policies[...]
│       ├── security.py                GET /api/security/events, GET /api/alerts
│       ├── dashboard.py               GET /api/dashboard
│       └── database.py                POST /api/database/seed
└── tests/
    ├── test_health.py                 5 tests - liveness, docs availability
    ├── test_access_control.py         17 tests - IAM/VPC/MFA/risk/policy, contractor01 scenarios
    ├── test_policy_management.py      10 tests - policy CRUD, validation, dynamic-policy demonstration
    ├── test_database_safety.py        9 tests - schema-version safety, persistence, explicit reset
    └── test_security_validation.py    41 tests - Step 7 comprehensive security validation
```

## Database Tables (`backend/app/db/models.py`)

| Table | Purpose |
|---|---|
| `roles` | Named roles (e.g. `DeveloperRole`, `ContractorRole`). |
| `users` | Simulated identities (username, display name, role, active flag). |
| `permissions` | Role -> action/resource-pattern grants (IAM). |
| `resources` | Simulated protected resources (classification, baseline VPC/MFA/external-access defaults). |
| `vpcs` | Simulated network boundaries (CIDR, trust level, `is_trusted`). |
| `policies` | The live, administrator-editable authorization configuration per resource. |
| `access_requests` | Full audit record of every evaluated request and its outcome. |
| `security_events` | Denied-request and policy-change security log. |
| `alerts` | HIGH/CRITICAL-risk alerts, linked to their originating request. |
| `schema_version` | Single-row schema-compatibility stamp (Step 6.1 database safety mechanism). |

## Frontend (`frontend/`)

```
frontend/
├── package.json / package-lock.json
├── vite.config.js                    Vite + Tailwind plugin, dev server on 127.0.0.1:5173
├── index.html
├── .env.example                       VITE_API_BASE_URL
├── public/
│   ├── favicon.svg
│   └── icons.svg
└── src/
    ├── main.jsx / App.jsx              Entry point, React Router routes
    ├── index.css                       Tailwind import + dark SOC theme tokens
    ├── services/api.js                 Centralized API client (every network call)
    ├── hooks/useApi.js                 Data-fetching + shared health-polling hooks
    ├── utils/formatting.js             Date/tone/color helpers
    ├── data/simulationScenarios.js     Attack Simulator scenario definitions (inputs only)
    ├── pages/                          Dashboard, AccessRequests, IAM, VPCSecurity, Storage,
    │                                   SecurityEvents, Alerts, Policies, Simulator
    └── components/
        ├── layout/                     Sidebar, TopBar, Layout
        ├── common/                     Card, Badge, Modal, ErrorState, EmptyState, LoadingState,
        │                               SearchInput, SelectFilter, Pagination
        ├── dashboard/                  MetricCard, PostureCard, DecisionChart, RiskChart,
        │                               DistributionBarChart, RecentEventsPanel
        ├── security/                   AccessDecisionCard, DecisionBadge, RiskBadge, SeverityBadge,
        │                               PassFailBadge, AccessBlockedBanner, AttackTimeline,
        │                               AccessRequestDetailModal, SecurityEventDetailModal,
        │                               PolicyDetailModal, PolicyEditorModal, ScenarioCard,
        │                               SimulationResultPanel, RiskFactorsList
        └── tables/                     TableShell
```

## Documentation (`docs/`)

```
docs/
├── architecture/
│   └── PROJECT_STRUCTURE.md            This file
├── diagrams/
│   ├── system-architecture.md
│   ├── authorization-flow.md
│   └── threat-model.md
├── research/
│   ├── SECURITY_DECISION_MODEL.md
│   ├── DYNAMIC_POLICY_EVALUATION.md
│   ├── METHODOLOGY.md
│   └── RESULTS.md
├── presentation/
│   ├── PRESENTATION_GUIDE.md
│   ├── VIVA_QUESTIONS.md
│   └── DEMO_SCRIPT.md
└── screenshots/                         Reserved for presentation screenshots
```
