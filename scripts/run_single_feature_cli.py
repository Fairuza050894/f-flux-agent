from pathlib import Path
from datetime import datetime
import argparse
import json
import os
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import skills.qa_automation.checker as checker


def extract_line(text, prefix):
    for line in str(text or "").splitlines():
        if line.strip().startswith(prefix):
            return line.strip()
    return ""


def extract_status(summary):
    line = extract_line(summary, "Status:")
    return line.replace("Status:", "").strip() if line else "UNKNOWN"


def extract_count(summary, label):
    line = extract_line(summary, f"- {label}:")
    if not line:
        return 0
    try:
        return int(line.split(":", 1)[1].strip())
    except Exception:
        return 0


def normalize_feature(value):
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def run_driver_daily_meal(url, mode):
    os.environ["QA_DRIVER_DAILY_MEAL_COMBINED"] = "true"

    # Driver Daily Meal memakai display name baru,
    # tetapi module/menu internal yang stabil masih Uang Makan Driver / Driver Meal.
    module_name = "Uang Makan Driver"

    try:
        if hasattr(checker, "get_feature_config"):
            config = checker.get_feature_config("driver daily meal")
            module_name = config.get("module_name") or module_name
    except Exception:
        pass

    if hasattr(checker, "perform_driver_daily_meal_combined_suite"):
        try:
            return checker.perform_driver_daily_meal_combined_suite(
                url,
                module_name,
                mode,
            )
        except TypeError:
            return checker.perform_driver_daily_meal_combined_suite(
                url=url,
                module_name=module_name,
                mode=mode,
            )

    return checker.perform_audit_for_telegram(
        url,
        module_name,
        mode,
    )


def run_feature(url, feature, mode):
    normalized = normalize_feature(feature)

    if normalized in {
        "driver daily meal",
        "driver meal",
        "uang makan driver",
        "uang makan",
        "meal allowance",
    }:
        return run_driver_daily_meal(url, mode)

    return checker.perform_audit_for_telegram(
        url,
        feature,
        mode,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature", required=True)
    parser.add_argument("--mode", default="regression")
    parser.add_argument(
        "--url",
        default=os.getenv(
            "QA_DEFAULT_URL",
            "https://mobospace-sandbox.pancaran-group.co.id",
        ),
    )
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = normalize_feature(args.feature).replace(" ", "_")

    output_dir = ROOT / "skills" / "qa_automation" / "artifacts" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = run_feature(args.url, args.feature, args.mode)
        summary = result.get("testing_summary", "")
        status = extract_status(summary)

        item = {
            "feature": args.feature,
            "mode": args.mode,
            "url": args.url,
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
            "testing_summary": summary,
        }

        json_path = output_dir / f"qa_single_{slug}_{run_id}.json"
        json_path.write_text(json.dumps(item, indent=2, ensure_ascii=False), encoding="utf-8")

        print(summary[:12000])
        print("")
        print(f"JSON_RESULT_PATH={json_path}")

        if status == "FAILED":
            sys.exit(2)

        if status == "NEED REVIEW":
            sys.exit(1)

        sys.exit(0)

    except Exception as exc:
        error_item = {
            "feature": args.feature,
            "mode": args.mode,
            "url": args.url,
            "status": "FAILED",
            "passed": 0,
            "failed": 1,
            "need_review": 0,
            "skipped": 0,
            "bugs_found": 1,
            "error": str(exc),
            "traceback": traceback.format_exc(),
        }

        json_path = output_dir / f"qa_single_{slug}_{run_id}_failed.json"
        json_path.write_text(json.dumps(error_item, indent=2, ensure_ascii=False), encoding="utf-8")

        print("=== ERROR ===")
        print(str(exc))
        traceback.print_exc()
        print("")
        print(f"JSON_RESULT_PATH={json_path}")
        sys.exit(2)


if __name__ == "__main__":
    main()
