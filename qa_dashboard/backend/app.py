from pathlib import Path
from typing import Optional
import json
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.qa_automation import perform_audit_for_telegram
import skills.qa_automation.checker as qa_checker

from qa_dashboard.backend.database import (
    database_health,
    initialize_database,
)
from qa_dashboard.backend.settings import (
    get_settings,
)


SETTINGS = get_settings()
initialize_database()

DEFAULT_BASE_URL = SETTINGS.default_base_url

HISTORY_PATH = ROOT / "skills" / "qa_automation" / "artifacts" / "history" / "qa_run_history.json"

FEATURES = [
    {
        "key": "driver_daily_meal",
        "name": "Driver Daily Meal",
        "module_name": "Uang Makan Driver",
        "aliases": ["driver daily meal", "driver meal", "uang makan driver", "meal allowance"],
        "type": "registered",
    },
    {
        "key": "shipment_details",
        "name": "Shipment Details",
        "module_name": "Shipment Details",
        "aliases": ["shipment details", "shipment detail"],
        "type": "registered",
    },
    {
        "key": "mobomap",
        "name": "MoboMap",
        "module_name": "MoboMap",
        "aliases": ["mobomap", "mobo map"],
        "type": "registered",
    },
    {
        "key": "inspection_result",
        "name": "Inspection Result",
        "module_name": "Inspection Result",
        "aliases": ["inspection result"],
        "type": "registered",
    },
    {
        "key": "notification_messages",
        "name": "Notification Messages",
        "module_name": "Notification Messages",
        "aliases": ["notification messages", "notification message"],
        "type": "registered",
    },
    {
        "key": "notification_management",
        "name": "Notification Management",
        "module_name": "Notification Management",
        "aliases": ["notification management", "management notif"],
        "type": "registered",
    },
    {
        "key": "all_features",
        "name": "All Features",
        "module_name": "All Features",
        "aliases": ["all", "all features", "semua", "semua fitur"],
        "type": "registered",
    },
]


class RunRequest(BaseModel):
    feature: str
    mode: str = "regression"
    url: Optional[str] = None


class CustomSmokeRequest(BaseModel):
    url: Optional[str] = None
    route: str
    feature_name: str = "Custom Smoke Test"
    expected_texts: Optional[list[str]] = None
    mode: str = "smoke"


app = FastAPI(
    title="Hermes QA Dashboard API",
    version="0.1.0",
    description="Local dashboard backend for Hermes QA Automation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(
        SETTINGS.frontend_origins
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_text(value: str) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def resolve_feature(feature_value: str):
    requested = normalize_text(feature_value)

    for feature in FEATURES:
        candidates = [
            normalize_text(feature["key"]),
            normalize_text(feature["name"]),
            normalize_text(feature["module_name"]),
        ]

        candidates.extend(normalize_text(alias) for alias in feature.get("aliases", []))

        if requested in candidates:
            return feature

    return None


def load_json_file(path: Path, fallback):
    if not path.exists():
        return fallback

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def load_standard_json_from_result(result: dict):
    if not isinstance(result, dict):
        return None

    if isinstance(result.get("standard_json"), dict):
        return result.get("standard_json")

    json_path = result.get("standard_json_path") or result.get("json_path")
    if not json_path:
        return None

    path = Path(json_path)
    if not path.exists():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@app.get("/health")
def health():
    database = database_health()

    return {
        "status": (
            "ok"
            if database.get("status")
            == "ready"
            else "degraded"
        ),
        "service":
            "Hermes QA Dashboard API",
        "configuration":
            SETTINGS.public_summary(),
        "database": database,
    }


@app.get("/features")
def get_features():
    return {
        "features": FEATURES,
        "modes": ["smoke", "regression"],
        "phase": "Phase 1 - Registered QA",
        "next_phase": "Phase 2 - Custom Smoke Test",
    }


@app.get("/history")
def get_history(limit: int = 20):
    history = load_json_file(HISTORY_PATH, [])

    if not isinstance(history, list):
        history = []

    return {
        "history_path": str(HISTORY_PATH),
        "total": len(history),
        "items": history[:limit],
    }


@app.post("/runs")
def create_run(request: RunRequest):
    feature = resolve_feature(request.feature)

    if not feature:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unknown feature",
                "requested_feature": request.feature,
                "available_features": [item["name"] for item in FEATURES],
            },
        )

    mode = normalize_text(request.mode or "regression")
    if mode not in {"smoke", "regression"}:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported mode",
                "requested_mode": request.mode,
                "supported_modes": ["smoke", "regression"],
            },
        )

    url = request.url or DEFAULT_BASE_URL

    result = perform_audit_for_telegram(
        url,
        feature["module_name"],
        mode,
    )

    standard_json = load_standard_json_from_result(result)

    return {
        "ok": True,
        "feature": feature,
        "mode": mode,
        "url": url,
        "status": result.get("status"),
        "testing_summary": result.get("testing_summary"),
        "standard_json_path": result.get("standard_json_path"),
        "history_path": result.get("history_path"),
        "report_path": result.get("report_path") or result.get("documentation_path"),
        "spreadsheet_path": result.get("spreadsheet_path"),
        "screenshot_path": result.get("screenshot_path"),
        "error_log_path": result.get("error_log_path"),
        "raw_output_path": result.get("raw_output_path"),
        "standard_json": standard_json,
    }


@app.get("/artifacts")
def get_artifact(path: str):
    target = Path(path).resolve()

    if not target.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    try:
        target.relative_to(ROOT)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(target)


@app.post("/custom-smoke")
def create_custom_smoke(request: CustomSmokeRequest):
    mode = normalize_text(request.mode or "smoke")

    if mode not in {"smoke", "regression"}:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported mode",
                "requested_mode": request.mode,
                "supported_modes": ["smoke", "regression"],
            },
        )

    if not request.route:
        raise HTTPException(
            status_code=400,
            detail="route is required",
        )

    url = request.url or DEFAULT_BASE_URL

    if not hasattr(qa_checker, "perform_custom_smoke_test"):
        raise HTTPException(
            status_code=500,
            detail="perform_custom_smoke_test is not available in checker.py",
        )

    result = qa_checker.perform_custom_smoke_test(
        url=url,
        route=request.route,
        expected_texts=request.expected_texts or [],
        feature_name=request.feature_name or "Custom Smoke Test",
        mode=mode,
    )

    standard_json = load_standard_json_from_result(result)

    return {
        "ok": True,
        "type": "custom_smoke",
        "feature_name": request.feature_name,
        "mode": mode,
        "url": url,
        "route": request.route,
        "status": result.get("status"),
        "testing_summary": result.get("testing_summary"),
        "standard_json_path": result.get("standard_json_path"),
        "history_path": result.get("history_path"),
        "report_path": result.get("report_path") or result.get("documentation_path"),
        "screenshot_path": result.get("screenshot_path"),
        "error_log_path": result.get("error_log_path"),
        "standard_json": standard_json,
    }


FRONTEND_DIR = ROOT / "qa_dashboard" / "frontend"
DASHBOARD_HTML_PATH = FRONTEND_DIR / "dashboard.html"


@app.get("/dashboard")
def dashboard_page():
    if not DASHBOARD_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(
        DASHBOARD_HTML_PATH,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )




# ============================================================
# Sensitive Data Masking for cURL Test
# ============================================================

def _qa_mask_sensitive_headers(headers):
    masked = {}

    sensitive_keys = [
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "apikey",
        "api-key",
        "cookie",
        "set-cookie",
        "x-auth-token",
        "token",
        "access-token",
        "refresh-token",
    ]

    for key, value in (headers or {}).items():
        lowered = str(key).lower()

        if any(secret_key in lowered for secret_key in sensitive_keys):
            masked[key] = "***MASKED***"
        else:
            masked[key] = value

    return masked


