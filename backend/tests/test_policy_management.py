"""
Policy management tests for CloudContextGuard.

Covers the Policy CRUD API (GET/PUT), validation, the POLICY_CHANGED audit
trail, and - the core Step 6 requirement - that updating a policy's
trusted_vpc actually changes how the very next access request is
evaluated, with no application source code change required.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.services.seed_service import ensure_contractor_identity, seed_if_empty

EDITABLE_FIELDS = ("name", "description", "required_role", "trusted_vpc", "mfa_required", "max_risk_score", "external_access_allowed", "is_enabled")


def _client() -> TestClient:
    return TestClient(app)


def _seed() -> None:
    db = SessionLocal()
    try:
        seed_if_empty(db)
        ensure_contractor_identity(db)
    finally:
        db.close()


def _financial_records_policy(client: TestClient) -> dict:
    policies = client.get("/api/policies").json()
    return next(p for p in policies if p["resource"] == "financial-records")


def _update_payload(policy: dict, **overrides) -> dict:
    payload = {field: policy[field] for field in EDITABLE_FIELDS}
    payload.update(overrides)
    return payload


def _submit(client: TestClient, **kwargs) -> dict:
    response = client.post("/api/access/request", json=kwargs)
    assert response.status_code == 200, response.text
    return response.json()


def test_1_list_policies_succeeds() -> None:
    with _client() as client:
        _seed()
        response = client.get("/api/policies")
    assert response.status_code == 200
    assert len(response.json()) >= 4


def test_2_get_single_policy_succeeds() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        response = client.get(f"/api/policies/{policy['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == policy["id"]


def test_2b_get_nonexistent_policy_returns_404() -> None:
    with _client() as client:
        _seed()
        response = client.get("/api/policies/999999")
    assert response.status_code == 404


def test_3_put_valid_policy_updates_database() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        payload = _update_payload(policy, description="Updated via test_3")
        response = client.put(f"/api/policies/{policy['id']}", json=payload)
        assert response.status_code == 200
        assert response.json()["description"] == "Updated via test_3"
        refetched = client.get(f"/api/policies/{policy['id']}").json()
        assert refetched["description"] == "Updated via test_3"

        # Restore, so this test doesn't leak state into others.
        client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy))


def test_4_put_invalid_max_risk_score_rejected() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        payload = _update_payload(policy, max_risk_score=150)
        response = client.put(f"/api/policies/{policy['id']}", json=payload)
    assert response.status_code == 422


def test_5_put_nonexistent_trusted_vpc_rejected() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        payload = _update_payload(policy, trusted_vpc="vpc-does-not-exist")
        response = client.put(f"/api/policies/{policy['id']}", json=payload)
    assert response.status_code == 422
    # The rejected update must not have been applied.
    with _client() as client:
        unchanged = client.get(f"/api/policies/{policy['id']}").json()
    assert unchanged["trusted_vpc"] == policy["trusted_vpc"]


def test_6_policy_update_creates_security_event() -> None:
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        before = client.get("/api/security/events", params={"limit": 500}).json()

        client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy, description="Changed for test_6"))
        after = client.get("/api/security/events", params={"limit": 500}).json()

        # Restore.
        client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy))

    assert len(after) > len(before)
    assert after[0]["event_type"] == "POLICY_CHANGED"
    assert after[0]["severity"] == "HIGH"
    assert after[0]["action_taken"] == "POLICY_UPDATED"
    assert "Description" in after[0]["description"]


def test_7_access_evaluation_uses_updated_trusted_vpc() -> None:
    """Step 6 core demonstration, part 1: change the policy's trusted VPC
    and confirm the very next access request is evaluated against it.
    Self-contained: restores vpc-finance before returning, so it doesn't
    leak state into other tests regardless of execution order."""
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)
        assert policy["trusted_vpc"] == "vpc-finance"

        baseline = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_vpc="external",
            mfa=True,
            request_type="NORMAL",
        )
        assert baseline["iam_result"]["result"] == "PASS"
        assert baseline["vpc_result"]["result"] == "FAIL"
        assert baseline["decision"] == "DENY"

        update_response = client.put(
            f"/api/policies/{policy['id']}", json=_update_payload(policy, trusted_vpc="vpc-development")
        )
        assert update_response.status_code == 200
        assert update_response.json()["trusted_vpc"] == "vpc-development"

        try:
            dynamic = _submit(
                client,
                user="contractor01",
                action="GetObject",
                resource="financial-records",
                source_vpc="vpc-development",
                mfa=True,
                request_type="NORMAL",
            )
            assert dynamic["vpc_result"]["result"] == "PASS"
            assert dynamic["vpc_result"]["expected_vpc"] == "vpc-development"
            assert dynamic["iam_result"]["result"] == "PASS"
        finally:
            client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy, trusted_vpc="vpc-finance"))


def test_8_policy_reverted_successfully() -> None:
    """Step 6 core demonstration, part 2: independently prove that
    reverting a changed policy restores the original behavior - external
    access is denied again exactly as before. Self-contained: performs its
    own change-then-revert cycle rather than relying on test_7's state."""
    with _client() as client:
        _seed()
        policy = _financial_records_policy(client)

        client.put(f"/api/policies/{policy['id']}", json=_update_payload(policy, trusted_vpc="vpc-development"))

        revert_response = client.put(
            f"/api/policies/{policy['id']}", json=_update_payload(policy, trusted_vpc="vpc-finance")
        )
        assert revert_response.status_code == 200
        assert revert_response.json()["trusted_vpc"] == "vpc-finance"

        reverted = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_vpc="external",
            mfa=True,
            request_type="NORMAL",
        )
    assert reverted["vpc_result"]["result"] == "FAIL"
    assert reverted["decision"] == "DENY"


def test_9_existing_contextual_authorization_tests_still_pass() -> None:
    """Sanity check that Step 5.1's contractor01 contextual-authorization
    behavior is unaffected by the policy-management additions."""
    with _client() as client:
        _seed()
        allowed = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_vpc="vpc-finance",
            mfa=True,
            request_type="NORMAL",
        )
        assert allowed["decision"] == "ALLOW"

        denied = _submit(
            client,
            user="contractor01",
            action="GetObject",
            resource="financial-records",
            source_vpc="external",
            mfa=False,
            request_type="SUSPICIOUS",
        )
    assert denied["iam_result"]["result"] == "PASS"
    assert denied["vpc_result"]["result"] == "FAIL"
    assert denied["decision"] == "DENY"
