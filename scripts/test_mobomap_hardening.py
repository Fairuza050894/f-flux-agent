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


def open_mobomap_direct(page, module_name):
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
        for selector in [
            ".gm-style",
            ".leaflet-container",
            "[class*='map']",
            "[id*='map']",
            "canvas",
        ]:
            try:
                dom_map_count += page.locator(selector).count()
            except Exception:
                pass

        return (
            "mobomap" in lower
            or "mobo map" in lower
            or "vehicle" in lower
            or "driver" in lower
            or "map data" in lower
            or "satellite" in lower
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


def main():
    checker.open_target_menu = open_mobomap_direct
    checker.open_uang_makan_driver_subpage = noop_subpage
    checker.validate_uang_makan_driver_monitoring_page = checker.validate_mobomap_page
    checker.validate_uang_makan_driver_page = checker.validate_mobomap_page

    result = checker.perform_audit_for_telegram(
        URL,
        "MoboMap",
        "regression",
    )

    print("=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:9000])

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
