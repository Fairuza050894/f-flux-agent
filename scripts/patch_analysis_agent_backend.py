from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(
    f"app.py.backup_before_analysis_agent_{timestamp}"
)
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text(encoding="utf-8")

route_code = r'''

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
'''

if '@app.post("/analysis/generate")' not in text:
    text = text.rstrip() + "\n" + route_code + "\n"
    APP_PATH.write_text(text, encoding="utf-8")
    print("Inserted /analysis/generate endpoint")
else:
    print("/analysis/generate endpoint already exists")

print(f"Backup created: {backup_path}")
