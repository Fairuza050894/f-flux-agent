from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(
    f"app.py.backup_before_execution_telemetry_{timestamp}"
)

shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text(encoding="utf-8")


telemetry_code = r'''

# ============================================================
# Structured Execution Telemetry MVP
# ============================================================

from typing import Optional as _TelOptional
from typing import Dict as _TelDict
from typing import Any as _TelAny
from pydantic import BaseModel as _TelBaseModel
import threading as _tel_threading


_tel_lock = _tel_threading.Lock()


class TelemetryStartRequest(_TelBaseModel):
    runner_type: str
    feature_name: str = ""


class TelemetryEventRequest(_TelBaseModel):
    session_id: str
    stage: str
    event: str
    level: str = "info"
    status: str = "running"
    message: str
    duration_ms: _TelOptional[int] = None
    metadata: _TelDict[str, _TelAny] = {}


class TelemetryCompleteRequest(_TelBaseModel):
    session_id: str
    execution_id: _TelOptional[str] = None
    standard_json_path: _TelOptional[str] = None
    result_status: str = "UNKNOWN"
    summary: _TelDict[str, _TelAny] = {}


def _qa_tel_now():
    from datetime import datetime

    return datetime.now().astimezone().isoformat(
        timespec="milliseconds"
    )


def _qa_tel_epoch_ms():
    import time

    return int(time.time() * 1000)


def _qa_tel_root():
    from pathlib import Path

    target = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "telemetry"
    )

    target.mkdir(
        parents=True,
        exist_ok=True,
    )

    return target


def _qa_tel_mask_text(value):
    import re

    text = str(value or "")

    replacements = [
        (
            r"(?i)(authorization\s*[:=]\s*bearer\s+)"
            r"[^\s\"']+",
            r"\1***MASKED***",
        ),
        (
            r"(?i)(bearer\s+)"
            r"[a-z0-9._~+/=-]+",
            r"\1***MASKED***",
        ),
        (
            r'(?i)("?(?:password|passwd|token|secret|'
            r'api[_-]?key|cookie)"?\s*[:=]\s*")'
            r'([^"]+)(")',
            r"\1***MASKED***\3",
        ),
        (
            r"(?i)((?:password|passwd|token|secret|"
            r"api[_-]?key|cookie)\s*[:=]\s*)"
            r"[^\s,;]+",
            r"\1***MASKED***",
        ),
    ]

    for pattern, replacement in replacements:
        text = re.sub(
            pattern,
            replacement,
            text,
        )

    return text[:1000]


def _qa_tel_safe_metadata(metadata):
    if not isinstance(metadata, dict):
        return {}

    allowed_keys = {
        "passed",
        "failed",
        "need_review",
        "skipped",
        "warnings",
        "bugs_found",
        "artifact_count",
        "status",
        "runner_type",
        "feature_name",
    }

    result = {}

    for key, value in metadata.items():
        normalized = str(key)

        if normalized not in allowed_keys:
            continue

        if isinstance(
            value,
            (str, int, float, bool),
        ) or value is None:
            result[normalized] = (
                _qa_tel_mask_text(value)
                if isinstance(value, str)
                else value
            )

    return result


def _qa_tel_session_path(session_id):
    import re

    safe_id = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        str(session_id or ""),
    ).strip("_")

    if not safe_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid telemetry session ID",
        )

    return (
        _qa_tel_root()
        / f"qa_telemetry_{safe_id}.json"
    )


def _qa_tel_read_session(session_id):
    import json

    path = _qa_tel_session_path(
        session_id
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Telemetry session not found: "
                + str(session_id)
            ),
        )

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to read telemetry session: "
                + str(error)
            ),
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid telemetry schema",
        )

    return path, data


def _qa_tel_write_session(path, data):
    import json

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _qa_tel_append_event(
    data,
    stage,
    event,
    level,
    status,
    message,
    duration_ms=None,
    metadata=None,
):
    events = data.get("events")

    if not isinstance(events, list):
        events = []
        data["events"] = events

    event_data = {
        "sequence": len(events) + 1,
        "timestamp": _qa_tel_now(),
        "timestamp_epoch_ms": _qa_tel_epoch_ms(),
        "stage": _qa_tel_mask_text(stage).lower(),
        "event": _qa_tel_mask_text(event).lower(),
        "level": _qa_tel_mask_text(level).lower(),
        "status": _qa_tel_mask_text(status).lower(),
        "message": _qa_tel_mask_text(message),
        "duration_ms": (
            int(duration_ms)
            if isinstance(duration_ms, int)
            else None
        ),
        "metadata": _qa_tel_safe_metadata(
            metadata or {}
        ),
    }

    events.append(event_data)

    data["updated_at"] = event_data[
        "timestamp"
    ]

    return event_data


def _qa_tel_safe_project_file(raw_path):
    from pathlib import Path

    if not raw_path:
        return None

    project_root = (
        Path(__file__).resolve()
        .parents[2]
        .resolve()
    )

    try:
        path = (
            Path(str(raw_path))
            .expanduser()
            .resolve()
        )

        path.relative_to(project_root)
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_tel_update_standard_json(
    standard_json_path,
    telemetry_data,
    telemetry_path,
):
    import json

    path = _qa_tel_safe_project_file(
        standard_json_path
    )

    if not path:
        return False

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(payload, dict):
            return False

        payload["execution_events"] = (
            telemetry_data.get("events") or []
        )

        execution = payload.get("execution")

        if not isinstance(execution, dict):
            execution = {}
            payload["execution"] = execution

        execution["telemetry_id"] = (
            telemetry_data.get("telemetry_id")
        )

        execution["duration_ms"] = (
            telemetry_data.get(
                "total_duration_ms"
            )
        )

        artifacts = payload.get("artifacts")

        if not isinstance(artifacts, dict):
            artifacts = {}
            payload["artifacts"] = artifacts

        artifacts["telemetry"] = str(
            telemetry_path
        )

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return True

    except Exception:
        return False


def _qa_tel_update_history(
    execution_id,
    telemetry_data,
    telemetry_path,
):
    import json

    if not execution_id:
        return False

    history_path = (
        _qa_tel_root().parent
        / "history"
        / "qa_run_history.json"
    )

    if not history_path.exists():
        return False

    try:
        history = json.loads(
            history_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return False

    if not isinstance(history, list):
        return False

    updated = False

    for item in history:
        if not isinstance(item, dict):
            continue

        if str(
            item.get("execution_id") or ""
        ) != str(execution_id):
            continue

        item["telemetry_path"] = str(
            telemetry_path
        )

        item["telemetry_event_count"] = len(
            telemetry_data.get("events") or []
        )

        item["duration_ms"] = (
            telemetry_data.get(
                "total_duration_ms"
            )
        )

        updated = True
        break

    if updated:
        history_path.write_text(
            json.dumps(
                history,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return updated


@app.post("/telemetry/start")
def start_execution_telemetry(
    request: TelemetryStartRequest,
):
    import uuid

    telemetry_id = (
        "TEL-"
        + uuid.uuid4().hex[:16].upper()
    )

    created_at = _qa_tel_now()
    created_epoch_ms = _qa_tel_epoch_ms()

    data = {
        "schema_version": "1.0",
        "telemetry_id": telemetry_id,
        "execution_id": None,
        "runner_type": _qa_tel_mask_text(
            request.runner_type
        ),
        "feature_name": _qa_tel_mask_text(
            request.feature_name
        ),
        "created_at": created_at,
        "created_at_epoch_ms": created_epoch_ms,
        "updated_at": created_at,
        "completed_at": None,
        "total_duration_ms": None,
        "result_status": "RUNNING",
        "events": [],
    }

    _qa_tel_append_event(
        data=data,
        stage="execution",
        event="session_started",
        level="info",
        status="running",
        message=(
            "Execution telemetry session started."
        ),
        metadata={
            "runner_type": request.runner_type,
            "feature_name": request.feature_name,
        },
    )

    path = _qa_tel_session_path(
        telemetry_id
    )

    with _tel_lock:
        _qa_tel_write_session(
            path,
            data,
        )

    return {
        "ok": True,
        "telemetry_id": telemetry_id,
        "telemetry_path": str(path),
        "created_at": created_at,
    }


@app.post("/telemetry/event")
def record_execution_telemetry(
    request: TelemetryEventRequest,
):
    with _tel_lock:
        path, data = _qa_tel_read_session(
            request.session_id
        )

        event_data = _qa_tel_append_event(
            data=data,
            stage=request.stage,
            event=request.event,
            level=request.level,
            status=request.status,
            message=request.message,
            duration_ms=request.duration_ms,
            metadata=request.metadata,
        )

        _qa_tel_write_session(
            path,
            data,
        )

    return {
        "ok": True,
        "telemetry_id": request.session_id,
        "event": event_data,
        "event_count": len(
            data.get("events") or []
        ),
    }


@app.post("/telemetry/complete")
def complete_execution_telemetry(
    request: TelemetryCompleteRequest,
):
    with _tel_lock:
        path, data = _qa_tel_read_session(
            request.session_id
        )

        completed_at = _qa_tel_now()
        completed_epoch_ms = (
            _qa_tel_epoch_ms()
        )

        created_epoch_ms = int(
            data.get(
                "created_at_epoch_ms"
            )
            or completed_epoch_ms
        )

        total_duration_ms = max(
            0,
            completed_epoch_ms
            - created_epoch_ms,
        )

        result_status = str(
            request.result_status
            or "UNKNOWN"
        ).upper()

        completion_level = (
            "error"
            if result_status == "FAILED"
            else "warning"
            if result_status == "NEED REVIEW"
            else "info"
        )

        _qa_tel_append_event(
            data=data,
            stage="execution",
            event="session_completed",
            level=completion_level,
            status="completed",
            message=(
                "Execution telemetry session "
                f"completed with status {result_status}."
            ),
            duration_ms=total_duration_ms,
            metadata=request.summary,
        )

        data["execution_id"] = (
            request.execution_id
        )

        data["completed_at"] = (
            completed_at
        )

        data["total_duration_ms"] = (
            total_duration_ms
        )

        data["result_status"] = (
            result_status
        )

        _qa_tel_write_session(
            path,
            data,
        )

        standard_json_updated = (
            _qa_tel_update_standard_json(
                request.standard_json_path,
                data,
                path,
            )
        )

        history_updated = (
            _qa_tel_update_history(
                request.execution_id,
                data,
                path,
            )
        )

    return {
        "ok": True,
        "telemetry_id": request.session_id,
        "execution_id": request.execution_id,
        "telemetry_path": str(path),
        "event_count": len(
            data.get("events") or []
        ),
        "total_duration_ms": (
            total_duration_ms
        ),
        "artifact_updates": {
            "standard_json_updated": (
                standard_json_updated
            ),
            "history_updated": (
                history_updated
            ),
        },
    }


@app.get("/telemetry/{session_id}")
def get_execution_telemetry(
    session_id: str,
):
    path, data = _qa_tel_read_session(
        session_id
    )

    return {
        "ok": True,
        "telemetry_path": str(path),
        "telemetry": data,
    }
'''


