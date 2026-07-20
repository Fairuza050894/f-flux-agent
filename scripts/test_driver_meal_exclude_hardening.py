from pathlib import Path
import os
import sys
import traceback

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
            scope.get_by_text(label, exact=False).first,
            page.locator(f".v-list-item:has-text('{label}')").last,
            page.locator(f"[role='button']:has-text('{label}')").last,
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


def open_driver_meal_exclude_subpage(page, test_cases, preferred_subpage="Monitoring"):
    labels = [
        "Exclude",
        "Pengecualian",
        "Exception",
        "Exceptions",
        "Excluded",
        "Exclusion",
    ]

    clicked_label = None

    for label in labels:
        if _click_label(page, label):
            clicked_label = label
            break

    if clicked_label:
        checker.add_test_case(
            test_cases,
            scenario="Open Driver Meal Exclude subpage",
            precondition="Driver Meal menu group is visible",
            steps=f"Click {clicked_label} submenu",
            expected="Driver Meal Exclude/Pengecualian subpage should be opened",
            actual=f"Opened submenu: {clicked_label}",
            status="PASS",
        )
    else:
        checker.add_test_case(
            test_cases,
            scenario="Open Driver Meal Exclude subpage",
            precondition="Driver Meal menu group is visible",
            steps="Click Exclude / Pengecualian submenu",
            expected="Driver Meal Exclude/Pengecualian subpage should be opened",
            actual="Exclude/Pengecualian submenu was not found",
            status="FAIL",
        )


def main():
    # Monkeypatch hanya untuk test hardening Exclude.
    checker.open_uang_makan_driver_subpage = open_driver_meal_exclude_subpage

    # Business validator Driver Meal diarahkan ke Exclude validator.
    checker.validate_uang_makan_driver_monitoring_page = checker.validate_driver_meal_exclude_page
    checker.validate_uang_makan_driver_page = checker.validate_driver_meal_exclude_page

    result = checker.perform_audit_for_telegram(
        URL,
        MODULE_NAME,
        "regression",
    )

    print("=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:5000])

    print("\n=== ARTIFACTS ===")
    print("Selector Inventory:", result.get("selector_inventory_path"))
    print("Screenshot:", result.get("screenshot_path"))
    print("Report:", result.get("report_path"))
    print("Spreadsheet:", result.get("spreadsheet_path"))

    print("\n=== METADATA ===")
    print("Markdown enriched:", result.get("metadata_markdown_enriched"))
    print("Excel enriched:", result.get("metadata_excel_enriched"))

    print("\n=== ERROR LOG REPORT ===")
    print((result.get("error_log_report") or "-")[:3000])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
