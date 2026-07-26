from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import sys

from qa_dashboard.backend import execution_store
from qa_dashboard.backend.audit_service import (
    audit_health,
    list_events,
    record_event,
)
from qa_dashboard.backend.database import (
    database_health,
)
from qa_dashboard.backend.report_delivery import (
    _read_delivery_store,
    _telegram_configuration,
    _public_delivery_record,
)
from qa_dashboard.backend.settings import (
    ROOT,
    get_settings,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(
    value: Any,
) -> Optional[datetime]:
    text = str(value or "").strip()

    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def _age_seconds(
    value: Any,
) -> Optional[float]:
    timestamp = _parse_timestamp(value)

    if timestamp is None:
        return None

    return max(
        0.0,
        (
            datetime.now(timezone.utc)
            - timestamp
        ).total_seconds(),
    )


def _status_counts(
    items: List[Dict[str, Any]],
) -> Dict[str, int]:
    counts = Counter(
        str(
            item.get("status")
            or "unknown"
        ).strip().lower()
        for item in items
        if isinstance(item, dict)
    )

    return dict(
        sorted(counts.items())
    )


def _is_stale_run(
    run: Dict[str, Any],
) -> bool:
    status = execution_store.normalize_status(
        run.get("status", "")
    )

    if status not in execution_store.ACTIVE_STATUSES:
        return False

    age = _age_seconds(
        run.get("updated_at")
        or run.get("started_at")
        or run.get("created_at")
    )

    if age is None:
        return False

    return (
        age
        >= get_settings()
        .stale_execution_seconds
    )


def execution_snapshot() -> Dict[str, Any]:
    store = execution_store.read_store()
    runs = [
        run
        for run in store.get(
            "runs",
            {},
        ).values()
        if isinstance(run, dict)
    ]

    runs.sort(
        key=lambda item:
            str(
                item.get("updated_at")
                or item.get("created_at")
                or ""
            ),
        reverse=True,
    )

    active = [
        run
        for run in runs
        if execution_store.normalize_status(
            run.get("status", "")
        ) in execution_store.ACTIVE_STATUSES
    ]
    stale = [
        run
        for run in active
        if _is_stale_run(run)
    ]
    recent_failures = [
        run
        for run in runs
        if execution_store.normalize_status(
            run.get("status", "")
        ) in {
            "failed",
            "need_review",
            "cancelled",
        }
    ][:10]

    return {
        "status":
            (
                "degraded"
                if stale
                else "ready"
            ),
        "total": len(runs),
        "active": len(active),
        "stale": len(stale),
        "status_counts":
            _status_counts(runs),
        "stale_after_seconds":
            get_settings()
            .stale_execution_seconds,
        "stale_runs": [
            {
                "run_id":
                    run.get("run_id"),
                "feature":
                    run.get("feature"),
                "status":
                    run.get("status"),
                "updated_at":
                    run.get("updated_at"),
                "current_stage":
                    run.get("current_stage"),
            }
            for run in stale[:20]
        ],
        "recent_failures": [
            {
                "run_id":
                    run.get("run_id"),
                "feature":
                    run.get("feature"),
                "status":
                    run.get("status"),
                "updated_at":
                    run.get("updated_at"),
                "error_message":
                    str(
                        run.get(
                            "error_message",
                            "",
                        )
                    )[:500],
            }
            for run in recent_failures
        ],
    }


def report_delivery_snapshot() -> Dict[str, Any]:
    records = [
        record
        for record in _read_delivery_store()
        if isinstance(record, dict)
    ]
    configuration = _telegram_configuration()
    failed = [
        record
        for record in records
        if str(
            record.get("status") or ""
        ).lower() == "failed"
    ]

    return {
        "status":
            (
                "ready"
                if configuration.get(
                    "configured"
                )
                else "not_configured"
            ),
        "configured":
            bool(
                configuration.get(
                    "configured"
                )
            ),
        "total": len(records),
        "failed": len(failed),
        "status_counts":
            _status_counts(records),
        "recent_failed": [
            _public_delivery_record(
                record
            )
            for record in failed[:10]
        ],
    }


def worker_snapshot() -> Dict[str, Any]:
    worker_path = (
        ROOT
        / "qa_dashboard"
        / "backend"
        / "execution_worker.py"
    )
    runtime_path = (
        ROOT
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "runtime"
    )

    try:
        runtime_path.mkdir(
            parents=True,
            exist_ok=True,
        )
        writable = os.access(
            runtime_path,
            os.W_OK,
        )
    except OSError:
        writable = False

    available = (
        worker_path.is_file()
        and bool(sys.executable)
        and writable
    )

    return {
        "status":
            (
                "ready"
                if available
                else "error"
            ),
        "worker_available":
            worker_path.is_file(),
        "python_available":
            bool(sys.executable),
        "runtime_writable":
            writable,
    }


def liveness_snapshot() -> Dict[str, Any]:
    return {
        "status": "alive",
        "service":
            "Hermes QA Dashboard API",
        "timestamp": utc_now(),
        "process_id": os.getpid(),
    }


def readiness_snapshot() -> Dict[str, Any]:
    settings = get_settings()
    database = database_health()
    worker = worker_snapshot()
    audit = audit_health()
    delivery = report_delivery_snapshot()

    components = [
        {
            "name": "database",
            **database,
            "required": True,
        },
        {
            "name": "execution_worker",
            **worker,
            "required": True,
        },
        {
            "name": "audit_store",
            **audit,
            "required": True,
        },
        {
            "name": "telegram_delivery",
            **delivery,
            "required":
                settings
                .readiness_require_telegram,
        },
    ]

    failed_required = [
        component
        for component in components
        if component.get("required")
        and component.get("status")
        not in {
            "ready",
            "alive",
        }
    ]

    degraded = [
        component
        for component in components
        if component.get("status")
        in {
            "degraded",
            "not_configured",
        }
    ]

    status = (
        "not_ready"
        if failed_required
        else (
            "degraded"
            if degraded
            else "ready"
        )
    )

    return {
        "status": status,
        "ready": not failed_required,
        "timestamp": utc_now(),
        "components": components,
        "required_failures": [
            component.get("name")
            for component in failed_required
        ],
    }


def incident_snapshot() -> Dict[str, Any]:
    readiness = readiness_snapshot()
    executions = execution_snapshot()
    deliveries = report_delivery_snapshot()
    audit = audit_health()

    items: List[Dict[str, Any]] = []

    for component in readiness.get(
        "components",
        [],
    ):
        if (
            component.get("required")
            and component.get("status")
            not in {"ready", "alive"}
        ):
            items.append({
                "id":
                    "component-"
                    + str(component.get("name")),
                "severity": "critical",
                "code":
                    "REQUIRED_COMPONENT_UNAVAILABLE",
                "title":
                    f"{component.get('name')} is unavailable",
                "detail":
                    str(
                        component.get("error")
                        or component.get("status")
                    ),
                "recommended_action":
                    "Review configuration and service logs.",
                "occurred_at": utc_now(),
            })

    if executions.get("stale"):
        items.append({
            "id": "stale-executions",
            "severity": "high",
            "code": "STALE_EXECUTIONS",
            "title":
                "Active executions have stopped updating",
            "detail":
                (
                    f"{executions['stale']} execution(s) "
                    "exceeded the configured stale threshold."
                ),
            "recommended_action":
                "Preview stale recovery, then apply it after confirming no worker is still active.",
            "occurred_at": utc_now(),
            "metadata": {
                "runs":
                    executions.get(
                        "stale_runs",
                        [],
                    ),
            },
        })

    if deliveries.get("failed"):
        items.append({
            "id": "failed-report-deliveries",
            "severity": "medium",
            "code": "REPORT_DELIVERY_FAILURES",
            "title":
                "Report delivery attempts failed",
            "detail":
                (
                    f"{deliveries['failed']} persisted "
                    "delivery attempt(s) are failed."
                ),
            "recommended_action":
                "Review Telegram configuration and retry the failed delivery from Reports.",
            "occurred_at": utc_now(),
        })

    if audit.get("status") != "ready":
        items.append({
            "id": "audit-store-error",
            "severity": "high",
            "code": "AUDIT_STORE_ERROR",
            "title":
                "Audit persistence is unavailable",
            "detail":
                str(
                    audit.get("error")
                    or audit.get("status")
                ),
            "recommended_action":
                "Review SQLite health and runtime directory permissions.",
            "occurred_at": utc_now(),
        })

    recent_errors = list_events(
        limit=20,
        result="failure",
        include_authentication=True,
    ).get("items", [])

    return {
        "items": items,
        "count": len(items),
        "recent_errors":
            recent_errors[:10],
        "generated_at": utc_now(),
    }


def operations_snapshot() -> Dict[str, Any]:
    readiness = readiness_snapshot()
    executions = execution_snapshot()
    deliveries = report_delivery_snapshot()
    audit = audit_health()
    incidents = incident_snapshot()

    status = (
        "critical"
        if not readiness.get("ready")
        else (
            "degraded"
            if (
                executions.get("stale")
                or deliveries.get("failed")
                or incidents.get("count")
            )
            else "healthy"
        )
    )

    return {
        "status": status,
        "generated_at": utc_now(),
        "summary": {
            "active_executions":
                executions.get("active", 0),
            "stale_executions":
                executions.get("stale", 0),
            "failed_deliveries":
                deliveries.get("failed", 0),
            "audit_events":
                audit.get("event_count", 0),
            "open_incidents":
                incidents.get("count", 0),
        },
        "readiness": readiness,
        "executions": executions,
        "report_delivery": deliveries,
        "audit": audit,
        "incidents":
            incidents.get("items", []),
    }


def recover_stale_executions(
    *,
    dry_run: bool,
    reason: str,
    actor: str,
    actor_role: str,
    request_id: str,
) -> Dict[str, Any]:
    recovered: List[str] = []
    candidates: List[str] = []
    timestamp = utc_now()

    with execution_store.LOCK:
        store = execution_store.read_store()
        runs = store.get("runs", {})

        for run_id, run in runs.items():
            if (
                not isinstance(run, dict)
                or not _is_stale_run(run)
            ):
                continue

            candidates.append(run_id)

            if dry_run:
                continue

            run["status"] = "failed"
            run["progress"] = min(
                100,
                max(
                    0,
                    float(
                        run.get("progress")
                        or 0
                    ),
                ),
            )
            run["current_stage"] = (
                "Recovered as stale"
            )
            run["current_step"] = (
                reason
                or (
                    "Execution stopped updating "
                    "and was closed by P8-C recovery."
                )
            )
            run["error_message"] = (
                reason
                or "Execution recovered after stale timeout."
            )
            run["completed_at"] = timestamp
            run["updated_at"] = timestamp

            safe_metadata = run.get(
                "safe_metadata",
                {},
            )

            if not isinstance(
                safe_metadata,
                dict,
            ):
                safe_metadata = {}

            safe_metadata[
                "p8c_recovery"
            ] = {
                "recovered_at": timestamp,
                "reason":
                    reason
                    or "stale_execution_timeout",
                "actor": actor,
            }
            run["safe_metadata"] = (
                execution_store.sanitize_value(
                    safe_metadata
                )
            )
            recovered.append(run_id)

        if recovered:
            execution_store.write_store(
                store
            )

    result = {
        "dry_run": dry_run,
        "candidate_count":
            len(candidates),
        "recovered_count":
            len(recovered),
        "candidate_run_ids":
            candidates,
        "recovered_run_ids":
            recovered,
        "timestamp": timestamp,
    }

    record_event(
        category="reliability",
        action=(
            "execution.recovery_previewed"
            if dry_run
            else "execution.recovered"
        ),
        result="success",
        actor=actor,
        actor_role=actor_role,
        resource="stale_executions",
        request_id=request_id,
        metadata=result,
    )

    return result
