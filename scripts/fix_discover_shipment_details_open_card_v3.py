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
'''

text = text[:start] + replacement + text[end:]
path.write_text(text)

print("Patched Shipment Details opener v3 using /shipmentdetail href")
