#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def write_envelope(
    output_path: Path,
    envelope: Dict[str, Any],
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = (
        tempfile.mkstemp(
            prefix=output_path.name + ".",
            suffix=".tmp",
            dir=str(output_path.parent),
        )
    )

    temporary_path = Path(
        temporary_name
    )

    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                envelope,
                handle,
                ensure_ascii=False,
                default=str,
            )

        temporary_path.replace(
            output_path
        )
    finally:
        if temporary_path.exists():
            temporary_path.unlink(
                missing_ok=True
            )


def normalize_text(
    value: Any,
) -> str:
    return re.sub(
        r"[^a-z0-9]+",
        " ",
        str(value or "").lower(),
    ).strip()


def normalize_case_status(
    value: Any,
) -> str:
    normalized = normalize_text(value).replace(
        " ",
        "_",
    )

    if normalized in {
        "fail",
        "failed",
        "error",
    }:
        return "failed"

    if normalized in {
        "need_review",
        "needs_review",
        "review",
    }:
        return "need_review"

    if normalized in {
        "pass",
        "passed",
        "success",
    }:
        return "passed"

    if normalized in {
        "skip",
        "skipped",
    }:
        return "skipped"

    return normalized or "unknown"


def read_target_descriptors(
    path_value: str,
) -> List[Dict[str, Any]]:
    if not path_value:
        return []

    path = Path(path_value)

    if not path.is_file():
        return []

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return []

    return [
        record
        for record in (
            payload
            if isinstance(
                payload,
                list,
            )
            else []
        )
        if isinstance(
            record,
            dict,
        )
    ]


def collect_target_aliases(
    descriptor: Dict[str, Any],
) -> set[str]:
    aliases: set[str] = set()

    candidates = [
        descriptor.get("asset_id"),
        descriptor.get("name"),
        descriptor.get(
            "automation_reference"
        ),
        descriptor.get(
            "runner_case_id"
        ),
        descriptor.get(
            "test_case_id"
        ),
    ]

    list_candidates = [
        descriptor.get(
            "automation_references"
        ),
        descriptor.get(
            "runner_case_ids"
        ),
        descriptor.get(
            "test_case_ids"
        ),
    ]

    for value in candidates:
        normalized = normalize_text(
            value
        )

        if normalized:
            aliases.add(normalized)

    for values in list_candidates:
        if not isinstance(
            values,
            list,
        ):
            continue

        for value in values:
            normalized = (
                normalize_text(value)
            )

            if normalized:
                aliases.add(
                    normalized
                )

    return aliases


def case_matches_targets(
    case: Dict[str, Any],
    targets: List[
        Dict[str, Any]
    ],
) -> bool:
    case_id = normalize_text(
        case.get("id")
        or case.get(
            "test_case_id"
        )
        or case.get(
            "testCaseId"
        )
    )

    scenario = normalize_text(
        case.get("scenario")
        or case.get("name")
        or case.get("title")
    )

    for target in targets:
        aliases = (
            collect_target_aliases(
                target
            )
        )

        for alias in aliases:
            if (
                case_id and
                case_id == alias
            ):
                return True

            if (
                scenario and
                len(alias) >= 5 and
                (
                    scenario == alias
                    or alias in scenario
                    or scenario in alias
                )
            ):
                return True

    return False


