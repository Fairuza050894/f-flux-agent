from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_all_features_telegram_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# All Features Telegram /audit_qa Integration
# ============================================================

def _qa_register_all_features():
    """
    Register All Features ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=all
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["all_features"] = {
        "display_name": "All Features",
        "module_name": "All Features",
        "menu_aliases": [
            "All Features",
            "All",
            "Semua",
        ],
        "aliases": [
            "all",
            "all features",
            "semua",
            "semua fitur",
            "full regression",
            "full all features",
            "all regression",
        ],
        "default_subfeatures": ["all"],
        "subfeature_aliases": {
            "all": [
                "all",
                "all features",
                "semua",
                "semua fitur",
                "full regression",
            ],
        },
    }


def should_run_all_features(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "all",
        "all features",
        "semua",
        "semua fitur",
        "full regression",
        "full all features",
        "all regression",
    }

    return value in aliases


def _qa_all_extract_line(text, prefix):
    for line in str(text or "").splitlines():
        if line.strip().startswith(prefix):
            return line.strip()
    return ""


def _qa_all_extract_status(summary):
    line = _qa_all_extract_line(summary, "Status:")
    return line.replace("Status:", "").strip() if line else "UNKNOWN"


def _qa_all_extract_count(summary, label):
    line = _qa_all_extract_line(summary, f"- {label}:")
    if not line:
        return 0
    try:
        return int(line.split(":", 1)[1].strip())
    except Exception:
        return 0


def _qa_all_read_json_result(stdout):
    try:
        from pathlib import Path
        import json

        for line in str(stdout or "").splitlines():
            if line.startswith("JSON_RESULT_PATH="):
                path = Path(line.split("=", 1)[1].strip())
                if path.exists():
                    return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass

    return None


def _qa_all_write_spreadsheet(spreadsheet_path, results, overall_status, mode, url):
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "All Features Summary"

        ws.append(["QA Full Regression - All Features"])
        ws.append(["Environment", "Sandbox"])
        ws.append(["Base URL", url])
        ws.append(["Mode", mode])
        ws.append(["Overall Status", overall_status])
        ws.append([])

        headers = ["No", "Feature", "Status", "Passed", "Failed", "Need Review", "Skipped", "Bugs", "Report", "Spreadsheet", "Screenshot"]
        ws.append(headers)

        for cell in ws[7]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="D9EAF7")
            cell.alignment = Alignment(horizontal="center")

        for idx, item in enumerate(results, start=1):
            ws.append([
                idx,
                item.get("feature"),
                item.get("status"),
                item.get("passed", 0),
                item.get("failed", 0),
                item.get("need_review", 0),
                item.get("skipped", 0),
                item.get("bugs_found", 0),
                item.get("report_path", "-"),
                item.get("spreadsheet_path", "-"),
                item.get("screenshot_path", "-"),
            ])

        for column_cells in ws.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                value = str(cell.value or "")
                if len(value) > max_length:
                    max_length = len(value)
            ws.column_dimensions[column_letter].width = min(max_length + 2, 60)

        wb.save(spreadsheet_path)
        return str(spreadsheet_path)

    except Exception:
        return None


def perform_all_features_suite(url, module_name="All Features", mode="regression"):
    """
    Runner all features untuk Telegram.

    Menjalankan setiap fitur melalui subprocess run_single_feature_cli.py agar isolated:
    - Driver Daily Meal
    - Shipment Details
    - MoboMap
    - Inspection Result
    - Notification Messages
    - Notification Management
    """

    from pathlib import Path
    from datetime import datetime
    import json
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[2]

    features = [
        "Driver Daily Meal",
        "Shipment Details",
        "MoboMap",
        "Inspection Result",
        "Notification Messages",
        "Notification Management",
    ]

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    report_dir = root / "skills" / "qa_automation" / "artifacts" / "reports"
    log_dir = root / "skills" / "qa_automation" / "artifacts" / "logs"
    spreadsheet_dir = root / "skills" / "qa_automation" / "artifacts" / "spreadsheets"

    report_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    spreadsheet_dir.mkdir(parents=True, exist_ok=True)

    results = []
    raw_outputs = []

    for index, feature in enumerate(features, start=1):
        cmd = [
            sys.executable,
            "-u",
            str(root / "scripts" / "run_single_feature_cli.py"),
            "--feature",
            feature,
            "--mode",
            mode,
            "--url",
            url,
        ]

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        completed = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=2400,
        )

        stdout = completed.stdout or ""
        raw_outputs.append(f"===== {feature} =====\n{stdout}\n")

        item = _qa_all_read_json_result(stdout)

        if item is None:
            item = {
                "feature": feature,
                "status": "FAILED",
                "passed": 0,
                "failed": 1,
                "need_review": 0,
                "skipped": 0,
                "bugs_found": 1,
                "error": "JSON_RESULT_PATH not found or unreadable",
                "return_code": completed.returncode,
            }

        results.append(item)

    total_passed = sum(int(item.get("passed", 0) or 0) for item in results)
    total_failed = sum(int(item.get("failed", 0) or 0) for item in results)
    total_need_review = sum(int(item.get("need_review", 0) or 0) for item in results)
    total_skipped = sum(int(item.get("skipped", 0) or 0) for item in results)
    total_bugs = sum(int(item.get("bugs_found", 0) or 0) for item in results)

    if any(item.get("status") == "FAILED" for item in results) or total_failed > 0 or total_bugs > 0:
        overall_status = "FAILED"
        icon = "❌"
    elif any(item.get("status") == "NEED REVIEW" for item in results) or total_need_review > 0:
        overall_status = "NEED REVIEW"
        icon = "⚠️"
    else:
        overall_status = "PASS"
        icon = "✅"

    feature_lines = []
    for item in results:
        feature_lines.append(
            f"- {item.get('feature')}: {item.get('status')} "
            f"(PASS={item.get('passed', 0)}, FAIL={item.get('failed', 0)}, "
            f"NEED_REVIEW={item.get('need_review', 0)}, BUGS={item.get('bugs_found', 0)})"
        )

    testing_summary = f"""{icon} QA Full Regression Completed

