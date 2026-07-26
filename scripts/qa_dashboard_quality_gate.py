#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "qa_dashboard" / "frontend_v3"


def run(
    command: Sequence[str],
    *,
    cwd: Path = ROOT,
) -> None:
    printable = " ".join(command)
    print()
    print("=" * 88)
    print(f"$ {printable}")
    print(f"cwd: {cwd}")
    print("=" * 88)

    completed = subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
    )

    if completed.returncode != 0:
        raise SystemExit(
            f"Quality gate failed with exit code "
            f"{completed.returncode}: {printable}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the canonical Hermes QA Dashboard "
            "MVP1 quality gates."
        )
    )
    parser.add_argument(
        "--generate-docs",
        action="store_true",
        help=(
            "Generate synchronized documentation before "
            "running the read-only documentation check."
        ),
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Run only backend and repository checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not FRONTEND.is_dir():
        raise SystemExit(
            f"Frontend directory was not found: {FRONTEND}"
        )

    if shutil.which("git") is None:
        raise SystemExit("git is required.")

    if not args.skip_frontend and shutil.which("npm") is None:
        raise SystemExit("npm is required.")

    print("Hermes QA Dashboard — MVP1 Quality Gates")
    print(f"Repository root: {ROOT}")
    print(f"Python: {sys.executable}")

    run(
        [
            sys.executable,
            "-m",
            "compileall",
            "qa_dashboard/backend",
            "tests/qa_dashboard",
        ]
    )

    run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/qa_dashboard",
            "-q",
        ]
    )

    if not args.skip_frontend:
        if args.generate_docs:
            run(
                ["npm", "run", "docs:generate"],
                cwd=FRONTEND,
            )

        run(
            ["npm", "run", "verify"],
            cwd=FRONTEND,
        )

    run(["git", "diff", "--check"])

    print()
    print("=" * 88)
    print("QA DASHBOARD QUALITY GATES PASSED")
    print("=" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
