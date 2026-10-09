from pathlib import Path
from datetime import datetime
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

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

REPORT_DIR = ROOT / "skills" / "qa_automation" / "artifacts" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def read_json_result(json_path):
    try:
        path = Path(json_path)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def main():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = []

    print("==============================================", flush=True)
    print(" QA FULL REGRESSION ISOLATED - ALL FEATURES", flush=True)
    print("==============================================", flush=True)
    print(f"Run ID : QA-ALL-ISO-{run_id}", flush=True)
    print(f"URL    : {BASE_URL}", flush=True)
    print(f"Mode   : {MODE}", flush=True)

    for index, feature in enumerate(FEATURES, start=1):
        print("", flush=True)
        print(f"[{index}/{len(FEATURES)}] Running isolated: {feature}", flush=True)
        print("-" * 60, flush=True)

        cmd = [
            sys.executable,
            "-u",
            str(ROOT / "scripts" / "run_single_feature_cli.py"),
            "--feature",
            feature,
            "--mode",
            MODE,
            "--url",
            BASE_URL,
        ]

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        process = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            bufsize=1,
        )

        json_path = None

        assert process.stdout is not None

        for line in process.stdout:
            print(line, end="", flush=True)

            if line.startswith("JSON_RESULT_PATH="):
                json_path = line.split("=", 1)[1].strip()

        return_code = process.wait()

        item = read_json_result(json_path) if json_path else None

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
                "return_code": return_code,
            }

        results.append(item)

        print("", flush=True)
        print(
            f"Finished: {feature} => {item.get('status')} "
            f"(PASS={item.get('passed', 0)}, FAIL={item.get('failed', 0)}, "
            f"NEED_REVIEW={item.get('need_review', 0)}, BUGS={item.get('bugs_found', 0)})",
            flush=True,
        )

    total_passed = sum(int(item.get("passed", 0) or 0) for item in results)
    total_failed = sum(int(item.get("failed", 0) or 0) for item in results)
    total_need_review = sum(int(item.get("need_review", 0) or 0) for item in results)
    total_skipped = sum(int(item.get("skipped", 0) or 0) for item in results)
    total_bugs = sum(int(item.get("bugs_found", 0) or 0) for item in results)

    if any(item.get("status") == "FAILED" for item in results) or total_failed > 0 or total_bugs > 0:
        overall_status = "FAILED"
    elif any(item.get("status") == "NEED REVIEW" for item in results) or total_need_review > 0:
        overall_status = "NEED REVIEW"
    else:
        overall_status = "PASS"

    markdown = [
        "# QA Full Regression Isolated - All Features",
        "",
        f"Run ID: QA-ALL-ISO-{run_id}",
        "Environment: Sandbox",
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
        markdown.append(
            f"| {i} | {item.get('feature')} | {item.get('status')} | "
            f"{item.get('passed', 0)} | {item.get('failed', 0)} | "
            f"{item.get('need_review', 0)} | {item.get('skipped', 0)} | "
            f"{item.get('bugs_found', 0)} |"
        )

    markdown.extend([
        "",
        "## Artifacts",
        "",
        "| Feature | Report | Spreadsheet | Screenshot | Error Log |",
        "|---|---|---|---|---|",
    ])

    for item in results:
        markdown.append(
            f"| {item.get('feature')} | "
            f"{item.get('report_path', '-')} | "
            f"{item.get('spreadsheet_path', '-')} | "
            f"{item.get('screenshot_path', '-')} | "
            f"{item.get('error_log_path', '-')} |"
        )

    markdown.extend([
        "",
        "## Raw JSON",
        "",
        "```json",
        json.dumps(results, indent=2, ensure_ascii=False),
        "```",
    ])

    output_path = REPORT_DIR / f"qa_full_regression_isolated_all_features_{run_id}.md"
    output_path.write_text("\n".join(markdown), encoding="utf-8")

    print("", flush=True)
    print("==============================================", flush=True)
    print(" QA FULL REGRESSION ISOLATED COMPLETED", flush=True)
    print("==============================================", flush=True)
    print(f"Overall Status : {overall_status}", flush=True)
    print(f"Features Tested: {len(results)}", flush=True)
    print(f"Passed         : {total_passed}", flush=True)
    print(f"Failed         : {total_failed}", flush=True)
    print(f"Need Review    : {total_need_review}", flush=True)
    print(f"Skipped        : {total_skipped}", flush=True)
    print(f"Bugs Found     : {total_bugs}", flush=True)
    print(f"Summary Report : {output_path}", flush=True)
    print("", flush=True)
    print("=== FEATURE RESULT TABLE ===", flush=True)

    for item in results:
        print(
            f"- {item.get('feature')}: {item.get('status')} "
            f"(PASS={item.get('passed', 0)}, FAIL={item.get('failed', 0)}, "
            f"NEED_REVIEW={item.get('need_review', 0)}, BUGS={item.get('bugs_found', 0)})",
            flush=True,
        )


if __name__ == "__main__":
    main()
