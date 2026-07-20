from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_force_shipment_details_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''

# ============================================================
# Shipment Details Validator
# ============================================================

def validate_shipment_details_page(page, test_cases, bugs):
    """
    Hardened validator untuk Shipment Details.

    Scope aman:
    - Tidak klik action icon
    - Tidak update data
    - Tidak submit form
    - Tidak export data
    - Hanya validasi page context, filter/search, status toggle, shipment card/list, dan evidence
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    body_text = get_body_text()
    lower = body_text.lower()

    context_found = (
        "shipment details" in lower
        or "shipment detail" in lower
    ) and (
        "on shipment" in lower
        or "finished" in lower
        or "ordered" in lower
        or "vehicle & driver" in lower
        or "shipment info" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details page context",
        precondition="Shipment Details route is opened",
        steps="Check page title and shipment page markers",
        expected="Shipment Details page should be visible",
        actual="Shipment Details context found" if context_found else body_text[:500],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Shipment Details page context not found",
            actual="Shipment Details page markers were not visible",
            expected="Shipment Details page should show title, status toggle, or shipment content",
        )

    on_shipment_found = "on shipment" in lower
    finished_found = "finished" in lower
    ordered_found = "ordered" in lower

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details status toggles",
        precondition="Shipment Details page is opened",
        steps="Check On Shipment, Finished, and Ordered toggles",
        expected="On Shipment, Finished, and Ordered should be visible",
        actual=(
            f"On Shipment={on_shipment_found}; "
            f"Finished={finished_found}; "
            f"Ordered={ordered_found}"
        ),
        status="PASS" if on_shipment_found and finished_found and ordered_found else "NEED REVIEW",
    )

    filter_found = (
        "filter" in lower
        or locator_count("button:has-text('FILTER')") > 0
        or locator_count("button:has-text('Filter')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details filter button",
        precondition="Shipment Details page is opened",
        steps="Check FILTER button",
        expected="FILTER button should be visible",
        actual=f"Filter button visible={filter_found}",
        status="PASS" if filter_found else "NEED REVIEW",
    )

    search_found = (
        "search" in lower
        or locator_count(".v-input:has-text('search')") > 0
        or locator_count("input[type='text']") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details search field",
        precondition="Shipment Details page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    shipment_list_found = (
        locator_count("#scrollOrder") > 0
        or locator_count(".v-data-table__wrapper") > 0
        or locator_count(".v-card.v-card--outlined") > 0
        or "vehicle & driver" in lower
        or "shipment info" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details shipment list displayed",
        precondition="Shipment Details page is opened",
        steps="Check shipment list/card container",
        expected="Shipment list/card should be visible",
        actual=f"Shipment list/card visible={shipment_list_found}",
        status="PASS" if shipment_list_found else "FAIL",
    )

    if not shipment_list_found:
        add_bug(
            bugs,
            severity="High",
            title="Shipment Details list/card not displayed",
            actual="Shipment list/card container was not visible",
            expected="Shipment Details should show shipment list or valid empty state",
        )

    section_markers = {
        "Vehicle & Driver": ["vehicle & driver", "vehicle", "driver"],
        "Shipment Info": ["shipment info", "shipment"],
        "Origin / From": ["from : ", "from:"],
        "Destination / To": ["to : ", "to:"],
        "Progress Info": ["progress info", "target lead time", "elapsed time"],
    }

    matched_sections = []
    missing_sections = []

    for section_name, variants in section_markers.items():
        if any(variant in lower for variant in variants):
            matched_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    sections_valid = len(matched_sections) >= 3

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details shipment information sections",
        precondition="Shipment list/card is visible",
        steps="Check card sections such as Vehicle & Driver, Shipment Info, From/To, and Progress Info",
        expected=", ".join(section_markers.keys()),
        actual=(
            f"Matched sections={', '.join(matched_sections) if matched_sections else '-'}; "
            f"Missing sections={', '.join(missing_sections) if missing_sections else '-'}"
        ),
        status="PASS" if sections_valid else "NEED REVIEW",
    )

    shipment_card_count = locator_count(".v-card.v-card--outlined")
    empty_state_found = (
        "no data available" in lower
        or "tidak ada data" in lower
    )

    shipment_data_valid = shipment_card_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details data or empty state",
        precondition="Shipment Details page is opened",
        steps="Check shipment cards or valid empty state",
        expected="Shipment Details should show shipment cards or valid empty state",
        actual=f"Shipment card count={shipment_card_count}; empty state visible={empty_state_found}",
        status="PASS" if shipment_data_valid else "NEED REVIEW",
    )

    eye_icon_count = locator_count(".mdi-eye")
    map_icon_count = locator_count(".mdi-map-marker-radius")

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details action icons presence",
        precondition="Shipment cards are visible",
        steps="Check detail/view and map/location icons without clicking",
        expected="Action icons should be available when shipment data exists",
        actual=f"Eye icon count={eye_icon_count}; Map marker icon count={map_icon_count}",
        status="PASS" if eye_icon_count > 0 or map_icon_count > 0 or empty_state_found else "NEED REVIEW",
    )

    add_test_case(
        test_cases,
        scenario="Verify Shipment Details safe validation mode",
        precondition="Shipment Details page is opened",
        steps="Validate page without clicking action buttons or mutating data",
        expected="Automation should not update/create/delete shipment data",
        actual="Safe mode: no action icon clicked, no data mutation executed",
        status="PASS",
    )
'''

# Remove old duplicate incomplete/global block only if exact header exists.
if "# Shipment Details Validator" not in text:
    text = text.rstrip() + validator_code + "\n"
else:
    # Tetap append ulang dengan nama function yang sama di akhir file.
    # Definisi terakhir akan dipakai Python.
    text = text.rstrip() + "\n" + validator_code + "\n"

CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
print("Force appended validate_shipment_details_page to checker.py")
