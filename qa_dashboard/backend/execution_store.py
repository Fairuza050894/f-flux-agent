from __future__ import annotations
import mimetypes
from fastapi.responses import FileResponse

import asyncio
import re
from typing import Optional
from fastapi import BackgroundTasks
from dotenv import load_dotenv
# QA UI EXECUTION STORE V2.2.1 MODULE


from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4
import json
import os
import signal
import sys
import tempfile

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from qa_dashboard.backend.database import (
    read_json_document,
    write_json_document,
)



QA_AUTOMATION_ENV_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "qa_automation"
    / ".env"
)

load_dotenv(
    QA_AUTOMATION_ENV_PATH,
    override=False,
)


router = APIRouter(
    prefix="/api/v1/executions", tags=["QA Executions"])

ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = (
    ROOT
    / "skills"
    / "qa_automation"
    / "artifacts"
    / "runtime"
    / "active_runs.json"
)
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

LOCK = RLock()

ACTIVE_STATUSES = {
    "queued",
    "running",
    "in_progress",
    "started",
    "executing",
    "processing",
    "cancelling",
}

TERMINAL_STATUSES = {
    "completed",
    "passed",
    "failed",
    "need_review",
    "cancelled",
}

SENSITIVE_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "cookie",
    "cookies",
    "session",
    "api_key",
    "apikey",
    "credential",
    "credentials",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_status(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )


def is_sensitive_key(value: str) -> bool:
    key = normalize_status(value)

    return key in SENSITIVE_KEYS or any(
        sensitive in key
        for sensitive in SENSITIVE_KEYS
    )


def sanitize_value(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "[MAX_DEPTH]"

    if isinstance(value, dict):
        cleaned: Dict[str, Any] = {}

        for key, nested in value.items():
            key_text = str(key)

            if is_sensitive_key(key_text):
                cleaned[key_text] = "[REDACTED]"
            else:
                cleaned[key_text] = sanitize_value(
                    nested,
                    depth + 1,
                )

        return cleaned

    if isinstance(value, (list, tuple)):
        return [
            sanitize_value(item, depth + 1)
            for item in value[:500]
        ]

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def default_store() -> Dict[str, Any]:
    return {
        "version": "2.2.1",
        "runs": {},
    }


def read_store() -> Dict[str, Any]:
    with LOCK:
        payload = read_json_document(
            "execution_store",
            "active_runs",
            fallback=default_store(),
            legacy_path=STORE_PATH,
        )

        if not isinstance(payload, dict):
            return default_store()

        if not isinstance(
            payload.get("runs"),
            dict,
        ):
            payload["runs"] = {}

        payload.setdefault(
            "version",
            "2.2.1",
        )
        return payload


def write_store(
    payload: Dict[str, Any],
) -> None:
    with LOCK:
        write_json_document(
            "execution_store",
            "active_runs",
            payload,
        )


class RunCreateRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=120)

    source: Literal[
        "ui_testing",
        "api_testing",
        "regression_testing",
        "unit_testing",
        "e2e_testing",
        "other",
    ] = "ui_testing"

    feature: str = Field(default="UI Test", max_length=240)
    test_type: str = Field(default="ui", max_length=80)
    environment: str = Field(default="", max_length=120)

    request_snapshot: Dict[str, Any] = Field(default_factory=dict)


class RunProgressRequest(BaseModel):
    status: Optional[str] = Field(default=None, max_length=80)
    progress: Optional[float] = Field(default=None, ge=0, le=100)
    current_stage: Optional[str] = Field(default=None, max_length=160)
    current_step: Optional[str] = Field(default=None, max_length=500)
    passed: Optional[int] = Field(default=None, ge=0)
    failed: Optional[int] = Field(default=None, ge=0)
    need_review: Optional[int] = Field(default=None, ge=0)

    safe_metadata: Dict[str, Any] = Field(default_factory=dict)


class RunCompleteRequest(BaseModel):
    status: Literal[
        "completed",
        "passed",
        "failed",
        "need_review",
        "cancelled",
    ] = "completed"

    progress: float = Field(default=100, ge=0, le=100)
    passed: Optional[int] = Field(default=None, ge=0)
    failed: Optional[int] = Field(default=None, ge=0)
    need_review: Optional[int] = Field(default=None, ge=0)

    result_summary: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)


class RunFailRequest(BaseModel):
    error_message: str = Field(min_length=1, max_length=4000)
    safe_metadata: Dict[str, Any] = Field(default_factory=dict)



class RunDispatchRequest(BaseModel):
    url: str = Field(
        default="",
        max_length=2048,
    )

    module_name: str = Field(
        default="",
        max_length=240,
    )

    mode: Optional[
        Literal[
            "smoke",
            "regression",
            "full",
            "cross_feature",
            "visual",
            "negative",
            "e2e",
        ]
    ] = None


class RunCancelRequest(BaseModel):
    reason: str = Field(
        default="",
        max_length=500,
    )


