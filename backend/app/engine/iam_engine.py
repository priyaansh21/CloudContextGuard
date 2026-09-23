"""
IAM authorization engine.

Answers one question only: does this identity's role carry a permission
that covers the requested action on the requested resource? Network
context, resource policy, MFA and risk are evaluated by other engines - the
IAM engine never touches them.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch

from app.schemas.engine_results import IAMResult


@dataclass(frozen=True)
class PermissionSpec:
    """A single role permission: an action pattern on a resource pattern."""

    action: str
    resource_pattern: str


def evaluate_iam(
    *,
    user_exists: bool,
    user_is_active: bool,
    role_name: str | None,
    action: str,
    resource_name: str,
    permissions: list[PermissionSpec],
) -> IAMResult:
    """Evaluate identity, role and permission for a single action/resource pair.

    Matching supports exact strings and shell-style wildcards (``*``) on both
    the action and the resource pattern, so a single permission such as
    ``action="*", resource_pattern="*"`` can grant broad (e.g. admin) access.
    """
    if not user_exists:
        return IAMResult(
            allowed=False,
            result="FAIL",
            reason="User does not exist",
            matched_permission=None,
        )

    if not user_is_active:
        return IAMResult(
            allowed=False,
            result="FAIL",
            reason="User account is not active",
            matched_permission=None,
        )

    if not role_name:
        return IAMResult(
            allowed=False,
            result="FAIL",
            reason="User has no assigned role",
            matched_permission=None,
        )

    for permission in permissions:
        if fnmatch(action, permission.action) and fnmatch(resource_name, permission.resource_pattern):
            return IAMResult(
                allowed=True,
                result="PASS",
                reason=f"{role_name} permits {action} on {resource_name}",
                matched_permission=f"{permission.action}:{permission.resource_pattern}",
            )

    return IAMResult(
        allowed=False,
        result="FAIL",
        reason=f"{role_name} does not permit {action} on {resource_name}",
        matched_permission=None,
    )
