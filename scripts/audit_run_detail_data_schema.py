from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "skills" / "qa_automation" / "artifacts"
OUTPUT_PATH = ROOT / "run_detail_schema_audit.txt"

HISTORY_CANDIDATES = [
    ARTIFACT_ROOT / "history" / "qa_run_history.json",
    ARTIFACT_ROOT / "qa_run_history.json",
]

SAFE_VALUE_KEYS = {
    "status",
    "mode",
    "type",
    "runner_type",
    "feature_name",
    "module_name",
    "generated_at",
    "timestamp",
    "created_at",
    "started_at",
    "completed_at",
    "duration_seconds",
    "duration_ms",
    "execution_id",
    "run_id",
    "plan_id",
}

SENSITIVE_MARKERS = {
    "authorization",
    "password",
    "passwd",
    "token",
    "secret",
    "cookie",
    "api_key",
    "apikey",
    "curl",
    "request",
    "response",
    "payload",
}


def find_history_path() -> Path:
    for path in HISTORY_CANDIDATES:
        if path.exists() and path.is_file():
            return path

    history_dir = ARTIFACT_ROOT / "history"

    if history_dir.exists():
        matches = sorted(
            history_dir.glob("*history*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )

        if matches:
            return matches[0]

    raise FileNotFoundError(
        "Run history JSON was not found under "
        f"{ARTIFACT_ROOT}"
    )


def collect_run_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    if not isinstance(data, dict):
        return []

    for key in (
        "runs",
        "history",
        "items",
        "records",
        "entries",
        "data",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return [
                item
                for item in value
                if isinstance(item, dict)
            ]

    run_markers = {
        "status",
        "feature",
        "feature_name",
        "run_id",
        "execution_id",
        "standard_json_path",
        "report_path",
        "documentation_path",
    }

    if any(key in data for key in run_markers):
        return [data]

    candidates: list[dict[str, Any]] = []

    for value in data.values():
        if isinstance(value, list):
            candidates.extend(
                item
                for item in value
                if isinstance(item, dict)
            )

    return candidates


def describe_value(value: Any) -> str:
    if isinstance(value, dict):
        return f"dict({len(value)} keys)"

    if isinstance(value, list):
        return f"list({len(value)} items)"

    if value is None:
        return "null"

    return type(value).__name__


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")

    return any(
        marker in lowered
        for marker in SENSITIVE_MARKERS
    )


def safe_value(key: str, value: Any) -> str:
    if is_sensitive_key(key):
        return "***NOT PRINTED***"

    if key not in SAFE_VALUE_KEYS:
        return describe_value(value)

    if isinstance(value, (dict, list)):
        return describe_value(value)

    return str(value)[:180]


def find_path_fields(
    node: Any,
    prefix: str = "",
) -> list[str]:
    found: list[str] = []

    if isinstance(node, dict):
        for key, value in node.items():
            current = (
                f"{prefix}.{key}"
                if prefix
                else key
            )

            if key.lower().endswith("_path"):
                found.append(current)

            if isinstance(value, (dict, list)):
                found.extend(
                    find_path_fields(value, current)
                )

    elif isinstance(node, list):
        for index, value in enumerate(node[:5]):
            current = f"{prefix}[{index}]"
            found.extend(
                find_path_fields(value, current)
            )

    return sorted(set(found))


def find_list_fields(
    node: dict[str, Any],
) -> list[str]:
    return [
        f"{key}: {len(value)} item(s)"
        for key, value in node.items()
        if isinstance(value, list)
    ]


def find_nested_dict_fields(
    node: dict[str, Any],
) -> list[str]:
    result = []

    for key, value in node.items():
        if isinstance(value, dict):
            nested_keys = (
                ", ".join(sorted(value.keys()))
                or "(empty)"
            )

            result.append(
                f"{key}: {nested_keys}"
            )

    return result


def render_sample(
    index: int,
    item: dict[str, Any],
) -> list[str]:
    lines = [
        "",
        f"=== SAMPLE RUN #{index + 1} ===",
        "Top-level keys:",
        ", ".join(sorted(item.keys())) or "(none)",
        "",
        "Safe field summary:",
    ]

    for key in sorted(item.keys()):
        lines.append(
            f"- {key}: {safe_value(key, item[key])}"
        )

    nested = find_nested_dict_fields(item)

    if nested:
        lines.extend([
            "",
            "Nested dictionary keys:",
            *(
                f"- {entry}"
                for entry in nested
            ),
        ])
    else:
        lines.extend([
            "",
            "Nested dictionary keys: none",
        ])

    list_fields = find_list_fields(item)

    if list_fields:
        lines.extend([
            "",
            "List fields:",
            *(
                f"- {entry}"
                for entry in list_fields
            ),
        ])
    else:
        lines.extend([
            "",
            "List fields: none",
        ])

    path_fields = find_path_fields(item)

    if path_fields:
        lines.extend([
            "",
            "Artifact/path field names:",
            *(
                f"- {entry}"
                for entry in path_fields
            ),
        ])
    else:
        lines.extend([
            "",
            "Artifact/path field names: none",
        ])

    analysis = (
        item.get("analysis")
        or item.get("analysis_summary")
    )

    lines.append("")
    lines.append(
        "Analysis data: "
        + (
            "present"
            if isinstance(analysis, dict)
            else "not present"
        )
    )

    candidate_case_fields = [
        key
        for key in (
            "test_cases",
            "tests",
            "cases",
            "results",
        )
        if isinstance(item.get(key), list)
    ]

    lines.append(
        "Structured test-case fields: "
        + (
            ", ".join(candidate_case_fields)
            or "none"
        )
    )

    return lines


def main() -> None:
    history_path = find_history_path()

    data = json.loads(
        history_path.read_text(
            encoding="utf-8"
        )
    )

    runs = collect_run_items(data)

    lines = [
        "RUN DETAIL DATA SCHEMA AUDIT",
        "=" * 40,
        f"Project root: {ROOT}",
        f"History path: {history_path}",
        f"Top-level JSON type: {type(data).__name__}",
    ]

    if isinstance(data, dict):
        lines.append(
            "Top-level JSON keys: "
            + (
                ", ".join(sorted(data.keys()))
                or "(none)"
            )
        )

    lines.append(
        f"Detected run entries: {len(runs)}"
    )

    if not runs:
        lines.extend([
            "",
            "No run entries were detected.",
            "Do not build Run Detail UI until "
            "the history writer schema is confirmed.",
        ])
    else:
        sample_indexes = [0]

        if len(runs) > 1:
            sample_indexes.append(
                len(runs) - 1
            )

        for sample_index in sample_indexes:
            lines.extend(
                render_sample(
                    sample_index,
                    runs[sample_index],
                )
            )

    analysis_dir = ARTIFACT_ROOT / "analysis"

    latest_analysis = sorted(
        analysis_dir.glob("*.json")
        if analysis_dir.exists()
        else [],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )

    lines.extend([
        "",
        "=== RELATED ARTIFACT CHECK ===",
        "Latest analysis JSON: "
        + (
            str(latest_analysis[0])
            if latest_analysis
            else "not found"
        ),
        "",
        "Security note:",
        "- Raw cURL, tokens, passwords, payloads, "
        "requests, and responses are not printed.",
        "- This audit only reports schema, field names, "
        "types, and selected safe metadata.",
    ])

    output = "\n".join(lines) + "\n"

    OUTPUT_PATH.write_text(
        output,
        encoding="utf-8",
    )

    print(output)
    print(
        f"Audit saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
