from pathlib import Path

path = Path("scripts/discover_shipment_details.py")
text = path.read_text()

start = text.find("def open_shipment_details_menu(")
end = text.find("\ndef open_shipment_details_no_subpage", start)

if start == -1 or end == -1:
    raise SystemExit("Target function block not found")

replacement = r'''def open_shipment_details_menu(page, *args, **kwargs):
    """
    Robust opener untuk Shipment Details.

    Catatan:
    Shipment Details muncul sebagai card di Operational Dashboard,
    bukan langsung sebagai sidebar leaf menu.
    Function ini harus return tuple:
    (menu_opened, menu_text)
    """

    def wait_after_click():
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(2000)

    def body_text_lower():
        try:
            return page.locator("body").inner_text(timeout=5000).lower()
        except Exception:
            return ""

    def is_actual_shipment_details_page():
        text = body_text_lower()

        # Jangan anggap berhasil kalau masih di launcher Operational Dashboard.
        still_launcher = (
            "operational dashboard" in text
            and "shipment activity dashboard" in text
            and "mobomap" in text
            and "verify activities" in text
        )

        actual_markers = [
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

        return marker_count >= 2 and not still_launcher

    # 1. Pastikan area dashboard/operational dashboard terbuka
    for parent_label in [
        "Dashboard",
        "Operational Dashboard",
        "Tracking",
    ]:
        try:
            _click_label(page, parent_label)
            wait_after_click()
        except Exception:
            pass

    # 2. Klik card Shipment Details secara spesifik
    card_selectors = [
        ".homeContainer:has-text('Shipment Details')",
        ".v-card:has-text('Shipment Details')",
        "[class*='homeContainer']:has-text('Shipment Details')",
        "div:has-text('Shipment Details')",
    ]

    for selector in card_selectors:
        try:
            locator = page.locator(selector).first

            if locator.count() <= 0:
                continue

            locator.scroll_into_view_if_needed(timeout=3000)

            try:
                locator.click(timeout=5000, force=True)
            except Exception:
                try:
                    locator.evaluate("(el) => el.click()")
                except Exception:
                    continue

            wait_after_click()

            if is_actual_shipment_details_page():
                return True, f"Shipment Details opened via selector: {selector}"

        except Exception:
            continue

    # 3. Fallback klik text biasa
    labels = [
        "Shipment Details",
        "Shipment Detail",
    ]

    for label in labels:
        if _click_label(page, label):
            wait_after_click()

            if is_actual_shipment_details_page():
                return True, label

    # 4. Kalau masih belum kebuka, tetap return false supaya jelas
    return False, "Shipment Details card found but actual detail page was not loaded"
'''

text = text[:start] + replacement + text[end:]
path.write_text(text)

print("Patched Shipment Details opener to click dashboard card/container")
