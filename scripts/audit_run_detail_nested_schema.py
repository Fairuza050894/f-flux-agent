from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_ROOT = ROOT / "skills" / "qa_automation" / "artifacts"
HISTORY_PATH = ARTIFACT_ROOT / "history" / "qa_run_history.json"
OUTPUT_PATH = ROOT / "run_detail_nested_schema_audit.txt"

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
    "body",
    "header",
    "credential",
}

SAFE_VALUE_KEYS = {
    "execution_id",
    "run_id",
    "status",
    "feature",
    "feature_name",
    "module",
    "module_name",
    "mode",
    "environment",
    "created_at",
    "executed_at",
    "started_at",
    "completed_at",
    "generated_at",
    "duration",
    "duration_ms",
    "duration_seconds",
    "passed",
    "failed",
    "need_review",
    "skipped",
    "warnings",
    "bugs_found",
    "title",
    "name",
    "test_id",
    "case_id",
    "priority",
    "severity",
    "category",
    "confidence",
}


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")

    return any(
        marker in normalized
        for marker in SENSITIVE_MARKERS
    )


def describe(value: Any) -> str:
    if isinstance(value, dict):
        return f"dict({len(value)} keys)"

    if isinstance(value, list):
        return f"list({len(value)} items)"

    if value is None:
        return "null"

    return type(value).__name__


def safe_value(key: str, value: Any) -> str:
    if is_sensitive_key(key):
        return "***NOT PRINTED***"

    if isinstance(value, (dict, list)):
        return describe(value)

    if key in SAFE_VALUE_KEYS:
        return str(value)[:200]

    return describe(value)


def render_dict_schema(
    value: dict[str, Any],
    title: str,
    indent: int = 0,
    max_depth: int = 3,
) -> list[str]:
    prefix = "  " * indent

    lines = [
        "",
        f"{prefix}{title}",
        f"{prefix}{'-' * max(10, len(title))}",
    ]

    for key in sorted(value.keys()):
        item = value[key]

        lines.append(
            f"{prefix}- {key}: {safe_value(key, item)}"
        )

        if indent >= max_depth:
            continue

        if isinstance(item, dict):
            nested_keys = ", ".join(
                sorted(item.keys())
            ) or "(empty)"

            lines.append(
                f"{prefix}  nested keys: {nested_keys}"
            )

        elif isinstance(item, list):
            lines.append(
                f"{prefix}  list count: {len(item)}"
            )

            if item and isinstance(item[0], dict):
                item_keys = ", ".join(
                    sorted(item[0].keys())
                ) or "(empty)"

                lines.append(
                    f"{prefix}  first item keys: {item_keys}"
                )

    return lines


def resolve_safe_project_path(raw_path: Any) -> Path | None:
    if not raw_path:
        return None

    try:
        path = Path(str(raw_path)).expanduser().resolve()
        path.relative_to(ROOT.resolve())
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def read_json_file(path: Path | None) -> Any:
    if not path:
        return None

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except Exception:
        return None