def _qa_mask_sensitive_text(value):
    import re

    text_value = str(value or "")

    patterns = [
        r"(Bearer\s+)[A-Za-z0-9._\-+/=]+",
        r"(authorization['\"]?\s*:\s*['\"]?)[^,'\"\s}]+",
        r"(access_token['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(refresh_token['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(password['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(token['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
        r"(api_key['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+",
    ]

    masked = text_value

    for pattern in patterns:
        masked = re.sub(pattern, r"\1***MASKED***", masked, flags=re.I)

    return masked

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
    test_case_type: str = "positive"
    negative_case_title: _CurlOptional[str] = None
    expected_error_contains: _CurlOptional[_CurlList[str]] = None


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

    test_case_type = str(getattr(request, "test_case_type", "positive") or "positive").strip().lower()
    if test_case_type not in ["positive", "negative"]:
        test_case_type = "positive"

    negative_case_title = str(getattr(request, "negative_case_title", "") or "").strip()
    expected_error_contains = getattr(request, "expected_error_contains", None) or []

    if test_case_type == "negative":
        for item in expected_error_contains:
            if item not in expected_contains:
                expected_contains.append(item)


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

        if test_case_type == "negative":
            scenario_label = negative_case_title or "Negative API scenario"
            add_tc("TC-NEG", "PASS", "Negative case selected: " + scenario_label)
        else:
            add_tc("TC-POS", "PASS", "Positive case selected")

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

    response_preview = _qa_mask_sensitive_text(str(response_data.get("body") or "")[:5000])

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
        + "- Test Case Type: " + test_case_type.upper() + "\n"
        + ("- Negative Scenario: " + negative_case_title + "\n" if test_case_type == "negative" and negative_case_title else "")
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
        "test_case_type": test_case_type,
        "negative_case_title": negative_case_title,
        "expected_error_contains": expected_error_contains,
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
            "headers": _qa_mask_sensitive_headers(parsed.get("headers")),
            "body": _qa_mask_sensitive_text(parsed.get("body")),
        },
        "response": {
            "status_code": response_data.get("status_code"),
            "reason": response_data.get("reason"),
            "headers": _qa_mask_sensitive_headers(response_data.get("headers")),
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


# ============================================================
# Saved QA Test Case Templates
# ============================================================

from typing import Optional as _TemplateOptional, Dict as _TemplateDict, Any as _TemplateAny
from pydantic import BaseModel as _TemplateBaseModel


class QATestTemplateRequest(_TemplateBaseModel):
    id: _TemplateOptional[str] = None
    type: str
    name: str
    description: _TemplateOptional[str] = ""
    payload: _TemplateDict[str, _TemplateAny]


def _qa_templates_root():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    target = root / "skills" / "qa_automation" / "artifacts" / "templates"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _qa_templates_path():
    return _qa_templates_root() / "qa_test_templates.json"


def _qa_template_slug(value):
    import re
    from datetime import datetime

    base = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "template").lower()).strip("_")
    base = base or "template"
    return base + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")


def _qa_read_templates():
    import json

    path = _qa_templates_path()

    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("templates"), list):
            return data.get("templates")
    except Exception:
        pass

    return []


def _qa_write_templates(items):
    import json

    path = _qa_templates_path()
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


@app.get("/test-templates")
def list_test_templates(type: str = "all"):
    items = _qa_read_templates()

    type_value = str(type or "all").strip().lower()

    if type_value != "all":
        items = [item for item in items if str(item.get("type", "")).lower() == type_value]

    return {
        "ok": True,
        "total": len(items),
        "items": items,
        "path": str(_qa_templates_path()),
    }


@app.post("/test-templates")
def save_test_template(request: QATestTemplateRequest):
    from datetime import datetime

    template_type = str(request.type or "").strip().lower()
    name = str(request.name or "").strip()

    if template_type not in ["custom_smoke", "api_curl"]:
        raise HTTPException(status_code=400, detail="type must be custom_smoke or api_curl")

    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    items = _qa_read_templates()

    template_id = str(request.id or "").strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    if not template_id:
        template_id = _qa_template_slug(name)

    existing_index = None

    for index, item in enumerate(items):
        if str(item.get("id")) == template_id:
            existing_index = index
            break

    new_item = {
        "id": template_id,
        "type": template_type,
        "name": name,
        "description": request.description or "",
        "payload": request.payload or {},
        "updated_at": now,
    }

    if existing_index is not None:
        created_at = items[existing_index].get("created_at") or now
        new_item["created_at"] = created_at
        items[existing_index] = new_item
        action = "updated"
    else:
        new_item["created_at"] = now
        items.insert(0, new_item)
        action = "created"

    path = _qa_write_templates(items)

    return {
        "ok": True,
        "action": action,
        "template": new_item,
        "path": str(path),
    }


@app.delete("/test-templates/{template_id}")
def delete_test_template(template_id: str):
    items = _qa_read_templates()
    before = len(items)
    items = [item for item in items if str(item.get("id")) != str(template_id)]
    path = _qa_write_templates(items)

    return {
        "ok": True,
        "deleted": before - len(items),
        "path": str(path),
    }


# ============================================================
# Test Planning & Scenario Generator
# ============================================================

from typing import Optional as _PlanOptional, List as _PlanList
from pydantic import BaseModel as _PlanBaseModel


class TestPlanRequest(_PlanBaseModel):
    input_type: str = "requirement"
    feature_name: str
    requirement: str = ""
    target_route: _PlanOptional[str] = ""
    api_curl: _PlanOptional[str] = ""
    risk_level: str = "medium"


def _qa_plan_slug(value):
    import re
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "test_plan").lower()).strip("_") or "test_plan"


def _qa_plan_artifact_dir():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    target = root / "skills" / "qa_automation" / "artifacts" / "plans"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _qa_detect_keywords(text_value):
    text_lower = str(text_value or "").lower()

    return {
        "has_create": any(x in text_lower for x in ["create", "add", "submit", "tambah", "buat", "simpan"]),
        "has_update": any(x in text_lower for x in ["update", "edit", "ubah", "modify"]),
        "has_delete": any(x in text_lower for x in ["delete", "hapus", "remove"]),
        "has_approval": any(x in text_lower for x in ["approve", "reject", "approval", "decision", "verify"]),
        "has_upload": any(x in text_lower for x in ["upload", "photo", "video", "file", "attachment", "pod"]),
        "has_filter": any(x in text_lower for x in ["filter", "search", "sort", "pagination", "export"]),
        "has_notification": any(x in text_lower for x in ["notification", "notif", "message", "email", "whatsapp"]),
        "has_map": any(x in text_lower for x in ["map", "gps", "tracking", "location", "vehicle"]),
        "has_driver": any(x in text_lower for x in ["driver", "meal", "allowance", "uang makan"]),
        "has_api": any(x in text_lower for x in ["api", "endpoint", "curl", "request", "response"]),
    }


def _qa_generate_test_scope(feature_name, input_type, requirement, target_route, api_curl, risk_level):
    combined = " ".join([
        str(feature_name or ""),
        str(input_type or ""),
        str(requirement or ""),
        str(target_route or ""),
        str(api_curl or ""),
    ])

    flags = _qa_detect_keywords(combined)

    scope = [
        "Validate access to target feature or endpoint.",
        "Validate main positive flow.",
        "Validate negative/error handling flow.",
        "Validate required data or required UI elements.",
        "Validate generated evidence and report output.",
    ]

    if target_route:
        scope.append("Validate page route can be opened after authentication.")

    if api_curl:
        scope.append("Validate API request status code and response body.")

    if flags["has_create"]:
        scope.append("Validate create/add/submit action.")
        scope.append("Validate required field behavior for submit action.")

    if flags["has_update"]:
        scope.append("Validate edit/update action and data consistency.")

    if flags["has_delete"]:
        scope.append("Validate delete/remove action with confirmation and permission.")

    if flags["has_approval"]:
        scope.append("Validate approval/rejection/verification decision flow.")

    if flags["has_upload"]:
        scope.append("Validate upload evidence, file type, and file size handling.")

    if flags["has_filter"]:
        scope.append("Validate filter, search, sorting, pagination, and export behavior.")

    if flags["has_notification"]:
        scope.append("Validate notification/message template and delivery status.")

    if flags["has_map"]:
        scope.append("Validate map/tracking/GPS data visibility and interaction.")

    if str(risk_level or "").lower() == "high":
        scope.append("Validate role permission and audit trail because risk level is high.")
        scope.append("Validate rollback or recovery behavior for failed transaction.")

    return scope


