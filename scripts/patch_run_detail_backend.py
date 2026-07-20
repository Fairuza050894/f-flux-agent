from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(
    f"app.py.backup_before_run_detail_{timestamp}"
)

shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text(encoding="utf-8")


route_code = r'''

# ============================================================
# Run Detail MVP
# ============================================================

def _qa_rd_project_root():
    from pathlib import Path

    return Path(__file__).resolve().parents[2].resolve()


def _qa_rd_history_path():
    return (
        _qa_rd_project_root()
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "history"
        / "qa_run_history.json"
    )


def _qa_rd_safe_file_path(raw_path):
    from pathlib import Path

    if not raw_path:
        return None

    project_root = _qa_rd_project_root()

    try:
        path = Path(str(raw_path)).expanduser().resolve()
        path.relative_to(project_root)
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_rd_read_json(path):
    import json

    if not path:
        return None

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return None


def _qa_rd_mask_text(value):
    import re

    text = str(value or "")

    patterns = [
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
            r'(?i)("?(?:password|passwd|token|secret|api[_-]?key)"?'
            r'\s*[:=]\s*")([^"]+)(")',
            r'\1***MASKED***\3',
        ),
        (
            r"(?i)((?:password|passwd|token|secret|api[_-]?key)"
            r"\s*[:=]\s*)[^\s,;]+",
            r"\1***MASKED***",
        ),
    ]

    for pattern, replacement in patterns:
        text = re.sub(
            pattern,
            replacement,
            text,
        )

    return text[:12000]


def _qa_rd_file_metadata(key, label, raw_path):
    from datetime import datetime
    from urllib.parse import quote

    path = _qa_rd_safe_file_path(raw_path)

    if not path:
        return {
            "key": key,
            "label": label,
            "available": False,
            "filename": None,
            "path": None,
            "size_bytes": None,
            "modified_at": None,
            "open_url": None,
        }

    stat = path.stat()

    return {
        "key": key,
        "label": label,
        "available": True,
        "filename": path.name,
        "path": str(path),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "open_url": (
            "/artifacts?path="
            + quote(str(path), safe="")
        ),
    }


def _qa_rd_find_run(execution_id):
    import json

    history_path = _qa_rd_history_path()

    if not history_path.exists():
        raise HTTPException(
            status_code=404,
            detail="QA run history file not found",
        )

    try:
        data = json.loads(
            history_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to read QA run history: "
                + str(error)
            ),
        )

    if not isinstance(data, list):
        raise HTTPException(
            status_code=500,
            detail="QA run history root is not a list",
        )

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        if str(item.get("execution_id") or "") == execution_id:
            return index, item

    raise HTTPException(
        status_code=404,
        detail=(
            "Run not found for execution_id: "
            + execution_id
        ),
    )


def _qa_rd_resolve_analysis(run, standard_json):
    analysis = None

    if isinstance(standard_json, dict):
        candidate = standard_json.get("analysis")

        if isinstance(candidate, dict):
            analysis = candidate

    analysis_summary = run.get(
        "analysis_summary"
    )

    if analysis is None and isinstance(
        analysis_summary,
        dict,
    ):
        analysis_path = _qa_rd_safe_file_path(
            analysis_summary.get("analysis_path")
        )

        loaded_analysis = _qa_rd_read_json(
            analysis_path
        )

        if isinstance(loaded_analysis, dict):
            analysis = loaded_analysis
        else:
            analysis = dict(analysis_summary)

    return analysis


def _qa_rd_build_timeline(run, standard_json, analysis):
    events = []
    seen = set()

    execution = {}

    if isinstance(standard_json, dict):
        candidate = standard_json.get(
            "execution"
        )

        if isinstance(candidate, dict):
            execution = candidate

    executed_at = (
        execution.get("executed_at")
        or run.get("executed_at")
    )

    created_at = run.get("created_at")

    analysis_generated_at = (
        analysis.get("generated_at")
        if isinstance(analysis, dict)
        else None
    )

    def add_event(
        event_type,
        label,
        timestamp_value,
        description,
    ):
        if not timestamp_value:
            return

        key = (
            str(timestamp_value),
            str(label),
        )

        if key in seen:
            return

        seen.add(key)

        events.append({
            "type": event_type,
            "label": label,
            "timestamp": str(timestamp_value),
            "description": description,
        })

    add_event(
        "execution",
        "Execution recorded",
        executed_at,
        (
            "QA execution result was recorded "
            "by the runner."
        ),
    )

    if (
        created_at
        and str(created_at) != str(executed_at)
    ):
        add_event(
            "history",
            "History entry created",
            created_at,
            (
                "The run was added to "
                "qa_run_history.json."
            ),
        )

    add_event(
        "analysis",
        "Analysis generated",
        analysis_generated_at,
        (
            "Analysis Agent generated root-cause "
            "and release recommendations."
        ),
    )

    return events


def _qa_rd_normalize_feature_results(
    run,
    standard_json,
):
    source = None

    if isinstance(standard_json, dict):
        candidate = standard_json.get("features")

        if isinstance(candidate, list):
            source = candidate

    if source is None:
        candidate = run.get("feature_results")

        if isinstance(candidate, list):
            source = candidate

    if not isinstance(source, list):
        return []

    allowed_fields = [
        "name",
        "status",
        "passed",
        "failed",
        "need_review",
        "skipped",
        "warnings",
        "bugs_found",
    ]

    results = []

    for item in source:
        if not isinstance(item, dict):
            continue

        normalized = {
            field: item.get(field)
            for field in allowed_fields
        }

        results.append(normalized)

    return results


@app.get("/history/{execution_id}")
def get_run_detail(execution_id: str):
    history_index, run = _qa_rd_find_run(
        execution_id
    )

    standard_json_path = _qa_rd_safe_file_path(
        run.get("standard_json_path")
    )

    standard_json = _qa_rd_read_json(
        standard_json_path
    )

    if not isinstance(standard_json, dict):
        standard_json = {}

    execution = standard_json.get(
        "execution"
    )

    if not isinstance(execution, dict):
        execution = {}

    summary = standard_json.get("summary")

    if not isinstance(summary, dict):
        summary = {
            "passed": run.get("passed", 0),
            "failed": run.get("failed", 0),
            "need_review": run.get(
                "need_review",
                0,
            ),
            "skipped": run.get("skipped", 0),
            "warnings": run.get("warnings", 0),
            "bugs_found": run.get(
                "bugs_found",
                0,
            ),
            "features_tested": len(
                run.get("feature_results") or []
            ),
        }

    analysis = _qa_rd_resolve_analysis(
        run,
        standard_json,
    )

    standard_artifacts = standard_json.get(
        "artifacts"
    )

    if not isinstance(
        standard_artifacts,
        dict,
    ):
        standard_artifacts = {}

    analysis_summary = run.get(
        "analysis_summary"
    )

    if not isinstance(
        analysis_summary,
        dict,
    ):
        analysis_summary = {}

    artifact_sources = [
        (
            "report",
            "QA Report",
            run.get("report_path")
            or standard_artifacts.get("report"),
        ),
        (
            "screenshot",
            "Screenshot",
            run.get("screenshot_path")
            or standard_artifacts.get("screenshot"),
        ),
        (
            "error_log",
            "Error Log",
            run.get("error_log_path")
            or standard_artifacts.get("error_log"),
        ),
        (
            "spreadsheet",
            "Spreadsheet",
            run.get("spreadsheet_path")
            or standard_artifacts.get("spreadsheet"),
        ),
        (
            "standard_json",
            "Standard JSON",
            run.get("standard_json_path"),
        ),
        (
            "raw_output",
            "Raw Output",
            run.get("raw_output_path")
            or standard_artifacts.get("raw_output"),
        ),
        (
            "analysis",
            "Analysis JSON",
            analysis_summary.get("analysis_path")
            or standard_artifacts.get("analysis_path"),
        ),
    ]

    artifacts = [
        _qa_rd_file_metadata(
            key,
            label,
            raw_path,
        )
        for key, label, raw_path
        in artifact_sources
    ]

    raw_data = standard_json.get("raw")

    if not isinstance(raw_data, dict):
        raw_data = {}

    testing_summary = _qa_rd_mask_text(
        raw_data.get("testing_summary")
    )

    feature_results = (
        _qa_rd_normalize_feature_results(
            run,
            standard_json,
        )
    )

    timeline = _qa_rd_build_timeline(
        run,
        standard_json,
        analysis,
    )

    return {
        "ok": True,
        "type": "run_detail",
        "history_index": history_index,
        "run": {
            "execution_id": run.get(
                "execution_id"
            ),
            "feature": run.get("feature"),
            "environment": (
                execution.get("environment")
                or run.get("environment")
            ),
            "mode": (
                execution.get("mode")
                or run.get("mode")
            ),
            "status": (
                execution.get("overall_status")
                or run.get("status")
            ),
            "base_url": (
                execution.get("base_url")
                or run.get("base_url")
            ),
            "executed_at": (
                execution.get("executed_at")
                or run.get("executed_at")
            ),
            "created_at": run.get(
                "created_at"
            ),
        },
        "summary": summary,
        "feature_results": feature_results,
        "timeline": timeline,
        "analysis": analysis,
        "artifacts": artifacts,
        "testing_summary": testing_summary,
        "data_availability": {
            "structured_feature_results": bool(
                feature_results
            ),
            "structured_test_cases": False,
            "request_response": False,
            "per_step_timestamps": False,
            "analysis": isinstance(
                analysis,
                dict,
            ),
            "notes": [
                (
                    "Current schema stores feature-level "
                    "aggregates, not individual test cases."
                ),
                (
                    "Current schema does not store "
                    "structured request/response data."
                ),
                (
                    "Timeline only contains timestamps "
                    "that are present in stored artifacts."
                ),
            ],
        },
    }
'''

if '@app.get("/history/{execution_id}")' not in text:
    text = text.rstrip() + "\n" + route_code + "\n"

    APP_PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Inserted GET /history/{execution_id}"
    )
else:
    print(
        "GET /history/{execution_id} already exists"
    )

print(f"Backup created: {backup_path}")
