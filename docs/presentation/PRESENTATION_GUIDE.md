# Presentation Guide

A structured 7-10 minute live demonstration of CloudContextGuard. Each
section below gives what to show, what to say, and the expected result,
so the presenter can prepare without needing to improvise. This guide
assumes the demo sequence in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md); the two
are meant to be used together (this guide for pacing and talking points,
the demo script for exact clicks and verified values).

Target total time: **7-10 minutes**. Suggested pacing is noted per
section; adjust based on audience familiarity.

## 1. Introduction (approx. 45 seconds)

**What to show:** the Dashboard (`/`), landing view.

**What to say:** "This is CloudContextGuard - a working simulation of
context-aware cloud access control. It answers one question: is a valid
IAM permission enough to grant access to a cloud resource? The answer
this project demonstrates, with a real running system, is no."

**Expected result:** dashboard loads with live metrics (not zeros unless
the database is freshly seeded); API status shows ONLINE.

## 2. Problem (approx. 45 seconds)

**What to show:** nothing new on screen; this is spoken over the
dashboard.

**What to say:** "Traditional IAM checks one thing: does this identity
have permission? A stolen credential inherits every permission that
identity has, from anywhere, with no extra friction. This project adds
independent checks - network origin, MFA, and a risk score - so a valid
permission alone is not sufficient."

**Expected result:** sets up the central claim the rest of the demo
proves.

## 3. Architecture (approx. 1 minute)

**What to show:** briefly describe (or, if presenting slides alongside,
show) the flow: Frontend -> API -> Access Service -> IAM / VPC / Policy
/ MFA / Risk engines -> Decision Engine -> Database -> Security Events /
Alerts -> Dashboard.

**What to say:** "Every engine is a pure function - it takes plain
inputs and returns a structured result, never just true or false. Only
one component, the decision engine, ever produces the final ALLOW or
DENY. The frontend never computes a decision itself - everything you'll
see is a live API response."

**Expected result:** audience understands that IAM, VPC, MFA, and risk
are independently evaluated, not layered ad hoc.

## 4. Legitimate Access (approx. 45 seconds)

**What to show:** Attack Simulator (`/simulator`), run "Legitimate
Developer Access."

**What to say:** "First, a baseline: a developer accessing their own
project data, from the trusted development network, with MFA. This
should simply work."

**Expected result:** IAM PASS, VPC PASS, MFA PASS, LOW risk, **ALLOW**.

## 5. Contextual Attack (approx. 1.5 minutes)

**What to show:** run "Trusted Identity, Untrusted Network"
(`contractor01`, `financial-records`, external network, no MFA,
SUSPICIOUS).

**What to say:** "Now the key scenario. `contractor01` genuinely has
permission to read financial records - this is not a broken or
misconfigured identity. But the request comes from an untrusted external
network, without MFA. Watch what happens to IAM specifically."

**Expected result:** **IAM PASS** (call this out explicitly), VPC FAIL,
MFA FAIL, CRITICAL risk (100), **FINAL: DENY**. "Valid identity detected,
but contextual authorization failed" - the exact wording used by the
system's own explanation.

## 6. Security Event (approx. 45 seconds)

**What to show:** Security Events page (`/security-events`).

**What to say:** "Every denied request creates a real, queryable audit
record - not a log line, a database row with structured fields."

**Expected result:** top row shows `event_type=BLOCKED_DATABASE_ACCESS`,
severity CRITICAL, `action_taken=BLOCKED`.

## 7. Alert (approx. 30 seconds)

**What to show:** Alerts page (`/alerts`).

**What to say:** "High and critical risk requests also raise an alert,
independent of whether they were denied - an allowed but risky request
would raise one too."

**Expected result:** top alert, severity CRITICAL, status OPEN.

## 8. Dynamic Policy Change (approx. 1.5 minutes)

**What to show:** Policies page (`/policies`), edit
`financial-records-policy`, change Trusted VPC from `vpc-finance` to
`vpc-development`.

**What to say:** "This policy isn't hardcoded - it's a database row an
administrator can change live. Because this is a security-sensitive
field, the system requires an explicit confirmation before saving."

**Expected result:** confirmation step appears with a warning and a
before/after diff; save succeeds; a `POLICY_CHANGED` security event is
created (visible on the Security Events page if time allows).

## 9. Re-test (approx. 1 minute)

**What to show:** submit the same `contractor01`/`financial-records`
request again, now from `vpc-development`, with MFA provided.

**What to say:** "Same identity, same resource - but now the network
matches what the policy currently trusts, with no code change and no
restart."

**Expected result:** IAM PASS, **VPC PASS** (expected VPC shown as
`vpc-development` - proof the live database value was used), risk 40
(MEDIUM), decision ALLOW - determined by the remaining controls, not
predetermined. Then restore the policy to `vpc-finance` before ending.

## 10. Conclusion (approx. 45 seconds)

**What to show:** Dashboard, updated metrics.

**What to say:** "To summarize: this system independently enforces
identity, network, MFA, policy, and risk. A valid permission was denied
because of context, and a policy change - made live, by an
administrator - was applied to the very next request. Everything shown
was a real API response; nothing was simulated in the frontend."

**Expected result:** dashboard reflects every action performed during
the demo (total requests, denied count, critical events, open alerts all
increased).

## General Presenter Notes

- Keep the tone natural - narrate what the system is doing, don't read
  this guide verbatim.
- If a live demo step fails unexpectedly, fall back to the verified
  values in [`../research/RESULTS.md`](../research/RESULTS.md) and
  [`../research/DYNAMIC_POLICY_EVALUATION.md`](../research/DYNAMIC_POLICY_EVALUATION.md)
  rather than improvising a different number.
- Always state plainly that this is a local simulation - no real AWS
  account or credential is involved anywhere in this project.
