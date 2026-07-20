from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_registered_runner_fallback_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Registered Runner Fallback
# ============================================================

def _custom_smoke_get_registered_feature_by_route(route):
    route_value = str(route or "").strip().lower()

    if route_value.startswith("http://") or route_value.startswith("https://"):
        route_value = "/" + route_value.rstrip("/").split("/")[-1]

    if not route_value.startswith("/"):
        route_value = "/" + route_value

    route_map = {
        "/managementnotif": "Notification Management",
        "/notificationmessage": "Notification Messages",
        "/shipmentdetail": "Shipment Details",
        "/mobomap": "MoboMap",
        "/inspectionresult": "Inspection Result",
    }

    return route_map.get(route_value), route_value


if not globals().get("_CUSTOM_SMOKE_REGISTERED_RUNNER_FALLBACK_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_REGISTERED_RUNNER_FALLBACK = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        expected_texts = expected_texts or []
        base_url = str(url or "").rstrip("/")
        registered_feature, route_value = _custom_smoke_get_registered_feature_by_route(route)

        if registered_feature:
            runner = globals().get("perform_audit_for_telegram")

            if runner:
                try:
                    result = runner(
                        url=base_url,
                        module_name=registered_feature,
                        mode=mode,
                    )
                except TypeError:
                    result = runner(base_url, registered_feature, mode)

                if isinstance(result, dict):
                    target_url = base_url + route_value

                    result["custom_smoke"] = True
                    result["custom_smoke_strategy"] = "registered_runner_fallback"
                    result["feature_name"] = feature_name
                    result["registered_feature"] = registered_feature
                    result["route"] = route_value
                    result["target_url"] = target_url
                    result["expected_texts"] = expected_texts

                    bridge_note = (
                        "\n\nCustom Smoke Bridge:\n"
                        + "- Custom Feature: " + str(feature_name) + "\n"
                        + "- Route: " + str(route_value) + "\n"
                        + "- Target URL: " + str(target_url) + "\n"
                        + "- Registered Runner Used: " + str(registered_feature) + "\n"
                        + "- Strategy: reuse stable registered QA login and validation flow\n"
                        + "- Expected Texts: " + ", ".join([str(item) for item in expected_texts]) + "\n"
                    )

                    result["testing_summary"] = str(result.get("testing_summary", "")) + bridge_note

                    try:
                        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
                        if enrich_fn:
                            result = enrich_fn(result, base_url, feature_name, mode)
                    except Exception as exc:
                        result["standard_json_error"] = str(exc)

                    try:
                        append_history_fn = globals().get("append_qa_run_history")
                        if append_history_fn:
                            result = append_history_fn(result, base_url, feature_name, mode)
                    except Exception as exc:
                        result["history_error"] = str(exc)

                    return result

        if _CUSTOM_SMOKE_BEFORE_REGISTERED_RUNNER_FALLBACK is None:
            raise RuntimeError("Previous perform_custom_smoke_test not found")

        return _CUSTOM_SMOKE_BEFORE_REGISTERED_RUNNER_FALLBACK(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

    _CUSTOM_SMOKE_REGISTERED_RUNNER_FALLBACK_INSTALLED = True
'''

if "# Custom Smoke Registered Runner Fallback" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Custom Smoke registered runner fallback")
else:
    print("Custom Smoke registered runner fallback already exists")

print(f"Backup created: {backup_path}")
