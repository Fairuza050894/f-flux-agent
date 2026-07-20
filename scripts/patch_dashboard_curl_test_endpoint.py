from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_curl_test_endpoint_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

route_code = r'''

# ============================================================
# API cURL Test Endpoint
# ============================================================

from typing import Optional as _CurlOptional, List as _CurlList
from pydantic import BaseModel as _CurlBaseModel


class CurlTestRequest(_CurlBaseModel):
    feature_name: str = "Custom API cURL Test"
    mode: str = "api"
    curl: str
    expected_status: int = 200
    expected_contains: _CurlOptional[_CurlList[str]] = None
    timeout_seconds: int = 30


def _qa_curl_slug(value):
    import re
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "curl_test").lower()).strip("_") or "curl_test"


def _qa_parse_curl_command(curl_command):
    import shlex

    tokens = shlex.split(curl_command or "")
    if not tokens:
        raise ValueError("cURL command is empty")

    if tokens[0].lower() == "curl":
        tokens = tokens[1:]

    method = None
    headers = {}
    body_parts = []
    url = None
    insecure = False

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ["-k", "--insecure"]:
            insecure = True
            i += 1
            continue

        if token in ["-X", "--request"]:
            if i + 1 >= len(tokens):
                raise ValueError("Missing value after " + token)
            method = tokens[i + 1].upper()
            i += 2
            continue

        if token.startswith("--request="):
            method = token.split("=", 1)[1].upper()
            i += 1
            continue

        if token.startswith("-X") and len(token) > 2:
            method = token[2:].upper()
            i += 1
            continue

        if token in ["-H", "--header"]:
            if i + 1 >= len(tokens):
                raise ValueError("Missing header value after " + token)
            header_value = tokens[i + 1]
            if ":" in header_value:
                key, value = header_value.split(":", 1)
                headers[key.strip()] = value.strip()
            i += 2
            continue

        if token.startswith("--header="):
            header_value = token.split("=", 1)[1]
            if ":" in header_value:
                key, value = header_value.split(":", 1)
                headers[key.strip()] = value.strip()
            i += 1
            continue

        if token.startswith("-H") and len(token) > 2:
            header_value = token[2:]
            if ":" in header_value:
                key, value = header_value.split(":", 1)
                headers[key.strip()] = value.strip()
            i += 1
            continue

        if token in ["-d", "--data", "--data-raw", "--data-binary", "--data-ascii"]:
            if i + 1 >= len(tokens):
                raise ValueError("Missing data value after " + token)
            body_parts.append(tokens[i + 1])
            i += 2
            continue

        if (
            token.startswith("--data=")
            or token.startswith("--data-raw=")
            or token.startswith("--data-binary=")
            or token.startswith("--data-ascii=")
        ):
            body_parts.append(token.split("=", 1)[1])
            i += 1
            continue

        if token.startswith("http://") or token.startswith("https://"):
            url = token
            i += 1
            continue

        i += 1

    if not url:
        raise ValueError("URL not found in cURL command")

    body = None
    if body_parts:
        body = "&".join(body_parts)
        if not method:
            method = "POST"

    if not method:
        method = "GET"

    return {
        "method": method,
        "url": url,
        "headers": headers,
        "body": body,
        "insecure": insecure,
    }


def _qa_execute_curl_request(parsed, timeout_seconds):
    import ssl
    import urllib.request
    import urllib.error

    method = parsed["method"]
    url = parsed["url"]
    headers = parsed.get("headers") or {}
    body = parsed.get("body")
    insecure = parsed.get("insecure")

    data = None
    if body is not None:
        data = body.encode("utf-8")

    context = None
    if insecure:
        context = ssl._create_unverified_context()

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
            raw_body = response.read(500000)
            response_text = raw_body.decode("utf-8", errors="replace")
            response_headers = dict(response.headers)
            return {
                "ok": True,
                "status_code": response.status,
                "reason": response.reason,
                "headers": response_headers,
                "body": response_text,
            }
    except urllib.error.HTTPError as exc:
        raw_body = exc.read(500000)
        response_text = raw_body.decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status_code": exc.code,
            "reason": exc.reason,
            "headers": dict(exc.headers),
            "body": response_text,
        }


@app.post("/curl-test")
def create_curl_test(request: CurlTestRequest):
    from pathlib import Path
    from datetime import datetime
    import json
    import platform
    import sys

    qa_root = Path(__file__).resolve().parents[2]

    report_dir = qa_root / "skills" / "qa_automation" / "artifacts" / "reports"
    log_dir = qa_root / "skills" / "qa_automation" / "artifacts" / "logs"
    json_dir = qa_root / "skills" / "qa_automation" / "artifacts" / "json"

    report_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")
    feature_name = request.feature_name or "Custom API cURL Test"
    mode = request.mode or "api"
    slug = _qa_curl_slug(feature_name)

    report_path = report_dir / f"qa_documentation_curl_test_{slug}_{run_id}.md"
    error_log_path = log_dir / f"qa_error_log_curl_test_{slug}_{run_id}.md"
    standard_json_path = json_dir / f"qa_result_standard_curl_test_{slug}_{run_id}.json"

    expected_contains = request.expected_contains or []

    test_cases = []
    bugs = []
    parsed = {}
    response_data = {}

    def add_tc(tc_id, status, title):
        test_cases.append({
            "id": tc_id,
            "status": status,
            "title": title,
        })

    try:
        parsed = _qa_parse_curl_command(request.curl)
        add_tc("TC-001", "PASS", "Parse cURL command")

        response_data = _qa_execute_curl_request(parsed, request.timeout_seconds)
        add_tc("TC-002", "PASS", "Execute HTTP request")

        actual_status = int(response_data.get("status_code") or 0)
        expected_status = int(request.expected_status or 200)

        if actual_status == expected_status:
            add_tc("TC-003", "PASS", f"Validate status code {expected_status}")
        else:
            add_tc("TC-003", "FAIL", f"Expected status {expected_status}, got {actual_status}")
            bugs.append(f"Expected status {expected_status}, got {actual_status}")

        response_body = response_data.get("body") or ""

        tc_index = 4
        for expected in expected_contains:
            expected_value = str(expected)
            tc_id = "TC-" + str(tc_index).zfill(3)

            if expected_value.lower() in response_body.lower():
                add_tc(tc_id, "PASS", "Expected response text found: " + expected_value)
            else:
                add_tc(tc_id, "FAIL", "Expected response text missing: " + expected_value)
                bugs.append("Expected response text missing: " + expected_value)

            tc_index += 1

    except Exception as exc:
        add_tc("TC-999", "FAIL", "API cURL runtime")
        bugs.append("API cURL runtime error: " + str(exc))

    passed = sum(1 for tc in test_cases if tc["status"] == "PASS")
    failed = sum(1 for tc in test_cases if tc["status"] == "FAIL")
    status = "FAILED" if failed > 0 or bugs else "PASS"
    icon = "❌" if status == "FAILED" else "✅"

    verified_lines = []
    failed_lines = []

    for tc in test_cases:
        line = tc["id"] + " " + tc["status"] + " - " + tc["title"]
        if tc["status"] == "PASS":
            verified_lines.append(line)
        elif tc["status"] == "FAIL":
            failed_lines.append(line)

    bug_lines = bugs if bugs else ["No bug found"]

    response_preview = str(response_data.get("body") or "")[:5000]

    testing_summary = (
        icon + " QA API cURL Test Completed\n\n"
        + "Module: " + str(feature_name) + "\n"
        + "Mode: " + str(mode) + "\n"
        + "Environment: Sandbox / External API\n"
        + "Status: " + status + "\n\n"
        + "Execution Info:\n"
        + "- Execution ID: QA-CURL-" + run_id + "\n"
        + "- Executed At: " + executed_at + "\n"
        + "- Executed By: Hermes QA Dashboard\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Method: " + str(parsed.get("method", "-")) + "\n"
        + "- URL: " + str(parsed.get("url", "-")) + "\n\n"
        + "Runtime Environment:\n"
        + "- OS: " + platform.platform() + "\n"
        + "- Machine: " + platform.machine() + "\n"
        + "- Runtime: FastAPI / urllib\n"
        + "- Python Version: " + sys.version.split()[0] + "\n\n"
        + "Summary:\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Need Review: 0\n"
        + "- Skipped: 0\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n\n"
        + "Verified:\n" + ("\n".join(verified_lines) if verified_lines else "-") + "\n\n"
        + "Failed:\n" + ("\n".join(failed_lines) if failed_lines else "-") + "\n\n"
        + "Bugs:\n" + "\n".join(bug_lines) + "\n\n"
        + "Artifacts:\n"
        + "- Report: " + str(report_path) + "\n"
        + "- Error Log: " + str(error_log_path) + "\n"
        + "- Standard JSON: " + str(standard_json_path)
    )

    documentation_report = (
        "# QA API cURL Test Report\n\n"
        + "## Execution\n\n"
        + "- Execution ID: QA-CURL-" + run_id + "\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Mode: " + str(mode) + "\n"
        + "- Status: " + status + "\n"
        + "- Method: " + str(parsed.get("method", "-")) + "\n"
        + "- URL: " + str(parsed.get("url", "-")) + "\n"
        + "- Expected Status: " + str(request.expected_status) + "\n"
        + "- Actual Status: " + str(response_data.get("status_code", "-")) + "\n\n"
        + "## Test Cases\n\n"
        + json.dumps(test_cases, indent=2, ensure_ascii=False) + "\n\n"
        + "## Bugs\n\n"
        + "\n".join(bug_lines) + "\n\n"
        + "## Response Preview\n\n"
        + response_preview
    )

    error_log_report = (
        "# QA API cURL Error Log\n\n"
        + "Status: " + status + "\n"
        + "Execution ID: QA-CURL-" + run_id + "\n"
        + "Feature: " + str(feature_name) + "\n\n"
        + "Bugs:\n"
        + "\n".join(bug_lines) + "\n\n"
        + "Response Status: " + str(response_data.get("status_code", "-")) + "\n"
    )

    standard_payload = {
        "type": "api_curl_test",
        "execution_id": "QA-CURL-" + run_id,
        "executed_at": executed_at,
        "feature_name": feature_name,
        "mode": mode,
        "status": status,
        "summary": {
            "passed": passed,
            "failed": failed,
            "need_review": 0,
            "skipped": 0,
            "bugs_found": len(bugs),
        },
        "request": {
            "method": parsed.get("method"),
            "url": parsed.get("url"),
            "headers": parsed.get("headers"),
            "body": parsed.get("body"),
        },
        "response": {
            "status_code": response_data.get("status_code"),
            "reason": response_data.get("reason"),
            "headers": response_data.get("headers"),
            "body_preview": response_preview,
        },
        "test_cases": test_cases,
        "bugs": bugs,
        "artifacts": {
            "report_path": str(report_path),
            "error_log_path": str(error_log_path),
            "standard_json_path": str(standard_json_path),
        },
    }

    report_path.write_text(documentation_report, encoding="utf-8")
    error_log_path.write_text(error_log_report, encoding="utf-8")
    standard_json_path.write_text(json.dumps(standard_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    result = {
        "ok": status == "PASS",
        "type": "api_curl_test",
        "status": status,
        "feature_name": feature_name,
        "mode": mode,
        "testing_summary": testing_summary,
        "documentation_report": documentation_report,
        "error_log_report": error_log_report,
        "standard_json_path": str(standard_json_path),
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "screenshot_path": "",
        "spreadsheet_path": "",
        "passed": passed,
        "failed": failed,
        "need_review": 0,
        "bugs_found": len(bugs),
        "request": standard_payload["request"],
        "response": standard_payload["response"],
    }

    try:
        import skills.qa_automation.checker as qa_checker
        append_history_fn = getattr(qa_checker, "append_qa_run_history", None)
        if append_history_fn:
            result = append_history_fn(result, str(parsed.get("url", "")), feature_name, mode)
    except Exception as exc:
        result["history_error"] = str(exc)

    return result
'''

if '@app.post("/curl-test")' not in text:
    text = text.rstrip() + "\n" + route_code + "\n"
    APP_PATH.write_text(text)
    print("Inserted /curl-test endpoint")
else:
    print("/curl-test endpoint already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
