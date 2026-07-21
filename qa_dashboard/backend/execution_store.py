# QA UI EXECUTION STORE V2.2.1 MODULE

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4
import json
import os
import tempfile

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


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
        if not STORE_PATH.exists():
            return default_store()

        try:
            payload = json.loads(
                STORE_PATH.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            return default_store()

        if not isinstance(payload, dict):
            return default_store()

        if not isinstance(payload.get("runs"), dict):
            payload["runs"] = {}

        payload.setdefault("version", "2.2.1")
        return payload


def write_store(payload: Dict[str, Any]) -> None:
    with LOCK:
        STORE_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        serialized = json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

        file_descriptor, temp_name = tempfile.mkstemp(
            prefix="active_runs_",
            suffix=".json",
            dir=str(STORE_PATH.parent),
        )

        try:
            with os.fdopen(
                file_descriptor,
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(serialized)

            os.replace(temp_name, STORE_PATH)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


class RunCreateRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=120)

    source: Literal[
        "ui_testing",
        "api_testing",
        "regression_testing",
        "unit_testing",
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


@router.get("/{run_id}")
def get_run(run_id: str) -> Dict[str, Any]:
    return get_run_or_404(run_id)


@router.patch("/{run_id}/progress")
def update_run_progress(
    run_id: str,
    request: RunProgressRequest,
) -> Dict[str, Any]:
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
    store = read_store()
    run = store["runs"].get(run_id)

    if not isinstance(run, dict):
        raise HTTPException(
            status_code=404,
            detail=f"Run not found: {run_id}",
        )

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
    store = read_store()
    run = store["runs"].get(run_id)

    if not isinstance(run, dict):
        raise HTTPException(
            status_code=404,
            detail=f"Run not found: {run_id}",
        )

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
