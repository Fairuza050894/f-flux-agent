from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from threading import RLock
from time import monotonic
from typing import Any, Awaitable, Callable, Dict, Optional
from urllib.parse import urlparse
from uuid import uuid4
import base64
import ipaddress
import json
import socket

from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import JSONResponse, Response

from hermes_cli.dashboard_auth import (
    get_provider,
    register_provider,
)
from hermes_cli.dashboard_auth.middleware import (
    gated_auth_middleware,
)
from hermes_cli.dashboard_auth.routes import (
    router as dashboard_auth_router,
)
from plugins.dashboard_auth.basic import (
    BasicAuthProvider,
    hash_password,
)

from qa_dashboard.backend.settings import (
    DashboardSettings,
    get_settings,
)


ROLE_LEVELS = {
    "viewer": 10,
    "tester": 20,
    "qa_lead": 30,
    "admin": 40,
}

ROLE_PERMISSIONS = {
    "viewer": (
        "dashboard:read",
        "reports:read",
        "artifacts:read",
    ),
    "tester": (
        "dashboard:read",
        "reports:read",
        "artifacts:read",
        "executions:create",
        "executions:dispatch",
        "executions:cancel",
        "executions:retry",
    ),
    "qa_lead": (
        "dashboard:read",
        "reports:read",
        "artifacts:read",
        "executions:create",
        "executions:dispatch",
        "executions:cancel",
        "executions:retry",
        "workspace:write",
        "test_assets:write",
        "test_plans:write",
        "test_cycles:write",
        "reports:deliver",
        "integrations:write",
    ),
    "admin": (
        "*",
    ),
}

SAFE_METHODS = {
    "GET",
    "HEAD",
    "OPTIONS",
}

PUBLIC_PATHS = {
    "/health",
    "/login",
    "/favicon.ico",
    "/api/auth/providers",
}

RATE_LIMIT_LOCK = RLock()
RATE_LIMIT_BUCKETS: Dict[
    tuple[str, str],
    deque[float],
] = defaultdict(deque)

IDEMPOTENCY_LOCK = RLock()
IDEMPOTENCY_KEYS: Dict[
    tuple[str, str, str, str],
    float,
] = {}

IDEMPOTENCY_TTL_SECONDS = 300
WRITE_RATE_WINDOW_SECONDS = 60

security_router = APIRouter(
    prefix="/api/v1/security",
    tags=["QA Security"],
)


@dataclass(
    frozen=True,
)
class SecurityActor:
    user_id: str
    email: str
    display_name: str
    provider: str
    role: str

    @property
    def permissions(
        self,
    ) -> tuple[str, ...]:
        return ROLE_PERMISSIONS[
            self.role
        ]

    def public_payload(
        self,
    ) -> dict:
        return {
            "user_id":
                self.user_id,
            "email":
                self.email,
            "display_name":
                self.display_name,
            "provider":
                self.provider,
            "role":
                self.role,
            "permissions":
                list(self.permissions),
        }


def utc_now() -> str:
    return datetime.now(
        timezone.utc,
    ).isoformat()


def _decode_secret(
    raw_value: str,
) -> bytes:
    value = str(
        raw_value or ""
    ).strip()

    if not value:
        return sha256(
            uuid4().bytes
        ).digest()

    for decoder in (
        lambda item: base64.b64decode(
            item,
            validate=True,
        ),
        bytes.fromhex,
    ):
        try:
            decoded = decoder(value)

            if len(decoded) >= 16:
                return decoded
        except (
            ValueError,
            TypeError,
            base64.binascii.Error,
        ):
            continue

    encoded = value.encode("utf-8")

    if len(encoded) < 16:
        raise RuntimeError(
            "Dashboard auth secret must be "
            "at least 16 bytes."
        )

    return encoded


def configure_auth_provider(
    settings: Optional[
        DashboardSettings
    ] = None,
) -> None:
    active_settings = (
        settings
        or get_settings()
    )

    if not active_settings.auth_required:
        return

    if get_provider("basic") is not None:
        return

    password_hash = (
        active_settings.auth_password_hash
    )

    if not password_hash:
        password_hash = hash_password(
            active_settings.auth_password
        )

    provider = BasicAuthProvider(
        username=
            active_settings.auth_username,
        password_hash=
            password_hash,
        secret=
            _decode_secret(
                active_settings.auth_secret
            ),
        ttl_seconds=
            active_settings.auth_ttl_seconds,
    )

    register_provider(provider)


def _identity_values(
    user_id: str,
    email: str,
) -> set[str]:
    return {
        value.strip().lower()
        for value in (
            user_id,
            email,
        )
        if value and value.strip()
    }


