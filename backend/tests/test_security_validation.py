"""
Step 7 comprehensive security validation for CloudContextGuard.

Uses the project's real database and API, exactly like the rest of this
suite. Covers server-side authorization, IAM/VPC/MFA/risk/policy
enforcement (including engine-level unit checks for risk scoring and
decision thresholds), audit/alert integrity, input validation, injection
resistance, mass-assignment resistance, and database integrity.
"""

from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from app.core.paths import DATABASE_PATH
from app.db.database import SessionLocal
from app.engine.decision_engine import decide
from app.engine.risk_engine import calculate_risk
from app.main import app
from app.schemas.engine_results import IAMResult, MFAResult, PolicyResult, VPCResult
from app.services.seed_service import ensure_contractor_identity, seed_if_empty

EDITABLE_POLICY_FIELDS = (
    "name",
    "description",
    "required_role",
    "trusted_vpc",
    "mfa_required",
    "max_risk_score",
    "external_access_allowed",
    "is_enabled",
)


def _client() -> TestClient:
    return TestClient(app)


def _seed() -> None:
    db = SessionLocal()
    try:
        seed_if_empty(db)
        ensure_contractor_identity(db)
    finally:
        db.close()


def _submit(client: TestClient, expect_status: int = 200, **kwargs) -> dict:
    response = client.post("/api/access/request", json=kwargs)
    assert response.status_code == expect_status, response.text
    return response.json()


def _financial_records_policy(client: TestClient) -> dict:
    return next(p for p in client.get("/api/policies").json() if p["resource"] == "financial-records")


def _update_payload(policy: dict, **overrides) -> dict:
    payload = {field: policy[field] for field in EDITABLE_POLICY_FIELDS}
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# 1. SERVER-SIDE AUTHORIZATION
# ---------------------------------------------------------------------------


def test_server_cannot_be_forced_to_allow_via_client_supplied_decision() -> None:
    with _client() as client:
        _seed()
        # A request that should genuinely be denied (no IAM permission),
        # with the client attempting to smuggle a forced ALLOW.
        response = client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "financial-records",
                "source_vpc": "external",
                "mfa": False,
                "request_type": "SUSPICIOUS",
                "decision": "ALLOW",
                "risk_score": 0,
                "risk_level": "LOW",
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "DENY"
    assert body["iam_result"]["result"] == "FAIL"


# ---------------------------------------------------------------------------
# 2. IAM TESTS
# ---------------------------------------------------------------------------


def test_iam_a_valid_user_valid_permission_passes() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["iam_result"]["result"] == "PASS"


def test_iam_b_valid_user_unauthorized_action_fails() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="developer01",
            action="DeleteObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["iam_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


def test_iam_c_valid_user_unauthorized_resource_fails() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="credentials-vault",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["iam_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


def test_iam_d_unknown_user_returns_clean_error() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "no-such-user",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            },
        )
    assert response.status_code == 404
    assert "detail" in response.json()


