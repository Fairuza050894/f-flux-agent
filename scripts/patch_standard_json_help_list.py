from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_standard_json_help_list_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Standard Result JSON + QA Help/List Integration
# ============================================================

def _qa_register_help_list_features():
    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["qa_help"] = {
        "display_name": "QA Help",
        "module_name": "QA Help",
        "menu_aliases": ["QA Help", "Help"],
        "aliases": ["help", "qa help", "bantuan", "cara pakai", "?"],
        "default_subfeatures": ["help"],
        "subfeature_aliases": {
            "help": ["help", "bantuan", "cara pakai"],
        },
    }

    FEATURE_REGISTRY["qa_list"] = {
        "display_name": "QA Feature List",
        "module_name": "QA Feature List",
        "menu_aliases": ["QA Feature List", "List"],
        "aliases": ["list", "feature list", "features", "daftar", "daftar fitur", "list fitur"],
        "default_subfeatures": ["list"],
        "subfeature_aliases": {
            "list": ["list", "features", "daftar", "daftar fitur"],
        },
    }


def should_run_qa_help(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")
    return value in {"help", "qa help", "bantuan", "cara pakai", "?"}


def should_run_qa_list(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")
    return value in {"list", "feature list", "features", "daftar", "daftar fitur", "list fitur", "qa feature list"}


def perform_qa_help_suite(url, module_name="QA Help", mode="help"):
    testing_summary = f"""✅ QA Automation Help

Module: QA Help
Mode: help
Environment: Sandbox
Status: PASS

Available Commands:

Run single feature:
- /audit_qa mode=regression fitur=driver daily meal
- /audit_qa mode=regression fitur=shipment details
- /audit_qa mode=regression fitur=mobomap
- /audit_qa mode=regression fitur=inspection result
- /audit_qa mode=regression fitur=notification messages
- /audit_qa mode=regression fitur=notification management

Run all features:
- /audit_qa mode=regression fitur=all

Utility:
- /audit_qa help
- /audit_qa list

Supported Modes:
- smoke
- regression

Safe Mode:
- Automation tidak klik SEND
- Automation tidak klik ACTION untuk create/edit/delete
- Automation tidak submit form
- Automation hanya validasi UI, table/list, search/filter, console/network, screenshot, report, dan evidence

Current Base URL:
{url}
"""

    return {
        "testing_summary": testing_summary,
        "documentation_report": "# QA Automation Help\\n\\nCommand help generated.",
        "error_log_report": "# QA Help\\n\\nNo error.",
        "status": "PASS",
    }


def perform_qa_list_suite(url, module_name="QA Feature List", mode="list"):
    features = [
        ("driver daily meal", "Driver Daily Meal / Uang Makan Driver"),
        ("shipment details", "Shipment Details"),
        ("mobomap", "MoboMap"),
        ("inspection result", "Inspection Result"),
        ("notification messages", "Notification Messages"),
        ("notification management", "Notification Management"),
        ("all", "All Features"),
    ]

    feature_lines = [f"- {alias} → {name}" for alias, name in features]

    testing_summary = f"""✅ QA Feature List

Module: QA Feature List
Mode: list
Environment: Sandbox
Status: PASS

Available QA Features:
{chr(10).join(feature_lines)}

Examples:
- /audit_qa mode=regression fitur=mobomap
- /audit_qa mode=regression fitur=notification management
- /audit_qa mode=regression fitur=all
"""

    return {
        "testing_summary": testing_summary,
        "documentation_report": "# QA Feature List\\n\\n" + "\\n".join(feature_lines),
        "error_log_report": "# QA Feature List\\n\\nNo error.",
        "status": "PASS",
    }


def _qa_std_slug(value):
    import re
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return slug or "qa_result"


def _qa_std_extract_value(text, label):
    for line in str(text or "").splitlines():
        clean = line.strip()
        if clean.startswith(label + ":") or clean.startswith("- " + label + ":"):
            try:
                return clean.split(":", 1)[1].strip()
            except Exception:
                return ""
    return ""


def _qa_std_extract_count(summary, label):
    try:
        return int(_qa_std_extract_value(summary, label) or 0)
    except Exception:
        return 0


def _qa_std_extract_warning_count(summary):
    count = _qa_std_extract_count(summary, "Non-blocking Warnings")
    if count:
        return count

    total = 0
    for line in str(summary or "").splitlines():
        if "WARNING-" in line.upper():
            total += 1
    return total


def enrich_qa_result_with_standard_json(result, url, module_name, mode):
    if not isinstance(result, dict):
        return result

    try:
        from pathlib import Path
        from datetime import datetime
        import json

        root = Path(__file__).resolve().parents[2]
        json_dir = root / "skills" / "qa_automation" / "artifacts" / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        summary = result.get("testing_summary", "") or ""

        execution_id = (
            _qa_std_extract_value(summary, "Execution ID")
            or f"QA-STD-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        executed_at = (
            _qa_std_extract_value(summary, "Executed At")
            or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        status = result.get("status") or _qa_std_extract_value(summary, "Status") or "UNKNOWN"
        feature_name = str(module_name or "").strip() or "Unknown Feature"

        if isinstance(result.get("all_feature_results"), list):
            features = []
            for item in result.get("all_feature_results") or []:
                features.append({
                    "name": item.get("feature") or item.get("name"),
                    "status": item.get("status"),
                    "passed": int(item.get("passed", 0) or 0),
                    "failed": int(item.get("failed", 0) or 0),
                    "need_review": int(item.get("need_review", 0) or 0),
                    "skipped": int(item.get("skipped", 0) or 0),
                    "bugs_found": int(item.get("bugs_found", 0) or 0),
                    "warnings": int(item.get("warnings", 0) or 0),
                    "artifacts": {
                        "screenshot": item.get("screenshot_path"),
                        "report": item.get("report_path"),
                        "spreadsheet": item.get("spreadsheet_path"),
                        "error_log": item.get("error_log_path"),
                        "selector_inventory": item.get("selector_inventory_path"),
                    },
                })
        else:
            features = [{
                "name": feature_name,
                "status": status,
                "passed": _qa_std_extract_count(summary, "Passed"),
                "failed": _qa_std_extract_count(summary, "Failed"),
                "need_review": _qa_std_extract_count(summary, "Need Review"),
                "skipped": _qa_std_extract_count(summary, "Skipped"),
                "bugs_found": _qa_std_extract_count(summary, "Bugs Found"),
                "warnings": _qa_std_extract_warning_count(summary),
                "artifacts": {
                    "screenshot": result.get("screenshot_path"),
                    "report": result.get("report_path") or result.get("documentation_path"),
                    "spreadsheet": result.get("spreadsheet_path"),
                    "error_log": result.get("error_log_path"),
                    "selector_inventory": result.get("selector_inventory_path"),
                },
            }]

        standard_result = {
            "schema_version": "1.0",
            "execution": {
                "execution_id": execution_id,
                "executed_at": executed_at,
                "executed_by": "Hermes QA Automation",
                "environment": "Sandbox",
                "base_url": url,
                "mode": mode,
                "requested_feature": feature_name,
                "overall_status": status,
            },
            "summary": {
                "features_tested": len(features),
                "passed": sum(item.get("passed", 0) for item in features),
                "failed": sum(item.get("failed", 0) for item in features),
                "need_review": sum(item.get("need_review", 0) for item in features),
                "skipped": sum(item.get("skipped", 0) for item in features),
                "bugs_found": sum(item.get("bugs_found", 0) for item in features),
                "warnings": sum(item.get("warnings", 0) for item in features),
            },
            "features": features,
            "artifacts": {
                "screenshot": result.get("screenshot_path"),
                "report": result.get("report_path") or result.get("documentation_path"),
                "spreadsheet": result.get("spreadsheet_path"),
                "error_log": result.get("error_log_path"),
                "raw_output": result.get("raw_output_path"),
            },
            "raw": {
                "testing_summary": summary,
            },
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = _qa_std_slug(feature_name)
        json_path = json_dir / f"qa_result_standard_{slug}_{timestamp}.json"

        json_path.write_text(
            json.dumps(standard_result, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        result["standard_json"] = standard_result
        result["standard_json_path"] = str(json_path)
        result["json_path"] = str(json_path)

        if result.get("testing_summary") and "Standard JSON:" not in result["testing_summary"]:
            result["testing_summary"] = result["testing_summary"].rstrip() + f"\\n\\nStandard JSON:\\n- {json_path}\\n"

        return result

    except Exception as exc:
        result["standard_json_error"] = str(exc)
        return result


_qa_register_help_list_features()


if not globals().get("_STANDARD_JSON_HELP_LIST_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_STANDARD_JSON = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_qa_help(module_name, mode):
            result = perform_qa_help_suite(url, module_name, mode)
            return enrich_qa_result_with_standard_json(result, url, module_name, mode)

        if should_run_qa_list(module_name, mode):
            result = perform_qa_list_suite(url, module_name, mode)
            return enrich_qa_result_with_standard_json(result, url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_STANDARD_JSON is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        result = _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_STANDARD_JSON(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

        return enrich_qa_result_with_standard_json(result, url, module_name, mode)

    _STANDARD_JSON_HELP_LIST_PATCH_INSTALLED = True
'''

if "# Standard Result JSON + QA Help/List Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Standard JSON + QA Help/List integration")
else:
    print("Standard JSON + QA Help/List block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