def get_run_or_404(run_id: str) -> Dict[str, Any]:
    run = read_store()["runs"].get(run_id)

    if not isinstance(run, dict):
        raise HTTPException(
            status_code=404,
            detail=f"Run not found: {run_id}",
        )

    return run


@router.post("")
def create_run(request: RunCreateRequest) -> Dict[str, Any]:
    with LOCK:
        store = read_store()

        run_id = (
            "run-"
            + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            + "-"
            + uuid4().hex[:8]
        )

        now = utc_now()

        run = {
            "run_id": run_id,
            "project_id": request.project_id.strip(),
            "source": request.source,
            "feature": request.feature.strip() or "UI Test",
            "test_type": request.test_type.strip() or "ui",
            "environment": request.environment.strip(),
            "status": "queued",
            "progress": 0,
            "current_stage": "queued",
            "current_step": "",
            "passed": 0,
            "failed": 0,
            "need_review": 0,
            "request_snapshot": sanitize_value(request.request_snapshot),
            "safe_metadata": {},
            "result_summary": {},
            "artifacts": [],
            "error_message": "",
            "created_at": now,
            "started_at": None,
            "updated_at": now,
            "completed_at": None,
        }

        store["runs"][run_id] = run
        write_store(store)
        return run


@router.get("/active")
def list_active_runs(
    project_id: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    runs = list(read_store()["runs"].values())

    result = [
        run
        for run in runs
        if (
            isinstance(run, dict)
            and normalize_status(run.get("status", ""))
            in ACTIVE_STATUSES
            and (
                not project_id
                or run.get("project_id") == project_id
            )
            and (
                not source
                or run.get("source") == source
            )
        )
    ]

    result.sort(
        key=lambda item: (
            item.get("started_at")
            or item.get("created_at")
            or ""
        ),
        reverse=True,
    )

    return {
        "runs": result,
        "count": len(result),
    }


@router.get(
    "/{run_id}/artifacts/{artifact_index}"
)
def get_run_artifact(
    run_id: str,
    artifact_index: int,
    download: bool = Query(default=False),
) -> FileResponse:
    run = get_run_or_404(run_id)

    artifacts = run.get(
        "artifacts",
        [],
    )

    if not isinstance(artifacts, list):
        raise HTTPException(
            status_code=404,
            detail="Run does not contain artifacts",
        )

    if (
        artifact_index < 0
        or artifact_index >= len(artifacts)
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "Artifact index not found: "
                f"{artifact_index}"
            ),
        )

    artifact = artifacts[artifact_index]

    if not isinstance(artifact, dict):
        raise HTTPException(
            status_code=404,
            detail="Invalid artifact record",
        )

    raw_path = str(
        artifact.get(
            "path",
            "",
        )
        or ""
    ).strip()

    if not raw_path:
        raise HTTPException(
            status_code=404,
            detail="Artifact path is not available",
        )

    artifacts_root = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "qa_automation"
        / "artifacts"
    ).resolve()

    artifact_path = (
        Path(raw_path)
        .expanduser()
        .resolve()
    )

    if (
        artifact_path != artifacts_root
        and artifacts_root
        not in artifact_path.parents
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Artifact path is outside "
                "the allowed directory"
            ),
        )

    if not artifact_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Artifact file no longer exists",
        )

    media_type = (
        mimetypes.guess_type(
            artifact_path.name
        )[0]
        or "application/octet-stream"
    )

    artifact_name = Path(
        str(
            artifact.get(
                "name",
                artifact_path.name,
            )
        )
    ).name

    return FileResponse(
        path=str(artifact_path),
        media_type=media_type,
        filename=artifact_name,
        content_disposition_type=(
            "attachment"
            if download
            else "inline"
        ),
    )


