"""API and Legacy runner adapters.

ApiExecutionRunner
    Executes a single HTTP request (parsed from a cURL-like command or a
    direct URL) without Playwright.  Used for ``api`` / ``curl`` test types.

LegacyCheckerAdapter
    Thin adapter wrapping ``skills.qa_automation.checker.perform_audit_for_telegram``.
    Preserves full backward compatibility with the legacy registered-run workflow.
    checker.py is NOT rewritten.

Both adapters implement :class:`~qa_dashboard.ports.execution_runner.ExecutionRunner`.
"""

from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from typing import Any, Dict

from qa_dashboard.ports.execution_runner import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionRunner,
    TestCaseResult,
)


# ---------------------------------------------------------------------------
# API Execution Runner
# ---------------------------------------------------------------------------

class ApiExecutionRunner(ExecutionRunner):
    """Executes HTTP requests for API / cURL test types.

    Deterministic PASS/FAIL is driven solely by HTTP status code and body
    assertions in *request.parameters*.  AI analysis is strictly optional
    and never affects the status.
    """

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        url = request.target_url
        method = str(request.parameters.get("method", "GET")).upper()
        headers: Dict[str, str] = dict(request.parameters.get("headers", {}))
        body_str: str | None = request.parameters.get("body")
        expected_status: int = int(request.parameters.get("expected_status", 200))
        expected_contains: list = list(request.parameters.get("expected_contains", []))
        timeout: int = int(request.parameters.get("timeout_seconds", 30))

        test_cases: list[TestCaseResult] = []
        bugs: list[str] = []

        def add_tc(tc_id: str, status: str, title: str) -> None:
            test_cases.append(TestCaseResult(id=tc_id, title=title, status=status))

        response_body = ""
        actual_status = 0

        try:
            data = body_str.encode("utf-8") if body_str else None
            req = urllib.request.Request(
                url=url,
                data=data,
                headers=headers,
                method=method,
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                actual_status = resp.status
                response_body = resp.read(500_000).decode("utf-8", errors="replace")
            add_tc("TC-001", "PASS", "Execute HTTP request")
        except urllib.error.HTTPError as exc:
            actual_status = exc.code
            try:
                response_body = exc.read(500_000).decode("utf-8", errors="replace")
            except Exception:
                response_body = ""
            add_tc("TC-001", "PASS", "Execute HTTP request (received HTTP error response)")
        except Exception as exc:
            add_tc("TC-001", "FAIL", f"Execute HTTP request: {exc}")
            bugs.append(str(exc))

        # Status code assertion
        if actual_status == expected_status:
            add_tc("TC-002", "PASS", f"Status code matches expected {expected_status}")
        else:
            add_tc("TC-002", "FAIL", f"Expected status {expected_status}, got {actual_status}")
            bugs.append(f"Expected status {expected_status}, got {actual_status}")

        # Body content assertions
        for i, expected in enumerate(expected_contains, start=3):
            tc_id = f"TC-{i:03d}"
            if str(expected).lower() in response_body.lower():
                add_tc(tc_id, "PASS", f"Response contains: {expected}")
            else:
                add_tc(tc_id, "FAIL", f"Response missing: {expected}")
                bugs.append(f"Missing expected content: {expected}")

        passed = sum(1 for tc in test_cases if tc.status == "PASS")
        failed = sum(1 for tc in test_cases if tc.status == "FAIL")
        # Deterministic status – AI does NOT determine this
        final_status = "FAILED" if failed > 0 else "PASS"

        return ExecutionResult(
            status=final_status,
            test_cases=test_cases,
            passed=passed,
            failed=failed,
            need_review=0,
            artifacts={},
            summary=f"API test: {method} {url} → {actual_status}",
            error_message="; ".join(bugs) if bugs else "",
            ai_analysis=None,  # AI enrichment is optional and injected separately
        )


# ---------------------------------------------------------------------------
# Legacy Checker Adapter
# ---------------------------------------------------------------------------

class LegacyCheckerAdapter(ExecutionRunner):
    """Adapter wrapping checker.py's perform_audit_for_telegram.

    checker.py is left unchanged.  This adapter is the sole import point so
    that the rest of the codebase never imports checker.py directly.
    """

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        # Lazy import keeps checker.py out of import-time scope
        import skills.qa_automation.checker as qa_checker  # type: ignore[import]

        feature_name = request.feature
        mode = request.mode or "smoke"
        url = request.target_url

        raw_result: Dict[str, Any] = qa_checker.perform_audit_for_telegram(
            url,
            feature_name,
            mode,
        )

        status = str(raw_result.get("status", "NEED REVIEW"))
        test_cases = [
            TestCaseResult(
                id="TC-LEGACY-001",
                title=f"Legacy registered run for {feature_name}",
                status=status,
                details=str(raw_result.get("testing_summary", "")),
            )
        ]

        artifacts = {
            k: v
            for k, v in {
                "report": raw_result.get("report_path") or "",
                "spreadsheet": raw_result.get("spreadsheet_path") or "",
                "screenshot": raw_result.get("screenshot_path") or "",
                "error_log": raw_result.get("error_log_path") or "",
                "standard_json": raw_result.get("standard_json_path") or "",
            }.items()
            if v
        }

        return ExecutionResult(
            status=status,
            test_cases=test_cases,
            passed=1 if status == "PASS" else 0,
            failed=1 if status == "FAILED" else 0,
            need_review=1 if status == "NEED REVIEW" else 0,
            artifacts=artifacts,
            summary=str(raw_result.get("testing_summary", "")),
            error_message="",
            ai_analysis=raw_result.get("ai_analysis"),
        )
