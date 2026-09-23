# System Architecture Diagram

Reflects the actual implemented components (`backend/app/main.py`,
`backend/app/services/access_service.py`, `backend/app/engine/*.py`,
`backend/app/db/models.py`, `frontend/src/`).

```mermaid
flowchart TD
    FE["React Frontend<br/>(Vite dev server, 127.0.0.1:5173)"]
    API["FastAPI API<br/>(backend/app/main.py)"]
    SVC["Access Service<br/>(access_service.py)"]

    subgraph ENGINES["Security Engines (pure functions)"]
        IAM["IAM Engine"]
        VPC["VPC Engine"]
        POL["Policy Engine (+ MFA)"]
        RISK["Risk Engine"]
    end

    DEC["Decision Engine<br/>(sole ALLOW/DENY authority)"]
    DB[("SQLite Database<br/>roles, users, permissions,<br/>resources, vpcs, policies,<br/>access_requests, security_events,<br/>alerts, schema_version")]
    SE["Security Events"]
    AL["Alerts"]
    DASH["Dashboard Aggregation"]

    FE -->|"HTTP / JSON"| API
    API --> SVC
    SVC --> IAM
    SVC --> VPC
    SVC --> POL
    SVC --> RISK
    IAM --> DEC
    VPC --> DEC
    POL --> DEC
    RISK --> DEC
    DEC --> SVC
    SVC -->|"persist AccessRequest"| DB
    SVC -->|"on DENY"| SE
    SVC -->|"on HIGH/CRITICAL risk"| AL
    SE --> DB
    AL --> DB
    DB --> DASH
    DASH -->|"HTTP / JSON"| FE
```

## Notes

- The frontend never computes a security decision; every value shown is
  read from an API response.
- Every engine is a pure function (plain inputs in, a structured result
  out) - none of them query the database directly. Only the access
  service (and, for policy edits, the policy service) touches the
  database.
- The decision engine is the only component that produces a final
  ALLOW/DENY value.