@router.get("/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    return get_run_or_404(run_id)


@router.patch("/{run_id}/progress")
def update_run_progress(
    run_id: str,
    request: RunProgressRequest,
) -> Dict[str, Any]:
    with LOCK:
        store = read_store()
        run = store["runs"].get(run_id)

        if not isinstance(run, dict):
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        current_status = normalize_status(run.get("status", ""))

        if current_status in TERMINAL_STATUSES:
            raise HTTPException(
                status_code=409,
                detail="Terminal run cannot receive progress updates",
            )

        next_status = normalize_status(request.status or "running")
        run["status"] = next_status

        if next_status in ACTIVE_STATUSES and not run.get("started_at"):
            run["started_at"] = utc_now()

        if request.progress is not None:
            run["progress"] = float(request.progress)

        if request.current_stage is not None:
            run["current_stage"] = request.current_stage.strip()

        if request.current_step is not None:
            run["current_step"] = request.current_step.strip()

        if request.passed is not None:
            run["passed"] = request.passed

        if request.failed is not None:
            run["failed"] = request.failed

        if request.need_review is not None:
            run["need_review"] = request.need_review

        if request.safe_metadata:
            run["safe_metadata"].update(
                sanitize_value(request.safe_metadata)
            )

        run["updated_at"] = utc_now()

        store["runs"][run_id] = run
        write_store(store)
        return run


@router.post("/{run_id}/complete")
def complete_run(
    run_id: str,
    request: RunCompleteRequest,
) -> Dict[str, Any]:
    with LOCK:
        store = read_store()
        run = store["runs"].get(run_id)

        if not isinstance(run, dict):
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        if normalize_status(run.get("status", "")) in {"cancelling", "cancelled"}:
            return run

        now = utc_now()

        run["status"] = normalize_status(request.status)
        run["progress"] = float(request.progress)

        if request.passed is not None:
            run["passed"] = request.passed

        if request.failed is not None:
            run["failed"] = request.failed

        if request.need_review is not None:
            run["need_review"] = request.need_review

        run["result_summary"] = sanitize_value(request.result_summary)
        run["artifacts"] = sanitize_value(request.artifacts)
        run["current_stage"] = "completed"
        run["current_step"] = ""
        run["updated_at"] = now
        run["completed_at"] = now

        if not run.get("started_at"):
            run["started_at"] = run.get("created_at") or now

        store["runs"][run_id] = run
        write_store(store)
        return run


@router.post("/{run_id}/fail")
def fail_run(
    run_id: str,
    request: RunFailRequest,
) -> Dict[str, Any]:
    with LOCK:
        store = read_store()
        run = store["runs"].get(run_id)

        if not isinstance(run, dict):
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        if normalize_status(run.get("status", "")) in {"cancelling", "cancelled"}:
            return run

        now = utc_now()

        run["status"] = "failed"
        run["current_stage"] = "failed"
        run["current_step"] = ""
        run["error_message"] = request.error_message.strip()

        run["safe_metadata"].update(
            sanitize_value(request.safe_metadata)
        )

        run["updated_at"] = now
        run["completed_at"] = now

        if not run.get("started_at"):
            run["started_at"] = run.get("created_at") or now

        store["runs"][run_id] = run
        write_store(store)
        return run


SUPPORTED_DISPATCH_SOURCES = {
    "ui_testing",
    "regression_testing",
}

DISPATCHABLE_STATUSES = {
    "queued",
    "pending",
    "created",
    "ready",
    "not_started",
}

DISPATCH_ACTIVE_STATUSES = {
    "processing",
    "running",
    "in_progress",
    "cancelling",
}

DISPATCH_TERMINAL_STATUSES = {
    "completed",
    "passed",
    "failed",
    "need_review",
    "cancelled",
    "error",
    "not_implemented",
}

# Playwright sync runner dijalankan satu per satu
# selama fase MVP.
RUNNER_DISPATCH_LOCK = asyncio.Lock()

# MVP1_P6_CANCEL_EXECUTION_START
RUNNER_RESULT_DIR = (
    STORE_PATH.parent
    / "runner_results"
)
RUNNER_RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

RUNNER_WORKER_PATH = (
    Path(__file__).resolve().parent
    / "execution_worker.py"
)

RUNNER_PROCESSES: Dict[
    str,
    asyncio.subprocess.Process,
] = {}

RUNNER_PROCESSES_LOCK = RLock()

CANCELLABLE_STATUSES = (
    DISPATCHABLE_STATUSES
    | DISPATCH_ACTIVE_STATUSES
    | {
        "queued",
        "started",
        "executing",
        "cancelling",
    }
)


def is_run_cancelled(
    run_id: str,
) -> bool:
    try:
        run = get_run_or_404(
            run_id
        )
    except HTTPException:
        return True

    return (
        normalize_status(
            run.get(
                "status",
                "",
            )
        )
        in {"cancelling", "cancelled"}
    )


def mark_run_cancelling(
    run_id: str,
    reason: str,
) -> Dict[str, Any]:
    with LOCK:
        store = read_store()
        run = store["runs"].get(
            run_id
        )

        if not isinstance(run, dict):
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Run not found: {run_id}"
                ),
            )

        current_status = (
            normalize_status(
                run.get(
                    "status",
                    "",
                )
            )
        )

        if current_status in (
            TERMINAL_STATUSES
        ):
            return run

        now = utc_now()
        metadata = run.setdefault(
            "safe_metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}
            run["safe_metadata"] = (
                metadata
            )

        run["status"] = (
            "cancelling"
        )
        run["current_stage"] = (
            "cancelling"
        )
        run["current_step"] = (
            reason
            or "Cancellation requested."
        )
        run[
            "cancellation_requested_at"
        ] = now
        run["updated_at"] = now

        metadata.update(
            {
                "cancellation_requested":
                    True,
                "cancellation_reason":
                    reason,
            }
        )

        store["runs"][run_id] = run
        write_store(store)

        return run


def mark_run_cancelled(
    run_id: str,
    reason: str,
) -> Dict[str, Any]:
    with LOCK:
        store = read_store()
        run = store["runs"].get(
            run_id
        )

        if not isinstance(run, dict):
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Run not found: {run_id}"
                ),
            )

        current_status = (
            normalize_status(
                run.get(
                    "status",
                    "",
                )
            )
        )

        if current_status == (
            "cancelled"
        ):
            return run

        if current_status in (
            TERMINAL_STATUSES
        ):
            return run

        now = utc_now()
        metadata = run.setdefault(
            "safe_metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}
            run["safe_metadata"] = (
                metadata
            )

        run["status"] = "cancelled"
        run["current_stage"] = (
            "cancelled"
        )
        run["current_step"] = (
            reason
            or "Execution cancelled."
        )
        run["error_message"] = ""
        run["updated_at"] = now
        run["completed_at"] = now
        run["cancelled_at"] = now

        metadata.update(
            {
                "cancelled": True,
                "cancellation_reason":
                    reason,
            }
        )

        store["runs"][run_id] = run
        write_store(store)

        return run


async def terminate_runner_process(
    process: asyncio.subprocess.Process,
) -> None:
    if process.returncode is not None:
        return

    try:
        if (
            os.name == "posix"
            and process.pid
        ):
            os.killpg(
                os.getpgid(
                    process.pid
                ),
                signal.SIGTERM,
            )
        else:
            process.terminate()
    except (
        ProcessLookupError,
        OSError,
    ):
        return

    try:
        await asyncio.wait_for(
            process.wait(),
            timeout=5,
        )
        return
    except asyncio.TimeoutError:
        pass

    try:
        if (
            os.name == "posix"
            and process.pid
        ):
            os.killpg(
                os.getpgid(
                    process.pid
                ),
                signal.SIGKILL,
            )
        else:
            process.kill()
    except (
        ProcessLookupError,
        OSError,
    ):
        return

    try:
        await process.wait()
    except ProcessLookupError:
        pass
# MVP1_P6_CANCEL_EXECUTION_END


def coerce_nonnegative_int(
    value: Any,
) -> Optional[int]:
    if isinstance(value, bool):
        return None

    try:
        parsed = int(value)
    except (
        TypeError,
        ValueError,
    ):
        return None

    return max(0, parsed)


def find_nested_value(
    payload: Any,
    key: str,
    depth: int = 0,
) -> Any:
    if depth > 4:
        return None

    if isinstance(payload, dict):
        if key in payload:
            return payload[key]

        for value in payload.values():
            result = find_nested_value(
                value,
                key,
                depth + 1,
            )

            if result is not None:
                return result

    if isinstance(payload, list):
        for value in payload:
            result = find_nested_value(
                value,
                key,
                depth + 1,
            )

            if result is not None:
                return result

    return None


def extract_summary_count(
    result: Dict[str, Any],
    key: str,
    label: str,
) -> int:
    direct_value = find_nested_value(
        result,
        key,
    )

    parsed_value = coerce_nonnegative_int(
        direct_value,
    )

    if parsed_value is not None:
        return parsed_value

    summary_text = str(
        result.get(
            "testing_summary",
            "",
        )
        or ""
    )

    match = re.search(
        rf"{re.escape(label)}\s*:\s*(\d+)",
        summary_text,
        flags=re.IGNORECASE,
    )

    if not match:
        return 0

    return int(match.group(1))


def extract_bug_count(
    result: Dict[str, Any],
) -> int:
    direct_value = find_nested_value(
        result,
        "bugs_found",
    )

    parsed_value = coerce_nonnegative_int(
        direct_value,
    )

    if parsed_value is not None:
        return parsed_value

    bugs = find_nested_value(
        result,
        "bugs",
    )

    if isinstance(bugs, list):
        return len(bugs)

    return extract_summary_count(
        result,
        "bugs_found",
        "Bugs Found",
    )


def collect_runner_artifacts(
    result: Dict[str, Any],
) -> list[Dict[str, Any]]:
    definitions = [
        (
            "screenshot",
            [
                "screenshot_path",
            ],
        ),
        (
            "documentation",
            [
                "documentation_path",
                "report_path",
            ],
        ),
        (
            "error_log",
            [
                "error_log_path",
            ],
        ),
        (
            "spreadsheet",
            [
                "spreadsheet_path",
            ],
        ),
    ]

    artifacts = []

    for artifact_type, keys in definitions:
        artifact_path = ""

        for key in keys:
            value = result.get(key)

            if value:
                artifact_path = str(value)
                break

        if not artifact_path:
            continue

        expanded_path = Path(
            artifact_path
        ).expanduser()

        artifacts.append(
            {
                "type": artifact_type,
                "path": artifact_path,
                "name": expanded_path.name,
                "exists": expanded_path.exists(),
            }
        )

    return artifacts


def parse_testing_summary_metrics(
    summary_text: str,
) -> Dict[str, Any]:
    text = str(summary_text or "")

    def extract_count(
        label: str,
    ) -> Optional[int]:
        match = re.search(
            rf"^\s*-\s*{re.escape(label)}"
            rf"\s*:\s*(\d+)\s*$",
            text,
            flags=re.IGNORECASE
            | re.MULTILINE,
        )

        if not match:
            return None

        return int(match.group(1))

    status_match = re.search(
        r"^\s*Status\s*:\s*(.+?)\s*$",
        text,
        flags=re.IGNORECASE
        | re.MULTILINE,
    )

    declared_status = (
        normalize_status(
            status_match.group(1)
        )
        if status_match
        else ""
    )

    return {
        "declared_status":
            declared_status,
        "passed":
            extract_count("Passed"),
        "failed":
            extract_count("Failed"),
        "need_review":
            extract_count(
                "Need Review"
            ),
        "skipped":
            extract_count("Skipped"),
        "bugs_found":
            extract_count(
                "Bugs Found"
            ),
        "non_blocking_warnings":
            extract_count(
                "Non-blocking Warnings"
            ),
    }



def get_structured_test_cases(
    result: Dict[str, Any],
) -> List[Dict[str, Any]]:
    values = result.get(
        "test_cases",
        [],
    )

    if not isinstance(
        values,
        list,
    ):
        return []

    return [
        sanitize_value(record)
        for record in values[:500]
        if isinstance(
            record,
            dict,
        )
    ]


def count_structured_test_cases(
    test_cases: List[
        Dict[str, Any]
    ],
) -> Dict[str, int]:
    counts = {
        "passed": 0,
        "failed": 0,
        "need_review": 0,
        "skipped": 0,
    }

    for record in test_cases:
        status = normalize_status(
            str(
                record.get(
                    "status",
                    "",
                )
            )
        )

        if status in {
            "pass",
            "passed",
            "success",
        }:
            counts["passed"] += 1

        elif status in {
            "fail",
            "failed",
            "error",
        }:
            counts["failed"] += 1

        elif status in {
            "need_review",
            "needs_review",
            "review",
        }:
            counts[
                "need_review"
            ] += 1

        elif status in {
            "skip",
            "skipped",
        }:
            counts["skipped"] += 1

    return counts


def build_target_asset_descriptors(
    run: Dict[str, Any],
) -> List[Dict[str, Any]]:
    snapshot = run.get(
        "request_snapshot",
        {},
    )

    if not isinstance(
        snapshot,
        dict,
    ):
        return []

    raw_ids = snapshot.get(
        "target_asset_ids",
        [],
    )

    target_ids = [
        str(value).strip()
        for value in (
            raw_ids
            if isinstance(
                raw_ids,
                list,
            )
            else []
        )
        if str(value).strip()
    ]

    if not target_ids:
        return []

    raw_snapshots = snapshot.get(
        "target_asset_snapshots",
        [],
    )

    snapshots = (
        raw_snapshots
        if isinstance(
            raw_snapshots,
            list,
        )
        else []
    )

    snapshot_by_id: Dict[
        str,
        Dict[str, Any],
    ] = {}

    for record in snapshots:
        if not isinstance(
            record,
            dict,
        ):
            continue

        asset_id = str(
            record.get(
                "assetId",
                record.get(
                    "asset_id",
                    "",
                ),
            )
        ).strip()

        if asset_id:
            snapshot_by_id[
                asset_id
            ] = record

    descriptors: List[
        Dict[str, Any]
    ] = []

    for asset_id in target_ids:
        record = snapshot_by_id.get(
            asset_id,
            {},
        )

        asset_snapshot = record.get(
            "snapshot",
            {},
        )

        if not isinstance(
            asset_snapshot,
            dict,
        ):
            asset_snapshot = {}

        def first_value(
            *keys: str,
        ) -> Any:
            for key in keys:
                value = (
                    asset_snapshot.get(
                        key
                    )
                )

                if value not in (
                    None,
                    "",
                    [],
                ):
                    return value

            return None

        descriptors.append({
            "asset_id":
                asset_id,
            "name":
                first_value(
                    "name",
                    "title",
                ),
            "automation_reference":
                first_value(
                    "automationReference",
                    "automation_reference",
                    "runnerCaseId",
                    "runner_case_id",
                    "testCaseId",
                    "test_case_id",
                ),
            "automation_references":
                first_value(
                    "automationReferences",
                    "automation_references",
                    "runnerCaseIds",
                    "runner_case_ids",
                    "testCaseIds",
                    "test_case_ids",
                )
                or [],
            "version_id":
                record.get(
                    "versionId",
                    record.get(
                        "version_id",
                    ),
                ),
            "version_number":
                record.get(
                    "versionNumber",
                    record.get(
                        "version_number",
                    ),
                ),
        })

    return sanitize_value(
        descriptors
    )


def normalize_runner_result(
    raw_result: Any,
    module_name: str,
    mode: str,
) -> Dict[str, Any]:
    if isinstance(raw_result, dict):
        result = raw_result
    else:
        result = {
            "status": "completed",
            "testing_summary": str(
                raw_result
            ),
        }

    structured_test_cases = (
        get_structured_test_cases(
            result
        )
    )

    structured_metrics = (
        count_structured_test_cases(
            structured_test_cases
        )
    )

    testing_summary = str(
        result.get(
            "testing_summary",
            "",
        )
        or ""
    )

    summary_metrics = (
        parse_testing_summary_metrics(
            testing_summary
        )
    )

    passed = (
        structured_metrics[
            "passed"
        ]
        if structured_test_cases
        else (
            summary_metrics["passed"]
            if summary_metrics["passed"]
            is not None
            else extract_summary_count(
                result,
                "passed",
                "Passed",
            )
        )
    )

    failed = (
        structured_metrics[
            "failed"
        ]
        if structured_test_cases
        else (
            summary_metrics["failed"]
            if summary_metrics["failed"]
            is not None
            else extract_summary_count(
                result,
                "failed",
                "Failed",
            )
        )
    )

    need_review = (
        structured_metrics[
            "need_review"
        ]
        if structured_test_cases
        else (
            summary_metrics["need_review"]
            if summary_metrics[
                "need_review"
            ]
            is not None
            else extract_summary_count(
                result,
                "need_review",
                "Need Review",
            )
        )
    )

    skipped = (
        structured_metrics[
            "skipped"
        ]
        if structured_test_cases
        else (
            summary_metrics["skipped"]
            if summary_metrics["skipped"]
            is not None
            else 0
        )
    )

    bugs_found = (
        summary_metrics["bugs_found"]
        if summary_metrics[
            "bugs_found"
        ]
        is not None
        else extract_bug_count(
            result
        )
    )

    non_blocking_warnings = (
        summary_metrics[
            "non_blocking_warnings"
        ]
        if summary_metrics[
            "non_blocking_warnings"
        ]
        is not None
        else 0
    )

    runner_status = normalize_status(
        str(
            result.get(
                "status",
                "",
            )
            or ""
        )
    )

    declared_status = (
        summary_metrics[
            "declared_status"
        ]
    )

    if (
        failed > 0
        or bugs_found > 0
        or runner_status
        in {
            "failed",
            "fail",
            "error",
        }
        or declared_status
        in {
            "failed",
            "fail",
            "error",
        }
    ):
        final_status = "failed"

    elif (
        need_review > 0
        or runner_status
        in {
            "need_review",
            "needs_review",
            "review",
        }
        or declared_status
        in {
            "need_review",
            "needs_review",
            "review",
        }
    ):
        final_status = "need_review"

    elif (
        passed > 0
        or runner_status
        in {
            "pass",
            "passed",
            "success",
        }
        or declared_status
        in {
            "pass",
            "passed",
            "success",
        }
    ):
        final_status = "passed"

    else:
        final_status = "completed"

    result_summary = {
        "module_name":
            module_name,
        "mode":
            mode,
        "runner_status":
            result.get("status"),
        "declared_status":
            declared_status,
        "feature_name":
            result.get(
                "feature_name"
            ),
        "route":
            result.get("route"),
        "target_url":
            result.get(
                "target_url"
            ),
        "custom_smoke":
            bool(
                result.get(
                    "custom_smoke"
                )
            ),
        "passed":
            passed,
        "failed":
            failed,
        "need_review":
            need_review,
        "skipped":
            skipped,
        "bugs_found":
            bugs_found,
        "non_blocking_warnings":
            non_blocking_warnings,
        "test_cases":
            structured_test_cases,
        "target_asset_ids":
            sanitize_value(
                result.get(
                    "target_asset_ids",
                    [],
                )
            ),
        "target_asset_descriptors":
            sanitize_value(
                result.get(
                    "target_asset_descriptors",
                    [],
                )
            ),
        "targeting_mode":
            result.get(
                "targeting_mode",
                "full_scope",
            ),
        "targeting_verified":
            bool(
                result.get(
                    "targeting_verified",
                    False,
                )
            ),
        "full_suite_test_case_count":
            result.get(
                "full_suite_test_case_count",
                len(
                    structured_test_cases
                ),
            ),
        "testing_summary":
            testing_summary[:12000],
    }

    return {
        "status":
            final_status,
        "passed":
            passed,
        "failed":
            failed,
        "need_review":
            need_review,
        "result_summary":
            sanitize_value(
                result_summary
            ),
        "artifacts":
            sanitize_value(
                collect_runner_artifacts(
                    result
                )
            ),
    }


async def execute_dispatched_run(
    run_id: str,
    target_url: str,
    module_name: str,
    mode: str,
) -> None:
    result_path = (
        RUNNER_RESULT_DIR
        / f"{run_id}.json"
    )

    target_path = (
        RUNNER_RESULT_DIR
        / f"{run_id}.targets.json"
    )

    process: Optional[
        asyncio.subprocess.Process
    ] = None

    try:
        async with RUNNER_DISPATCH_LOCK:
            if is_run_cancelled(
                run_id
            ):
                return

            run = get_run_or_404(
                run_id
            )

            target_descriptors = (
                build_target_asset_descriptors(
                    run
                )
            )

            if target_descriptors:
                target_path.write_text(
                    json.dumps(
                        target_descriptors,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            update_run_progress(
                run_id,
                RunProgressRequest(
                    status="running",
                    progress=10,
                    current_stage=(
                        "Starting QA runner"
                    ),
                    current_step=(
                        "Preparing isolated "
                        "Playwright execution."
                    ),
                    safe_metadata={
                        "runner": (
                            "perform_audit_"
                            "for_telegram"
                        ),
                        "runner_isolation":
                            "subprocess",
                        "mode": mode,
                        "target_asset_count":
                            len(
                                target_descriptors
                            ),
                        "targeting_mode":
                            (
                                "post_run_case_filter"
                                if target_descriptors
                                else "full_scope"
                            ),
                    },
                ),
            )

            if not (
                RUNNER_WORKER_PATH
                .is_file()
            ):
                raise RuntimeError(
                    "Execution worker is "
                    "not available."
                )

            update_run_progress(
                run_id,
                RunProgressRequest(
                    status="running",
                    progress=20,
                    current_stage=(
                        "Executing QA tests"
                    ),
                    current_step=(
                        f"Running {module_name} "
                        f"in {mode} mode."
                    ),
                ),
            )

            worker_command = [
                sys.executable,
                str(
                    RUNNER_WORKER_PATH
                ),
                "--run-id",
                run_id,
                "--url",
                target_url,
                "--module-name",
                module_name,
                "--mode",
                mode,
                "--output",
                str(result_path),
            ]

            if target_descriptors:
                worker_command.extend([
                    "--targets-file",
                    str(target_path),
                ])

            process = (
                await asyncio
                .create_subprocess_exec(
                    *worker_command,
                    stdout=(
                        asyncio.subprocess.PIPE
                    ),
                    stderr=(
                        asyncio.subprocess.PIPE
                    ),
                    start_new_session=True,
                    cwd=str(ROOT),
                )
            )

            with RUNNER_PROCESSES_LOCK:
                RUNNER_PROCESSES[
                    run_id
                ] = process

            stdout, stderr = (
                await process.communicate()
            )

            if is_run_cancelled(
                run_id
            ):
                return

            envelope: Dict[
                str,
                Any,
            ] = {}

            if result_path.is_file():
                try:
                    envelope = (
                        json.loads(
                            result_path
                            .read_text(
                                encoding=(
                                    "utf-8"
                                ),
                            )
                        )
                    )
                except (
                    json.JSONDecodeError,
                    OSError,
                ) as exc:
                    raise RuntimeError(
                        "Runner result could "
                        "not be read."
                    ) from exc

            if (
                process.returncode != 0
                or not envelope.get(
                    "ok"
                )
            ):
                error_message = str(
                    envelope.get(
                        "error",
                        "",
                    )
                ).strip()

                stderr_text = (
                    stderr.decode(
                        "utf-8",
                        errors="replace",
                    )
                    if stderr
                    else ""
                ).strip()

                raise RuntimeError(
                    error_message
                    or stderr_text[-4000:]
                    or (
                        "Isolated QA runner "
                        "failed."
                    )
                )

            raw_result = envelope.get(
                "result",
                {},
            )

            if is_run_cancelled(
                run_id
            ):
                return

            update_run_progress(
                run_id,
                RunProgressRequest(
                    status="running",
                    progress=90,
                    current_stage=(
                        "Processing QA result"
                    ),
                    current_step=(
                        "Normalizing result and "
                        "collecting artifacts."
                    ),
                    safe_metadata={
                        "worker_stdout":
                            (
                                stdout.decode(
                                    "utf-8",
                                    errors=(
                                        "replace"
                                    ),
                                )[-2000:]
                                if stdout
                                else ""
                            ),
                    },
                ),
            )

            normalized_result = (
                normalize_runner_result(
                    raw_result,
                    module_name,
                    mode,
                )
            )

            if is_run_cancelled(
                run_id
            ):
                return

            complete_run(
                run_id,
                RunCompleteRequest(
                    status=(
                        normalized_result[
                            "status"
                        ]
                    ),
                    progress=100,
                    passed=(
                        normalized_result[
                            "passed"
                        ]
                    ),
                    failed=(
                        normalized_result[
                            "failed"
                        ]
                    ),
                    need_review=(
                        normalized_result[
                            "need_review"
                        ]
                    ),
                    result_summary=(
                        normalized_result[
                            "result_summary"
                        ]
                    ),
                    artifacts=(
                        normalized_result[
                            "artifacts"
                        ]
                    ),
                ),
            )
    except asyncio.CancelledError:
        if process is not None:
            await terminate_runner_process(
                process
            )

        if not is_run_cancelled(
            run_id
        ):
            mark_run_cancelled(
                run_id,
                (
                    "Execution task was "
                    "cancelled."
                ),
            )

        raise
    except Exception as exc:
        if is_run_cancelled(
            run_id
        ):
            return

        fail_run(
            run_id,
            RunFailRequest(
                error_message=str(exc),
                safe_metadata={
                    "stage":
                        "runner_dispatch",
                    "exception_type":
                        type(exc).__name__,
                    "module_name":
                        module_name,
                    "mode": mode,
                },
            ),
        )
    finally:
        with RUNNER_PROCESSES_LOCK:
            registered = (
                RUNNER_PROCESSES.get(
                    run_id
                )
            )

            if (
                registered is
                process
            ):
                RUNNER_PROCESSES.pop(
                    run_id,
                    None,
                )

        result_path.unlink(
            missing_ok=True
        )

        target_path.unlink(
            missing_ok=True
        )

@router.post(
    "/{run_id}/cancel",
)
async def cancel_run(
    run_id: str,
    request: RunCancelRequest,
) -> Dict[str, Any]:
    run = get_run_or_404(run_id)

    current_status = (
        normalize_status(
            run.get(
                "status",
                "",
            )
        )
    )

    if current_status == (
        "cancelled"
    ):
        return {
            "accepted": False,
            "message": (
                "Execution is already "
                "cancelled."
            ),
            "run": run,
        }

    if current_status in (
        TERMINAL_STATUSES
    ):
        return {
            "accepted": False,
            "message": (
                "Terminal execution cannot "
                "be cancelled."
            ),
            "run": run,
        }

    if current_status not in (
        CANCELLABLE_STATUSES
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Execution cannot be "
                    "cancelled from its "
                    "current status."
                ),
                "status": current_status,
            },
        )

    reason = (
        request.reason.strip()
        or "Cancelled by user."
    )

    mark_run_cancelling(
        run_id,
        reason,
    )

    with RUNNER_PROCESSES_LOCK:
        process = (
            RUNNER_PROCESSES.get(
                run_id
            )
        )

    if process is not None:
        await terminate_runner_process(
            process
        )

    cancelled_run = (
        mark_run_cancelled(
            run_id,
            reason,
        )
    )

    return {
        "accepted": True,
        "message": (
            "Execution cancelled."
        ),
        "run": cancelled_run,
    }

@router.post(
    "/{run_id}/dispatch",
    status_code=202,
)
def dispatch_run(
    run_id: str,
    request: RunDispatchRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    run = get_run_or_404(run_id)

    source = normalize_status(
        str(
            run.get(
                "source",
                "",
            )
        )
    )

    current_status = normalize_status(
        str(
            run.get(
                "status",
                "",
            )
        )
    )

    if source not in (
        SUPPORTED_DISPATCH_SOURCES
    ):
        update_run_progress(
            run_id,
            RunProgressRequest(
                status="not_implemented",
                progress=0,
                current_stage=(
                    "Runner unavailable"
                ),
                current_step=(
                    f"The {source or 'unknown'} "
                    "runner is not implemented "
                    "in the MVP."
                ),
                safe_metadata={
                    "dispatch_supported": False,
                    "source": source,
                },
            ),
        )

        return {
            "accepted": False,
            "message": (
                f"Runner source {source} "
                "is not implemented in MVP."
            ),
            "run": get_run_or_404(
                run_id
            ),
        }

    if current_status in (
        DISPATCH_ACTIVE_STATUSES
    ):
        return {
            "accepted": False,
            "message": (
                "Execution is already active."
            ),
            "run": run,
        }

    if current_status in (
        DISPATCH_TERMINAL_STATUSES
    ):
        return {
            "accepted": False,
            "message": (
                "Execution has already reached "
                "a terminal status."
            ),
            "run": run,
        }

    if current_status not in (
        DISPATCHABLE_STATUSES
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "message": (
                    "Execution cannot be "
                    "dispatched from its "
                    "current status."
                ),
                "status": current_status,
            },
        )

    snapshot = run.get(
        "request_snapshot",
        {},
    )

    if not isinstance(snapshot, dict):
        snapshot = {}

    target_url = (
        request.url.strip()
        or str(
            snapshot.get(
                "environment_url",
                "",
            )
        ).strip()
        or os.getenv(
            "QA_DEFAULT_URL",
            "",
        ).strip()
    )

    if not target_url:
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Target URL is not "
                    "configured. Add an "
                    "environment URL or set "
                    "QA_DEFAULT_URL."
                )
            },
        )

    module_name = (
        request.module_name.strip()
        or str(
            snapshot.get(
                "module",
                "",
            )
        ).strip()
        or str(
            snapshot.get(
                "feature",
                "",
            )
        ).strip()
        or str(
            run.get(
                "feature",
                "",
            )
        ).strip()
        or "Uang Makan Driver"
    )

    mode = request.mode

    if not mode:
        mode = (
            "regression"
            if source
            == "regression_testing"
            else "smoke"
        )

    update_run_progress(
        run_id,
        RunProgressRequest(
            status="processing",
            progress=5,
            current_stage=(
                "Waiting for runner"
            ),
            current_step=(
                "Execution accepted and "
                "queued for Playwright."
            ),
            safe_metadata={
                "dispatch_supported": True,
                "source": source,
                "mode": mode,
            },
        ),
    )

    background_tasks.add_task(
        execute_dispatched_run,
        run_id,
        target_url,
        module_name,
        mode,
    )

    return {
        "accepted": True,
        "message": (
            "Execution dispatch accepted."
        ),
        "run": get_run_or_404(
            run_id
        ),
    }