def _qa_generate_scenarios(feature_name, requirement, target_route, api_curl, risk_level):
    combined = " ".join([
        str(feature_name or ""),
        str(requirement or ""),
        str(target_route or ""),
        str(api_curl or ""),
    ])

    flags = _qa_detect_keywords(combined)
    scenarios = []

    if target_route:
        scenarios.append({
            "id": "SCN-UI-001",
            "type": "ui_smoke",
            "case_type": "positive",
            "priority": "high",
            "title": "Open feature page successfully",
            "steps": [
                "Login to Mobospace sandbox.",
                "Open target route: " + str(target_route),
                "Verify main page content is visible.",
                "Capture screenshot evidence.",
            ],
            "expected_result": "Target feature page opens successfully and expected text is visible.",
            "recommended_runner": "Custom Smoke Test",
        })

        scenarios.append({
            "id": "SCN-UI-NEG-001",
            "type": "ui_smoke",
            "case_type": "negative",
            "priority": "medium",
            "title": "Validate unavailable or unauthorized page behavior",
            "steps": [
                "Login with current QA credential.",
                "Open target route: " + str(target_route),
                "Verify whether page is accessible or redirected.",
                "Check visible error or permission message if access is denied.",
            ],
            "expected_result": "System shows proper page, redirect, or permission handling.",
            "recommended_runner": "Custom Smoke Test",
        })

    if api_curl:
        method = "-"
        url = "-"

        try:
            parsed = _qa_parse_curl_command(api_curl)
            method = parsed.get("method") or "-"
            url = parsed.get("url") or "-"
        except Exception:
            pass

        scenarios.append({
            "id": "SCN-API-001",
            "type": "api_curl",
            "case_type": "positive",
            "priority": "high",
            "title": "Validate API positive response",
            "steps": [
                "Run cURL request from dashboard.",
                "Validate expected HTTP status code.",
                "Validate response body contains expected success indicator.",
            ],
            "expected_result": "API returns expected success status and response body.",
            "recommended_runner": "API cURL Test",
            "method": method,
            "url": url,
        })

        scenarios.append({
            "id": "SCN-API-NEG-001",
            "type": "api_curl",
            "case_type": "negative",
            "priority": "high",
            "title": "Validate API negative response",
            "steps": [
                "Modify request with invalid ID, missing field, invalid token, or invalid payload.",
                "Run cURL request from dashboard.",
                "Validate expected error status code.",
                "Validate response body contains expected error message.",
            ],
            "expected_result": "API rejects invalid request with proper error response.",
            "recommended_runner": "API cURL Test",
            "method": method,
            "url": url,
        })

    if flags["has_create"]:
        scenarios.append({
            "id": "SCN-FUNC-001",
            "type": "functional",
            "case_type": "positive",
            "priority": "high",
            "title": "Submit valid data successfully",
            "steps": [
                "Open feature page.",
                "Fill all required fields with valid data.",
                "Submit form.",
                "Verify success message or updated data.",
            ],
            "expected_result": "Data is submitted successfully and visible in result/history.",
            "recommended_runner": "Registered QA or Custom Smoke Test",
        })

        scenarios.append({
            "id": "SCN-FUNC-NEG-001",
            "type": "functional",
            "case_type": "negative",
            "priority": "high",
            "title": "Submit with missing required field",
            "steps": [
                "Open feature page.",
                "Leave one or more required fields empty.",
                "Submit form.",
                "Verify validation message.",
            ],
            "expected_result": "System blocks submit and shows clear validation message.",
            "recommended_runner": "Registered QA when feature is mature",
        })

    if flags["has_filter"]:
        scenarios.append({
            "id": "SCN-FILTER-001",
            "type": "ui_validation",
            "case_type": "positive",
            "priority": "medium",
            "title": "Validate search/filter/pagination",
            "steps": [
                "Open list/table page.",
                "Apply filter or search keyword.",
                "Verify result data updates correctly.",
                "Validate pagination if available.",
            ],
            "expected_result": "Filter/search/pagination works and does not break the page.",
            "recommended_runner": "Registered QA when feature is mature",
        })

    if flags["has_approval"]:
        scenarios.append({
            "id": "SCN-APPROVAL-001",
            "type": "workflow",
            "case_type": "positive",
            "priority": "high",
            "title": "Validate approval or rejection workflow",
            "steps": [
                "Open pending item.",
                "Perform approve or reject action.",
                "Verify status is updated.",
                "Verify result appears in history/log.",
            ],
            "expected_result": "Decision is saved and status changes correctly.",
            "recommended_runner": "Registered QA when workflow is stable",
        })

    if flags["has_notification"]:
        scenarios.append({
            "id": "SCN-NOTIF-001",
            "type": "integration",
            "case_type": "positive",
            "priority": "medium",
            "title": "Validate notification/message behavior",
            "steps": [
                "Trigger notification action.",
                "Verify message template or recipient data.",
                "Verify sent status or log.",
            ],
            "expected_result": "Notification is generated with correct content and delivery status.",
            "recommended_runner": "Custom Smoke Test or Registered QA",
        })

    if not scenarios:
        scenarios.append({
            "id": "SCN-GEN-001",
            "type": "general",
            "case_type": "positive",
            "priority": "medium",
            "title": "Validate basic feature availability",
            "steps": [
                "Open target feature or run target API.",
                "Verify expected result.",
                "Capture evidence.",
            ],
            "expected_result": "Feature/API behaves according to requirement.",
            "recommended_runner": "Custom Smoke Test or API cURL Test",
        })

    return scenarios


def _qa_generate_acceptance_criteria(feature_name, target_route, api_curl, requirement):
    criteria = [
        "Test can be executed from Hermes QA Dashboard.",
        "Result status is clearly shown as PASS, FAILED, or NEED REVIEW.",
        "Report, error log, and standard JSON are generated.",
        "Run history is updated after execution.",
    ]

    if target_route:
        criteria.extend([
            "Target route is accessible after login.",
            "Expected UI text or main component is visible.",
            "Screenshot evidence is captured.",
        ])

    if api_curl:
        criteria.extend([
            "API request returns expected HTTP status.",
            "API response body contains expected success or error indicator.",
            "Sensitive headers or tokens are masked in report output.",
        ])

    if requirement:
        criteria.append("Generated scenarios cover the main requirement and error handling.")

    return criteria


def _qa_generate_recommended_templates(feature_name, target_route, api_curl, scenarios):
    templates = []

    if target_route:
        templates.append({
            "type": "custom_smoke",
            "name": str(feature_name or "Feature") + " - UI Smoke",
            "description": "Generated UI smoke template suggestion.",
            "payload": {
                "feature_name": str(feature_name or "Generated UI Smoke"),
                "mode": "smoke",
                "url": "https://mobospace-sandbox.pancaran-group.co.id",
                "route": target_route,
                "expected_texts": [
                    str(feature_name or "").strip() or "Page Title",
                    "Search",
                    "Filter",
                ],
            },
        })

    if api_curl:
        templates.append({
            "type": "api_curl",
            "name": str(feature_name or "API") + " - API Positive",
            "description": "Generated API positive template suggestion.",
            "payload": {
                "feature_name": str(feature_name or "Generated API Positive"),
                "mode": "api",
                "curl": api_curl,
                "expected_status": 200,
                "expected_contains": [],
                "test_case_type": "positive",
                "negative_case_title": "",
                "expected_error_contains": [],
            },
        })

        templates.append({
            "type": "api_curl",
            "name": str(feature_name or "API") + " - API Negative",
            "description": "Generated API negative template suggestion.",
            "payload": {
                "feature_name": str(feature_name or "Generated API Negative"),
                "mode": "api",
                "curl": api_curl,
                "expected_status": 400,
                "expected_contains": [],
                "test_case_type": "negative",
                "negative_case_title": "Invalid request should return proper error response",
                "expected_error_contains": [
                    "error",
                    "invalid",
                ],
            },
        })

    return templates


@app.post("/test-plan/generate")
def generate_test_plan(request: TestPlanRequest):
    from datetime import datetime
    import json

    feature_name = str(request.feature_name or "").strip()
    input_type = str(request.input_type or "requirement").strip().lower()
    requirement = str(request.requirement or "").strip()
    target_route = str(request.target_route or "").strip()
    api_curl = str(request.api_curl or "").strip()
    risk_level = str(request.risk_level or "medium").strip().lower()

    if not feature_name:
        raise HTTPException(status_code=400, detail="feature_name is required")

    if risk_level not in ["low", "medium", "high"]:
        risk_level = "medium"

    test_scope = _qa_generate_test_scope(
        feature_name=feature_name,
        input_type=input_type,
        requirement=requirement,
        target_route=target_route,
        api_curl=api_curl,
        risk_level=risk_level,
    )

    scenarios = _qa_generate_scenarios(
        feature_name=feature_name,
        requirement=requirement,
        target_route=target_route,
        api_curl=api_curl,
        risk_level=risk_level,
    )

    acceptance_criteria = _qa_generate_acceptance_criteria(
        feature_name=feature_name,
        target_route=target_route,
        api_curl=api_curl,
        requirement=requirement,
    )

    recommended_templates = _qa_generate_recommended_templates(
        feature_name=feature_name,
        target_route=target_route,
        api_curl=api_curl,
        scenarios=scenarios,
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    payload = {
        "ok": True,
        "type": "test_plan",
        "plan_id": "QA-PLAN-" + run_id,
        "generated_at": generated_at,
        "input": {
            "input_type": input_type,
            "feature_name": feature_name,
            "requirement": requirement,
            "target_route": target_route,
            "api_curl": _qa_mask_sensitive_text(api_curl) if "_qa_mask_sensitive_text" in globals() else api_curl,
            "risk_level": risk_level,
        },
        "test_scope": test_scope,
        "scenarios": scenarios,
        "acceptance_criteria": acceptance_criteria,
        "recommended_templates": recommended_templates,
        "summary": {
            "scope_count": len(test_scope),
            "scenario_count": len(scenarios),
            "acceptance_criteria_count": len(acceptance_criteria),
            "recommended_template_count": len(recommended_templates),
        },
    }

    artifact_dir = _qa_plan_artifact_dir()
    slug = _qa_plan_slug(feature_name)
    artifact_path = artifact_dir / f"qa_test_plan_{slug}_{run_id}.json"

    artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["artifact_path"] = str(artifact_path)

    return payload


# ============================================================
# Analysis Agent MVP
# ============================================================

from typing import Dict as _AnalysisDict, Any as _AnalysisAny
from pydantic import BaseModel as _AnalysisBaseModel


class AnalysisAgentRequest(_AnalysisBaseModel):
    result: _AnalysisDict[str, _AnalysisAny]


def _qa_analysis_root():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    target = (
        root
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "analysis"
    )
    target.mkdir(parents=True, exist_ok=True)
    return target


def _qa_analysis_slug(value):
    import re

    slug = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        str(value or "qa_analysis").lower(),
    ).strip("_")

    return slug or "qa_analysis"


