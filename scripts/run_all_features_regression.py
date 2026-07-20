from pathlib import Path
from datetime import datetime
import os
import sys
import traceback
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills.qa_automation import perform_audit_for_telegram


BASE_URL = os.getenv(
    "QA_DEFAULT_URL",
    "https://mobospace-sandbox.pancaran-group.co.id",
)

MODE = os.getenv("QA_ALL_FEATURES_MODE", "regression")

FEATURES = [
    "Driver Daily Meal",
    "Shipment Details",
    "MoboMap",
    "Inspection Result",
    "Notification Messages",
    "Notification Management",
]


ARTIFACT_DIR = ROOT / "skills" / "qa_automation" / "artifacts" / "reports"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def extract_line(text, prefix):
    for line in str(text or "").splitlines():
        if line.strip().startswith(prefix):
            return line.strip()
    return ""


def extract_status(summary):
    line = extract_line(summary, "Status:")
    if not line:
        return "UNKNOWN"
    return line.replace("Status:", "").strip()


def extract_count(summary, label):
    line = extract_line(summary, f"- {label}:")
    if not line:
        return 0
    try:
        return int(line.split(":", 1)[1].strip())
    except Exception:
        return 0


def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    print("==============================================")
    print(" QA FULL REGRESSION - ALL REGISTERED FEATURES")
    print("==============================================")
    print(f"Run ID : QA-ALL-{run_id}")
    print(f"URL    : {BASE_URL}")
    print(f"Mode   : {MODE}")
    print("")

    for index, feature in enumerate(FEATURES, start=1):
        print(f"\n[{index}/{len(FEATURES)}] Running: {feature}")
        print("-" * 60)

        try:
            result = perform_audit_for_telegram(
                BASE_URL,
                feature,
                MODE,
            )

            summary = result.get("testing_summary", "")
            status = extract_status(summary)

            item = {
                "feature": feature,
                "status": status,
                "passed": extract_count(summary, "Passed"),
                "failed": extract_count(summary, "Failed"),
                "need_review": extract_count(summary, "Need Review"),
                "skipped": extract_count(summary, "Skipped"),
                "bugs_found": extract_count(summary, "Bugs Found"),
                "screenshot_path": result.get("screenshot_path"),
                "report_path": result.get("report_path"),
                "error_log_path": result.get("error_log_path"),
                "spreadsheet_path": result.get("spreadsheet_path"),
                "selector_inventory_path": result.get("selector_inventory_path"),
            }

            results.append(item)

            print(summary[:7000])
            print("")
            print(f"Result: {feature} => {status}")
            print(f"Report: {item['report_path']}")
            print(f"Spreadsheet: {item['spreadsheet_path']}")
            print(f"Screenshot: {item['screenshot_path']}")

        except Exception as exc:
            print(f"FAILED TO RUN FEATURE: {feature}")
            print(str(exc))
            traceback.print_exc()

            results.append({
                "feature": feature,
                "status": "FAILED",
                "passed": 0,
                "failed": 1,
                "need_review": 0,
                "skipped": 0,
                "bugs_found": 1,
                "error": str(exc),
            })

    total_passed = sum(item.get("passed", 0) for item in results)
    total_failed = sum(item.get("failed", 0) for item in results)
    total_need_review = sum(item.get("need_review", 0) for item in results)
    total_skipped = sum(item.get("skipped", 0) for item in results)
    total_bugs = sum(item.get("bugs_found", 0) for item in results)

    if any(item.get("status") == "FAILED" for item in results) or total_failed > 0 or total_bugs > 0:
        overall_status = "FAILED"
    elif any(item.get("status") == "NEED REVIEW" for item in results) or total_need_review > 0:
        overall_status = "NEED REVIEW"
    elif all(item.get("status") == "PASS" for item in results):
        overall_status = "PASS"
    else:
        overall_status = "NEED REVIEW"

    markdown_lines = [
        f"# QA Full Regression - All Features",
        "",
        f"Run ID: QA-ALL-{run_id}",
        f"Environment: Sandbox",
        f"Base URL: {BASE_URL}",
        f"Mode: {MODE}",
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

    for i, item in enumerate(results, start=1):
        markdown_lines.append(
            f"| {i} | {item.get('feature')} | {item.get('status')} | "
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
        "",
    ])

    output_path = ARTIFACT_DIR / f"qa_full_regression_all_features_{run_id}.md"
    output_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    print("\n==============================================")
    print(" QA FULL REGRESSION COMPLETED")
    print("==============================================")
    print(f"Overall Status : {overall_status}")
    print(f"Features Tested: {len(results)}")
    print(f"Passed         : {total_passed}")
    print(f"Failed         : {total_failed}")
    print(f"Need Review    : {total_need_review}")
    print(f"Skipped        : {total_skipped}")
    print(f"Bugs Found     : {total_bugs}")
    print(f"Summary Report : {output_path}")
    print("")

    print("=== FEATURE RESULT TABLE ===")
    for item in results:
        print(
            f"- {item.get('feature')}: {item.get('status')} "
            f"(PASS={item.get('passed', 0)}, FAIL={item.get('failed', 0)}, "
            f"NEED_REVIEW={item.get('need_review', 0)}, BUGS={item.get('bugs_found', 0)})"
        )


if __name__ == "__main__":
    main()