if '@app.post("/telemetry/start")' not in text:
    text = (
        text.rstrip()
        + "\n"
        + telemetry_code
        + "\n"
    )

    print("Inserted telemetry endpoints")
else:
    print("Telemetry endpoints already exist")


# ------------------------------------------------------------
# Run Detail: prefer structured execution events
# ------------------------------------------------------------

timeline_marker = '''def _qa_rd_build_timeline(run, standard_json, analysis):
    events = []
    seen = set()
'''

timeline_replacement = '''def _qa_rd_build_timeline(run, standard_json, analysis):
    events = []
    seen = set()

    stored_events = (
        standard_json.get("execution_events")
        if isinstance(standard_json, dict)
        else None
    )

    if isinstance(stored_events, list) and stored_events:
        structured_events = []

        for item in stored_events:
            if not isinstance(item, dict):
                continue

            message = str(
                item.get("message")
                or item.get("event")
                or "Execution event"
            )

            stage = str(
                item.get("stage")
                or "execution"
            )

            event_name = str(
                item.get("event")
                or "event"
            )

            label = (
                stage.replace("_", " ").title()
                + " · "
                + event_name.replace("_", " ").title()
            )

            structured_events.append({
                "type": stage,
                "label": label,
                "timestamp": str(
                    item.get("timestamp") or "-"
                ),
                "description": message,
                "level": str(
                    item.get("level") or "info"
                ),
                "status": str(
                    item.get("status") or "-"
                ),
                "duration_ms": item.get(
                    "duration_ms"
                ),
                "sequence": item.get(
                    "sequence"
                ),
            })

        if structured_events:
            return structured_events
'''