def build_target_summary(
    test_cases: List[
        Dict[str, Any]
    ],
    targets: List[
        Dict[str, Any]
    ],
    matched: bool,
) -> str:
    counts = {
        "passed": 0,
        "failed": 0,
        "need_review": 0,
        "skipped": 0,
    }

    for case in test_cases:
        status = (
            normalize_case_status(
                case.get("status")
            )
        )

        if status in counts:
            counts[status] += 1

    target_ids = [
        str(
            target.get(
                "asset_id",
                "",
            )
        ).strip()
        for target in targets
        if str(
            target.get(
                "asset_id",
                "",
            )
        ).strip()
    ]

    lines = [
        "Targeted Asset Rerun",
        (
            "Target Assets: "
            + (
                ", ".join(target_ids)
                or "Not specified"
            )
        ),
        (
            "Targeting Mode: "
            "post-run structured case filter"
        ),
    ]

    if matched:
        lines.extend([
            f"Passed: {counts['passed']}",
            f"Failed: {counts['failed']}",
            (
                "Need Review: "
                f"{counts['need_review']}"
            ),
            f"Skipped: {counts['skipped']}",
        ])
    else:
        lines.extend([
            (
                "Need Review: No structured "
                "runner case matched the selected "
                "Test Asset identity or name."
            ),
            (
                "Result is not reported as a pass "
                "because targeted mapping could not "
                "be verified."
            ),
        ])

    return "\n".join(lines)


def apply_target_filter(
    result: Any,
    targets: List[
        Dict[str, Any]
    ],
) -> Any:
    if not targets:
        return result

    if not isinstance(
        result,
        dict,
    ):
        result = {
            "status": "NEED_REVIEW",
            "testing_summary":
                str(result),
            "test_cases": [],
        }

    all_cases = (
        result.get("test_cases")
        if isinstance(
            result.get(
                "test_cases"
            ),
            list,
        )
        else []
    )

    matching_cases = [
        case
        for case in all_cases
        if (
            isinstance(
                case,
                dict,
            )
            and case_matches_targets(
                case,
                targets,
            )
        )
    ]

    target_ids = [
        str(
            target.get(
                "asset_id",
                "",
            )
        ).strip()
        for target in targets
        if str(
            target.get(
                "asset_id",
                "",
            )
        ).strip()
    ]

    filtered = {
        **result,
        "full_suite_test_case_count":
            len(all_cases),
        "target_asset_descriptors":
            targets,
        "target_asset_ids":
            target_ids,
        "targeting_mode":
            "post_run_case_filter",
        "targeting_verified":
            bool(matching_cases),
        "test_cases":
            matching_cases,
    }

    if matching_cases:
        statuses = [
            normalize_case_status(
                case.get("status")
            )
            for case in matching_cases
        ]

        if "failed" in statuses:
            status = "FAILED"
        elif "need_review" in statuses:
            status = "NEED_REVIEW"
        elif "passed" in statuses:
            status = "PASSED"
        else:
            status = "NEED_REVIEW"

        filtered["status"] = status
        filtered["testing_summary"] = (
            build_target_summary(
                matching_cases,
                targets,
                matched=True,
            )
        )
    else:
        filtered["status"] = (
            "NEED_REVIEW"
        )
        filtered["testing_summary"] = (
            build_target_summary(
                [],
                targets,
                matched=False,
            )
        )

    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run an isolated Hermes QA execution."
        )
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )
    parser.add_argument(
        "--url",
        required=True,
    )
    parser.add_argument(
        "--module-name",
        required=True,
    )
    parser.add_argument(
        "--mode",
        required=True,
    )
    parser.add_argument(
        "--output",
        required=True,
    )
    parser.add_argument(
        "--targets-file",
        default="",
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    try:
        from skills.qa_automation import (
            perform_audit_for_telegram,
        )

        result = perform_audit_for_telegram(
            args.url,
            args.module_name,
            args.mode,
        )

        targets = (
            read_target_descriptors(
                args.targets_file,
            )
        )

        result = apply_target_filter(
            result,
            targets,
        )

        write_envelope(
            output_path,
            {
                "ok": True,
                "run_id": args.run_id,
                "result": result,
            },
        )

        return 0
    except BaseException as exc:
        write_envelope(
            output_path,
            {
                "ok": False,
                "run_id": args.run_id,
                "error": str(exc),
                "exception_type":
                    type(exc).__name__,
                "traceback":
                    traceback.format_exc(),
            },
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
