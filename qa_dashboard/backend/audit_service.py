from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4
import json
import logging
import os
import re

from qa_dashboard.backend.database import (
    RevisionConflict,
    read_document,
    write_document,
)
from qa_dashboard.backend.settings import get_settings


LOGGER = logging.getLogger("qa_dashboard.observability")
AUDIT_LOCK = RLock()
AUDIT_NAMESPACE = "observability"
AUDIT_DOCUMENT_KEY = "audit_events"
AUDIT_SCHEMA_VERSION = 1

SENSITIVE_KEY_FRAGMENTS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "password",
    "refresh_token",
    "secret",
    "session",
    "token",
}

SENSITIVE_TEXT_PATTERNS = (
    re.compile(
        r"(?i)(bearer\s+)[a-z0-9._~+\-/=]+"
    ),
    re.compile(
        r"(?i)((?:password|secret|token|api[_-]?key)"
        r"\s*[:=]\s*)[^\s,;]+"
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_sensitive_key(value: str) -> bool:
    normalized = (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "_")
    )

    return any(
        fragment in normalized
        for fragment in SENSITIVE_KEY_FRAGMENTS
    )


def sanitize_value(
    value: Any,
    *,
    depth: int = 0,
) -> Any:
    if depth > 8:
        return "[MAX_DEPTH]"

    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}

        for key, nested in list(value.items())[:250]:
            key_text = str(key)

            if _is_sensitive_key(key_text):
                cleaned[key_text] = "[REDACTED]"
            else:
                cleaned[key_text] = sanitize_value(
                    nested,
                    depth=depth + 1,
                )

        return cleaned

    if isinstance(value, (list, tuple, set)):
        return [
            sanitize_value(
                item,
                depth=depth + 1,
            )
            for item in list(value)[:250]
        ]

    if isinstance(value, str):
        sanitized = value[:8000]

        for pattern in SENSITIVE_TEXT_PATTERNS:
            sanitized = pattern.sub(
                r"\1[REDACTED]",
                sanitized,
            )

        return sanitized

    if isinstance(
        value,
        (int, float, bool),
    ) or value is None:
        return value

    return sanitize_value(
        str(value),
        depth=depth + 1,
    )


def _default_store() -> Dict[str, Any]:
    return {
        "version": AUDIT_SCHEMA_VERSION,
        "events": [],
    }


def _read_store() -> tuple[Dict[str, Any], int]:
    document = read_document(
        AUDIT_NAMESPACE,
        AUDIT_DOCUMENT_KEY,
    )

    if document is None:
        return _default_store(), 0

    payload = document.get("payload")

    if not isinstance(payload, dict):
        payload = _default_store()

    events = payload.get("events")

    if not isinstance(events, list):
        payload["events"] = []

    payload.setdefault(
        "version",
        AUDIT_SCHEMA_VERSION,
    )

    return (
        payload,
        int(document.get("revision") or 0),
    )


def _maximum_events() -> int:
    return max(
        100,
        min(
            20000,
            int(
                get_settings().audit_max_events
            ),
        ),
    )


def structured_log(
    level: int,
    event: str,
    **fields: Any,
) -> None:
    payload = {
        "timestamp": utc_now(),
        "event": event,
        **sanitize_value(fields),
    }

    LOGGER.log(
        level,
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
    )


