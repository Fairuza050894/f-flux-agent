from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_test_planning_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

route_code = r'''

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
'''

if '@app.post("/test-plan/generate")' not in text:
    text = text.rstrip() + "\n" + route_code + "\n"
    APP_PATH.write_text(text)
    print("Inserted /test-plan/generate endpoint")
else:
    print("/test-plan/generate endpoint already exists")

print(f"Backup created: {backup_path}")
