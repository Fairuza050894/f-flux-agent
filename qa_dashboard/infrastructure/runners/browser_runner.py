"""BrowserExecutionRunner implementing ExecutionRunner port."""

from typing import Any, Dict
from qa_dashboard.ports.execution_runner import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionRunner,
    TestCaseResult,
)


class BrowserExecutionRunner(ExecutionRunner):
    """Adapter that executes Playwright-backed browser checks via checker.py."""

    def __init__(self):
        # Lazy load checker to decouple import-time dependencies
        pass

    def run(self, request: ExecutionRequest) -> ExecutionResult:
        import skills.qa_automation.checker as qa_checker

        feature_name = request.feature
        mode = request.mode or "smoke"
        url = request.target_url

        if request.test_type == "custom":
            route = request.parameters.get("route", "")
            expected_texts = request.parameters.get("expected_texts", [])
            raw_result = qa_checker.perform_custom_smoke_test(
                url=url,
                route=route,
                feature_name=feature_name,
                expected_texts=expected_texts,
                mode=mode,
            )
        else:
            raw_result = qa_checker.perform_audit_for_telegram(
                url,
                feature_name,
                mode,
            )

        status = str(raw_result.get("status", "NEED REVIEW"))
        test_cases = [
            TestCaseResult(
                id="TC-BROWSER-001",
                title=f"Browser execution for {feature_name}",
                status=status,
                details=str(raw_result.get("testing_summary", "")),
            )
        ]

        artifacts = {
            "report": raw_result.get("report_path") or "",
            "spreadsheet": raw_result.get("spreadsheet_path") or "",
            "screenshot": raw_result.get("screenshot_path") or "",
            "error_log": raw_result.get("error_log_path") or "",
            "standard_json": raw_result.get("standard_json_path") or "",
        }

        return ExecutionResult(
            status=status,
            test_cases=test_cases,
            passed=1 if status == "PASS" else 0,
            failed=1 if status == "FAILED" else 0,
            need_review=1 if status == "NEED REVIEW" else 0,
            artifacts={k: v for k, v in artifacts.items() if v},
            summary=str(raw_result.get("testing_summary", "")),
            error_message="",
            ai_analysis=raw_result.get("ai_analysis"),
        )
