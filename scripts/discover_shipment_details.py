from pathlib import Path
import os
import sys
import traceback

# Disable Driver Daily Meal combined suite for this focused discovery.
os.environ["QA_DRIVER_DAILY_MEAL_COMBINED"] = "false"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import skills.qa_automation.checker as checker


URL = os.getenv(
    "QA_DEFAULT_URL",
    "https://mobospace-sandbox.pancaran-group.co.id",
)

MODULE_NAME = "Shipment Details"


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


def open_shipment_details_menu(page, *args, **kwargs):
    """
    Robust opener untuk Shipment Details.

    Dari card debug:
    Shipment Details memiliki anchor:
    /shipmentdetail

    Jadi opener ini:
    1. Coba klik anchor a[href*="/shipmentdetail"]
    2. Kalau gagal, langsung page.goto(origin + "/shipmentdetail")
    3. Validasi halaman detail sudah terbuka.
    """

    def wait_after_click(ms=2500):
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(ms)

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception:
            return ""

    def body_text_lower():
        return get_body_text().lower()

    def current_origin():
        try:
            current = page.url
            parts = current.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def is_wrong_dashboard_page():
        text = body_text_lower()

        return (
            "shipment activity dashboard" in text
            or "pdt vehicle performance" in text
            or (
                "operated" in text
                and "not operated" in text
                and "inactive" in text
            )
        )

    def is_launcher_page():
        text = body_text_lower()

        return (
            "operational dashboard" in text
            and "shipment activity dashboard" in text
            and "mobomap" in text
            and "shipment details" in text
            and "verify activities" in text
        )

    def is_actual_shipment_details_page():
        text = body_text_lower()

        if is_wrong_dashboard_page() or is_launcher_page():
            return False

        actual_markers = [
            "shipment details",
            "on shipment",
            "finished",
            "ordered",
            "shipment no",
            "shipment number",
            "customer",
            "origin",
            "destination",
            "driver",
            "vehicle",
            "rows per page",
            "filter",
            "search",
        ]

        marker_count = sum(1 for marker in actual_markers if marker in text)

        return marker_count >= 2

    # 1. Coba klik anchor exact dari card debug.
    anchor_selectors = [
        "a[href*='/shipmentdetail']",
        "a[href$='shipmentdetail']",
        "#textDec[href*='shipmentdetail']",
    ]

    for selector in anchor_selectors:
        try:
            locator = page.locator(selector).first

            if locator.count() <= 0:
                continue

            locator.scroll_into_view_if_needed(timeout=3000)
            locator.click(timeout=8000, force=True)
            wait_after_click(3000)

            if is_actual_shipment_details_page():
                return True, f"Shipment Details opened via anchor: {selector}"

        except Exception:
            continue

    # 2. Fallback langsung ke route.
    try:
        target_url = current_origin() + "/shipmentdetail"
        page.goto(target_url, wait_until="networkidle", timeout=30000)
        wait_after_click(3000)

        if is_actual_shipment_details_page():
            return True, f"Shipment Details opened via direct route: {target_url}"

    except Exception as exc:
        return False, f"Direct route /shipmentdetail failed: {exc}"

    preview = get_body_text()[:700].replace("\n", " / ")

    return (
        False,
        "Shipment Details route opened but actual detail markers were not detected. "
        f"url={page.url}; "
        f"is_launcher={is_launcher_page()}; "
        f"is_wrong_dashboard={is_wrong_dashboard_page()}; "
        f"preview={preview}"
    )

def open_shipment_details_no_subpage(page, test_cases, preferred_subpage=""):
    """
    Tidak ada subpage khusus.
    Setelah target menu terbuka, langsung discovery halaman.
    """

    try:
        body_text = page.locator("body").inner_text(timeout=5000)
    except Exception as exc:
        body_text = f"FAILED_TO_READ_BODY: {exc}"

    lower = body_text.lower()

    context_found = (
        "shipment details" in lower
        or "on shipment" in lower
        or "finished" in lower
        or "ordered" in lower
        or "shipment" in lower
    )

    checker.add_test_case(
        test_cases,
        scenario="Open Shipment Details page",
        precondition="User is logged in and sidebar menu is visible",
        steps="Open Shipment Details menu",
        expected="Shipment Details page should be opened",
        actual="Shipment Details context found" if context_found else body_text[:500],
        status="PASS" if context_found else "NEED REVIEW",
    )


def validate_shipment_details_discovery_page(page, test_cases, bugs):
    try:
        body_text = page.locator("body").inner_text(timeout=5000)
    except Exception as exc:
        body_text = f"FAILED_TO_READ_BODY: {exc}"

    lower = body_text.lower()

    markers = [
        "shipment details",
        "on shipment",
        "finished",
        "ordered",
        "shipment",
        "driver",
        "vehicle",
        "search",
        "filter",
    ]

    matched = [marker for marker in markers if marker in lower]

    context_found = len(matched) >= 2

    checker.add_test_case(
        test_cases,
        scenario="Discover Shipment Details page context",
        precondition="Shipment Details page is opened",
        steps="Read visible page markers",
        expected="Shipment Details page markers should be discoverable",
        actual=f"Matched markers: {matched}",
        status="PASS" if context_found else "NEED REVIEW",
    )


def main():
    # Monkeypatch hanya untuk script discovery ini.
    checker.open_target_menu = open_shipment_details_menu
    checker.open_uang_makan_driver_subpage = open_shipment_details_no_subpage
    checker.validate_uang_makan_driver_monitoring_page = validate_shipment_details_discovery_page
    checker.validate_uang_makan_driver_page = validate_shipment_details_discovery_page

    result = checker.perform_audit_for_telegram(
        URL,
        MODULE_NAME,
        "smoke",
    )

    print("=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:6000])

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