def record_event(
    *,
    category: str,
    action: str,
    result: str,
    actor: str = "",
    actor_role: str = "",
    resource: str = "",
    request_id: str = "",
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    event = {
        "id": f"audit-{uuid4().hex}",
        "timestamp": timestamp or utc_now(),
        "category":
            str(category or "system")[:80],
        "action":
            str(action or "unknown")[:160],
        "result":
            str(result or "unknown")[:40],
        "actor":
            str(actor or "anonymous")[:240],
        "actor_role":
            str(actor_role or "")[:80],
        "resource":
            str(resource or "")[:500],
        "request_id":
            str(request_id or "")[:160],
        "status_code":
            (
                int(status_code)
                if status_code is not None
                else None
            ),
        "duration_ms":
            (
                round(float(duration_ms), 2)
                if duration_ms is not None
                else None
            ),
        "metadata":
            sanitize_value(metadata or {}),
    }

    with AUDIT_LOCK:
        last_error: Optional[Exception] = None

        for _attempt in range(3):
            store, revision = _read_store()
            events = [
                item
                for item in store.get("events", [])
                if isinstance(item, dict)
            ]

            events.insert(0, event)
            store["events"] = events[
                :_maximum_events()
            ]

            try:
                write_document(
                    AUDIT_NAMESPACE,
                    AUDIT_DOCUMENT_KEY,
                    store,
                    schema_version=
                        AUDIT_SCHEMA_VERSION,
                    expected_revision=revision,
                )
                last_error = None
                break
            except RevisionConflict as error:
                last_error = error
                continue
            except Exception as error:
                last_error = error
                break

        if last_error is not None:
            structured_log(
                logging.WARNING,
                "audit.persistence_failed",
                error_type=
                    type(last_error).__name__,
                error=str(last_error),
                action=event["action"],
                request_id=event["request_id"],
            )

    log_level = (
        logging.ERROR
        if event["result"] == "failure"
        else logging.INFO
    )
    structured_log(
        log_level,
        "audit.event",
        **event,
    )
    return event


def derive_http_action(
    method: str,
    path: str,
) -> tuple[str, str]:
    normalized_method = (
        str(method or "GET").upper()
    )
    normalized_path = str(path or "/")

    if normalized_path.startswith(
        "/api/v1/executions"
    ):
        if normalized_path.endswith("/dispatch"):
            return "execution.dispatched", "execution"
        if normalized_path.endswith("/cancel"):
            return "execution.cancelled", "execution"
        if normalized_path.endswith("/retry"):
            return "execution.retried", "execution"
        if normalized_method == "POST":
            return "execution.created", "execution"
        return "execution.updated", "execution"

    if normalized_path.startswith(
        "/api/v1/reports/deliveries"
    ):
        if normalized_path.endswith("/retry"):
            return (
                "report.delivery_retried",
                "report_delivery",
            )
        return (
            "report.delivery_requested",
            "report_delivery",
        )

    if normalized_path.startswith(
        "/api/v1/reports"
    ):
        return "report.exported", "report"

    if normalized_path.startswith(
        "/api/v1/workspace"
    ):
        return "workspace.updated", "workspace"

    if normalized_path.startswith(
        "/api/v1/operations/recovery"
    ):
        return (
            "execution.recovery_requested",
            "reliability",
        )

    if (
        normalized_path.startswith("/auth/")
        or normalized_path == "/login"
    ):
        return (
            "authentication.request",
            "authentication",
        )

    if normalized_path.startswith(
        "/api/v1/security"
    ):
        return "security.updated", "security"

    return (
        f"api.{normalized_method.lower()}",
        "api",
    )


def _auth_audit_path() -> Path:
    hermes_home = (
        os.environ.get("HERMES_HOME")
        or str(Path.home() / ".hermes")
    )
    return (
        Path(hermes_home)
        / "logs"
        / "dashboard-auth.log"
    )


def _authentication_result(
    event_name: str,
) -> str:
    normalized = str(event_name or "").lower()

    if any(
        token in normalized
        for token in (
            "failure",
            "rejected",
            "revoked",
        )
    ):
        return "failure"

    if any(
        token in normalized
        for token in (
            "success",
            "logout",
            "minted",
            "start",
        )
    ):
        return "success"

    return "unknown"


def _read_authentication_events(
    limit: int,
) -> List[Dict[str, Any]]:
    path = _auth_audit_path()

    if not path.is_file():
        return []

    try:
        raw_lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()[-max(limit * 4, 100):]
    except OSError:
        return []

    items: List[Dict[str, Any]] = []

    for raw_line in reversed(raw_lines):
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        if not isinstance(payload, dict):
            continue

        event_name = str(
            payload.get("event") or "auth_event"
        )
        timestamp = str(
            payload.get("ts")
            or payload.get("timestamp")
            or ""
        )
        actor = str(
            payload.get("email")
            or payload.get("user_id")
            or payload.get("username")
            or payload.get("subject")
            or "anonymous"
        )
        request_id = str(
            payload.get("request_id") or ""
        )

        metadata = {
            key: value
            for key, value in payload.items()
            if key not in {
                "ts",
                "timestamp",
                "event",
                "email",
                "user_id",
                "username",
                "subject",
                "request_id",
            }
        }

        digest = sha256(
            raw_line.encode(
                "utf-8",
                errors="replace",
            )
        ).hexdigest()[:20]

        items.append({
            "id": f"auth-{digest}",
            "timestamp": timestamp,
            "category": "authentication",
            "action":
                f"authentication.{event_name}",
            "result":
                _authentication_result(
                    event_name
                ),
            "actor": actor,
            "actor_role": "",
            "resource": "dashboard-session",
            "request_id": request_id,
            "status_code": None,
            "duration_ms": None,
            "metadata":
                sanitize_value(metadata),
            "source": "hermes-dashboard-auth",
        })

        if len(items) >= limit:
            break

    return items


def _event_matches(
    item: Dict[str, Any],
    *,
    category: str,
    action: str,
    result: str,
    actor: str,
    request_id: str,
) -> bool:
    checks = (
        (
            category,
            str(item.get("category") or ""),
        ),
        (
            action,
            str(item.get("action") or ""),
        ),
        (
            result,
            str(item.get("result") or ""),
        ),
        (
            actor,
            str(item.get("actor") or ""),
        ),
        (
            request_id,
            str(item.get("request_id") or ""),
        ),
    )

    return all(
        not expected
        or expected.lower() in actual.lower()
        for expected, actual in checks
    )


def list_events(
    *,
    limit: int = 100,
    category: str = "",
    action: str = "",
    result: str = "",
    actor: str = "",
    request_id: str = "",
    include_authentication: bool = True,
) -> Dict[str, Any]:
    safe_limit = max(
        1,
        min(500, int(limit)),
    )

    store, _revision = _read_store()
    local_items = [
        {
            **item,
            "source": "qa-dashboard",
        }
        for item in store.get("events", [])
        if isinstance(item, dict)
    ]

    auth_items = (
        _read_authentication_events(
            safe_limit,
        )
        if include_authentication
        else []
    )

    merged = [
        item
        for item in (
            local_items + auth_items
        )
        if _event_matches(
            item,
            category=category,
            action=action,
            result=result,
            actor=actor,
            request_id=request_id,
        )
    ]

    merged.sort(
        key=lambda item:
            str(item.get("timestamp") or ""),
        reverse=True,
    )

    visible = merged[:safe_limit]

    return {
        "items": visible,
        "count": len(visible),
        "local_count": len(local_items),
        "authentication_count":
            len(auth_items),
        "filters": {
            "category": category,
            "action": action,
            "result": result,
            "actor": actor,
            "request_id": request_id,
        },
    }


def audit_health() -> Dict[str, Any]:
    try:
        store, revision = _read_store()
        event_count = len(
            [
                item
                for item in store.get(
                    "events",
                    [],
                )
                if isinstance(item, dict)
            ]
        )

        auth_path = _auth_audit_path()

        return {
            "status": "ready",
            "event_count": event_count,
            "revision": revision,
            "maximum_events":
                _maximum_events(),
            "authentication_log_available":
                auth_path.is_file(),
        }
    except Exception as error:
        return {
            "status": "error",
            "error_type":
                type(error).__name__,
            "error": str(error),
        }
