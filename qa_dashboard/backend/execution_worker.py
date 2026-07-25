#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict

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
