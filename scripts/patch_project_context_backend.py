from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]

APP_PATH = (
    ROOT
    / "qa_dashboard"
    / "backend"
    / "app.py"
)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_path = APP_PATH.with_name(
    "app.py.backup_before_project_context_mvp_"
    + timestamp
)

shutil.copy2(
    APP_PATH,
    backup_path,
)

text = APP_PATH.read_text(
    encoding="utf-8"
)


project_context_code = r'''

# ============================================================
# Project Context Attachment MVP
# ============================================================

from pydantic import BaseModel as _PCBaseModel
from typing import Optional as _PCOptional
from typing import Dict as _PCDict
from typing import Any as _PCAny


class ProjectContextAttachRequest(_PCBaseModel):
    project_id: str
    execution_id: _PCOptional[str] = None
    standard_json_path: _PCOptional[str] = None
    telemetry_id: _PCOptional[str] = None
    artifact_paths: _PCDict[str, _PCAny] = {}


def _qa_pc_project_root():
    from pathlib import Path

    return (
        Path(__file__).resolve()
        .parents[2]
        .resolve()
    )


def _qa_pc_artifact_root():
    path = (
        _qa_pc_project_root()
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "project_metadata"
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def _qa_pc_now():
    from datetime import datetime

    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def _qa_pc_read_json(path, default=None):
    import json

    if default is None:
        default = {}

    if not path or not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


def _qa_pc_write_json(path, payload):
    import json

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _qa_pc_safe_file(raw_path):
    from pathlib import Path

    if not raw_path:
        return None

    root = _qa_pc_project_root()

    try:
        path = (
            Path(str(raw_path))
            .expanduser()
        )

        if not path.is_absolute():
            path = root / path

        path = path.resolve()
        path.relative_to(root)

    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_pc_safe_execution_id(value):
    import re

    text = str(
        value or ""
    ).strip()

    if not text:
        return None

    if not re.fullmatch(
        r"[A-Za-z0-9_-]{3,100}",
        text,
    ):
        return None

    return text


def _qa_pc_resolve_project(project_id):
    safe_project_id = _qa_project_safe_id(
        project_id
    )

    for entry in _qa_project_registry_entries():
        if str(
            entry.get("project_id") or ""
        ).lower() != safe_project_id:
            continue

        project = _qa_project_load_entry(
            entry
        )

        if project:
            return project

    raise HTTPException(
        status_code=404,
        detail=(
            "Project not found: "
            + safe_project_id
        ),
    )


def _qa_pc_build_context(project):
    environment_id = str(
        project.get(
            "default_environment"
        )
        or "custom"
    )

    environment_name = str(
        project.get(
            "default_environment_name"
        )
        or environment_id.title()
    )

    return {
        "project_id": str(
            project.get("project_id")
            or ""
        ),
        "project_name": str(
            project.get("name")
            or ""
        ),
        "environment_id": (
            environment_id
        ),
        "environment_name": (
            environment_name
        ),
        "project_status": str(
            project.get("status")
            or "unknown"
        ),
        "attached_at": _qa_pc_now(),
    }


def _qa_pc_allowed_artifacts(
    artifact_paths,
):
    allowed_keys = {
        "standard_json",
        "report",
        "screenshot",
        "error_log",
        "spreadsheet",
        "raw_output",
        "analysis",
        "telemetry",
    }

    result = {}

    if not isinstance(
        artifact_paths,
        dict,
    ):
        return result

    for key, raw_path in (
        artifact_paths.items()
    ):
        normalized_key = str(
            key
        ).strip().lower()

        if normalized_key not in allowed_keys:
            continue

        path = _qa_pc_safe_file(
            raw_path
        )

        if path:
            result[normalized_key] = (
                str(path)
            )

    return result


def _qa_pc_extract_standard_artifacts(
    standard_json,
):
    result = {}

    if not isinstance(
        standard_json,
        dict,
    ):
        return result

    artifacts = standard_json.get(
        "artifacts"
    )

    if not isinstance(
        artifacts,
        dict,
    ):
        return result

    aliases = {
        "standard_json": (
            "standard_json"
        ),
        "report": "report",
        "screenshot": "screenshot",
        "error_log": "error_log",
        "spreadsheet": "spreadsheet",
        "raw_output": "raw_output",
        "analysis_path": "analysis",
        "analysis": "analysis",
        "telemetry": "telemetry",
    }

    for source_key, target_key in (
        aliases.items()
    ):
        path = _qa_pc_safe_file(
            artifacts.get(source_key)
        )

        if path:
            result[target_key] = str(
                path
            )

    return result


def _qa_pc_update_standard_json(
    path,
    context,
    metadata_path,
):
    if not path:
        return False, {}

    payload = _qa_pc_read_json(
        path,
        {},
    )

    if not isinstance(payload, dict):
        return False, {}

    execution = payload.get(
        "execution"
    )

    if not isinstance(execution, dict):
        execution = {}
        payload["execution"] = execution

    execution.update({
        "project_id": (
            context["project_id"]
        ),
        "project_name": (
            context["project_name"]
        ),
        "environment_id": (
            context["environment_id"]
        ),
        "environment_name": (
            context["environment_name"]
        ),
    })

    payload["project_context"] = (
        context
    )

    artifacts = payload.get(
        "artifacts"
    )

    if not isinstance(artifacts, dict):
        artifacts = {}
        payload["artifacts"] = artifacts

    artifacts["project_metadata"] = str(
        metadata_path
    )

    _qa_pc_write_json(
        path,
        payload,
    )

    return True, payload


def _qa_pc_update_context_json(
    path,
    context,
    metadata_path,
):
    if not path:
        return False

    payload = _qa_pc_read_json(
        path,
        {},
    )

    if not isinstance(payload, dict):
        return False

    payload["project_context"] = (
        context
    )

    artifacts = payload.get(
        "artifacts"
    )

    if isinstance(artifacts, dict):
        artifacts[
            "project_metadata"
        ] = str(metadata_path)

    _qa_pc_write_json(
        path,
        payload,
    )

    return True


def _qa_pc_history_path():
    return (
        _qa_pc_project_root()
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "history"
        / "qa_run_history.json"
    )


def _qa_pc_update_history(
    execution_id,
    context,
    metadata_path,
):
    history_path = (
        _qa_pc_history_path()
    )

    history = _qa_pc_read_json(
        history_path,
        [],
    )

    if not isinstance(history, list):
        return False, {}

    matched = None

    for item in history:
        if not isinstance(item, dict):
            continue

        if str(
            item.get("execution_id")
            or ""
        ) != str(execution_id):
            continue

        item.update({
            "project_id": (
                context["project_id"]
            ),
            "project_name": (
                context["project_name"]
            ),
            "environment_id": (
                context["environment_id"]
            ),
            "environment_name": (
                context["environment_name"]
            ),
            "project_metadata_path": (
                str(metadata_path)
            ),
        })

        matched = item
        break

    if not matched:
        return False, {}

    _qa_pc_write_json(
        history_path,
        history,
    )

    return True, matched


def _qa_pc_telemetry_path(
    telemetry_id,
    artifact_paths,
):
    direct_path = _qa_pc_safe_file(
        artifact_paths.get(
            "telemetry"
        )
    )

    if direct_path:
        return direct_path

    if not telemetry_id:
        return None

    try:
        path = _qa_tel_session_path(
            telemetry_id
        )

        return (
            path
            if path.exists()
            else None
        )
    except Exception:
        return None


@app.post("/project-context/attach")
def attach_project_context(
    request: ProjectContextAttachRequest,
):
    project = _qa_pc_resolve_project(
        request.project_id
    )

    context = _qa_pc_build_context(
        project
    )

    execution_id = (
        _qa_pc_safe_execution_id(
            request.execution_id
        )
    )

    if not execution_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "A valid execution_id "
                "is required"
            ),
        )

    artifact_paths = (
        _qa_pc_allowed_artifacts(
            request.artifact_paths
        )
    )

    standard_json_path = (
        _qa_pc_safe_file(
            request.standard_json_path
        )
        or _qa_pc_safe_file(
            artifact_paths.get(
                "standard_json"
            )
        )
    )

    standard_payload = (
        _qa_pc_read_json(
            standard_json_path,
            {},
        )
        if standard_json_path
        else {}
    )

    standard_artifacts = (
        _qa_pc_extract_standard_artifacts(
            standard_payload
        )
    )

    artifact_paths.update(
        standard_artifacts
    )

    if standard_json_path:
        artifact_paths[
            "standard_json"
        ] = str(standard_json_path)

    telemetry_path = (
        _qa_pc_telemetry_path(
            request.telemetry_id,
            artifact_paths,
        )
    )

    if telemetry_path:
        artifact_paths[
            "telemetry"
        ] = str(telemetry_path)

    metadata_path = (
        _qa_pc_artifact_root()
        / (
            "project_context_"
            + execution_id
            + ".json"
        )
    )

    metadata_payload = {
        "schema_version": "1.0",
        "execution_id": execution_id,
        "project_context": context,
        "artifacts": artifact_paths,
        "security": {
            "credential_values_stored": (
                False
            ),
            "request_payload_stored": (
                False
            ),
        },
    }

    _qa_pc_write_json(
        metadata_path,
        metadata_payload,
    )

    standard_updated = False

    if standard_json_path:
        (
            standard_updated,
            standard_payload,
        ) = _qa_pc_update_standard_json(
            standard_json_path,
            context,
            metadata_path,
        )

    analysis_path = _qa_pc_safe_file(
        artifact_paths.get(
            "analysis"
        )
    )

    analysis_updated = (
        _qa_pc_update_context_json(
            analysis_path,
            context,
            metadata_path,
        )
        if analysis_path
        else False
    )

    telemetry_updated = (
        _qa_pc_update_context_json(
            telemetry_path,
            context,
            metadata_path,
        )
        if telemetry_path
        else False
    )

    (
        history_updated,
        history_item,
    ) = _qa_pc_update_history(
        execution_id,
        context,
        metadata_path,
    )

    return {
        "ok": True,
        "execution_id": execution_id,
        "project_context": context,
        "project_metadata_path": (
            str(metadata_path)
        ),
        "updates": {
            "history": (
                history_updated
            ),
            "standard_json": (
                standard_updated
            ),
            "telemetry": (
                telemetry_updated
            ),
            "analysis": (
                analysis_updated
            ),
        },
        "history_item": (
            history_item
            if history_updated
            else None
        ),
    }
'''


if (
    '@app.post("/project-context/attach")'
    not in text
):
    text = (
        text.rstrip()
        + "\n"
        + project_context_code
        + "\n"
    )

    print(
        "Inserted Project Context Attachment API"
    )
else:
    print(
        "Project Context Attachment API already exists"
    )


APP_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