def _qa_analysis_result_text(result):
    import json

    fields = [
        result.get("testing_summary"),
        result.get("error_log_report"),
        result.get("documentation_report"),
        result.get("status"),
        result.get("feature_name"),
        result.get("current_url"),
        result.get("target_url"),
        result.get("route"),
        result.get("bugs"),
        result.get("response"),
        result.get("request"),
    ]

    try:
        return json.dumps(
            fields,
            ensure_ascii=False,
            default=str,
        ).lower()
    except Exception:
        return " ".join(str(item or "") for item in fields).lower()


def _qa_analysis_extract_evidence(result):
    evidence = []

    current_url = str(result.get("current_url") or "").strip()
    target_url = str(result.get("target_url") or "").strip()

    if current_url:
        evidence.append("Current URL: " + current_url)

    if target_url:
        evidence.append("Target URL: " + target_url)

    response = result.get("response")

    if isinstance(response, dict):
        status_code = response.get("status_code")
        if status_code is not None:
            evidence.append("HTTP status: " + str(status_code))

    source_text = "\n".join([
        str(result.get("testing_summary") or ""),
        str(result.get("error_log_report") or ""),
    ])

    markers = [
        "error",
        "failed",
        "missing",
        "wrong",
        "timeout",
        "redirect",
        "not found",
        "forbidden",
        "unauthorized",
        "expected status",
        "internal server error",
    ]

    for line in source_text.splitlines():
        clean = line.strip()

        if not clean:
            continue

        lowered = clean.lower()

        if any(marker in lowered for marker in markers):
            short_line = clean[:240]

            if short_line not in evidence:
                evidence.append(short_line)

        if len(evidence) >= 8:
            break

    if not evidence:
        evidence.append(
            "No explicit blocking evidence was extracted from the result."
        )

    return evidence


def _qa_analysis_classify(result):
    status = str(result.get("status") or "UNKNOWN").upper()
    text = _qa_analysis_result_text(result)
    current_url = str(result.get("current_url") or "").lower()

    category = "general_test_failure"
    confidence = "medium"
    severity = "medium"
    root_cause = (
        "The execution failed, but the available result does not yet "
        "identify one specific technical cause."
    )
    impact = (
        "The affected test scope cannot be confirmed as working."
    )
    recommendations = [
        "Review the failed test cases and attached evidence.",
        "Confirm test data, environment, and expected result.",
        "Run the affected test again after validation.",
    ]
    retry_decision = "Retry after reviewing test evidence."
    release_recommendation = "CONDITIONAL for the affected scope."

    if status == "PASS":
        category = "no_blocking_issue"
        confidence = "high"
        severity = "low"
        root_cause = (
            "No blocking failure was detected in this execution."
        )
        impact = (
            "The tested scope completed according to its configured "
            "assertions."
        )
        recommendations = [
            "Keep the result as deployment evidence.",
            "Continue broader regression when the change has a wider impact.",
        ]
        retry_decision = "Retry is not required."
        release_recommendation = (
            "GO for the tested scope only. "
            "This is not a full release approval."
        )

    elif status == "NEED REVIEW":
        category = "non_blocking_warning"
        confidence = "high"
        severity = "medium"
        root_cause = (
            "The test completed without a blocking failure, but one or "
            "more warnings require manual review."
        )
        impact = (
            "The feature may remain usable, but the warning could affect "
            "quality or maintainability."
        )
        recommendations = [
            "Review all NEED REVIEW test cases.",
            "Confirm whether the warning is accepted or must be fixed.",
            "Record the decision in the release checklist.",
        ]
        retry_decision = "Retry after manual review when needed."
        release_recommendation = "CONDITIONAL pending warning review."

    elif (
        "/login" in current_url
        or "username or password is wrong" in text
        or "still on login page" in text
        or "authenticated session" in text
        or "credential" in text
        or "401" in text
    ):
        category = "authentication_session"
        confidence = "high"
        severity = "high"
        root_cause = (
            "Authentication did not produce a valid application session, "
            "or the supplied credential was rejected."
        )
        impact = (
            "Protected pages or APIs cannot be validated because the test "
            "is redirected to login or rejected."
        )
        recommendations = [
            "Verify the credential keys used by the runner.",
            "Confirm that the credential is valid in the target environment.",
            "Confirm workspace/company selection after login.",
            "Verify cookies or session storage remain available before navigation.",
        ]
        retry_decision = (
            "Safe to retry after authentication or session handling is fixed."
        )
        release_recommendation = (
            "NO-GO for the affected authenticated scope."
        )

    elif (
        "403" in text
        or "forbidden" in text
        or "permission" in text
        or "access denied" in text
    ):
        category = "authorization_permission"
        confidence = "high"
        severity = "high"
        root_cause = (
            "The authenticated user does not appear to have sufficient "
            "permission for the tested action or page."
        )
        impact = (
            "The feature cannot be validated for the current role."
        )
        recommendations = [
            "Confirm the expected user role and permission matrix.",
            "Check feature, menu, API, and tenant permissions.",
            "Repeat the test using an authorized QA account.",
        ]
        retry_decision = (
            "Retry after permission or role configuration is corrected."
        )
        release_recommendation = (
            "NO-GO for the affected role and permission scope."
        )

    elif (
        "500" in text
        or "502" in text
        or "503" in text
        or "internal server error" in text
        or "bad gateway" in text
        or "service unavailable" in text
    ):
        category = "server_error"
        confidence = "high"
        severity = "high"
        root_cause = (
            "The target service returned a server-side failure."
        )
        impact = (
            "The tested transaction or page may be unavailable or unstable."
        )
        recommendations = [
            "Check backend application logs and service dependencies.",
            "Check database, gateway, and downstream service health.",
            "Capture request correlation ID when available.",
            "Repeat the test after the server issue is resolved.",
        ]
        retry_decision = "Retry after backend service recovery."
        release_recommendation = "NO-GO for the affected transaction."

    elif (
        "timeout" in text
        or "timed out" in text
        or "connection refused" in text
        or "network error" in text
        or "dns" in text
        or "ssl" in text
    ):
        category = "network_timeout"
        confidence = "high"
        severity = "high"
        root_cause = (
            "The request or browser action could not complete within the "
            "configured time or network connection."
        )
        impact = (
            "The test result is blocked and the target may be unavailable "
            "or too slow."
        )
        recommendations = [
            "Check target environment availability.",
            "Check DNS, VPN, SSL, proxy, and network connectivity.",
            "Review response time before increasing automation timeout.",
        ]
        retry_decision = (
            "Retry after confirming network and service availability."
        )
        release_recommendation = (
            "NO-GO until environment stability is confirmed."
        )

    elif (
        "404" in text
        or "page not found" in text
        or "route not found" in text
        or "endpoint not found" in text
    ):
        category = "route_or_deployment"
        confidence = "high"
        severity = "high"
        root_cause = (
            "The requested route or endpoint is unavailable in the target "
            "deployment."
        )
        impact = (
            "The new feature or endpoint cannot be verified in this environment."
        )
        recommendations = [
            "Confirm the deployed route or endpoint path.",
            "Confirm the deployment version and environment.",
            "Check reverse proxy or API gateway route configuration.",
        ]
        retry_decision = (
            "Retry after deployment or route configuration is confirmed."
        )
        release_recommendation = (
            "NO-GO for the missing feature or endpoint."
        )

    elif (
        "expected status" in text
        or "status code" in text
        or "invalid payload" in text
        or "response text missing" in text
        or "expected response" in text
    ):
        category = "api_contract_validation"
        confidence = "high"
        severity = "medium"
        root_cause = (
            "The API response did not match the configured status or body "
            "assertion."
        )
        impact = (
            "The API contract or expected test configuration may have changed."
        )
        recommendations = [
            "Compare actual response with the current API specification.",
            "Confirm expected status and expected response assertions.",
            "Review payload, headers, authentication, and test data.",
        ]
        retry_decision = (
            "Retry after validating API contract and test configuration."
        )
        release_recommendation = (
            "CONDITIONAL or NO-GO depending on API contract impact."
        )

    elif (
        "expected text missing" in text
        or "selector" in text
        or "locator" in text
        or "element not found" in text
        or "not visible" in text
    ):
        category = "ui_change_or_deployment_mismatch"
        confidence = "high"
        severity = "medium"
        root_cause = (
            "The expected UI text or element was not found. The page may "
            "have changed, failed to deploy, or loaded an unexpected state."
        )
        impact = (
            "The UI smoke assertion cannot confirm the expected feature state."
        )
        recommendations = [
            "Open the screenshot and confirm the actual page state.",
            "Confirm whether labels or components changed in the deployment.",
            "Update expected text only after confirming the requirement.",
            "Check loading, permission, empty state, and feature flag behavior.",
        ]
        retry_decision = (
            "Retry after confirming deployment state and expected UI content."
        )
        release_recommendation = (
            "CONDITIONAL for the affected UI scope."
        )

    elif (
        "duplicate" in text
        or "conflict" in text
        or "not eligible" in text
        or "dependency" in text
        or "test data" in text
    ):
        category = "test_data_dependency"
        confidence = "medium"
        severity = "medium"
        root_cause = (
            "The execution appears to depend on unavailable, invalid, or "
            "conflicting test data."
        )
        impact = (
            "The feature behavior cannot be validated using the current data."
        )
        recommendations = [
            "Prepare deterministic test data before execution.",
            "Check eligibility, duplicate, and dependency conditions.",
            "Clean up or reset data after mutation tests.",
        ]
        retry_decision = "Retry with valid and isolated test data."
        release_recommendation = (
            "CONDITIONAL until the scenario is validated with correct data."
        )

    elif (
        "not available in checker.py" in text
        or "not found in .env" in text
        or "configuration" in text
        or "template not found" in text
    ):
        category = "test_configuration"
        confidence = "high"
        severity = "medium"
        root_cause = (
            "The automation configuration, helper, template, or credential "
            "mapping is incomplete."
        )
        impact = (
            "The failure may come from the test framework rather than the product."
        )
        recommendations = [
            "Validate automation configuration and environment variables.",
            "Compile the modified Python files.",
            "Confirm template, helper, and route registration.",
        ]
        retry_decision = (
            "Retry after fixing the automation configuration."
        )
        release_recommendation = (
            "INCONCLUSIVE. Do not use this result as a product release decision."
        )

    evidence = _qa_analysis_extract_evidence(result)

    return {
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "root_cause": root_cause,
        "evidence": evidence,
        "impact": impact,
        "recommendations": recommendations,
        "retry_decision": retry_decision,
        "release_recommendation": release_recommendation,
        "scope_note": (
            "This recommendation applies only to the scope covered by this execution."
        ),
    }