def _resolve_role(
    *,
    user_id: str,
    email: str,
    provider: str,
    settings: DashboardSettings,
) -> str:
    identities = _identity_values(
        user_id,
        email,
    )

    if (
        provider == "basic"
        and settings.auth_username.lower()
        in identities
    ):
        return settings.basic_auth_role

    role_groups = (
        (
            "admin",
            settings.admin_users,
        ),
        (
            "qa_lead",
            settings.qa_lead_users,
        ),
        (
            "tester",
            settings.tester_users,
        ),
        (
            "viewer",
            settings.viewer_users,
        ),
    )

    for role, configured_users in role_groups:
        if identities.intersection(
            configured_users
        ):
            return role

    return "viewer"


def resolve_actor(
    request: Request,
) -> SecurityActor:
    settings = get_settings()
    session = getattr(
        request.state,
        "session",
        None,
    )

    if session is not None:
        role = _resolve_role(
            user_id=
                str(
                    session.user_id
                    or ""
                ),
            email=
                str(
                    session.email
                    or ""
                ),
            provider=
                str(
                    session.provider
                    or ""
                ),
            settings=settings,
        )

        return SecurityActor(
            user_id=
                str(
                    session.user_id
                    or ""
                ),
            email=
                str(
                    session.email
                    or ""
                ),
            display_name=
                str(
                    session.display_name
                    or session.user_id
                    or ""
                ),
            provider=
                str(
                    session.provider
                    or ""
                ),
            role=role,
        )

    if not settings.auth_required:
        if settings.is_production:
            raise HTTPException(
                status_code=401,
                detail={
                    "code":
                        "AUTHENTICATION_REQUIRED",
                    "message":
                        "Production requests require "
                        "an authenticated session.",
                },
            )

        return SecurityActor(
            user_id=
                "local-development",
            email="",
            display_name=
                "Local Development",
            provider=
                "development-bypass",
            role="admin",
        )

    raise HTTPException(
        status_code=401,
        detail={
            "code":
                "AUTHENTICATION_REQUIRED",
            "message":
                "Authentication is required.",
        },
    )


def _is_public_path(
    path: str,
) -> bool:
    if path in PUBLIC_PATHS:
        return True

    return (
        path.startswith("/auth/")
        or path.startswith("/assets/")
        or path.startswith("/fonts/")
        or path.startswith("/ds-assets/")
    )


def _required_role(
    method: str,
    path: str,
) -> str:
    if method in SAFE_METHODS:
        return "viewer"

    if path.startswith(
        "/api/v1/executions"
    ):
        return "tester"

    if path in {
        "/runs",
        "/custom-smoke",
        "/curl-test",
    }:
        return "tester"

    if path.startswith(
        "/api/v1/reports"
    ):
        return "qa_lead"

    if path.startswith(
        "/api/v1/workspace"
    ):
        return "qa_lead"

    if (
        path.startswith(
            "/test-templates"
        )
        or path.startswith(
            "/test-plan"
        )
    ):
        return "qa_lead"

    return "qa_lead"


def _has_required_role(
    actor: SecurityActor,
    required_role: str,
) -> bool:
    return (
        ROLE_LEVELS[actor.role]
        >= ROLE_LEVELS[required_role]
    )


def _client_ip(
    request: Request,
) -> str:
    forwarded = request.headers.get(
        "x-forwarded-for",
        "",
    )

    if forwarded:
        return forwarded.split(
            ",",
            1,
        )[0].strip()

    if request.client is None:
        return "unknown"

    return request.client.host


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: Any = None,
    extra: Optional[dict] = None,
) -> JSONResponse:
    error = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }

    if details is not None:
        error["details"] = details

    content = {
        "detail": (
            details
            if details is not None
            else message
        ),
        "error": error,
    }

    if extra:
        content.update(extra)

    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={
            "X-Request-ID":
                request_id,
        },
    )


def _validate_content_length(
    request: Request,
) -> Optional[JSONResponse]:
    raw_length = request.headers.get(
        "content-length"
    )

    if not raw_length:
        return None

    try:
        content_length = int(raw_length)
    except ValueError:
        return _error_response(
            status_code=400,
            code=
                "INVALID_CONTENT_LENGTH",
            message=
                "Content-Length must be an integer.",
            request_id=
                request.state.request_id,
        )

    if (
        content_length
        > get_settings().max_request_bytes
    ):
        return _error_response(
            status_code=413,
            code=
                "REQUEST_TOO_LARGE",
            message=
                "Request body exceeds the "
                "configured size limit.",
            request_id=
                request.state.request_id,
            details={
                "maximum_bytes":
                    get_settings()
                    .max_request_bytes,
            },
        )

    return None