def test_iam_e_inactive_user_is_denied() -> None:
    from app.db.models import User

    with _client() as client:
        _seed()
        db = SessionLocal()
        try:
            if db.query(User).filter_by(username="inactive-test-user").first() is None:
                db.add(User(username="inactive-test-user", display_name="Inactive", role_id=None, is_active=False))
                db.commit()
        finally:
            db.close()

        body = _submit(
            client,
            user="inactive-test-user",
            action="GetObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["iam_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


# ---------------------------------------------------------------------------
# 3. VPC TESTS
# ---------------------------------------------------------------------------


def test_vpc_a_correct_trusted_vpc_passes() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="finance01",
            action="GetObject",
            resource="financial-records",
            source_vpc="vpc-finance",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["vpc_result"]["result"] == "PASS"


def test_vpc_b_wrong_trusted_vpc_fails() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="finance01",
            action="GetObject",
            resource="financial-records",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["vpc_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


def test_vpc_c_external_network_to_protected_resource_fails() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="finance01",
            action="GetObject",
            resource="financial-records",
            source_vpc="external",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["vpc_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


def test_vpc_d_external_network_to_explicitly_public_resource_follows_policy() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="public-assets",
            source_vpc="external",
            mfa=False,
            request_type="NORMAL",
        )
    assert body["vpc_result"]["result"] == "PASS"
    assert body["decision"] == "ALLOW"


# ---------------------------------------------------------------------------
# 4. MFA TESTS
# ---------------------------------------------------------------------------


def test_mfa_required_and_provided_passes() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="finance01",
            action="GetObject",
            resource="financial-records",
            source_vpc="vpc-finance",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["mfa_result"]["result"] == "PASS"


def test_mfa_required_and_missing_fails_and_denies() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="finance01",
            action="GetObject",
            resource="financial-records",
            source_vpc="vpc-finance",
            mfa=False,
            request_type="NORMAL",
        )
    assert body["mfa_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


def test_mfa_not_required_and_missing_does_not_deny_on_mfa_alone() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=False,
            request_type="NORMAL",
        )
    assert body["mfa_result"]["required"] is False
    assert body["mfa_result"]["result"] == "PASS"
    assert body["decision"] == "ALLOW"


# ---------------------------------------------------------------------------
# 5. RISK FACTOR UNIT TESTS (engine-level, each factor isolated)
# ---------------------------------------------------------------------------


def _risk(**overrides) -> dict:
    defaults = dict(
        vpc_check_failed=False,
        resource_classification=None,
        mfa_required=False,
        mfa_provided=True,
        source_vpc_trusted=True,
        repeated_failed_count=0,
        request_type="NORMAL",
        username="test-user",
    )
    defaults.update(overrides)
    result = calculate_risk(**defaults)
    return {"score": result.score, "level": result.level, "factor_names": [f.name for f in result.factors]}


def test_risk_factor_external_network_is_40() -> None:
    out = _risk(vpc_check_failed=True)
    assert out["score"] == 40
    assert "External network" in out["factor_names"]


def test_risk_factor_confidential_is_30() -> None:
    out = _risk(resource_classification="CONFIDENTIAL")
    assert out["score"] == 30


def test_risk_factor_restricted_is_40() -> None:
    out = _risk(resource_classification="RESTRICTED")
    assert out["score"] == 40


def test_risk_factor_missing_mfa_is_30() -> None:
    out = _risk(mfa_required=True, mfa_provided=False)
    assert out["score"] == 30


def test_risk_factor_untrusted_source_is_20() -> None:
    out = _risk(source_vpc_trusted=False)
    assert out["score"] == 20


def test_risk_factor_repeated_failures_is_10() -> None:
    out = _risk(repeated_failed_count=2)
    assert out["score"] == 10


def test_risk_factor_suspicious_request_is_20() -> None:
    out = _risk(request_type="SUSPICIOUS")
    assert out["score"] == 20


def test_risk_score_never_exceeds_100() -> None:
    out = _risk(
        vpc_check_failed=True,
        resource_classification="RESTRICTED",
        mfa_required=True,
        mfa_provided=False,
        source_vpc_trusted=False,
        repeated_failed_count=5,
        request_type="SUSPICIOUS",
    )
    assert out["score"] == 100


def test_risk_levels_match_documented_bands() -> None:
    assert calculate_risk(
        vpc_check_failed=False, resource_classification=None, mfa_required=False, mfa_provided=True,
        source_vpc_trusted=True, repeated_failed_count=0, request_type="NORMAL", username="u",
    ).level == "LOW"
    assert calculate_risk(
        vpc_check_failed=False, resource_classification="CONFIDENTIAL", mfa_required=False, mfa_provided=True,
        source_vpc_trusted=True, repeated_failed_count=0, request_type="NORMAL", username="u",
    ).level == "MEDIUM"  # 30
    assert calculate_risk(
        vpc_check_failed=True, resource_classification=None, mfa_required=False, mfa_provided=True,
        source_vpc_trusted=False, repeated_failed_count=0, request_type="NORMAL", username="u",
    ).level == "HIGH"  # 40 + 20 = 60
    assert calculate_risk(
        vpc_check_failed=True, resource_classification="RESTRICTED", mfa_required=False, mfa_provided=True,
        source_vpc_trusted=True, repeated_failed_count=0, request_type="NORMAL", username="u",
    ).level == "CRITICAL"  # 40 + 40 = 80


# ---------------------------------------------------------------------------
# 6. RISK DECISION UNIT TESTS (engine-level, decision thresholds isolated)
# ---------------------------------------------------------------------------


def _passing_iam() -> IAMResult:
    return IAMResult(allowed=True, result="PASS", reason="ok", matched_permission="GetObject:x")


def _passing_vpc() -> VPCResult:
    return VPCResult(allowed=True, result="PASS", reason="ok", expected_vpc="vpc-x", actual_vpc="vpc-x")


def _passing_policy() -> PolicyResult:
    return PolicyResult(
        allowed=True, result="PASS", reason="ok", is_enabled=True, required_role=None,
        trusted_vpc_required=False, mfa_required=False, external_access_allowed=True, max_risk_score=None,
    )


def _passing_mfa() -> MFAResult:
    return MFAResult(required=False, provided=False, result="PASS", reason="not required")


def _decide_with_risk(score: int, level: str) -> str:
    from app.schemas.engine_results import RiskResult

    return decide(
        iam_result=_passing_iam(),
        vpc_result=_passing_vpc(),
        policy_result=_passing_policy(),
        mfa_result=_passing_mfa(),
        risk_result=RiskResult(score=score, level=level, factors=[]),
        source_is_external=False,
    ).decision


def test_risk_80_denies() -> None:
    assert _decide_with_risk(80, "CRITICAL") == "DENY"


def test_risk_60_denies() -> None:
    assert _decide_with_risk(60, "HIGH") == "DENY"


def test_risk_below_60_continues_through_policy_controls() -> None:
    assert _decide_with_risk(59, "MEDIUM") == "ALLOW"


def test_decision_never_bypasses_iam_regardless_of_risk() -> None:
    from app.schemas.engine_results import RiskResult

    failing_iam = IAMResult(allowed=False, result="FAIL", reason="no permission", matched_permission=None)
    result = decide(
        iam_result=failing_iam,
        vpc_result=_passing_vpc(),
        policy_result=_passing_policy(),
        mfa_result=_passing_mfa(),
        risk_result=RiskResult(score=0, level="LOW", factors=[]),
        source_is_external=False,
    )
    assert result.decision == "DENY"


# ---------------------------------------------------------------------------
# 7 & 8. POLICY ENFORCEMENT AND DISABLED-POLICY TEST
# ---------------------------------------------------------------------------


def test_disabled_policy_denies_access_then_is_restored() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        assert policy["is_enabled"] is True

        disable_response = client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy, is_enabled=False))
        assert disable_response.status_code == 200
        assert disable_response.json()["is_enabled"] is False

        try:
            body = _submit(
                client,
                user="finance01",
                action="GetObject",
                resource="financial-records",
                source_vpc="vpc-finance",
                mfa=True,
                request_type="NORMAL",
            )
            assert body["decision"] == "DENY"
            assert body["resource_result"]["result"] == "FAIL"
        finally:
            restore_response = client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy, is_enabled=True))
            assert restore_response.status_code == 200
            assert restore_response.json()["is_enabled"] is True


