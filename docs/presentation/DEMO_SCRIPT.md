# Demo Script

A step-by-step live demonstration sequence using the actual running
application. Every value referenced below (event types, field names,
numbers) is taken from the real implementation and has been verified
against a live run - none of it is illustrative or approximate.

**Prerequisite:** both servers running (`start_all.bat`, or
`start_backend.bat` and `start_frontend.bat` separately). Frontend at
`http://127.0.0.1:5173`, backend at `http://127.0.0.1:8000`.

## Sequence

**1. Open the dashboard.**
Navigate to `http://127.0.0.1:5173/`.

**2. Show the healthy system.**
Point out the sidebar's API Status (ONLINE) and Database (CONNECTED)
indicators, and the Security Posture row (IAM: ACTIVE, VPC: PROTECTED,
STORAGE: PROTECTED, POLICY ENGINE: ACTIVE) - all computed from live
data, not hardcoded.

**3. Open Policies.**
Navigate to `/policies`.

**4. Show `financial-records-policy`.**
Locate the row for resource `financial-records`.

**5. Show Trusted VPC = `vpc-finance`.**
Point at the "Trusted VPC" column value for this row.

**6. Open Attack Simulator.**
Navigate to `/simulator`.

**7. Run "Legitimate Developer Access."**
Click RUN SIMULATION on the first scenario card
(`developer01`, `GetObject`, `project-data`, `vpc-development`, MFA
true).

**8. Show ALLOW.**
Point at the result panel: IAM PASS, VPC PASS, MFA PASS, LOW risk,
**FINAL DECISION: ALLOW**.

**9. Run "Trusted Identity, Untrusted Network."**
Click RUN SIMULATION on that scenario card (`contractor01`, `GetObject`,
`financial-records`, source IP `185.22.91.11`, source VPC `external`,
MFA false, `request_type="SUSPICIOUS"`).

**10. Show IAM PASS.**
Point at the IAM badge in the result panel - green, PASS. Note aloud:
`ContractorRole` genuinely does hold `GetObject:financial-records`.

**11. Show VPC FAIL.**
Point at the VPC badge - red, FAIL. Expected VPC `vpc-finance`, actual
`external`.

**12. Show MFA FAIL.**
Point at the MFA badge - red, FAIL. MFA was required and not provided.

**13. Show CRITICAL risk.**
Point at the risk badge - CRITICAL (100). Optionally expand the "Risk
Factors" list: External network (+40), CONFIDENTIAL resource (+30),
Missing MFA (+30), Unknown/untrusted source (+20), Suspicious request
(+20) - capped at 100.

**14. Show DENY.**
Point at the "ACCESS BLOCKED" banner and **FINAL DECISION: DENY**.

**15. Open Security Events.**
Navigate to `/security-events`.

**16. Show the actual event created.**
The top row: `event_type="BLOCKED_DATABASE_ACCESS"` (derived from
`financial-records`'s `resource_type="database"` -
`f"BLOCKED_{resource_family}_ACCESS"` in
`access_service.py::_build_security_event`), severity CRITICAL,
`action_taken="BLOCKED"`.

**17. Open Alerts.**
Navigate to `/alerts`.

**18. Show the critical alert.**
The top alert: severity CRITICAL, status OPEN, linked to the request
just submitted.

**19. Return to Policies.**
Navigate back to `/policies`.

**20. Change the trusted VPC for demonstration.**
Click Edit on `financial-records-policy`, change Trusted VPC to
`vpc-development`, click SAVE POLICY. Because this is a
security-sensitive field, a confirmation step appears
("Changing this policy will alter authorization decisions for protected
resources.") - click CONFIRM POLICY CHANGE. Point out the success
screen's before/after diff: `Trusted VPC: vpc-finance -> vpc-development`.

**21. Re-run a request from the new trusted VPC.**
Return to `/simulator`, or submit directly:
`contractor01`, `GetObject`, `financial-records`, source VPC
`vpc-development`, MFA true.

**22. Show the re-evaluation.**
IAM PASS, and now **VPC PASS** as well - the expected VPC shown is
`vpc-development`, proving the live database value was used, not a
cached or compiled-in one. Point out the risk score (40, MEDIUM) and the
resulting decision (ALLOW), noting this was determined by the remaining
risk controls, not hardcoded.

**23. Restore the original secure policy.**
Return to `/policies`, edit `financial-records-policy` again, set
Trusted VPC back to `vpc-finance`, confirm, and save. Optionally re-run
an external request to show DENY returns.

**24. End.**
Return to the Dashboard and point out the updated metrics (Total
Requests, Denied, Critical Events, Open Alerts) reflecting every action
just performed.