def _qa_analysis_safe_existing_path(raw_path):
    from pathlib import Path

    if not raw_path:
        return None

    root = Path(__file__).resolve().parents[2].resolve()

    try:
        path = Path(str(raw_path)).expanduser().resolve()
        path.relative_to(root)
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_analysis_markdown(analysis):
    lines = [
        "",
        "## Analysis Agent",
        "",
        "- Analysis ID: " + str(analysis.get("analysis_id") or "-"),
        "- Category: " + str(analysis.get("category") or "-"),
        "- Confidence: " + str(analysis.get("confidence") or "-"),
        "- Severity: " + str(analysis.get("severity") or "-"),
        "- Release Recommendation: "
        + str(analysis.get("release_recommendation") or "-"),
        "",
        "### Possible Root Cause",
        "",
        str(analysis.get("root_cause") or "-"),
        "",
        "### Evidence",
        "",
    ]

    for item in analysis.get("evidence") or []:
        lines.append("- " + str(item))

    lines.extend([
        "",
        "### Impact",
        "",
        str(analysis.get("impact") or "-"),
        "",
        "### Recommendations",
        "",
    ])

    for item in analysis.get("recommendations") or []:
        lines.append("- " + str(item))

    lines.extend([
        "",
        "### Retry Decision",
        "",
        str(analysis.get("retry_decision") or "-"),
        "",
        "### Scope Note",
        "",
        str(analysis.get("scope_note") or "-"),
        "",
    ])

    return "\n".join(lines)


def _qa_analysis_update_standard_json(path, analysis, analysis_path):
    import json

    target = _qa_analysis_safe_existing_path(path)

    if not target:
        return False

    try:
        data = json.loads(target.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            return False

        data["analysis"] = analysis

        artifacts = data.get("artifacts")

        if not isinstance(artifacts, dict):
            artifacts = {}
            data["artifacts"] = artifacts

        artifacts["analysis_path"] = str(analysis_path)

        target.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def _qa_analysis_append_markdown(path, analysis):
    target = _qa_analysis_safe_existing_path(path)

    if not target:
        return False

    marker = (
        "<!-- analysis_id: "
        + str(analysis.get("analysis_id") or "")
        + " -->"
    )

    try:
        current = target.read_text(encoding="utf-8")

        if marker in current:
            return True

        content = (
            current.rstrip()
            + "\n\n"
            + marker
            + "\n"
            + _qa_analysis_markdown(analysis)
            + "\n"
        )

        target.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def _qa_analysis_item_matches(item, target_paths):
    if not isinstance(item, dict):
        return False

    try:
        import json
        blob = json.dumps(item, ensure_ascii=False, default=str)
    except Exception:
        blob = str(item)

    return any(path and path in blob for path in target_paths)


def _qa_analysis_update_history(result, analysis, analysis_path):
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    history_path = (
        root
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "history"
        / "qa_run_history.json"
    )

    if not history_path.exists():
        return False

    target_paths = [
        str(result.get("standard_json_path") or ""),
        str(result.get("report_path") or ""),
        str(result.get("documentation_path") or ""),
        str(result.get("error_log_path") or ""),
    ]

    target_paths = [item for item in target_paths if item]

    if not target_paths:
        return False

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    updated = False

    summary = {
        "category": analysis.get("category"),
        "severity": analysis.get("severity"),
        "confidence": analysis.get("confidence"),
        "retry_decision": analysis.get("retry_decision"),
        "release_recommendation": analysis.get(
            "release_recommendation"
        ),
        "analysis_path": str(analysis_path),
    }

    def walk(node):
        nonlocal updated

        if updated:
            return

        if isinstance(node, list):
            for item in node:
                if isinstance(item, dict) and _qa_analysis_item_matches(
                    item,
                    target_paths,
                ):
                    item["analysis_summary"] = summary
                    updated = True
                    return

                walk(item)

                if updated:
                    return

        elif isinstance(node, dict):
            if (
                any(
                    key in node
                    for key in [
                        "feature",
                        "feature_name",
                        "status",
                        "mode",
                        "execution_id",
                    ]
                )
                and _qa_analysis_item_matches(node, target_paths)
            ):
                node["analysis_summary"] = summary
                updated = True
                return

            for value in node.values():
                walk(value)

                if updated:
                    return

    walk(data)

    if updated:
        history_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return updated


@app.post("/analysis/generate")
def generate_analysis(request: AnalysisAgentRequest):
    from datetime import datetime
    import json

    result = dict(request.result or {})

    feature_name = (
        result.get("feature_name")
        or (
            result.get("feature", {}).get("name")
            if isinstance(result.get("feature"), dict)
            else ""
        )
        or "QA Execution"
    )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_id = "QA-ANALYSIS-" + run_id
    generated_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S WIB"
    )

    analysis = _qa_analysis_classify(result)
    analysis["analysis_id"] = analysis_id
    analysis["generated_at"] = generated_at
    analysis["feature_name"] = str(feature_name)
    analysis["test_status"] = str(
        result.get("status") or "UNKNOWN"
    ).upper()

    analysis_dir = _qa_analysis_root()
    slug = _qa_analysis_slug(feature_name)
    analysis_path = (
        analysis_dir
        / f"qa_analysis_{slug}_{run_id}.json"
    )

    analysis_path.write_text(
        json.dumps(analysis, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    standard_json_updated = _qa_analysis_update_standard_json(
        result.get("standard_json_path"),
        analysis,
        analysis_path,
    )

    report_updated = _qa_analysis_append_markdown(
        result.get("report_path")
        or result.get("documentation_path"),
        analysis,
    )

    error_log_updated = _qa_analysis_append_markdown(
        result.get("error_log_path"),
        analysis,
    )

    history_updated = _qa_analysis_update_history(
        result,
        analysis,
        analysis_path,
    )

    return {
        "ok": True,
        "type": "qa_analysis",
        "analysis": analysis,
        "analysis_path": str(analysis_path),
        "artifact_updates": {
            "standard_json_updated": standard_json_updated,
            "report_updated": report_updated,
            "error_log_updated": error_log_updated,
            "history_updated": history_updated,
        },
    }


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

    stored_events = (
        standard_json.get("execution_events")
        if isinstance(standard_json, dict)
        else None
    )

    if isinstance(stored_events, list) and stored_events:
        structured_events = []

        for item in stored_events:
            if not isinstance(item, dict):
                continue

            message = str(
                item.get("message")
                or item.get("event")
                or "Execution event"
            )

            stage = str(
                item.get("stage")
                or "execution"
            )

            event_name = str(
                item.get("event")
                or "event"
            )

            label = (
                stage.replace("_", " ").title()
                + " · "
                + event_name.replace("_", " ").title()
            )

            structured_events.append({
                "type": stage,
                "label": label,
                "timestamp": str(
                    item.get("timestamp") or "-"
                ),
                "description": message,
                "level": str(
                    item.get("level") or "info"
                ),
                "status": str(
                    item.get("status") or "-"
                ),
                "duration_ms": item.get(
                    "duration_ms"
                ),
                "sequence": item.get(
                    "sequence"
                ),
            })

        if structured_events:
            return structured_events

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

    telemetry_path = _qa_rd_safe_file_path(
        run.get("telemetry_path")
    )

    telemetry_data = _qa_rd_read_json(
        telemetry_path
    )

    if (
        not isinstance(
            standard_json.get("execution_events"),
            list,
        )
        and isinstance(telemetry_data, dict)
        and isinstance(
            telemetry_data.get("events"),
            list,
        )
    ):
        standard_json["execution_events"] = (
            telemetry_data.get("events")
        )

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
            "telemetry",
            "Execution Telemetry",
            run.get("telemetry_path")
            or standard_artifacts.get("telemetry"),
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
            "per_step_timestamps": bool(
                isinstance(
                    standard_json.get("execution_events"),
                    list,
                )
                and standard_json.get("execution_events")
            ),
            "structured_execution_events": bool(
                isinstance(
                    standard_json.get("execution_events"),
                    list,
                )
                and standard_json.get("execution_events")
            ),
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


# ============================================================
# Structured Execution Telemetry MVP
# ============================================================

from typing import Optional as _TelOptional
from typing import Dict as _TelDict
from typing import Any as _TelAny
from pydantic import BaseModel as _TelBaseModel
import threading as _tel_threading


_tel_lock = _tel_threading.Lock()


class TelemetryStartRequest(_TelBaseModel):
    runner_type: str
    feature_name: str = ""


class TelemetryEventRequest(_TelBaseModel):
    session_id: str
    stage: str
    event: str
    level: str = "info"
    status: str = "running"
    message: str
    duration_ms: _TelOptional[int] = None
    metadata: _TelDict[str, _TelAny] = {}


class TelemetryCompleteRequest(_TelBaseModel):
    session_id: str
    execution_id: _TelOptional[str] = None
    standard_json_path: _TelOptional[str] = None
    result_status: str = "UNKNOWN"
    summary: _TelDict[str, _TelAny] = {}


def _qa_tel_now():
    from datetime import datetime

    return datetime.now().astimezone().isoformat(
        timespec="milliseconds"
    )


def _qa_tel_epoch_ms():
    import time

    return int(time.time() * 1000)


def _qa_tel_root():
    from pathlib import Path

    target = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "telemetry"
    )

    target.mkdir(
        parents=True,
        exist_ok=True,
    )

    return target


def _qa_tel_mask_text(value):
    import re

    text = str(value or "")

    replacements = [
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
            r'(?i)("?(?:password|passwd|token|secret|'
            r'api[_-]?key|cookie)"?\s*[:=]\s*")'
            r'([^"]+)(")',
            r"\1***MASKED***\3",
        ),
        (
            r"(?i)((?:password|passwd|token|secret|"
            r"api[_-]?key|cookie)\s*[:=]\s*)"
            r"[^\s,;]+",
            r"\1***MASKED***",
        ),
    ]

    for pattern, replacement in replacements:
        text = re.sub(
            pattern,
            replacement,
            text,
        )

    return text[:1000]


