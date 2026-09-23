# Authorization Flow Diagram

Reflects the exact processing order implemented in
`backend/app/services/access_service.py::evaluate_access_request`.

```mermaid
flowchart TD
    A["Access Request<br/>(POST /api/access/request)"] --> B["User Resolution<br/>(404 if user does not exist)"]
    B --> C["Resource Resolution<br/>(404 if resource does not exist)"]
    C --> D["IAM Evaluation<br/>(iam_engine.evaluate_iam)"]
    D --> E["VPC Evaluation<br/>(vpc_engine.evaluate_vpc,<br/>reads Policy.trusted_vpc_id)"]
    E --> F["Resource Policy Evaluation<br/>(policy_engine.evaluate_policy)"]
    F --> G["MFA Evaluation<br/>(policy_engine.evaluate_mfa)"]
    G --> H["Repeated-Failure Lookup<br/>(15-minute window)"]
    H --> I["Risk Calculation<br/>(risk_engine.calculate_risk)"]
    I --> J["Decision Engine<br/>(decision_engine.decide)"]
    J --> K["Persist AccessRequest"]
    K --> L{"Decision?"}
    L -->|"DENY"| M["Create SecurityEvent"]
    L -->|"ALLOW"| N["No SecurityEvent"]
    M --> O{"Risk HIGH/CRITICAL?"}
    N --> O
    O -->|"yes"| P["Create Alert"]
    O -->|"no"| Q["No Alert"]
    P --> R["API Response<br/>(AccessDecisionResponse)"]
    Q --> R
```

## Notes

- All five evaluations (IAM, VPC, policy, MFA, risk) run unconditionally
  on every request, regardless of whether an earlier one already fails -
  this is what allows the API response to explain every check, not just
  the first one that failed.
- Only the decision engine combines these results into a final
  ALLOW/DENY; no earlier step short-circuits the response.
- A `SecurityEvent` is created for every DENY (never for an ALLOW). An
  `Alert` is created for any HIGH/CRITICAL-risk request regardless of
  the final decision.