# ---------------------------------------------------------------------------
# 10. AUDIT INTEGRITY
# ---------------------------------------------------------------------------


def test_audit_record_fields_match_the_actual_request() -> None:
    with _client() as client:
        _seed()
        payload = dict(
            user="finance01",
            action="GetObject",
            resource="financial-records",
            source_ip="203.0.113.9",
            source_vpc="vpc-finance",
            mfa=True,
            request_type="NORMAL",
        )
        decision_response = _submit(client, **payload)
        request_id = decision_response["request_id"]

        rows = client.get("/api/access/requests", params={"limit": 500}).json()
        stored = next(r for r in rows if r["id"] == request_id)

    assert stored["user"] == payload["user"]
    assert stored["action"] == payload["action"]
    assert stored["resource"] == payload["resource"]
    assert stored["source_ip"] == payload["source_ip"]
    assert stored["source_vpc"] == payload["source_vpc"]
    assert stored["mfa"] == payload["mfa"]
    assert stored["request_type"] == payload["request_type"]
    assert stored["final_decision"] == decision_response["decision"]
    assert stored["risk_score"] == decision_response["risk_score"]
    assert stored["risk_level"] == decision_response["risk_level"]
    assert stored["timestamp"] == decision_response["timestamp"]


def test_denied_request_creates_security_event_allowed_does_not() -> None:
    with _client() as client:
        _seed()
        before = client.get("/api/security/events", params={"limit": 500}).json()

        denied = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="credentials-vault",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
        assert denied["decision"] == "DENY"
        after_deny = client.get("/api/security/events", params={"limit": 500}).json()

        allowed = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
        assert allowed["decision"] == "ALLOW"
        after_allow = client.get("/api/security/events", params={"limit": 500}).json()

    assert len(after_deny) == len(before) + 1
    assert len(after_allow) == len(after_deny)  # the ALLOW created no event


