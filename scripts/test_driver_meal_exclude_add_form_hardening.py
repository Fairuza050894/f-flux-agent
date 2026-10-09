from pathlib import Path
import os
import sys
import traceback

# Disable combined suite for this focused ADD Form hardening test.
# This script must run only Exclude -> ADD Form, not Monitoring + Exclude + History.
os.environ["QA_DRIVER_DAILY_MEAL_COMBINED"] = "false"

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


def open_driver_meal_exclude_add_form(page, test_cases, preferred_subpage="Monitoring"):
    opened_exclude = False

    for label in ["Exclude", "Pengecualian", "Exception", "Exceptions"]:
        if _click_label(page, label):
            opened_exclude = True
            break

    checker.add_test_case(
        test_cases,
        scenario="Open Driver Meal Exclude subpage",
        precondition="Driver Meal menu group is visible",
        steps="Click Exclude submenu",
        expected="Driver Meal Exclude subpage should be opened",
        actual="Exclude opened" if opened_exclude else "Exclude not opened",
        status="PASS" if opened_exclude else "FAIL",
    )

    if not opened_exclude:
        return

    opened_add = False

    for selector in ["button:has-text('ADD')", ".v-btn:has-text('ADD')", "text=ADD"]:
        try:
            locator = page.locator(selector).first

            if locator.count() <= 0:
                continue

            locator.scroll_into_view_if_needed(timeout=3000)
            locator.click(timeout=5000)
            page.wait_for_timeout(1500)
            opened_add = True
            break
        except Exception:
            continue

    checker.add_test_case(
        test_cases,
        scenario="Open Exclude ADD form",
        precondition="Driver Meal Exclude page is opened",
        steps="Click ADD button",
        expected="ADD form/dialog should be opened",
        actual="ADD form opened" if opened_add else "ADD form not opened",
        status="PASS" if opened_add else "FAIL",
    )


def main():
    checker.open_uang_makan_driver_subpage = open_driver_meal_exclude_add_form
    checker.validate_uang_makan_driver_monitoring_page = checker.validate_driver_meal_exclude_add_form_page
    checker.validate_uang_makan_driver_page = checker.validate_driver_meal_exclude_add_form_page

    result = checker.perform_audit_for_telegram(
        URL,
        MODULE_NAME,
        "regression",
    )

    print("=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:7000])

    print("\n=== ARTIFACTS ===")
    print("Selector Inventory:", result.get("selector_inventory_path"))
    print("Screenshot:", result.get("screenshot_path"))
    print("Report:", result.get("report_path"))
    print("Spreadsheet:", result.get("spreadsheet_path"))

    print("\n=== ERROR LOG REPORT ===")
    print((result.get("error_log_report") or "-")[:3000])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
