from pathlib import Path

path = Path("scripts/discover_shipment_details.py")
text = path.read_text(encoding="utf-8")

start = text.find("def open_shipment_details_menu(")
end = text.find("\ndef open_shipment_details_no_subpage", start)

if start == -1 or end == -1:
    raise SystemExit("Target function block not found")

replacement = r'''def open_shipment_details_menu(page, *args, **kwargs):
    """
    Robust opener untuk Shipment Details.

    Flow yang benar:
    1. Klik Shipment Activity di sidebar
    2. Tunggu launcher Operational Dashboard muncul
    3. Klik card Shipment Details
    4. Pastikan sudah masuk halaman detail, bukan Main Dashboard
    """

    def wait_after_click(ms=2000):
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

    def is_launcher_page():
        text = body_text_lower()
        return (
            "operational dashboard" in text
            and "shipment details" in text
            and "verify activities" in text
            and "mobomap" in text
        )

    def is_main_dashboard_page():
        text = body_text_lower()
        return (
            "pdt vehicle performance" in text
            or "operated" in text and "not operated" in text and "inactive" in text
        )

    def is_actual_shipment_details_page():
        text = body_text_lower()

        if is_launcher_page() or is_main_dashboard_page():
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

    # 1. Jangan klik Dashboard karena itu membuka PDT Vehicle Performance.
    #    Klik Shipment Activity untuk membuka launcher operational cards.
    shipment_activity_clicked = False

    for label in [
        "Shipment Activity",
        "Operational Dashboard",
    ]:
        try:
            if _click_label(page, label):
                shipment_activity_clicked = True
                wait_after_click(2500)
                break
        except Exception:
            pass

    # 2. Kalau belum masuk launcher, coba cari Shipment Activity dari sidebar secara spesifik.
    if not is_launcher_page():
        try:
            sidebar = page.locator(".v-navigation-drawer, .v-navigation-drawer__content, .v-list, nav, aside").first
            item = sidebar.get_by_text("Shipment Activity", exact=True).first

            if item.count() > 0:
                item.scroll_into_view_if_needed(timeout=3000)
                item.click(timeout=5000, force=True)
                shipment_activity_clicked = True
                wait_after_click(2500)
        except Exception:
            pass

    # 3. Klik card Shipment Details.
    card_clicked = False

    card_selectors = [
        ".homeContainer:has-text('Shipment Details')",
        ".v-card:has-text('Shipment Details')",
        "[class*='homeContainer']:has-text('Shipment Details')",
    ]

    for selector in card_selectors:
        try:
            locator = page.locator(selector).last

            if locator.count() <= 0:
                continue

            locator.scroll_into_view_if_needed(timeout=3000)

            try:
                locator.click(timeout=5000, force=True)
            except Exception:
                locator.evaluate("(el) => el.click()")

            card_clicked = True
            wait_after_click(3000)

            if is_actual_shipment_details_page():
                return True, f"Shipment Details opened via card selector: {selector}"

        except Exception:
            continue

    # 4. Fallback: klik element dengan text exact lalu click parent card via JS.
    try:
        clicked = page.evaluate("""
        () => {
            const candidates = Array.from(document.querySelectorAll('.homeContainer, .v-card, [class*="homeContainer"], div'));
            const target = candidates.find((el) => {
                const text = (el.innerText || '').trim();
                return text === 'Shipment Details';
            });

            if (target) {
                target.click();
                return true;
            }

            const textNode = Array.from(document.querySelectorAll('*')).find((el) => {
                const text = (el.innerText || '').trim();
                return text === 'Shipment Details';
            });

            if (textNode) {
                const parent = textNode.closest('.homeContainer, .v-card, [class*="homeContainer"]') || textNode;
                parent.click();
                return true;
            }

            return false;
        }
        """)

        if clicked:
            card_clicked = True
            wait_after_click(3000)

            if is_actual_shipment_details_page():
                return True, "Shipment Details opened via JS fallback"
    except Exception:
        pass

    # 5. Fallback terakhir: text locator.
    try:
        locator = page.get_by_text("Shipment Details", exact=True).last

        if locator.count() > 0:
            locator.scroll_into_view_if_needed(timeout=3000)
            locator.click(timeout=5000, force=True)
            card_clicked = True
            wait_after_click(3000)

            if is_actual_shipment_details_page():
                return True, "Shipment Details opened via text fallback"
    except Exception:
        pass

    current_preview = get_body_text()[:500].replace("\n", " / ")

    return (
        False,
        "Shipment Details detail page was not loaded. "
        f"shipment_activity_clicked={shipment_activity_clicked}; "
        f"card_clicked={card_clicked}; "
        f"is_launcher={is_launcher_page()}; "
        f"is_main_dashboard={is_main_dashboard_page()}; "
        f"current_preview={current_preview}"
    )
'''

text = text[:start] + replacement + text[end:]
path.write_text(text, encoding="utf-8")

print("Patched Shipment Details opener v2")