def select_sample_runs(
    runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    with_analysis = next(
        (
            run
            for run in runs
            if isinstance(
                run.get("analysis_summary"),
                dict,
            )
        ),
        None,
    )

    without_analysis = next(
        (
            run
            for run in runs
            if not isinstance(
                run.get("analysis_summary"),
                dict,
            )
        ),
        None,
    )

    with_feature_results = next(
        (
            run
            for run in runs
            if isinstance(
                run.get("feature_results"),
                list,
            )
            and run.get("feature_results")
        ),
        None,
    )

    for item in (
        with_analysis,
        without_analysis,
        with_feature_results,
    ):
        if not item:
            continue

        execution_id = item.get("execution_id")

        if any(
            existing.get("execution_id") == execution_id
            for existing in selected
        ):
            continue

        selected.append(item)

    return selected[:3]


def inspect_standard_json(
    run: dict[str, Any],
    lines: list[str],
) -> None:
    standard_path = resolve_safe_project_path(
        run.get("standard_json_path")
    )

    lines.extend([
        "",
        "STANDARD JSON CHECK",
        "-------------------",
        "Path status: "
        + (
            str(standard_path)
            if standard_path
            else "missing or inaccessible"
        ),
    ])

    standard_data = read_json_file(standard_path)

    if not isinstance(standard_data, dict):
        lines.append(
            "Standard JSON schema: unavailable"
        )
        return

    lines.extend(
        render_dict_schema(
            standard_data,
            "Standard JSON top-level schema",
        )
    )

    for candidate_key in (
        "test_cases",
        "tests",
        "results",
        "feature_results",
        "summary",
        "execution",
        "analysis",
        "artifacts",
        "metadata",
    ):
        candidate = standard_data.get(candidate_key)

        if isinstance(candidate, dict):
            lines.extend(
                render_dict_schema(
                    candidate,
                    f"Standard JSON.{candidate_key}",
                    indent=1,
                )
            )

        elif isinstance(candidate, list):
            lines.extend([
                "",
                f"Standard JSON.{candidate_key}",
                "  type: list",
                f"  count: {len(candidate)}",
            ])

            if candidate and isinstance(
                candidate[0],
                dict,
            ):
                lines.extend(
                    render_dict_schema(
                        candidate[0],
                        (
                            "Standard JSON."
                            f"{candidate_key}[0]"
                        ),
                        indent=1,
                    )
                )


def inspect_feature_results(
    run: dict[str, Any],
    lines: list[str],
) -> None:
    feature_results = run.get("feature_results")

    lines.extend([
        "",
        "FEATURE RESULTS CHECK",
        "---------------------",
    ])

    if not isinstance(feature_results, list):
        lines.append(
            "feature_results is not a list"
        )
        return

    lines.append(
        f"feature_results count: {len(feature_results)}"
    )

    for index, item in enumerate(
        feature_results[:3]
    ):
        if isinstance(item, dict):
            lines.extend(
                render_dict_schema(
                    item,
                    f"feature_results[{index}]",
                )
            )

            for nested_key in (
                "test_cases",
                "tests",
                "cases",
                "results",
                "steps",
                "checks",
            ):
                nested = item.get(nested_key)

                if isinstance(nested, list):
                    lines.extend([
                        "",
                        (
                            f"feature_results[{index}]"
                            f".{nested_key}"
                        ),
                        f"  count: {len(nested)}",
                    ])

                    if nested and isinstance(
                        nested[0],
                        dict,
                    ):
                        lines.extend(
                            render_dict_schema(
                                nested[0],
                                (
                                    f"feature_results[{index}]"
                                    f".{nested_key}[0]"
                                ),
                                indent=1,
                            )
                        )
        else:
            lines.append(
                f"feature_results[{index}]: "
                f"{describe(item)}"
            )


def main() -> None:
    if not HISTORY_PATH.exists():
        raise FileNotFoundError(
            f"History not found: {HISTORY_PATH}"
        )

    data = json.loads(
        HISTORY_PATH.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, list):
        raise TypeError(
            "Expected history root to be a list."
        )

    runs = [
        item
        for item in data
        if isinstance(item, dict)
    ]

    samples = select_sample_runs(runs)

    lines = [
        "RUN DETAIL NESTED SCHEMA AUDIT",
        "=" * 42,
        f"History path: {HISTORY_PATH}",
        f"Total runs: {len(runs)}",
        f"Selected samples: {len(samples)}",
        "",
        "This audit does not print request bodies,",
        "responses, cURL commands, credentials, or tokens.",
    ]

    for sample_number, run in enumerate(
        samples,
        start=1,
    ):
        lines.extend([
            "",
            "",
            "=" * 42,
            f"SAMPLE {sample_number}",
            "=" * 42,
            "Execution ID: "
            + str(
                run.get("execution_id") or "-"
            ),
            "Feature: "
            + str(run.get("feature") or "-"),
            "Status: "
            + str(run.get("status") or "-"),
            "Created At: "
            + str(run.get("created_at") or "-"),
            "Executed At: "
            + str(run.get("executed_at") or "-"),
        ])

        analysis_summary = run.get(
            "analysis_summary"
        )

        if isinstance(analysis_summary, dict):
            lines.extend(
                render_dict_schema(
                    analysis_summary,
                    "analysis_summary",
                )
            )
        else:
            lines.extend([
                "",
                "analysis_summary: not present",
            ])

        inspect_feature_results(
            run,
            lines,
        )

        inspect_standard_json(
            run,
            lines,
        )

        artifact_checks = [
            "report_path",
            "screenshot_path",
            "error_log_path",
            "spreadsheet_path",
            "standard_json_path",
            "raw_output_path",
        ]

        lines.extend([
            "",
            "ARTIFACT EXISTENCE",
            "------------------",
        ])

        for field in artifact_checks:
            resolved = resolve_safe_project_path(
                run.get(field)
            )

            lines.append(
                f"- {field}: "
                + (
                    "exists"
                    if resolved
                    else "missing"
                )
            )

    lines.extend([
        "",
        "",
        "NEXT IMPLEMENTATION RULE",
        "------------------------",
        (
            "Only fields confirmed in this audit "
            "will be rendered in Run Detail."
        ),
        (
            "Missing timestamps and stages will be "
            "shown as unavailable, not simulated."
        ),
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
