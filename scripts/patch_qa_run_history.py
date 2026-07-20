from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_qa_history_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# QA Run History Integration
# ============================================================

def _qa_register_history_feature():
    """
    Register QA History agar bisa dipanggil dari:
    /audit_qa history
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["qa_history"] = {
        "display_name": "QA History",
        "module_name": "QA History",
        "menu_aliases": ["QA History", "History"],
        "aliases": [
            "history",
            "qa history",
            "run history",
            "riwayat",
            "riwayat qa",
            "histori",
        ],
        "default_subfeatures": ["history"],
        "subfeature_aliases": {
            "history": ["history", "run history", "riwayat", "histori"],
        },
    }


def should_run_qa_history(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    return value in {
        "history",
        "qa history",
        "run history",
        "riwayat",
        "riwayat qa",
        "histori",
    }


def _qa_history_root():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    history_dir = root / "skills" / "qa_automation" / "artifacts" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def _qa_history_file():
    return _qa_history_root() / "qa_run_history.json"


def _qa_history_load():
    import json

    path = _qa_history_file()

    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        pass

    return []


def _qa_history_save(items):
    import json

    path = _qa_history_file()
    path.write_text(
        json.dumps(items, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    return str(path)


def _qa_history_extract_value(text, label):
    for line in str(text or "").splitlines():
        clean = line.strip()

        if clean.startswith(label + ":") or clean.startswith("- " + label + ":"):
            try:
                return clean.split(":", 1)[1].strip()
            except Exception:
                return ""

    return ""


def _qa_history_extract_count(text, label):
    try:
        return int(_qa_history_extract_value(text, label) or 0)
    except Exception:
        return 0


def _qa_history_load_standard_json(result):
    if not isinstance(result, dict):
        return None

    if isinstance(result.get("standard_json"), dict):
        return result.get("standard_json")

    path_value = result.get("standard_json_path") or result.get("json_path")

    if not path_value:
        return None

    try:
        from pathlib import Path
        import json

        path = Path(path_value)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass

    return None


def _qa_history_build_item(result, url, module_name, mode):
    from datetime import datetime

    summary_text = ""
    if isinstance(result, dict):
        summary_text = result.get("testing_summary", "") or ""

    standard = _qa_history_load_standard_json(result)

    if standard:
        execution = standard.get("execution", {}) or {}
        summary = standard.get("summary", {}) or {}
        artifacts = standard.get("artifacts", {}) or {}

        features = standard.get("features", []) or []
        feature_results = []
        for feature in features:
            feature_results.append({
                "name": feature.get("name"),
                "status": feature.get("status"),
                "passed": feature.get("passed", 0),
                "failed": feature.get("failed", 0),
                "need_review": feature.get("need_review", 0),
                "bugs_found": feature.get("bugs_found", 0),
            })

        item = {
            "execution_id": execution.get("execution_id") or f"QA-HIST-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executed_at": execution.get("executed_at"),
            "feature": execution.get("requested_feature") or module_name,
            "mode": execution.get("mode") or mode,
            "environment": execution.get("environment") or "Sandbox",
            "base_url": execution.get("base_url") or url,
            "status": execution.get("overall_status") or "UNKNOWN",
            "passed": int(summary.get("passed", 0) or 0),
            "failed": int(summary.get("failed", 0) or 0),
            "need_review": int(summary.get("need_review", 0) or 0),
            "skipped": int(summary.get("skipped", 0) or 0),
            "bugs_found": int(summary.get("bugs_found", 0) or 0),
            "warnings": int(summary.get("warnings", 0) or 0),
            "standard_json_path": result.get("standard_json_path") or result.get("json_path"),
            "report_path": artifacts.get("report"),
            "spreadsheet_path": artifacts.get("spreadsheet"),
            "screenshot_path": artifacts.get("screenshot"),
            "error_log_path": artifacts.get("error_log"),
            "raw_output_path": artifacts.get("raw_output"),
            "feature_results": feature_results,
        }

        return item

    status = "UNKNOWN"
    if isinstance(result, dict):
        status = result.get("status") or _qa_history_extract_value(summary_text, "Status") or "UNKNOWN"

    return {
        "execution_id": _qa_history_extract_value(summary_text, "Execution ID") or f"QA-HIST-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "executed_at": _qa_history_extract_value(summary_text, "Executed At"),
        "feature": module_name,
        "mode": mode,
        "environment": "Sandbox",
        "base_url": url,
        "status": status,
        "passed": _qa_history_extract_count(summary_text, "Passed"),
        "failed": _qa_history_extract_count(summary_text, "Failed"),
        "need_review": _qa_history_extract_count(summary_text, "Need Review"),
        "skipped": _qa_history_extract_count(summary_text, "Skipped"),
        "bugs_found": _qa_history_extract_count(summary_text, "Bugs Found"),
        "warnings": _qa_history_extract_count(summary_text, "Non-blocking Warnings"),
        "standard_json_path": result.get("standard_json_path") if isinstance(result, dict) else None,
        "report_path": result.get("report_path") if isinstance(result, dict) else None,
        "spreadsheet_path": result.get("spreadsheet_path") if isinstance(result, dict) else None,
        "screenshot_path": result.get("screenshot_path") if isinstance(result, dict) else None,
        "error_log_path": result.get("error_log_path") if isinstance(result, dict) else None,
        "raw_output_path": result.get("raw_output_path") if isinstance(result, dict) else None,
        "feature_results": [],
    }


def append_qa_run_history(result, url, module_name, mode):
    """
    Append hasil QA ke artifacts/history/qa_run_history.json.
    """

    import os

    if os.getenv("QA_HISTORY_DISABLE") == "1":
        return result

    utility_checkers = [
        globals().get("should_run_qa_help"),
        globals().get("should_run_qa_list"),
        globals().get("should_run_qa_history"),
    ]

    for checker_fn in utility_checkers:
        try:
            if checker_fn and checker_fn(module_name, mode):
                return result
        except Exception:
            pass

    try:
        item = _qa_history_build_item(result, url, module_name, mode)
        history = _qa_history_load()

        item_key = (
            str(item.get("execution_id")),
            str(item.get("feature")),
            str(item.get("standard_json_path")),
        )

        filtered_history = []
        for old_item in history:
            old_key = (
                str(old_item.get("execution_id")),
                str(old_item.get("feature")),
                str(old_item.get("standard_json_path")),
            )
            if old_key != item_key:
                filtered_history.append(old_item)

        filtered_history.insert(0, item)
        filtered_history = filtered_history[:300]

        history_path = _qa_history_save(filtered_history)

        if isinstance(result, dict):
            result["history_path"] = history_path

        return result

    except Exception as exc:
        if isinstance(result, dict):
            result["history_error"] = str(exc)
        return result


def perform_qa_history_suite(url, module_name="QA History", mode="history"):
    """
    Tampilkan recent QA run history.
    """

    history = _qa_history_load()
    recent_items = history[:10]
    history_path = str(_qa_history_file())

    if not recent_items:
        testing_summary = f"""✅ QA Run History