# ---------------------------------------------------------------------------
# 11. ALERT INTEGRITY
# ---------------------------------------------------------------------------


def test_alert_severity_matches_risk_and_starts_open_no_duplicates() -> None:
    with _client() as client:
        _seed()
        response = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="financial-records",
            source_ip="185.22.91.11",
            source_vpc="external",
            mfa=False,
            request_type="SUSPICIOUS",
        )
        assert response["risk_level"] in ("HIGH", "CRITICAL")

        alerts = client.get("/api/alerts", params={"limit": 500}).json()
        matching = [a for a in alerts if a["access_request_id"] == response["request_id"]]

    assert len(matching) == 1  # exactly one alert - no duplicates
    assert matching[0]["severity"] == response["risk_level"]
    assert matching[0]["status"] == "OPEN"


def test_low_risk_allowed_request_creates_no_alert() -> None:
    with _client() as client:
        _seed()
        response = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
        alerts = client.get("/api/alerts", params={"limit": 500}).json()
        matching = [a for a in alerts if a["access_request_id"] == response["request_id"]]

    assert response["risk_level"] not in ("HIGH", "CRITICAL")
    assert len(matching) == 0


# ---------------------------------------------------------------------------
# 12. INPUT VALIDATION
# ---------------------------------------------------------------------------


def test_missing_required_fields_return_422() -> None:
    with _client() as client:
        _seed()
        for missing_field in ("user", "action", "resource", "source_vpc"):
            payload = {
                "user": "developer01",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            }
            del payload[missing_field]
            response = client.post("/api/access/request", json=payload)
            assert response.status_code == 422, f"missing {missing_field} should be 422"
            assert "Traceback" not in response.text


def test_invalid_mfa_type_returns_422() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": "not-a-boolean",
                "request_type": "NORMAL",
            },
        )
    assert response.status_code == 422


def test_invalid_request_type_returns_422() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NOT_A_REAL_TYPE",
            },
        )
    assert response.status_code == 422


def test_invalid_source_vpc_and_resource_and_action_do_not_crash() -> None:
    with _client() as client:
        _seed()
        # Unknown source_vpc: a valid string, just not a known VPC - treated
        # as an untrusted/unrecognized network, not a validation error.
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="project-data",
            source_vpc="totally-unknown-vpc",
            mfa=True,
            request_type="NORMAL",
        )
        assert body["vpc_result"]["result"] == "FAIL"

        # Unknown resource: clean 404, not a crash.
        response = client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "no-such-resource",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            },
        )
        assert response.status_code == 404

        # Unknown action: a valid string, just not permitted - IAM FAIL, not a crash.
        body2 = _submit(
            client,
            user="developer01",
            action="TotallyMadeUpAction",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
        assert body2["iam_result"]["result"] == "FAIL"


# ---------------------------------------------------------------------------
# 13. INJECTION TESTS
# ---------------------------------------------------------------------------


def test_sql_like_input_is_treated_as_plain_data() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "' OR 1=1 --",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            },
        )
    assert response.status_code == 404  # no such user - not a SQL error, not a bypass

    # The database itself must remain intact and queryable afterward.
    with sqlite3.connect(DATABASE_PATH) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0


