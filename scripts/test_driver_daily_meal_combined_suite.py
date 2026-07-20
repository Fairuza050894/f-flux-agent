from pathlib import Path
import os
import sys
import traceback
import re

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import skills.qa_automation.checker as checker


URL = os.getenv(
    "QA_DEFAULT_URL",
    "https://mobospace-sandbox.pancaran-group.co.id",
)

MODULE_NAME = os.getenv(
    "QA_DEFAULT_MODULE",
    "Uang Makan Driver",
)


def _click_label(page, label: str) -> bool:
    scopes = [
        page.locator(".v-navigation-drawer, .v-navigation-drawer__content, .v-list, nav, aside").first,
        page.locator("body"),
    ]

    for scope in scopes:
        candidates = [
            scope.get_by_text(label, exact=True).first,
            page.locator(f".v-list-item:has-text('{label}')").last,
            page.locator(f"[role='button']:has-text('{label}')").last,
            scope.get_by_text(label, exact=False).first,
            page.get_by_text(label, exact=True).last,
            page.get_by_text(label, exact=False).last,
        ]

        for candidate in candidates:
            try:
                if candidate.count() <= 0:
                    continue

                candidate.scroll_into_view_if_needed(timeout=3000)
                candidate.wait_for(state="visible", timeout=4000)
                candidate.click(timeout=5000)

                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                page.wait_for_timeout(1500)
                return True

            except Exception:
                continue

    return False


def make_open_subpage(subfeature_name, labels):
    def open_subpage(page, test_cases, preferred_subpage="Monitoring"):
        clicked_label = None

        for label in labels:
            if _click_label(page, label):
                clicked_label = label
                break

        if clicked_label:
            checker.add_test_case(
                test_cases,
                scenario=f"Open Driver Meal {subfeature_name} subpage",
                precondition="Driver Meal menu group is visible",
                steps=f"Click {clicked_label} submenu",
                expected=f"Driver Meal {subfeature_name} subpage should be opened",
                actual=f"Opened submenu: {clicked_label}",
                status="PASS",
            )
        else:
            checker.add_test_case(
                test_cases,
                scenario=f"Open Driver Meal {subfeature_name} subpage",
                precondition="Driver Meal menu group is visible",
                steps=f"Click {subfeature_name} submenu",
                expected=f"Driver Meal {subfeature_name} subpage should be opened",
                actual=f"{subfeature_name} submenu was not found",
                status="FAIL",
            )

    return open_subpage


def get_status(result):
    status = result.get("overall_status")

    if status:
        return str(status).upper()

    summary = result.get("testing_summary") or ""

    match = re.search(r"Status:\s*(PASS|FAILED|NEED REVIEW)", summary)

    if match:
        return match.group(1).upper()

    return "UNKNOWN"


def extract_summary_counts(summary):
    counts = {
        "passed": 0,
        "failed": 0,
        "need_review": 0,
        "skipped": 0,
        "bugs": 0,
        "warnings": 0,
    }

    patterns = {
        "passed": r"- Passed:\s*(\d+)",
        "failed": r"- Failed:\s*(\d+)",
        "need_review": r"- Need Review:\s*(\d+)",
        "skipped": r"- Skipped:\s*(\d+)",
        "bugs": r"- Bugs Found:\s*(\d+)",
        "warnings": r"- Non-blocking Warnings:\s*(\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, summary)
        if match:
            counts[key] = int(match.group(1))

    return counts


def run_subfeature(name, open_func, validator_func):
    original_open = checker.open_uang_makan_driver_subpage
    original_monitoring_validator = getattr(checker, "validate_uang_makan_driver_monitoring_page", None)
    original_page_validator = getattr(checker, "validate_uang_makan_driver_page", None)

    try:
        checker.open_uang_makan_driver_subpage = open_func
        checker.validate_uang_makan_driver_monitoring_page = validator_func
        checker.validate_uang_makan_driver_page = validator_func

        result = checker.perform_audit_for_telegram(
            URL,
            MODULE_NAME,
            "regression",
        )

        return result

    finally:
        checker.open_uang_makan_driver_subpage = original_open

        if original_monitoring_validator:
            checker.validate_uang_makan_driver_monitoring_page = original_monitoring_validator

        if original_page_validator:
            checker.validate_uang_makan_driver_page = original_page_validator


def main():
    suites = [
        {
            "name": "Monitoring",
            "open": make_open_subpage("Monitoring", ["Monitoring"]),
            "validator": checker.validate_uang_makan_driver_monitoring_page,
        },
        {
            "name": "Exclude",
            "open": make_open_subpage("Exclude", ["Exclude", "Pengecualian", "Exception", "Exceptions"]),
            "validator": checker.validate_driver_meal_exclude_page,
        },
        {
            "name": "History / Inquiry",
            "open": make_open_subpage("History / Inquiry", ["History", "Inquiry", "Riwayat"]),
            "validator": checker.validate_driver_meal_history_page,
        },
    ]

    results = []

    for suite in suites:
        print(f"\n\n==============================")
        print(f"RUNNING: {suite['name']}")
        print(f"==============================")

        result = run_subfeature(
            suite["name"],
            suite["open"],
            suite["validator"],
        )

        status = get_status(result)
        summary = result.get("testing_summary") or ""
        counts = extract_summary_counts(summary)

        results.append(
            {
                "name": suite["name"],
                "status": status,
                "counts": counts,
                "result": result,
            }
        )

        print(summary[:3000])

    has_failed = any(item["status"] == "FAILED" for item in results)
    has_need_review = any(item["status"] == "NEED REVIEW" for item in results)

    if has_failed:
        overall = "FAILED"
    elif has_need_review:
        overall = "NEED REVIEW"
    else:
        overall = "PASS"

    total_counts = {
        "passed": sum(item["counts"]["passed"] for item in results),
        "failed": sum(item["counts"]["failed"] for item in results),
        "need_review": sum(item["counts"]["need_review"] for item in results),
        "skipped": sum(item["counts"]["skipped"] for item in results),
        "bugs": sum(item["counts"]["bugs"] for item in results),
        "warnings": sum(item["counts"]["warnings"] for item in results),
    }

    print("\n\n==============================")
    print("DRIVER DAILY MEAL COMBINED RESULT")
    print("==============================")
    print(f"Overall Status: {overall}")
    print("")
    print("Subfeature Results:")

    for item in results:
        print(f"- {item['name']}: {item['status']}")

    print("")
    print("Total Summary:")
    print(f"- Passed: {total_counts['passed']}")
    print(f"- Failed: {total_counts['failed']}")
    print(f"- Need Review: {total_counts['need_review']}")
    print(f"- Skipped: {total_counts['skipped']}")
    print(f"- Bugs Found: {total_counts['bugs']}")
    print(f"- Non-blocking Warnings: {total_counts['warnings']}")

    print("")
    print("Artifacts:")

    for item in results:
        result = item["result"]
        print(f"\n{item['name']}:")
        print(f"- Screenshot: {result.get('screenshot_path')}")
        print(f"- Report: {result.get('report_path')}")
        print(f"- Spreadsheet: {result.get('spreadsheet_path')}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