def _qa_tel_safe_metadata(metadata):
    if not isinstance(metadata, dict):
        return {}

    allowed_keys = {
        "passed",
        "failed",
        "need_review",
        "skipped",
        "warnings",
        "bugs_found",
        "artifact_count",
        "status",
        "runner_type",
        "feature_name",
    }

    result = {}

    for key, value in metadata.items():
        normalized = str(key)

        if normalized not in allowed_keys:
            continue

        if isinstance(
            value,
            (str, int, float, bool),
        ) or value is None:
            result[normalized] = (
                _qa_tel_mask_text(value)
                if isinstance(value, str)
                else value
            )

    return result


def _qa_tel_session_path(session_id):
    import re

    safe_id = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        str(session_id or ""),
    ).strip("_")

    if not safe_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid telemetry session ID",
        )

    return (
        _qa_tel_root()
        / f"qa_telemetry_{safe_id}.json"
    )


def _qa_tel_read_session(session_id):
    import json

    path = _qa_tel_session_path(
        session_id
    )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Telemetry session not found: "
                + str(session_id)
            ),
        )

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to read telemetry session: "
                + str(error)
            ),
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid telemetry schema",
        )

    return path, data


def _qa_tel_write_session(path, data):
    import json

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _qa_tel_append_event(
    data,
    stage,
    event,
    level,
    status,
    message,
    duration_ms=None,
    metadata=None,
):
    events = data.get("events")

    if not isinstance(events, list):
        events = []
        data["events"] = events

    event_data = {
        "sequence": len(events) + 1,
        "timestamp": _qa_tel_now(),
        "timestamp_epoch_ms": _qa_tel_epoch_ms(),
        "stage": _qa_tel_mask_text(stage).lower(),
        "event": _qa_tel_mask_text(event).lower(),
        "level": _qa_tel_mask_text(level).lower(),
        "status": _qa_tel_mask_text(status).lower(),
        "message": _qa_tel_mask_text(message),
        "duration_ms": (
            int(duration_ms)
            if isinstance(duration_ms, int)
            else None
        ),
        "metadata": _qa_tel_safe_metadata(
            metadata or {}
        ),
    }

    events.append(event_data)

    data["updated_at"] = event_data[
        "timestamp"
    ]

    return event_data


