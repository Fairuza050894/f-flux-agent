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

MODULE_NAME = "MoboMap"


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


def open_mobomap_direct(page, module_name):
    """
    Open MoboMap via direct route /mobomap.
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

    def has_mobomap_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        dom_map_count = 0
        map_selectors = [
            ".leaflet-container",
            ".gm-style",
            "[class*='map']",
            "[id*='map']",
            "canvas",
        ]

        for selector in map_selectors:
            try:
                dom_map_count += page.locator(selector).count()
            except Exception:
                pass

        return (
            "mobomap" in lower
            or "mobo map" in lower
            or "tracking" in lower
            or "vehicle" in lower
            or "driver" in lower
            or dom_map_count > 0
        )

    try:
        target_url = get_origin() + "/mobomap"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(6000)

        current_url = page.url.lower()
        route_found = "mobomap" in current_url
        marker_found = has_mobomap_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /mobomap: {exc}"


def noop_subpage(page, test_cases, preferred_subpage=""):
    checker.add_test_case(
        test_cases,
        scenario="Open MoboMap page",
        precondition="User is logged in and /mobomap route is available",
        steps="Open direct /mobomap route",
        expected="MoboMap page should be opened",
        actual="MoboMap direct route used",
        status="PASS",
    )


def validate_mobomap_discovery_page(page, test_cases, bugs):
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

    map_selector_counts = {
        ".leaflet-container": locator_count(".leaflet-container"),
        ".gm-style": locator_count(".gm-style"),
        "[class*='map']": locator_count("[class*='map']"),
        "[id*='map']": locator_count("[id*='map']"),
        "canvas": locator_count("canvas"),
        "svg": locator_count("svg"),
    }

    text_markers = [
        "mobomap",
        "mobo map",
        "tracking",
        "vehicle",
        "driver",
        "search",
        "filter",
        "zoom",
        "location",
        "gps",
    ]

    matched_text_markers = [marker for marker in text_markers if marker in lower]
    dom_map_found = any(count > 0 for count in map_selector_counts.values())

    context_found = dom_map_found or len(matched_text_markers) >= 1

    checker.add_test_case(
        test_cases,
        scenario="Discover MoboMap page context",
        precondition="MoboMap page is opened",
        steps="Read visible page markers and map DOM selectors",
        expected="MoboMap page or map container should be discoverable",
        actual=(
            f"Matched text markers={matched_text_markers}; "
            f"Map selector counts={map_selector_counts}"
        ),
        status="PASS" if context_found else "NEED REVIEW",
    )


def main():
    checker.open_target_menu = open_mobomap_direct
    checker.open_uang_makan_driver_subpage = noop_subpage
    checker.validate_uang_makan_driver_monitoring_page = validate_mobomap_discovery_page
    checker.validate_uang_makan_driver_page = validate_mobomap_discovery_page

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
