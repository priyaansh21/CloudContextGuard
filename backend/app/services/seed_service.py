"""
Database seed data for CloudContextGuard.

Seeds a small, realistic identity/network/resource catalog so the access
control API and dashboard have real data to evaluate against. Seeding only
ever runs when the database is empty, so it is safe to call on every
application startup.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Permission, Policy, Resource, Role, User, VPC


def is_database_empty(db: Session) -> bool:
    """The database is considered empty when no users have been created yet."""
    return db.query(User).first() is None


def seed_if_empty(db: Session) -> bool:
    """Populate the reference catalog if, and only if, the database is empty.

    Returns True if seeding ran, False if the database already had data.
    """
    if not is_database_empty(db):
        return False

    roles = {
        name: Role(name=name, description=description)
        for name, description in (
            ("DeveloperRole", "Application developers working on project data"),
            ("AdminRole", "Platform administrators; broad access for simulation purposes"),
            ("FinanceRole", "Finance team members working with financial records"),
            ("ReadOnlyRole", "Read-only auditors and observers"),
        )
    }
    db.add_all(roles.values())
    db.flush()

    users = [
        User(username="developer01", display_name="Developer One", role_id=roles["DeveloperRole"].id),
        User(username="developer02", display_name="Developer Two", role_id=roles["ReadOnlyRole"].id),
        User(username="admin01", display_name="Admin One", role_id=roles["AdminRole"].id),
        User(username="finance01", display_name="Finance One", role_id=roles["FinanceRole"].id),
    ]
    db.add_all(users)

    vpcs = {
        name: VPC(name=name, cidr=cidr, trust_level=trust_level, is_trusted=is_trusted, description=description)
        for name, cidr, trust_level, is_trusted, description in (
            ("vpc-prod", "10.0.0.0/16", "high", True, "Production network boundary"),
            ("vpc-development", "10.10.0.0/16", "medium", True, "Development network boundary"),
            ("vpc-finance", "10.20.0.0/16", "high", True, "Finance network boundary"),
            ("external", "0.0.0.0/0", "none", False, "Any network outside the known trusted VPCs"),
        )
    }
    db.add_all(vpcs.values())
    db.flush()

    resources = {
        "public-assets": Resource(
            name="public-assets",
            resource_type="storage-bucket",
            classification="PUBLIC",
            trusted_vpc=False,
            trusted_vpc_id=None,
            mfa_required=False,
            external_access_allowed=True,
            description="Publicly readable static assets",
        ),
        "project-data": Resource(
            name="project-data",
            resource_type="storage-bucket",
            classification="INTERNAL",
            trusted_vpc=True,
            trusted_vpc_id=vpcs["vpc-development"].id,
            mfa_required=False,
            external_access_allowed=False,
            description="Internal project working data",
        ),
        "financial-records": Resource(
            name="financial-records",
            resource_type="database",
            classification="CONFIDENTIAL",
            trusted_vpc=True,
            trusted_vpc_id=vpcs["vpc-finance"].id,
            mfa_required=True,
            external_access_allowed=False,
            description="Confidential financial records",
        ),
        "credentials-vault": Resource(
            name="credentials-vault",
            resource_type="secrets-store",
            classification="RESTRICTED",
            trusted_vpc=True,
            trusted_vpc_id=vpcs["vpc-prod"].id,
            mfa_required=True,
            external_access_allowed=False,
            description="Restricted credential and secret material",
        ),
    }
    db.add_all(resources.values())
    db.flush()

    permissions = [
        Permission(role_id=roles["DeveloperRole"].id, action="GetObject", resource_pattern="project-data"),
        Permission(role_id=roles["DeveloperRole"].id, action="PutObject", resource_pattern="project-data"),
        Permission(role_id=roles["DeveloperRole"].id, action="ListBucket", resource_pattern="project-data"),
        Permission(role_id=roles["DeveloperRole"].id, action="GetObject", resource_pattern="public-assets"),
        Permission(role_id=roles["DeveloperRole"].id, action="ListBucket", resource_pattern="public-assets"),
        Permission(role_id=roles["FinanceRole"].id, action="GetObject", resource_pattern="financial-records"),
        Permission(role_id=roles["FinanceRole"].id, action="PutObject", resource_pattern="financial-records"),
        Permission(role_id=roles["FinanceRole"].id, action="ListBucket", resource_pattern="financial-records"),
        Permission(role_id=roles["FinanceRole"].id, action="GetObject", resource_pattern="public-assets"),
        Permission(role_id=roles["FinanceRole"].id, action="ListBucket", resource_pattern="public-assets"),
        # Public assets are readable by anyone with a valid identity.
        Permission(role_id=roles["ReadOnlyRole"].id, action="GetObject", resource_pattern="*"),
        Permission(role_id=roles["ReadOnlyRole"].id, action="ListBucket", resource_pattern="*"),
        Permission(role_id=roles["AdminRole"].id, action="*", resource_pattern="*"),
    ]
    db.add_all(permissions)

    policies = [
        Policy(
            name="public-assets-policy",
            description="Public assets: no VPC or MFA restriction, external access allowed",
            resource_id=resources["public-assets"].id,
            required_role=None,
            trusted_vpc_id=None,
            mfa_required=False,
            max_risk_score=100,
            external_access_allowed=True,
            is_enabled=True,
        ),
        Policy(
            name="project-data-policy",
            description="Project data: development VPC boundary, no extra role gate",
            resource_id=resources["project-data"].id,
            required_role=None,
            trusted_vpc_id=vpcs["vpc-development"].id,
            mfa_required=False,
            max_risk_score=79,
            external_access_allowed=False,
            is_enabled=True,
        ),
        Policy(
            name="financial-records-policy",
            description=(
                "Financial records: finance VPC boundary and MFA required. No extra "
                "role gate - any role with IAM permission on this resource is "
                "subject to the same network/MFA context requirements."
            ),
            resource_id=resources["financial-records"].id,
            required_role=None,
            trusted_vpc_id=vpcs["vpc-finance"].id,
            mfa_required=True,
            max_risk_score=59,
            external_access_allowed=False,
            is_enabled=True,
        ),
        Policy(
            name="credentials-vault-policy",
            description="Credentials vault: production VPC boundary, MFA and AdminRole required",
            resource_id=resources["credentials-vault"].id,
            required_role=roles["AdminRole"].id,
            trusted_vpc_id=vpcs["vpc-prod"].id,
            mfa_required=True,
            max_risk_score=59,
            external_access_allowed=False,
            is_enabled=True,
        ),
    ]
    db.add_all(policies)

    db.commit()
    return True


CONTRACTOR_ROLE_NAME = "ContractorRole"
CONTRACTOR_USERNAME = "contractor01"
CONTRACTOR_PERMISSION_ACTIONS = ("GetObject", "ListBucket")


def ensure_contractor_identity(db: Session) -> bool:
    """Ensure the contractor01/ContractorRole demonstration identity exists.

    Demonstrates that a genuinely valid IAM permission does not by itself
    grant access: ContractorRole is deliberately given real read permission
    on financial-records, so a request that fails on network/MFA context
    proves the VPC/MFA controls act independently of IAM.

    Purely additive and idempotent - safe to call on every startup and
    against an already-populated database. Only ever creates rows that are
    missing; never touches audit history (AccessRequest/SecurityEvent/
    Alert), and never modifies a policy, role or permission that already
    exists - including one an administrator has since changed through the
    Policy Management page. (An earlier version of this function reset
    financial-records-policy's required_role on every startup; that
    one-time migration correction has already been applied to every
    database this function has run against, and continuing to enforce it
    would silently overwrite a future deliberate policy change.)
    """
    changed = False

    role = db.query(Role).filter_by(name=CONTRACTOR_ROLE_NAME).first()
    if role is None:
        role = Role(
            name=CONTRACTOR_ROLE_NAME,
            description=(
                "A controlled demonstration identity with IAM permission to request "
                "access to financial-records, but subject to strict contextual "
                "network and MFA policies."
            ),
        )
        db.add(role)
        db.flush()
        changed = True

    user = db.query(User).filter_by(username=CONTRACTOR_USERNAME).first()
    if user is None:
        db.add(
            User(
                username=CONTRACTOR_USERNAME,
                display_name="Cloud Storage Contractor",
                role_id=role.id,
            )
        )
        changed = True

    existing_permissions = {
        (permission.action, permission.resource_pattern)
        for permission in db.query(Permission).filter_by(role_id=role.id).all()
    }
    for action in CONTRACTOR_PERMISSION_ACTIONS:
        if (action, "financial-records") not in existing_permissions:
            db.add(Permission(role_id=role.id, action=action, resource_pattern="financial-records"))
            changed = True

    if changed:
        db.commit()
    return changed