Module: All Features
Mode: {mode}
Environment: Sandbox
Status: {overall_status}

Execution Info:
- Execution ID: QA-ALL-{run_id}
- Executed At: {run_id}
- Executed By: Hermes QA Automation
- Feature: All Features
- Suite / Mode: {mode}
- Environment: Sandbox
- Base URL: {url}

Summary:
- Features Tested: {len(results)}
- Passed: {total_passed}
- Failed: {total_failed}
- Need Review: {total_need_review}
- Skipped: {total_skipped}
- Bugs Found: {total_bugs}

Feature Results:
{chr(10).join(feature_lines)}

Recommendation:
{"Review non-blocking warnings before release." if overall_status == "NEED REVIEW" else "No blocking issue found from automation result. Continue with manual business verification if needed."}
"""

    markdown_lines = [
        "# QA Full Regression - All Features",
        "",
        f"Execution ID: QA-ALL-{run_id}",
        "Environment: Sandbox",
        f"Base URL: {url}",
        f"Mode: {mode}",
        f"Overall Status: {overall_status}",
        "",
        "## Summary",
        "",
        f"- Features Tested: {len(results)}",
        f"- Passed Test Cases: {total_passed}",
        f"- Failed Test Cases: {total_failed}",
        f"- Need Review: {total_need_review}",
        f"- Skipped: {total_skipped}",
        f"- Bugs Found: {total_bugs}",
        "",
        "## Feature Results",
        "",
        "| No | Feature | Status | Passed | Failed | Need Review | Skipped | Bugs |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]

    for idx, item in enumerate(results, start=1):
        markdown_lines.append(
            f"| {idx} | {item.get('feature')} | {item.get('status')} | "
            f"{item.get('passed', 0)} | {item.get('failed', 0)} | "
            f"{item.get('need_review', 0)} | {item.get('skipped', 0)} | "
            f"{item.get('bugs_found', 0)} |"
        )

    markdown_lines.extend([
        "",
        "## Artifacts",
        "",
        "| Feature | Report | Spreadsheet | Screenshot | Error Log |",
        "|---|---|---|---|---|",
    ])

    for item in results:
        markdown_lines.append(
            f"| {item.get('feature')} | "
            f"{item.get('report_path', '-')} | "
            f"{item.get('spreadsheet_path', '-')} | "
            f"{item.get('screenshot_path', '-')} | "
            f"{item.get('error_log_path', '-')} |"
        )

    markdown_lines.extend([
        "",
        "## Raw JSON",
        "",
        "```json",
        json.dumps(results, indent=2, ensure_ascii=False),
        "```",
    ])

    report_path = report_dir / f"qa_documentation_all_features_{run_id}.md"
    report_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    error_log_report = f"""# QA Error / Bug Log - All Features

Environment: Sandbox
Mode: {mode}
Status: {overall_status}
Execution Time: {run_id}

---

## 1. Bug Digest

{"- No bug found" if total_bugs == 0 else f"- Bugs found: {total_bugs}"}

---

## 2. Failed Test Cases

{"- No failed test case" if total_failed == 0 else f"- Failed test cases: {total_failed}"}

---

## 3. Need Review Items

{"- No need review item" if total_need_review == 0 else f"- Need review items: {total_need_review}"}

---

## 4. Feature Results

{chr(10).join(feature_lines)}

---

## 5. Raw Execution Output

See documentation report for per-feature artifact links.
"""

    error_log_path = log_dir / f"qa_error_log_all_features_{run_id}.md"
    error_log_path.write_text(error_log_report, encoding="utf-8")

    raw_output_path = log_dir / f"qa_raw_output_all_features_{run_id}.log"
    raw_output_path.write_text("\n".join(raw_outputs), encoding="utf-8")

    spreadsheet_path = spreadsheet_dir / f"qa_report_all_features_{run_id}.xlsx"
    spreadsheet_result = _qa_all_write_spreadsheet(spreadsheet_path, results, overall_status, mode, url)

    first_screenshot = None
    for item in results:
        if item.get("screenshot_path"):
            first_screenshot = item.get("screenshot_path")
            break

    return {
        "testing_summary": testing_summary,
        "documentation_report": "\n".join(markdown_lines),
        "error_log_report": error_log_report,
        "status": overall_status,
        "screenshot_path": first_screenshot,
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "spreadsheet_path": spreadsheet_result or str(spreadsheet_path),
        "raw_output_path": str(raw_output_path),
        "all_feature_results": results,
    }


_qa_register_all_features()


if not globals().get("_ALL_FEATURES_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_ALL_FEATURES = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_all_features(module_name, mode):
            return perform_all_features_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_ALL_FEATURES is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_ALL_FEATURES(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _ALL_FEATURES_TELEGRAM_PATCH_INSTALLED = True
'''

if "# All Features Telegram /audit_qa Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted All Features Telegram integration")
else:
    print("All Features Telegram integration block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
