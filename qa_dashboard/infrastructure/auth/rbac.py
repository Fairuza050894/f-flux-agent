"""Lightweight RBAC (Role-Based Access Control) for the QA Dashboard.

Design goals
------------
* No external IdP dependency in Phase-02.
* Environment-variable controlled auth mode.
* Future OIDC integration is a drop-in behind the same ``AuthorizationService`` interface.

Auth modes (QA_AUTH_MODE)
--------------------------
development
    A default ``admin`` principal is provided automatically.
    Suitable for local development; MUST NOT be used in production.
production
    Requests without a valid token are rejected with HTTP 401.
    Token validation is currently a placeholder (stub); wire a real JWT
    validator in Phase-03.

Roles and permissions
---------------------
viewer      : runs:read, artifacts:read
tester      : runs:read, runs:execute, artifacts:read
maintainer  : runs:read, runs:execute, runs:cancel, artifacts:read, settings:write
admin       : all permissions

To extend: add permissions to :class:`Permission`, update ``ROLE_PERMISSIONS``.

Future OIDC integration
-----------------------
Replace ``_extract_principal_from_token`` in ``get_current_principal`` with a
real JWT validation library (e.g., ``python-jose``, ``authlib``).  The
``AuthorizationService`` and ``Principal`` interfaces are unchanged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class Permission(str, Enum):
    RUNS_READ = "runs:read"
    RUNS_EXECUTE = "runs:execute"
    RUNS_CANCEL = "runs:cancel"
    ARTIFACTS_READ = "artifacts:read"
    SETTINGS_WRITE = "settings:write"
    ADMIN_MANAGE = "admin:manage"


# ---------------------------------------------------------------------------
# Roles → Permission sets
# ---------------------------------------------------------------------------

ROLE_PERMISSIONS: dict[str, FrozenSet[Permission]] = {
    "viewer": frozenset({
        Permission.RUNS_READ,
        Permission.ARTIFACTS_READ,
    }),
    "tester": frozenset({
        Permission.RUNS_READ,
        Permission.RUNS_EXECUTE,
        Permission.ARTIFACTS_READ,
    }),
    "maintainer": frozenset({
        Permission.RUNS_READ,
        Permission.RUNS_EXECUTE,
        Permission.RUNS_CANCEL,
        Permission.ARTIFACTS_READ,
        Permission.SETTINGS_WRITE,
    }),
    "admin": frozenset({
        Permission.RUNS_READ,
        Permission.RUNS_EXECUTE,
        Permission.RUNS_CANCEL,
        Permission.ARTIFACTS_READ,
        Permission.SETTINGS_WRITE,
        Permission.ADMIN_MANAGE,
    }),
}


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Principal:
    """Authenticated caller identity."""

    principal_id: str
    roles: FrozenSet[str] = field(default_factory=frozenset)

    @classmethod
    def anonymous(cls) -> "Principal":
        return cls(principal_id="anonymous", roles=frozenset())

    @classmethod
    def development_admin(cls) -> "Principal":
        """Pre-configured admin principal for local development."""
        return cls(principal_id="dev-admin", roles=frozenset({"admin"}))

    @property
    def permissions(self) -> FrozenSet[Permission]:
        perms: set[Permission] = set()
        for role in self.roles:
            perms.update(ROLE_PERMISSIONS.get(role, frozenset()))
        return frozenset(perms)

    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions

    def is_anonymous(self) -> bool:
        return self.principal_id == "anonymous"


# ---------------------------------------------------------------------------
# AuthorizationService
# ---------------------------------------------------------------------------

class AuthorizationError(Exception):
    """Raised when a principal lacks a required permission."""

    def __init__(self, principal: Principal, permission: Permission) -> None:
        self.principal = principal
        self.permission = permission
        super().__init__(
            f"Principal '{principal.principal_id}' lacks permission '{permission.value}'"
        )


class AuthorizationService:
    """Enforces permission checks against a :class:`Principal`.

    This is the single chokepoint for authorization decisions.  Pass an
    instance into :class:`RunService` via dependency injection.
    """

    def check(self, principal: Principal, permission: Permission) -> None:
        """Assert that *principal* holds *permission*.

        Raises :class:`AuthorizationError` if the check fails.
        """
        if not principal.has_permission(permission):
            raise AuthorizationError(principal, permission)

    def can(self, principal: Principal, permission: Permission) -> bool:
        """Return True if *principal* holds *permission*; False otherwise."""
        return principal.has_permission(permission)


# ---------------------------------------------------------------------------
# Auth mode
# ---------------------------------------------------------------------------

class AuthMode(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


def get_auth_mode() -> AuthMode:
    raw = os.getenv("QA_AUTH_MODE", "production").strip().lower()
    if raw == "development":
        return AuthMode.DEVELOPMENT
    return AuthMode.PRODUCTION


def is_development_mode() -> bool:
    return get_auth_mode() == AuthMode.DEVELOPMENT


# ---------------------------------------------------------------------------
# Token extraction (stub – replace with real JWT in Phase-03)
# ---------------------------------------------------------------------------

def _extract_principal_from_token(token: str) -> "Principal | None":
    """Stub token validator.

    In Phase-03 replace with a real JWT library (e.g., python-jose) that
    verifies the signature against the OIDC provider's JWKS endpoint.

    Currently accepts:
    - ``dev-admin``  → admin principal
    - ``dev-tester`` → tester principal
    - ``dev-viewer`` → viewer principal
    """
    token = token.strip()
    _STUB_TOKENS: dict[str, Principal] = {
        "dev-admin": Principal(principal_id="dev-admin", roles=frozenset({"admin"})),
        "dev-tester": Principal(principal_id="dev-tester", roles=frozenset({"tester"})),
        "dev-viewer": Principal(principal_id="dev-viewer", roles=frozenset({"viewer"})),
    }
    return _STUB_TOKENS.get(token)


def resolve_principal(authorization_header: "str | None") -> Principal:
    """Resolve the caller's :class:`Principal` from an Authorization header.

    In development mode, missing or invalid tokens fall back to the dev-admin
    principal.  In production mode, missing or invalid tokens return the
    anonymous principal (callers must reject anonymous for protected routes).

    Parameters
    ----------
    authorization_header:
        Value of the ``Authorization`` HTTP header, e.g. ``"Bearer <token>"``.

    Returns
    -------
    Principal
        The resolved caller identity.  Never None.
    """
    token: str | None = None
    if authorization_header:
        parts = authorization_header.strip().split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()

    if token:
        principal = _extract_principal_from_token(token)
        if principal is not None:
            return principal

    if is_development_mode():
        return Principal.development_admin()

    return Principal.anonymous()
