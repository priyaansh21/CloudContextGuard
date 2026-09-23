# Threat Model Diagram

A generalized view of every threat scenario in
[`THREAT_MODEL.md`](../../THREAT_MODEL.md); each is a real request
submitted to the running application, never a real-world attack.

```mermaid
flowchart TD
    A["External Actor<br/>(simulated)"] --> B["Compromised or Misused Credential<br/>(a genuinely valid identity, used unexpectedly)"]
    B --> C["Access Request<br/>(POST /api/access/request)"]
    C --> D["Context Evaluation"]
    D --> E["IAM"]
    D --> F["VPC"]
    D --> G["MFA"]
    D --> H["Risk"]
    E --> I{"Decision Engine"}
    F --> I
    G --> I
    H --> I
    I -->|"any check fails,<br/>or risk >= 60"| J["DENY"]
    I -->|"all checks pass,<br/>and risk < 60"| K["ALLOW"]
    J --> L["SecurityEvent recorded"]
    J --> M{"Risk HIGH/CRITICAL?"}
    K --> M
    M -->|"yes"| N["Alert raised"]
```

## Interpretation

A valid identity (IAM PASS) reaching the decision engine is not, by
itself, evidence that access should be granted - VPC, MFA, and risk are
evaluated independently and any one of them can still produce DENY. This
diagram generalizes threats T1-T5 from the threat model (compromised
credential, wrong network, missing MFA, unauthorized resource,
privilege escalation); T6 (repeated requests) is reflected in the Risk
box via the repeated-failure factor, and T7 (sensitive storage exposure)
is a configuration-review concern rather than a per-request decision
path and is therefore not part of this per-request flow.
