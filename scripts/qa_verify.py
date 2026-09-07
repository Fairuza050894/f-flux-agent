#!/usr/bin/env python3
"""Single QA verification script for Hermes QA Automation Dashboard.

Runs:
1. Python syntax & bytecode compilation validation on QA modules.
2. Route uniqueness audit (ensures no duplicate method/path registrations).
3. Focused QA dashboard test suite via pytest.
"""

from collections import Counter
from pathlib import Path
import py_compile
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def step_syntax_compile() -> bool:
    print_header("Step 1: Python Syntax & Compilation Verification")
    qa_files = [
        ROOT / "qa_dashboard" / "backend" / "app.py",
        ROOT / "qa_dashboard" / "backend" / "execution_store.py",
        ROOT / "skills" / "qa_automation" / "checker.py",
        ROOT / "skills" / "qa_automation" / "telegram_router.py",
    ]

    all_passed = True
    for file_path in qa_files:
        rel_path = file_path.relative_to(ROOT)
        if not file_path.exists():
            print(f"  [MISSING] {rel_path}")
            all_passed = False
            continue
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"  [PASS] {rel_path}")
        except py_compile.PyCompileError as exc:
            print(f"  [FAIL] {rel_path}: {exc}")
            all_passed = False

    return all_passed


def step_duplicate_routes() -> bool:
    print_header("Step 2: FastAPI Route Uniqueness Audit")
    try:
        from qa_dashboard.backend.app import app
    except Exception as exc:
        print(f"  [FAIL] Unable to import QA Dashboard FastAPI app: {exc}")
        return False

    route_methods = []
    for route in app.routes:
        methods = getattr(route, "methods", None) or ["GET"]
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            route_methods.append((route.path, method))

    counts = Counter(route_methods)
    duplicates = [f"{method} {path}" for (path, method), count in counts.items() if count > 1]

    if duplicates:
        print(f"  [FAIL] Detected duplicate route registrations:")
        for dup in duplicates:
            print(f"         - {dup}")
        return False

    print(f"  [PASS] Verified {len(route_methods)} unique endpoints; 0 duplicate route registrations.")
    return True


def step_qa_tests() -> bool:
    print_header("Step 3: Focused QA Dashboard Tests")
    test_dir = ROOT / "tests" / "qa_dashboard"
    if not test_dir.exists():
        print(f"  [FAIL] Test directory missing: {test_dir}")
        return False

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(test_dir),
        "-v",
        "--tb=short",
    ]
    cmd_str = " ".join(cmd)
    print(f"  Executing: {cmd_str}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode == 0:
        print("  [PASS] QA dashboard test suite passed cleanly.")
        return True
    else:
        print(f"  [FAIL] Test suite failed with exit code {result.returncode}.")
        return False


def main() -> int:
    print("==================================================", flush=True)
    print("      HERMES QA DASHBOARD VERIFICATION SUITE      ", flush=True)
    print("==================================================", flush=True)

    ok_syntax = step_syntax_compile()
    ok_routes = step_duplicate_routes()
    ok_tests = step_qa_tests()

    results = {
        "Syntax & Compile": ok_syntax,
        "Route Uniqueness": ok_routes,
        "QA Dashboard Tests": ok_tests,
    }

    print_header("Verification Summary")
    all_ok = True
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        if not passed:
            all_ok = False
        print(f"  - {name:<22}: {status}", flush=True)

    if all_ok:
        print("\n>>> ALL QA VERIFICATION CHECKS PASSED <<<\n", flush=True)
        return 0
    else:
        print("\n>>> QA VERIFICATION CHECKS FAILED <<<\n", flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
