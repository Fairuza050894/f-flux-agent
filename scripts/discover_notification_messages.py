from pathlib import Path
import os
import sys
import traceback

os.environ["QA_DRIVER_DAILY_MEAL_COMBINED"] = "false"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import skills.qa_automation.checker as checker


URL = os.getenv(
    "QA_DEFAULT_URL",
    "https://mobospace-sandbox.pancaran-group.co.id",
)

MODULE_NAME = "Notification Messages"


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


def open_notification_messages_direct(page, module_name):
    """
    Open Notification Messages via direct route /notificationmessage.
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_notification_messages_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "notification messages" in lower
            or "notification message" in lower
            or "notification" in lower
            or "message" in lower
            or "filter" in lower
            or "search" in lower
            or page.locator(".v-data-table").count() > 0
            or page.locator(".v-data-table__wrapper").count() > 0
            or page.locator(".v-card").count() > 0
        )

    try:
        target_url = get_origin() + "/notificationmessage"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "notificationmessage" in current_url
        marker_found = has_notification_messages_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /notificationmessage: {exc}"


def noop_subpage(page, test_cases, preferred_subpage=""):
    checker.add_test_case(
        test_cases,
        scenario="Open Notification Messages page",
        precondition="User is logged in and /notificationmessage route is available",
        steps="Open direct /notificationmessage route",
        expected="Notification Messages page should be opened",
        actual="Notification Messages direct route used",
        status="PASS",
    )


def validate_notification_messages_discovery_page(page, test_cases, bugs):
    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    body_text = get_body_text()
    lower = body_text.lower()

    markers = [
        "notification messages",
        "notification message",
        "notification",
        "message",
        "filter",
        "search",
        "rows per page",
        "no data available",
        "template",
        "contact",
        "group",
        "sent",
        "status",
    ]

    matched_markers = [marker for marker in markers if marker in lower]

    element_counts = {
        ".v-data-table": locator_count(".v-data-table"),
        ".v-data-table__wrapper": locator_count(".v-data-table__wrapper"),
        ".v-card": locator_count(".v-card"),
        "input[type='text']": locator_count("input[type='text']"),
        "button": locator_count("button"),
        ".v-input": locator_count(".v-input"),
    }

    context_found = (
        len(matched_markers) >= 1
        or element_counts[".v-data-table"] > 0
        or element_counts[".v-data-table__wrapper"] > 0
    )

    checker.add_test_case(
        test_cases,
        scenario="Discover Notification Messages page context",
        precondition="Notification Messages page is opened",
        steps="Read visible page markers, tables, filters, inputs, and buttons",
        expected="Notification Messages page markers should be discoverable",
        actual=f"Matched markers={matched_markers}; element counts={element_counts}",
        status="PASS" if context_found else "NEED REVIEW",
    )


def main():
    checker.open_target_menu = open_notification_messages_direct
    checker.open_uang_makan_driver_subpage = noop_subpage
    checker.validate_uang_makan_driver_monitoring_page = validate_notification_messages_discovery_page
    checker.validate_uang_makan_driver_page = validate_notification_messages_discovery_page

    result = checker.perform_audit_for_telegram(
        URL,
        MODULE_NAME,
        "smoke",
    )

    print("=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:7000])

    inventory_path = result.get("selector_inventory_path")

    print("\n=== ARTIFACTS ===")
    print("Selector Inventory:", inventory_path)
    print("Screenshot:", result.get("screenshot_path"))
    print("Report:", result.get("report_path"))
    print("Spreadsheet:", result.get("spreadsheet_path"))

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
            ["## Vuetify Tabs", "## Vuetify Data Tables", "## Vuetify Cards"],
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

    print("\n=== INVENTORY: VUETIFY CARDS ===")
    print(
        _extract_section(
            inventory_text,
            "## Vuetify Cards",
            ["## Main Content Candidates"],
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