def _qa_tel_safe_project_file(raw_path):
    from pathlib import Path

    if not raw_path:
        return None

    project_root = (
        Path(__file__).resolve()
        .parents[2]
        .resolve()
    )

    try:
        path = (
            Path(str(raw_path))
            .expanduser()
            .resolve()
        )

        path.relative_to(project_root)
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_tel_update_standard_json(
    standard_json_path,
    telemetry_data,
    telemetry_path,
):
    import json

    path = _qa_tel_safe_project_file(
        standard_json_path
    )

    if not path:
        return False

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(payload, dict):
            return False

        payload["execution_events"] = (
            telemetry_data.get("events") or []
        )

        execution = payload.get("execution")

        if not isinstance(execution, dict):
            execution = {}
            payload["execution"] = execution

        execution["telemetry_id"] = (
            telemetry_data.get("telemetry_id")
        )

        execution["duration_ms"] = (
            telemetry_data.get(
                "total_duration_ms"
            )
        )

        artifacts = payload.get("artifacts")

        if not isinstance(artifacts, dict):
            artifacts = {}
            payload["artifacts"] = artifacts

        artifacts["telemetry"] = str(
            telemetry_path
        )

        path.write_text(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return True

    except Exception:
        return False


def _qa_tel_update_history(
    execution_id,
    telemetry_data,
    telemetry_path,
):
    import json

    if not execution_id:
        return False

    history_path = (
        _qa_tel_root().parent
        / "history"
        / "qa_run_history.json"
    )

    if not history_path.exists():
        return False

    try:
        history = json.loads(
            history_path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return False

    if not isinstance(history, list):
        return False

    updated = False

    for item in history:
        if not isinstance(item, dict):
            continue

        if str(
            item.get("execution_id") or ""
        ) != str(execution_id):
            continue

        item["telemetry_path"] = str(
            telemetry_path
        )

        item["telemetry_event_count"] = len(
            telemetry_data.get("events") or []
        )

        item["duration_ms"] = (
            telemetry_data.get(
                "total_duration_ms"
            )
        )

        updated = True
        break

    if updated:
        history_path.write_text(
            json.dumps(
                history,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    return updated


@app.post("/telemetry/start")
def start_execution_telemetry(
    request: TelemetryStartRequest,
):
    import uuid

    telemetry_id = (
        "TEL-"
        + uuid.uuid4().hex[:16].upper()
    )

    created_at = _qa_tel_now()
    created_epoch_ms = _qa_tel_epoch_ms()

    data = {
        "schema_version": "1.0",
        "telemetry_id": telemetry_id,
        "execution_id": None,
        "runner_type": _qa_tel_mask_text(
            request.runner_type
        ),
        "feature_name": _qa_tel_mask_text(
            request.feature_name
        ),
        "created_at": created_at,
        "created_at_epoch_ms": created_epoch_ms,
        "updated_at": created_at,
        "completed_at": None,
        "total_duration_ms": None,
        "result_status": "RUNNING",
        "events": [],
    }

    _qa_tel_append_event(
        data=data,
        stage="execution",
        event="session_started",
        level="info",
        status="running",
        message=(
            "Execution telemetry session started."
        ),
        metadata={
            "runner_type": request.runner_type,
            "feature_name": request.feature_name,
        },
    )

    path = _qa_tel_session_path(
        telemetry_id
    )

    with _tel_lock:
        _qa_tel_write_session(
            path,
            data,
        )

    return {
        "ok": True,
        "telemetry_id": telemetry_id,
        "telemetry_path": str(path),
        "created_at": created_at,
    }


@app.post("/telemetry/event")
def record_execution_telemetry(
    request: TelemetryEventRequest,
):
    with _tel_lock:
        path, data = _qa_tel_read_session(
            request.session_id
        )

        event_data = _qa_tel_append_event(
            data=data,
            stage=request.stage,
            event=request.event,
            level=request.level,
            status=request.status,
            message=request.message,
            duration_ms=request.duration_ms,
            metadata=request.metadata,
        )

        _qa_tel_write_session(
            path,
            data,
        )

    return {
        "ok": True,
        "telemetry_id": request.session_id,
        "event": event_data,
        "event_count": len(
            data.get("events") or []
        ),
    }


@app.post("/telemetry/complete")
def complete_execution_telemetry(
    request: TelemetryCompleteRequest,
):
    with _tel_lock:
        path, data = _qa_tel_read_session(
            request.session_id
        )

        completed_at = _qa_tel_now()
        completed_epoch_ms = (
            _qa_tel_epoch_ms()
        )

        created_epoch_ms = int(
            data.get(
                "created_at_epoch_ms"
            )
            or completed_epoch_ms
        )

        total_duration_ms = max(
            0,
            completed_epoch_ms
            - created_epoch_ms,
        )

        result_status = str(
            request.result_status
            or "UNKNOWN"
        ).upper()

        completion_level = (
            "error"
            if result_status == "FAILED"
            else "warning"
            if result_status == "NEED REVIEW"
            else "info"
        )

        _qa_tel_append_event(
            data=data,
            stage="execution",
            event="session_completed",
            level=completion_level,
            status="completed",
            message=(
                "Execution telemetry session "
                f"completed with status {result_status}."
            ),
            duration_ms=total_duration_ms,
            metadata=request.summary,
        )

        data["execution_id"] = (
            request.execution_id
        )

        data["completed_at"] = (
            completed_at
        )

        data["total_duration_ms"] = (
            total_duration_ms
        )

        data["result_status"] = (
            result_status
        )

        _qa_tel_write_session(
            path,
            data,
        )

        standard_json_updated = (
            _qa_tel_update_standard_json(
                request.standard_json_path,
                data,
                path,
            )
        )

        history_updated = (
            _qa_tel_update_history(
                request.execution_id,
                data,
                path,
            )
        )

    return {
        "ok": True,
        "telemetry_id": request.session_id,
        "execution_id": request.execution_id,
        "telemetry_path": str(path),
        "event_count": len(
            data.get("events") or []
        ),
        "total_duration_ms": (
            total_duration_ms
        ),
        "artifact_updates": {
            "standard_json_updated": (
                standard_json_updated
            ),
            "history_updated": (
                history_updated
            ),
        },
    }


@app.get("/telemetry/{session_id}")
def get_execution_telemetry(
    session_id: str,
):
    path, data = _qa_tel_read_session(
        session_id
    )

    return {
        "ok": True,
        "telemetry_path": str(path),
        "telemetry": data,
    }


# ============================================================
# QA Project Registry API
# ============================================================

def _qa_project_root():
    from pathlib import Path

    return (
        Path(__file__).resolve()
        .parents[2]
        / "skills"
        / "qa_automation"
        / "projects"
    )


def _qa_project_read_json(
    path,
    default=None,
):
    import json

    if default is None:
        default = {}

    if not path.exists() or not path.is_file():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


def _qa_project_safe_id(project_id):
    import re

    value = str(
        project_id or ""
    ).strip().lower()

    if not re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{0,63}",
        value,
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid project ID",
        )

    return value


def _qa_project_resolve_file(
    base_path,
    relative_path,
):
    from pathlib import Path

    if not relative_path:
        return None

    root = _qa_project_root().resolve()

    try:
        path = (
            Path(base_path)
            / str(relative_path)
        ).resolve()

        path.relative_to(root)
    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_project_environment_name(
    project_dir,
    project_config,
):
    files = project_config.get("files")

    if not isinstance(files, dict):
        files = {}

    environment_path = (
        _qa_project_resolve_file(
            project_dir,
            files.get("environments"),
        )
    )

    environment_data = (
        _qa_project_read_json(
            environment_path,
            {},
        )
        if environment_path
        else {}
    )

    environments = environment_data.get(
        "environments"
    )

    if not isinstance(environments, list):
        environments = []

    default_environment = str(
        project_config.get(
            "default_environment"
        )
        or ""
    )

    for environment in environments:
        if not isinstance(
            environment,
            dict,
        ):
            continue

        if str(
            environment.get(
                "environment_id"
            )
            or ""
        ) == default_environment:
            return str(
                environment.get("name")
                or default_environment
                or "Custom"
            )

    return (
        default_environment.title()
        if default_environment
        else "Custom"
    )


def _qa_project_count_items(
    project_dir,
    project_config,
    file_key,
    collection_key,
):
    files = project_config.get("files")

    if not isinstance(files, dict):
        files = {}

    path = _qa_project_resolve_file(
        project_dir,
        files.get(file_key),
    )

    if not path:
        return 0

    data = _qa_project_read_json(
        path,
        {},
    )

    items = data.get(collection_key)

    return (
        len(items)
        if isinstance(items, list)
        else 0
    )


def _qa_project_registry_entries():
    root = _qa_project_root()

    registry_path = (
        root
        / "project_registry.json"
    )

    registry = _qa_project_read_json(
        registry_path,
        {
            "projects": [],
        },
    )

    entries = registry.get("projects")

    if not isinstance(entries, list):
        return []

    return [
        item
        for item in entries
        if isinstance(item, dict)
    ]


def _qa_project_load_entry(entry):
    root = _qa_project_root()

    config_path = _qa_project_resolve_file(
        root,
        entry.get("config_path"),
    )

    if not config_path:
        return None

    config = _qa_project_read_json(
        config_path,
        {},
    )

    if not isinstance(config, dict):
        return None

    project_dir = config_path.parent

    return {
        "project_id": str(
            config.get("project_id")
            or entry.get("project_id")
            or ""
        ),
        "name": str(
            config.get("name")
            or entry.get("name")
            or ""
        ),
        "description": str(
            config.get("description")
            or entry.get("description")
            or ""
        ),
        "status": str(
            config.get("status")
            or entry.get("status")
            or "unknown"
        ),
        "default_environment": (
            config.get(
                "default_environment"
            )
        ),
        "default_environment_name": (
            _qa_project_environment_name(
                project_dir,
                config,
            )
        ),
        "supported_test_types": (
            config.get(
                "supported_test_types"
            )
            if isinstance(
                config.get(
                    "supported_test_types"
                ),
                list,
            )
            else []
        ),
        "runner_adapter": config.get(
            "runner_adapter"
        ),
        "feature_count": (
            _qa_project_count_items(
                project_dir,
                config,
                "features",
                "features",
            )
        ),
        "regression_suite_count": (
            _qa_project_count_items(
                project_dir,
                config,
                "regression_suites",
                "regression_suites",
            )
        ),
    }


@app.get("/projects")
def list_qa_projects():
    projects = []

    for entry in (
        _qa_project_registry_entries()
    ):
        project = _qa_project_load_entry(
            entry
        )

        if project:
            projects.append(project)

    return {
        "ok": True,
        "count": len(projects),
        "projects": projects,
    }


@app.get("/projects/{project_id}")
def get_qa_project(project_id: str):
    safe_project_id = (
        _qa_project_safe_id(
            project_id
        )
    )

    matched_entry = None

    for entry in (
        _qa_project_registry_entries()
    ):
        if str(
            entry.get("project_id") or ""
        ).lower() == safe_project_id:
            matched_entry = entry
            break

    if not matched_entry:
        raise HTTPException(
            status_code=404,
            detail=(
                "Project not found: "
                + safe_project_id
            ),
        )

    root = _qa_project_root()

    config_path = _qa_project_resolve_file(
        root,
        matched_entry.get(
            "config_path"
        ),
    )

    if not config_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "Project configuration "
                "was not found"
            ),
        )

    config = _qa_project_read_json(
        config_path,
        {},
    )

    project_dir = config_path.parent
    files = config.get("files")

    if not isinstance(files, dict):
        files = {}

    detail = {
        "project": _qa_project_load_entry(
            matched_entry
        ),
        "environments": [],
        "features": [],
        "regression_suites": [],
        "api_collections": [],
        "e2e_flows": [],
    }

    file_mapping = {
        "environments": "environments",
        "features": "features",
        "regression_suites": (
            "regression_suites"
        ),
        "api_collections": (
            "api_collections"
        ),
        "e2e_flows": "e2e_flows",
    }

    for file_key, collection_key in (
        file_mapping.items()
    ):
        path = _qa_project_resolve_file(
            project_dir,
            files.get(file_key),
        )

        if not path:
            continue

        payload = _qa_project_read_json(
            path,
            {},
        )

        collection = payload.get(
            collection_key
        )

        if isinstance(collection, list):
            detail[collection_key] = (
                collection
            )

    return {
        "ok": True,
        **detail,
    }


# ============================================================
# Project Context Attachment MVP
# ============================================================

from pydantic import BaseModel as _PCBaseModel
from typing import Optional as _PCOptional
from typing import Dict as _PCDict
from typing import Any as _PCAny


class ProjectContextAttachRequest(_PCBaseModel):
    project_id: str
    execution_id: _PCOptional[str] = None
    standard_json_path: _PCOptional[str] = None
    telemetry_id: _PCOptional[str] = None
    artifact_paths: _PCDict[str, _PCAny] = {}


def _qa_pc_project_root():
    from pathlib import Path

    return (
        Path(__file__).resolve()
        .parents[2]
        .resolve()
    )


def _qa_pc_artifact_root():
    path = (
        _qa_pc_project_root()
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "project_metadata"
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def _qa_pc_now():
    from datetime import datetime

    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def _qa_pc_read_json(path, default=None):
    import json

    if default is None:
        default = {}

    if not path or not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return default


def _qa_pc_write_json(path, payload):
    import json

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _qa_pc_safe_file(raw_path):
    from pathlib import Path

    if not raw_path:
        return None

    root = _qa_pc_project_root()

    try:
        path = (
            Path(str(raw_path))
            .expanduser()
        )

        if not path.is_absolute():
            path = root / path

        path = path.resolve()
        path.relative_to(root)

    except Exception:
        return None

    if not path.exists() or not path.is_file():
        return None

    return path


def _qa_pc_safe_execution_id(value):
    import re

    text = str(
        value or ""
    ).strip()

    if not text:
        return None

    if not re.fullmatch(
        r"[A-Za-z0-9_-]{3,100}",
        text,
    ):
        return None

    return text


def _qa_pc_resolve_project(project_id):
    safe_project_id = _qa_project_safe_id(
        project_id
    )

    for entry in _qa_project_registry_entries():
        if str(
            entry.get("project_id") or ""
        ).lower() != safe_project_id:
            continue

        project = _qa_project_load_entry(
            entry
        )

        if project:
            return project

    raise HTTPException(
        status_code=404,
        detail=(
            "Project not found: "
            + safe_project_id
        ),
    )


def _qa_pc_build_context(project):
    environment_id = str(
        project.get(
            "default_environment"
        )
        or "custom"
    )

    environment_name = str(
        project.get(
            "default_environment_name"
        )
        or environment_id.title()
    )

    return {
        "project_id": str(
            project.get("project_id")
            or ""
        ),
        "project_name": str(
            project.get("name")
            or ""
        ),
        "environment_id": (
            environment_id
        ),
        "environment_name": (
            environment_name
        ),
        "project_status": str(
            project.get("status")
            or "unknown"
        ),
        "attached_at": _qa_pc_now(),
    }


def _qa_pc_allowed_artifacts(
    artifact_paths,
):
    allowed_keys = {
        "standard_json",
        "report",
        "screenshot",
        "error_log",
        "spreadsheet",
        "raw_output",
        "analysis",
        "telemetry",
    }

    result = {}

    if not isinstance(
        artifact_paths,
        dict,
    ):
        return result

    for key, raw_path in (
        artifact_paths.items()
    ):
        normalized_key = str(
            key
        ).strip().lower()

        if normalized_key not in allowed_keys:
            continue

        path = _qa_pc_safe_file(
            raw_path
        )

        if path:
            result[normalized_key] = (
                str(path)
            )

    return result


def _qa_pc_extract_standard_artifacts(
    standard_json,
):
    result = {}

    if not isinstance(
        standard_json,
        dict,
    ):
        return result

    artifacts = standard_json.get(
        "artifacts"
    )

    if not isinstance(
        artifacts,
        dict,
    ):
        return result

    aliases = {
        "standard_json": (
            "standard_json"
        ),
        "report": "report",
        "screenshot": "screenshot",
        "error_log": "error_log",
        "spreadsheet": "spreadsheet",
        "raw_output": "raw_output",
        "analysis_path": "analysis",
        "analysis": "analysis",
        "telemetry": "telemetry",
    }

    for source_key, target_key in (
        aliases.items()
    ):
        path = _qa_pc_safe_file(
            artifacts.get(source_key)
        )

        if path:
            result[target_key] = str(
                path
            )

    return result


def _qa_pc_update_standard_json(
    path,
    context,
    metadata_path,
):
    if not path:
        return False, {}

    payload = _qa_pc_read_json(
        path,
        {},
    )

    if not isinstance(payload, dict):
        return False, {}

    execution = payload.get(
        "execution"
    )

    if not isinstance(execution, dict):
        execution = {}
        payload["execution"] = execution

    execution.update({
        "project_id": (
            context["project_id"]
        ),
        "project_name": (
            context["project_name"]
        ),
        "environment_id": (
            context["environment_id"]
        ),
        "environment_name": (
            context["environment_name"]
        ),
    })

    payload["project_context"] = (
        context
    )

    artifacts = payload.get(
        "artifacts"
    )

    if not isinstance(artifacts, dict):
        artifacts = {}
        payload["artifacts"] = artifacts

    artifacts["project_metadata"] = str(
        metadata_path
    )

    _qa_pc_write_json(
        path,
        payload,
    )

    return True, payload


def _qa_pc_update_context_json(
    path,
    context,
    metadata_path,
):
    if not path:
        return False

    payload = _qa_pc_read_json(
        path,
        {},
    )

    if not isinstance(payload, dict):
        return False

    payload["project_context"] = (
        context
    )

    artifacts = payload.get(
        "artifacts"
    )

    if isinstance(artifacts, dict):
        artifacts[
            "project_metadata"
        ] = str(metadata_path)

    _qa_pc_write_json(
        path,
        payload,
    )

    return True


def _qa_pc_history_path():
    return (
        _qa_pc_project_root()
        / "skills"
        / "qa_automation"
        / "artifacts"
        / "history"
        / "qa_run_history.json"
    )


def _qa_pc_update_history(
    execution_id,
    context,
    metadata_path,
):
    history_path = (
        _qa_pc_history_path()
    )

    history = _qa_pc_read_json(
        history_path,
        [],
    )

    if not isinstance(history, list):
        return False, {}

    matched = None

    for item in history:
        if not isinstance(item, dict):
            continue

        if str(
            item.get("execution_id")
            or ""
        ) != str(execution_id):
            continue

        item.update({
            "project_id": (
                context["project_id"]
            ),
            "project_name": (
                context["project_name"]
            ),
            "environment_id": (
                context["environment_id"]
            ),
            "environment_name": (
                context["environment_name"]
            ),
            "project_metadata_path": (
                str(metadata_path)
            ),
        })

        matched = item
        break

    if not matched:
        return False, {}

    _qa_pc_write_json(
        history_path,
        history,
    )

    return True, matched


def _qa_pc_telemetry_path(
    telemetry_id,
    artifact_paths,
):
    direct_path = _qa_pc_safe_file(
        artifact_paths.get(
            "telemetry"
        )
    )

    if direct_path:
        return direct_path

    if not telemetry_id:
        return None

    try:
        path = _qa_tel_session_path(
            telemetry_id
        )

        return (
            path
            if path.exists()
            else None
        )
    except Exception:
        return None


@app.post("/project-context/attach")
def attach_project_context(
    request: ProjectContextAttachRequest,
):
    project = _qa_pc_resolve_project(
        request.project_id
    )

    context = _qa_pc_build_context(
        project
    )

    execution_id = (
        _qa_pc_safe_execution_id(
            request.execution_id
        )
    )

    if not execution_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "A valid execution_id "
                "is required"
            ),
        )

    artifact_paths = (
        _qa_pc_allowed_artifacts(
            request.artifact_paths
        )
    )

    standard_json_path = (
        _qa_pc_safe_file(
            request.standard_json_path
        )
        or _qa_pc_safe_file(
            artifact_paths.get(
                "standard_json"
            )
        )
    )

    standard_payload = (
        _qa_pc_read_json(
            standard_json_path,
            {},
        )
        if standard_json_path
        else {}
    )

    standard_artifacts = (
        _qa_pc_extract_standard_artifacts(
            standard_payload
        )
    )

    artifact_paths.update(
        standard_artifacts
    )

    if standard_json_path:
        artifact_paths[
            "standard_json"
        ] = str(standard_json_path)

    telemetry_path = (
        _qa_pc_telemetry_path(
            request.telemetry_id,
            artifact_paths,
        )
    )

    if telemetry_path:
        artifact_paths[
            "telemetry"
        ] = str(telemetry_path)

    metadata_path = (
        _qa_pc_artifact_root()
        / (
            "project_context_"
            + execution_id
            + ".json"
        )
    )

    metadata_payload = {
        "schema_version": "1.0",
        "execution_id": execution_id,
        "project_context": context,
        "artifacts": artifact_paths,
        "security": {
            "credential_values_stored": (
                False
            ),
            "request_payload_stored": (
                False
            ),
        },
    }

    _qa_pc_write_json(
        metadata_path,
        metadata_payload,
    )

    standard_updated = False

    if standard_json_path:
        (
            standard_updated,
            standard_payload,
        ) = _qa_pc_update_standard_json(
            standard_json_path,
            context,
            metadata_path,
        )

    analysis_path = _qa_pc_safe_file(
        artifact_paths.get(
            "analysis"
        )
    )

    analysis_updated = (
        _qa_pc_update_context_json(
            analysis_path,
            context,
            metadata_path,
        )
        if analysis_path
        else False
    )

    telemetry_updated = (
        _qa_pc_update_context_json(
            telemetry_path,
            context,
            metadata_path,
        )
        if telemetry_path
        else False
    )

    (
        history_updated,
        history_item,
    ) = _qa_pc_update_history(
        execution_id,
        context,
        metadata_path,
    )

    return {
        "ok": True,
        "execution_id": execution_id,
        "project_context": context,
        "project_metadata_path": (
            str(metadata_path)
        ),
        "updates": {
            "history": (
                history_updated
            ),
            "standard_json": (
                standard_updated
            ),
            "telemetry": (
                telemetry_updated
            ),
            "analysis": (
                analysis_updated
            ),
        },
        "history_item": (
            history_item
            if history_updated
            else None
        ),
    }

# QA UI EXECUTION STORE V2.2.1 ROUTER
from qa_dashboard.backend.execution_store import (
    router as execution_store_router,
)

app.include_router(execution_store_router)

# QA REPORTING AND DELIVERY ROUTER
from qa_dashboard.backend.report_delivery import (
    router as report_delivery_router,
)

app.include_router(report_delivery_router)

# QA WORKSPACE DATABASE PERSISTENCE ROUTER
from qa_dashboard.backend.workspace_api import (
    router as workspace_router,
)

app.include_router(workspace_router)