def _validate_origin(
    request: Request,
) -> Optional[JSONResponse]:
    if request.method in SAFE_METHODS:
        return None

    origin = request.headers.get(
        "origin",
        "",
    ).strip()

    if not origin:
        return None

    allowed = set(
        get_settings().frontend_origins
    )

    if origin in allowed:
        return None

    return _error_response(
        status_code=403,
        code="ORIGIN_NOT_ALLOWED",
        message=
            "The request origin is not allowed.",
        request_id=
            request.state.request_id,
        details={
            "origin": origin,
        },
    )


def _rate_limit_for_path(
    path: str,
) -> int:
    configured = (
        get_settings()
        .write_rate_limit_per_minute
    )

    if path == "/curl-test":
        return min(
            configured,
            10,
        )

    if (
        path.startswith(
            "/api/v1/reports"
        )
        and (
            "delivery" in path
            or "deliver" in path
            or "retry" in path
        )
    ):
        return min(
            configured,
            20,
        )

    return configured


def _validate_rate_limit(
    request: Request,
) -> Optional[JSONResponse]:
    if request.method in SAFE_METHODS:
        return None

    now = monotonic()
    key = (
        _client_ip(request),
        request.url.path,
    )
    limit = _rate_limit_for_path(
        request.url.path,
    )

    with RATE_LIMIT_LOCK:
        bucket = RATE_LIMIT_BUCKETS[
            key
        ]

        while (
            bucket
            and now - bucket[0]
            >= WRITE_RATE_WINDOW_SECONDS
        ):
            bucket.popleft()

        if len(bucket) >= limit:
            return _error_response(
                status_code=429,
                code="RATE_LIMITED",
                message=
                    "Too many write requests. "
                    "Wait and retry.",
                request_id=
                    request.state.request_id,
                details={
                    "limit_per_minute":
                        limit,
                },
            )

        bucket.append(now)

    return None


def _validate_idempotency(
    request: Request,
    actor: SecurityActor,
) -> Optional[JSONResponse]:
    if request.method in SAFE_METHODS:
        return None

    idempotency_key = (
        request.headers.get(
            "x-idempotency-key",
            "",
        ).strip()
    )

    if not idempotency_key:
        return None

    now = monotonic()
    identity = (
        actor.user_id,
        request.method,
        request.url.path,
        idempotency_key,
    )

    with IDEMPOTENCY_LOCK:
        expired = [
            key
            for key, created_at
            in IDEMPOTENCY_KEYS.items()
            if (
                now - created_at
                >= IDEMPOTENCY_TTL_SECONDS
            )
        ]

        for key in expired:
            IDEMPOTENCY_KEYS.pop(
                key,
                None,
            )

        if identity in IDEMPOTENCY_KEYS:
            return _error_response(
                status_code=409,
                code=
                    "DUPLICATE_REQUEST",
                message=
                    "This idempotency key has "
                    "already been used.",
                request_id=
                    request.state.request_id,
                details={
                    "idempotency_key":
                        idempotency_key,
                },
            )

        IDEMPOTENCY_KEYS[
            identity
        ] = now

    return None


def _apply_security_headers(
    response: Response,
    request_id: str,
) -> Response:
    response.headers[
        "X-Request-ID"
    ] = request_id
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"
    response.headers[
        "X-Frame-Options"
    ] = "DENY"
    response.headers[
        "Referrer-Policy"
    ] = "same-origin"
    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), microphone=(), "
        "geolocation=()"
    )
    response.headers[
        "Cache-Control"
    ] = (
        response.headers.get(
            "Cache-Control"
        )
        or "no-store"
    )
    return response


async def _authorized_request(
    request: Request,
    call_next: Callable[
        [Request],
        Awaitable[Response],
    ],
) -> Response:
    size_error = _validate_content_length(
        request
    )

    if size_error is not None:
        return size_error

    origin_error = _validate_origin(
        request
    )

    if origin_error is not None:
        return origin_error

    if _is_public_path(
        request.url.path
    ):
        return await call_next(
            request
        )

    actor = resolve_actor(
        request
    )
    request.state.qa_actor = actor

    required_role = _required_role(
        request.method,
        request.url.path,
    )

    if not _has_required_role(
        actor,
        required_role,
    ):
        return _error_response(
            status_code=403,
            code="PERMISSION_DENIED",
            message=
                "The current role cannot perform "
                "this action.",
            request_id=
                request.state.request_id,
            details={
                "current_role":
                    actor.role,
                "required_role":
                    required_role,
            },
        )

    rate_error = _validate_rate_limit(
        request
    )

    if rate_error is not None:
        return rate_error

    duplicate_error = (
        _validate_idempotency(
            request,
            actor,
        )
    )

    if duplicate_error is not None:
        return duplicate_error

    return await call_next(
        request
    )