if (
    "stored_events = (" not in text
    and timeline_marker in text
):
    text = text.replace(
        timeline_marker,
        timeline_replacement,
        1,
    )

    print(
        "Patched Run Detail structured timeline"
    )
else:
    print(
        "Run Detail structured timeline already patched"
    )


# ------------------------------------------------------------
# Run Detail: load telemetry when Standard JSON has no events
# ------------------------------------------------------------

standard_json_marker = '''    if not isinstance(standard_json, dict):
        standard_json = {}

    execution = standard_json.get(
'''

standard_json_replacement = '''    if not isinstance(standard_json, dict):
        standard_json = {}

    telemetry_path = _qa_rd_safe_file_path(
        run.get("telemetry_path")
    )

    telemetry_data = _qa_rd_read_json(
        telemetry_path
    )

    if (
        not isinstance(
            standard_json.get("execution_events"),
            list,
        )
        and isinstance(telemetry_data, dict)
        and isinstance(
            telemetry_data.get("events"),
            list,
        )
    ):
        standard_json["execution_events"] = (
            telemetry_data.get("events")
        )

    execution = standard_json.get(
'''

if (
    "telemetry_data = _qa_rd_read_json" not in text
    and standard_json_marker in text
):
    text = text.replace(
        standard_json_marker,
        standard_json_replacement,
        1,
    )

    print(
        "Patched Run Detail telemetry fallback"
    )
