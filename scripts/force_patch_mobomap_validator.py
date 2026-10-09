from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_force_mobomap_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''

# ============================================================
# MoboMap Validator
# ============================================================

def validate_mobomap_page(page, test_cases, bugs):
    """
    Hardened validator untuk MoboMap.

    Scope aman:
    - Tidak klik marker
    - Tidak klik eye/link/star action
    - Tidak update tracking
    - Tidak share link
    - Tidak mutate data
    - Hanya validasi map, filter/toggle, search, vehicle list, dan controls
    """

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

    # 1. Page / map context
    map_selector_counts = {
        ".gm-style": locator_count(".gm-style"),
        ".leaflet-container": locator_count(".leaflet-container"),
        "[class*='map']": locator_count("[class*='map']"),
        "[id*='map']": locator_count("[id*='map']"),
        "canvas": locator_count("canvas"),
    }

    google_map_text_found = (
        "map data" in lower
        or "keyboard shortcuts" in lower
        or "report a map error" in lower
        or "google" in lower
        or "satellite" in lower
    )

    map_context_found = any(count > 0 for count in map_selector_counts.values()) or google_map_text_found

    add_test_case(
        test_cases,
        scenario="Verify MoboMap map context",
        precondition="MoboMap route is opened",
        steps="Check map container and Google Map context",
        expected="Map container should be visible",
        actual=f"Map selector counts={map_selector_counts}; google_map_text_found={google_map_text_found}",
        status="PASS" if map_context_found else "FAIL",
    )

    if not map_context_found:
        add_bug(
            bugs,
            severity="High",
            title="MoboMap map container not found",
            actual="Map container or Google Map context was not detected",
            expected="MoboMap should display map container",
        )

    # 2. Sidebar / vehicle context
    sidebar_context_found = (
        "vehicle" in lower
        or "driver" in lower
        or "phone number" in lower
        or "vehicle type" in lower
        or locator_count("#scrollTable") > 0
        or locator_count(".tbldrw") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle sidebar/list context",
        precondition="MoboMap page is opened",
        steps="Check vehicle list/sidebar markers",
        expected="Vehicle sidebar/list should be visible",
        actual=f"Vehicle/sidebar context visible={sidebar_context_found}",
        status="PASS" if sidebar_context_found else "NEED REVIEW",
    )

    # 3. Vehicle status toggles
    on_job_found = "on job" in lower
    available_found = "available" in lower
    maintained_found = "maintained" in lower

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle status toggles",
        precondition="MoboMap page is opened",
        steps="Check On Job, Available, and Maintained toggles",
        expected="On Job, Available, and Maintained toggles should be visible",
        actual=(
            f"On Job={on_job_found}; "
            f"Available={available_found}; "
            f"Maintained={maintained_found}"
        ),
        status="PASS" if on_job_found and available_found and maintained_found else "NEED REVIEW",
    )

    # 4. Search vehicle / location inputs
    search_input_count = (
        locator_count("input[placeholder='Search']")
        + locator_count("input[placeholder*='Search']")
        + locator_count(".searchVehicle")
        + locator_count("input.pac-target-input")
    )

    location_input_found = (
        locator_count("input[placeholder='Enter a location']") > 0
        or "enter a location" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify MoboMap search inputs",
        precondition="MoboMap page is opened",
        steps="Check vehicle search and location search inputs",
        expected="Search input and location input should be available",
        actual=f"search_input_count={search_input_count}; location_input_found={location_input_found}",
        status="PASS" if search_input_count > 0 or location_input_found else "NEED REVIEW",
    )

    # 5. Vehicle list table
    vehicle_table_count = (
        locator_count("#scrollTable")
        + locator_count(".v-data-table.tbldrw")
        + locator_count(".v-data-table__wrapper")
    )

    vehicle_data_markers = {
        "Driver": "driver" in lower,
        "Phone Number": "phone number" in lower,
        "Vehicle Type": "vehicle type" in lower,
        "Site": "site" in lower,
        "Customer": "customer" in lower,
    }

    vehicle_data_found = vehicle_table_count > 0 or any(vehicle_data_markers.values())

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle list data",
        precondition="MoboMap vehicle sidebar/list is visible",
        steps="Check vehicle list/table and key data fields",
        expected="Vehicle list should show driver, phone, vehicle type, site, or customer data",
        actual=f"vehicle_table_count={vehicle_table_count}; markers={vehicle_data_markers}",
        status="PASS" if vehicle_data_found else "NEED REVIEW",
    )

    # 6. Map controls
    map_control_counts = {
        "Map": locator_count("button[aria-label='Show street map']"),
        "Satellite": locator_count("button[aria-label='Show satellite imagery']"),
        "Zoom In": locator_count("button[aria-label='Zoom in']"),
        "Zoom Out": locator_count("button[aria-label='Zoom out']"),
        "Fullscreen": locator_count("button[aria-label='Toggle fullscreen view']"),
        "Keyboard Shortcuts": locator_count("button[aria-label='Keyboard shortcuts']"),
    }

    map_controls_found = (
        map_control_counts["Map"] > 0
        or map_control_counts["Satellite"] > 0
        or map_control_counts["Zoom In"] > 0
        or map_control_counts["Zoom Out"] > 0
        or "map" in lower and "satellite" in lower
        or "zoom in" in lower
        or "zoom out" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify MoboMap map controls",
        precondition="Map is visible",
        steps="Check Map/Satellite and zoom controls",
        expected="Map controls should be visible",
        actual=f"map_control_counts={map_control_counts}",
        status="PASS" if map_controls_found else "NEED REVIEW",
    )

    # 7. Vehicle action icons, read-only check only
    eye_icon_count = locator_count(".mdi-eye")
    link_icon_count = locator_count(".mdi-link-variant")
    star_icon_count = locator_count(".material-icons:text('star')")

    # Playwright CSS tidak selalu support :text untuk class material-icons di semua versi,
    # jadi fallback dari visible text.
    if star_icon_count == 0 and "star" in lower:
        star_icon_count = 1

    add_test_case(
        test_cases,
        scenario="Verify MoboMap vehicle action icons presence",
        precondition="Vehicle list is visible",
        steps="Check eye/link/star icons without clicking",
        expected="Vehicle action icons should be present when data exists",
        actual=f"eye_icon_count={eye_icon_count}; link_icon_count={link_icon_count}; star_icon_count={star_icon_count}",
        status="PASS" if eye_icon_count > 0 or link_icon_count > 0 or star_icon_count > 0 else "NEED REVIEW",
    )

    # 8. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify MoboMap safe validation mode",
        precondition="MoboMap page is opened",
        steps="Validate MoboMap without clicking marker/action/share controls",
        expected="Automation should not update, share, or mutate tracking data",
        actual="Safe mode: no marker clicked, no action icon clicked, no share/update executed",
        status="PASS",
    )
'''

text = text.rstrip() + "\n" + validator_code + "\n"
CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
print("Force appended validate_mobomap_page to checker.py")
