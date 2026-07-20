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


def _extract_section(text: str, start_marker: str, end_markers: list[str]) -> str:
    start = text.find(start_marker)
    if start == -1:
        return f"{start_marker}\n- Section not found\n"

    end_candidates = [
        text.find(marker, start + len(start_marker))
        for marker in end_markers
        if text.find(marker, start + len(start_marker)) != -1
    ]

    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end].strip() + "\n"


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


def open_driver_meal_history_subpage(page, test_cases, preferred_subpage="Monitoring"):
    labels = [
        "History",
        "Inquiry",
        "Riwayat",
    ]

    clicked_label = None

    for label in labels:
        if _click_label(page, label):
            clicked_label = label
            break

    if clicked_label:
        checker.add_test_case(
            test_cases,
            scenario="Open Driver Meal History subpage",
            precondition="Driver Meal menu group is visible",
            steps=f"Click {clicked_label} submenu",
            expected="Driver Meal History/Inquiry subpage should be opened",
            actual=f"Opened submenu: {clicked_label}",
            status="PASS",
        )
    else:
        checker.add_test_case(
            test_cases,
            scenario="Open Driver Meal History subpage",
            precondition="Driver Meal menu group is visible",
            steps="Click History / Inquiry submenu",
            expected="Driver Meal History/Inquiry subpage should be opened",
            actual="History/Inquiry submenu was not found",
            status="FAIL",
        )


def validate_driver_meal_history_discovery_page(page, test_cases, bugs):
    try:
        body_text = page.locator("body").inner_text(timeout=5000)
    except Exception as exc:
        body_text = f"FAILED_TO_READ_BODY: {exc}"

    lower = body_text.lower()

    context_found = (
        "driver meal history" in lower
        or "history" in lower
        or "inquiry" in lower
        or "transaction date" in lower
        or "driver name" in lower
        or "eligible" in lower
    )

    checker.add_test_case(
        test_cases,
        scenario="Verify Driver Meal History discovery context",
        precondition="Driver Meal History/Inquiry subpage is opened",
        steps="Check body text markers for History/Inquiry page",
        expected="History/Inquiry page context should be visible",
        actual="History/Inquiry context found" if context_found else body_text[:500],
        status="PASS" if context_found else "NEED REVIEW",
    )


def main():
    checker.open_uang_makan_driver_subpage = open_driver_meal_history_subpage
    checker.validate_uang_makan_driver_monitoring_page = validate_driver_meal_history_discovery_page
    checker.validate_uang_makan_driver_page = validate_driver_meal_history_discovery_page

    result = checker.perform_audit_for_telegram(
        URL,
        MODULE_NAME,
        "smoke",
    )

    print("=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:5000])

    inventory_path = result.get("selector_inventory_path")
    screenshot_path = result.get("screenshot_path")
    spreadsheet_path = result.get("spreadsheet_path")
    report_path = result.get("report_path")

    print("\n=== ARTIFACTS ===")
    print("Selector Inventory:", inventory_path)
    print("Screenshot:", screenshot_path)
    print("Report:", report_path)
    print("Spreadsheet:", spreadsheet_path)

    print("\n=== ERROR LOG REPORT ===")
    print((result.get("error_log_report") or "-")[:3000])

    if not inventory_path or not Path(inventory_path).exists():
        print("\nSelector inventory not found.")
        return

    inventory_text = Path(inventory_path).read_text(encoding="utf-8")

    print("\n=== INVENTORY: VISIBLE TEXT ===")
    print(
        _extract_section(
            inventory_text,
            "## Visible Text Preview",
            ["## Buttons"],
        )
    )

    print("\n=== INVENTORY: BUTTONS ===")
    print(
        _extract_section(
            inventory_text,
            "## Buttons",
            ["## Inputs", "## Inputs and Textareas", "## ARIA Interactive Elements"],
        )
    )

    print("\n=== INVENTORY: INPUTS ===")
    print(
        _extract_section(
            inventory_text,
            "## Inputs and Textareas",
            ["## ARIA Interactive Elements", "## Vuetify Inputs"],
        )
    )

    print("\n=== INVENTORY: VUETIFY INPUTS ===")
    print(
        _extract_section(
            inventory_text,
            "## Vuetify Inputs",
            ["## Vuetify Tabs", "## Vuetify Data Tables"],
        )
    )

    print("\n=== INVENTORY: VUETIFY TABS ===")
    print(
        _extract_section(
            inventory_text,
            "## Vuetify Tabs",
            ["## Vuetify Data Tables", "## Vuetify Cards"],
        )
    )

    print("\n=== INVENTORY: VUETIFY DATA TABLES ===")
    print(
        _extract_section(
            inventory_text,
            "## Vuetify Data Tables",
            ["## Vuetify Cards", "## Main Content Candidates"],
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