else:
    print(
        "Run Detail telemetry fallback already patched"
    )


# ------------------------------------------------------------
# Run Detail: add telemetry artifact
# ------------------------------------------------------------

artifact_marker = '''        (
            "raw_output",
            "Raw Output",
            run.get("raw_output_path")
            or standard_artifacts.get("raw_output"),
        ),
        (
            "analysis",
'''

artifact_replacement = '''        (
            "raw_output",
            "Raw Output",
            run.get("raw_output_path")
            or standard_artifacts.get("raw_output"),
        ),
        (
            "telemetry",
            "Execution Telemetry",
            run.get("telemetry_path")
            or standard_artifacts.get("telemetry"),
        ),
        (
            "analysis",
'''

if (
    '"Execution Telemetry"' not in text
    and artifact_marker in text
):
    text = text.replace(
        artifact_marker,
        artifact_replacement,
        1,
    )

    print(
        "Added telemetry to Run Detail artifacts"
    )
else:
    print(
        "Run Detail telemetry artifact already exists"
    )


# ------------------------------------------------------------
# Run Detail: mark per-step timestamp availability accurately
# ------------------------------------------------------------

availability_marker = '''            "per_step_timestamps": False,
            "analysis": isinstance(
'''

availability_replacement = '''            "per_step_timestamps": bool(
                isinstance(
                    standard_json.get("execution_events"),
                    list,
                )
                and standard_json.get("execution_events")
            ),
            "structured_execution_events": bool(
                isinstance(
                    standard_json.get("execution_events"),
                    list,
                )
                and standard_json.get("execution_events")
            ),
            "analysis": isinstance(
'''

if availability_marker in text:
    text = text.replace(
        availability_marker,
        availability_replacement,
        1,
    )

    print(
        "Patched telemetry data availability"
    )
elif '"structured_execution_events"' in text:
    print(
        "Telemetry availability already patched"
    )
else:
    print(
        "WARNING: availability marker not found"
    )


APP_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