async def qa_security_middleware(
    request: Request,
    call_next: Callable[
        [Request],
        Awaitable[Response],
    ],
) -> Response:
    request_id = (
        request.headers.get(
            "x-request-id",
            "",
        ).strip()
        or f"req-{uuid4().hex}"
    )
    request.state.request_id = request_id

    if (
        request.method == "OPTIONS"
        or request.url.path == "/health"
    ):
        response = await call_next(
            request
        )
        return _apply_security_headers(
            response,
            request_id,
        )

    async def after_auth(
        authorized_request: Request,
    ) -> Response:
        return await _authorized_request(
            authorized_request,
            call_next,
        )

    response = await gated_auth_middleware(
        request,
        after_auth,
    )

    return _apply_security_headers(
        response,
        request_id,
    )


@security_router.get(
    "/session",
)
def security_session(
    request: Request,
):
    actor = resolve_actor(
        request
    )

    return {
        "authenticated":
            bool(
                getattr(
                    request.state,
                    "session",
                    None,
                )
            ),
        "auth_required":
            get_settings().auth_required,
        "actor":
            actor.public_payload(),
        "issued_at":
            utc_now(),
    }


@security_router.get(
    "/configuration",
)
def security_configuration(
    request: Request,
):
    actor = resolve_actor(
        request
    )
    settings = get_settings()

    return {
        "actor":
            actor.public_payload(),
        "configuration":
            settings.public_summary(),
        "roles": {
            role:
                list(permissions)
            for role, permissions
            in ROLE_PERMISSIONS.items()
        },
    }


async def _http_exception_handler(
    request: Request,
    error: HTTPException,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        f"req-{uuid4().hex}",
    )

    detail = error.detail
    code = (
        detail.get("code")
        if isinstance(
            detail,
            dict,
        )
        else None
    ) or "HTTP_ERROR"

    message = (
        detail.get("message")
        if isinstance(
            detail,
            dict,
        )
        else str(detail)
    ) or "Request failed."

    return _error_response(
        status_code=
            error.status_code,
        code=str(code),
        message=str(message),
        request_id=request_id,
        details=detail,
        extra=(
            {
                "headers":
                    dict(
                        error.headers
                        or {}
                    )
            }
            if error.headers
            else None
        ),
    )


async def _validation_exception_handler(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        f"req-{uuid4().hex}",
    )

    return _error_response(
        status_code=422,
        code=
            "REQUEST_VALIDATION_FAILED",
        message=
            "Request validation failed.",
        request_id=request_id,
        details=error.errors(),
    )


def install_security(
    app: FastAPI,
) -> None:
    settings = get_settings()
    configure_auth_provider(
        settings
    )

    app.state.auth_required = (
        settings.auth_required
    )

    app.include_router(
        dashboard_auth_router
    )
    app.include_router(
        security_router
    )

    app.middleware("http")(
        qa_security_middleware
    )

    app.add_exception_handler(
        HTTPException,
        _http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        _validation_exception_handler,
    )


def validate_outbound_url(
    url: str,
) -> str:
    value = str(
        url or ""
    ).strip()

    if len(value) > 2048:
        raise ValueError(
            "Target URL exceeds 2048 characters."
        )

    parsed = urlparse(
        value
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "Only HTTP and HTTPS targets are allowed."
        )

    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError(
            "Target URL host is invalid."
        )

    hostname = parsed.hostname.lower()

    if hostname in {
        "localhost",
        "localhost.localdomain",
    }:
        if (
            not get_settings()
            .allow_private_targets
        ):
            raise ValueError(
                "Localhost targets are blocked."
            )
        return value

    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port
            or (
                443
                if parsed.scheme == "https"
                else 80
            ),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as error:
        raise ValueError(
            "Target host could not be resolved."
        ) from error

    if (
        get_settings()
        .allow_private_targets
    ):
        return value

    for address_info in addresses:
        address = address_info[4][0]

        try:
            ip = ipaddress.ip_address(
                address
            )
        except ValueError:
            continue

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError(
                "Private, local, link-local, "
                "reserved, multicast, and "
                "unspecified targets are blocked."
            )

    return value


def validate_artifact_path(
    raw_path: str,
    artifact_root,
):
    from pathlib import Path

    root = Path(
        artifact_root
    ).resolve()

    target = Path(
        raw_path
    ).expanduser().resolve()

    try:
        target.relative_to(
            root
        )
    except ValueError as error:
        raise HTTPException(
            status_code=403,
            detail={
                "code":
                    "ARTIFACT_ACCESS_DENIED",
                "message":
                    "Artifact path is outside "
                    "the allowed artifact directory.",
            },
        ) from error

    if not target.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "code":
                    "ARTIFACT_NOT_FOUND",
                "message":
                    "Artifact was not found.",
            },
        )

    if not target.is_file():
        raise HTTPException(
            status_code=400,
            detail={
                "code":
                    "ARTIFACT_PATH_INVALID",
                "message":
                    "Artifact path must reference "
                    "a file.",
            },
        )

    return target
