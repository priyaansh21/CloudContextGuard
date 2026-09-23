"""
Access control tests for CloudContextGuard's security intelligence layer.

Uses the project's actual portable configuration and real database (same
convention as ``test_health.py``) - no mocked paths, no mocked data. Each
test seeds the catalog (a no-op if already seeded) before submitting
requests through the real API.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.services.seed_service import ensure_contractor_identity, seed_if_empty


def _client() -> TestClient:
    return TestClient(app)


def _seed() -> None:
    db = SessionLocal()
    try:
        seed_if_empty(db)
        ensure_contractor_identity(db)
    finally:
        db.close()


def _submit(client: TestClient, **kwargs) -> dict:
    response = client.post("/api/access/request", json=kwargs)
    assert response.status_code == 200, response.text
    return response.json()


def test_1_developer_allowed_on_own_project_data() -> None:
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
    assert body["decision"] == "ALLOW"
    assert body["iam_result"]["allowed"] is True
    assert body["vpc_result"]["allowed"] is True


def test_2_developer_denied_financial_records_from_external_no_mfa() -> None:
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="financial-records",
            source_vpc="external",
            mfa=False,
            request_type="NORMAL",
        )
    assert body["decision"] == "DENY"
    assert body["vpc_result"]["result"] == "FAIL"
    assert body["mfa_result"]["result"] == "FAIL"
    assert body["risk_level"] in ("HIGH", "CRITICAL")


def test_3_finance_allowed_on_financial_records_in_trusted_vpc_with_mfa() -> None:
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
    assert body["decision"] == "ALLOW"
    assert body["iam_result"]["result"] == "PASS"
    assert body["vpc_result"]["result"] == "PASS"
    assert body["mfa_result"]["result"] == "PASS"


def test_4_developer_denied_credentials_vault_no_iam_permission() -> None:
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
    assert body["decision"] == "DENY"
    assert body["iam_result"]["result"] == "FAIL"


def test_5_finance_denied_financial_records_missing_mfa() -> None:
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
    assert body["decision"] == "DENY"
    assert body["iam_result"]["result"] == "PASS"
    assert body["vpc_result"]["result"] == "PASS"
    assert body["mfa_result"]["result"] == "FAIL"


def test_6_public_asset_allowed_from_external() -> None:
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
    assert body["decision"] == "ALLOW"


def test_7_repeated_failures_increase_risk() -> None:
    with _client() as client:
        _seed()
        first = _submit(
            client,
            user="developer02",
            action="GetObject",
            resource="credentials-vault",
            source_vpc="external",
            mfa=False,
            request_type="NORMAL",
        )
        second = _submit(
            client,
            user="developer02",
            action="GetObject",
            resource="credentials-vault",
            source_vpc="external",
            mfa=False,
            request_type="NORMAL",
        )
        third = _submit(
            client,
            user="developer02",
            action="GetObject",
            resource="credentials-vault",
            source_vpc="external",
            mfa=False,
            request_type="NORMAL",
        )
    assert first["decision"] == "DENY"
    assert second["decision"] == "DENY"
    assert third["decision"] == "DENY"
    factor_names = [f["name"] for f in third["risk_factors"]]
    assert "Repeated failed requests" in factor_names
    assert third["risk_score"] >= first["risk_score"]


def test_8_denied_request_creates_security_event() -> None:
    with _client() as client:
        _seed()
        before = client.get("/api/security/events", params={"limit": 500}).json()
        body = _submit(
            client,
            user="developer01",
            action="DeleteObject",
            resource="credentials-vault",
            source_vpc="external",
            mfa=False,
            request_type="NORMAL",
        )
        after = client.get("/api/security/events", params={"limit": 500}).json()
    assert len(after) > len(before)
    assert after[0]["action_taken"] == "BLOCKED"
    assert after[0]["access_request_id"] == body["request_id"]


def test_9_high_risk_request_creates_alert() -> None:
    with _client() as client:
        _seed()
        before = client.get("/api/alerts", params={"limit": 500}).json()
        body = _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="financial-records",
            source_vpc="external",
            mfa=False,
            request_type="SUSPICIOUS",
        )
        after = client.get("/api/alerts", params={"limit": 500}).json()
    assert body["risk_level"] in ("HIGH", "CRITICAL")
    assert len(after) > len(before)
    assert after[0]["status"] == "OPEN"
    assert after[0]["access_request_id"] == body["request_id"]


def test_10_valid_iam_but_invalid_network_context_denies() -> None:
    """Core principle: a valid identity with valid IAM permission is still denied
    when network context, MFA or risk fail."""
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
    assert body["iam_result"]["allowed"] is True
    assert body["vpc_result"]["allowed"] is False
    assert body["decision"] == "DENY"


def test_11_unknown_user_returns_404() -> None:
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


def test_12_unknown_resource_returns_404() -> None:
    with _client() as client:
        _seed()
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


def test_valid_credentials_do_not_guarantee_access() -> None:
    """Section 18: explicit demonstration that IAM=PASS + VPC=FAIL => DENY."""
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
    assert body["iam_result"]["result"] == "PASS"
    assert body["vpc_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"


def test_dashboard_reflects_real_data() -> None:
    with _client() as client:
        _seed()
        _submit(
            client,
            user="developer01",
            action="GetObject",
            resource="project-data",
            source_vpc="vpc-development",
            mfa=True,
            request_type="NORMAL",
        )
        response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] >= 1
    assert body["protected_resources"] == 3


def test_13_contractor_allowed_financial_records_trusted_vpc_with_mfa() -> None:
    """Step 5.1: valid IAM + valid context (trusted VPC, MFA) -> ALLOW."""
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_vpc="vpc-finance",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["iam_result"]["result"] == "PASS"
    assert body["vpc_result"]["result"] == "PASS"
    assert body["mfa_result"]["result"] == "PASS"
    assert body["decision"] == "ALLOW"


def test_14_contractor_denied_external_network_no_mfa() -> None:
    """Step 5.1 primary demonstration: valid IAM permission does not
    guarantee access - VPC and MFA context independently deny it."""
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_ip="185.22.91.11",
            source_vpc="external",
            mfa=False,
            request_type="SUSPICIOUS",
        )
    assert body["iam_result"]["result"] == "PASS"
    assert body["vpc_result"]["result"] == "FAIL"
    assert body["mfa_result"]["result"] == "FAIL"
    assert body["risk_level"] in ("HIGH", "CRITICAL")
    assert body["decision"] == "DENY"


def test_15_contractor_denied_external_network_vpc_alone_blocks() -> None:
    """Step 5.1: even with MFA satisfied, the VPC boundary alone denies
    access - proving the network control acts independently of MFA."""
    with _client() as client:
        _seed()
        body = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_ip="185.22.91.11",
            source_vpc="external",
            mfa=True,
            request_type="NORMAL",
        )
    assert body["iam_result"]["result"] == "PASS"
    assert body["vpc_result"]["result"] == "FAIL"
    assert body["decision"] == "DENY"