def test_html_and_script_like_input_is_treated_as_plain_data() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "<script>alert(1)</script>",
                "action": "GetObject",
                "resource": "project-data",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            },
        )
    assert response.status_code == 404
    assert "<script>" not in response.text or response.json()["detail"]


def test_path_traversal_like_input_is_treated_as_plain_data() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "../../database.db",
                "source_vpc": "vpc-development",
                "mfa": True,
                "request_type": "NORMAL",
            },
        )
    assert response.status_code == 404  # no such resource - no filesystem access occurred
    assert DATABASE_PATH.exists()  # the real database file is untouched


# ---------------------------------------------------------------------------
# 14. MASS-ASSIGNMENT TEST
# ---------------------------------------------------------------------------


def test_client_supplied_security_fields_are_ignored() -> None:
    with _client() as client:
        _seed()
        response = client.post(
            "/api/access/request",
            json={
                "user": "developer01",
                "action": "GetObject",
                "resource": "financial-records",
                "source_ip": "185.22.91.11",
                "source_vpc": "external",
                "mfa": False,
                "request_type": "SUSPICIOUS",
                # Attempted overrides of server-controlled fields:
                "role": "AdminRole",
                "is_admin": True,
                "decision": "ALLOW",
                "risk_score": 0,
                "risk_level": "LOW",
                "severity": "LOW",
                "action_taken": "NONE",
            },
        )
    assert response.status_code == 200
    body = response.json()
    # The genuinely-computed values must reflect reality, not the client's claims.
    assert body["decision"] == "DENY"
    assert body["risk_score"] > 0
    assert body["risk_level"] in ("HIGH", "CRITICAL")


# ---------------------------------------------------------------------------
# 15. POLICY MASS-ASSIGNMENT TEST
# ---------------------------------------------------------------------------


def test_policy_protected_fields_cannot_be_overridden_via_put() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        payload = _update_payload(policy)
        payload["id"] = 999999
        payload["resource_id"] = 999999
        payload["created_at"] = "1999-01-01T00:00:00"
        payload["updated_at"] = "1999-01-01T00:00:00"

        response = client.put(f"/api/policies/{policy['id']}", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == policy["id"]  # unchanged - the path parameter, not the body, selects the row
    assert body["resource"] == policy["resource"]  # unchanged
    assert body["created_at"] == policy["created_at"]  # unchanged
    assert body["updated_at"] != "1999-01-01T00:00:00"  # server-stamped, not client-supplied


# ---------------------------------------------------------------------------
# 16. DATABASE INTEGRITY
# ---------------------------------------------------------------------------


def test_foreign_keys_valid_and_no_orphaned_rows() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert fk_violations == []

        orphan_checks = {
            "access_requests.user_id": "SELECT COUNT(*) FROM access_requests WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM users)",
            "access_requests.resource_id": "SELECT COUNT(*) FROM access_requests WHERE resource_id IS NOT NULL AND resource_id NOT IN (SELECT id FROM resources)",
            "policies.resource_id": "SELECT COUNT(*) FROM policies WHERE resource_id IS NOT NULL AND resource_id NOT IN (SELECT id FROM resources)",
            "policies.trusted_vpc_id": "SELECT COUNT(*) FROM policies WHERE trusted_vpc_id IS NOT NULL AND trusted_vpc_id NOT IN (SELECT id FROM vpcs)",
            "users.role_id": "SELECT COUNT(*) FROM users WHERE role_id IS NOT NULL AND role_id NOT IN (SELECT id FROM roles)",
            "permissions.role_id": "SELECT COUNT(*) FROM permissions WHERE role_id NOT IN (SELECT id FROM roles)",
            "alerts.access_request_id": "SELECT COUNT(*) FROM alerts WHERE access_request_id IS NOT NULL AND access_request_id NOT IN (SELECT id FROM access_requests)",
        }
        for label, sql in orphan_checks.items():
            count = conn.execute(sql).fetchone()[0]
            assert count == 0, f"orphaned rows found for {label}"