Module: QA History
Mode: history
Environment: Sandbox
Status: PASS

Recent QA Runs:
- No QA run history found yet.

History File:
{history_path}
"""

        return {
            "testing_summary": testing_summary,
            "documentation_report": "# QA Run History\n\nNo QA run history found yet.",
            "error_log_report": "# QA Run History\n\nNo error.",
            "status": "PASS",
            "history_path": history_path,
        }

    lines = []
    for index, item in enumerate(recent_items, start=1):
        feature = item.get("feature") or "-"
        status = item.get("status") or "-"
        mode_value = item.get("mode") or "-"
        created_at = item.get("created_at") or item.get("executed_at") or "-"
        passed = item.get("passed", 0)
        failed = item.get("failed", 0)
        need_review = item.get("need_review", 0)
        bugs = item.get("bugs_found", 0)

        lines.append(
            f"{index}. {feature} - {status} - {mode_value} - {created_at} "
            f"(PASS={passed}, FAIL={failed}, NEED_REVIEW={need_review}, BUGS={bugs})"
        )

    testing_summary = f"""✅ QA Run History

Module: QA History
Mode: history
Environment: Sandbox
Status: PASS

Recent QA Runs:
{chr(10).join(lines)}

History File:
{history_path}
"""

    markdown_lines = [
        "# QA Run History",
        "",
        f"History File: {history_path}",
        "",
        "| No | Feature | Status | Mode | Created At | Passed | Failed | Need Review | Bugs |",
        "|---|---|---|---|---|---:|---:|---:|---:|",
    ]

    for index, item in enumerate(recent_items, start=1):
        markdown_lines.append(
            f"| {index} | {item.get('feature')} | {item.get('status')} | "
            f"{item.get('mode')} | {item.get('created_at') or item.get('executed_at')} | "
            f"{item.get('passed', 0)} | {item.get('failed', 0)} | "
            f"{item.get('need_review', 0)} | {item.get('bugs_found', 0)} |"
        )

    return {
        "testing_summary": testing_summary,
        "documentation_report": "\n".join(markdown_lines),
        "error_log_report": "# QA Run History\n\nNo error.",
        "status": "PASS",
        "history_path": history_path,
    }


_qa_register_history_feature()


if not globals().get("_QA_RUN_HISTORY_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_HISTORY = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_qa_history(module_name, mode):
            result = perform_qa_history_suite(url, module_name, mode)

            enrich_fn = globals().get("enrich_qa_result_with_standard_json")
            if enrich_fn:
                result = enrich_fn(result, url, module_name, mode)

            return result

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_HISTORY is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        import os

        is_all_features = False
        all_checker = globals().get("should_run_all_features")
        try:
            is_all_features = bool(all_checker and all_checker(module_name, mode))
        except Exception:
            is_all_features = False

        previous_history_disable = os.environ.get("QA_HISTORY_DISABLE")

        try:
            if is_all_features:
                os.environ["QA_HISTORY_DISABLE"] = "1"

            result = _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_HISTORY(
                url,
                module_name,
                mode,
                *args,
                **kwargs,
            )

        finally:
            if is_all_features:
                if previous_history_disable is None:
                    os.environ.pop("QA_HISTORY_DISABLE", None)
                else:
                    os.environ["QA_HISTORY_DISABLE"] = previous_history_disable

        return append_qa_run_history(result, url, module_name, mode)

    _QA_RUN_HISTORY_PATCH_INSTALLED = True
'''

if "# QA Run History Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted QA Run History integration")
else:
    print("QA Run History block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
