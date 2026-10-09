from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_force_inspection_result_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''

# ============================================================
# Inspection Result Validator
# ============================================================

def validate_inspection_result_page(page, test_cases, bugs):
    """
    Hardened validator untuk Inspection Result.

    Scope aman:
    - Tidak klik CHOOSE
    - Tidak approve/reject decision
    - Tidak submit form
    - Tidak update inspection result
    - Hanya validasi page context, status toggle, filter/search, card/list, dan evidence
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

    # 1. Page context
    context_found = (
        "inspection result" in lower
        or "inspection" in lower
    ) and (
        "waiting for decision" in lower
        or "approved" in lower
        or "rejected" in lower
        or "in progress" in lower
        or "inspection info" in lower
        or "inspection type" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result page context",
        precondition="Inspection Result route is opened",
        steps="Check page title and inspection result markers",
        expected="Inspection Result page should be visible",
        actual="Inspection Result context found" if context_found else body_text[:500],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Inspection Result page context not found",
            actual="Inspection Result markers were not visible",
            expected="Inspection Result page should show title, status toggle, or inspection content",
        )

    # 2. Status toggles
    waiting_found = "waiting for decision" in lower
    approved_found = "approved" in lower
    rejected_found = "rejected" in lower
    in_progress_found = "in progress" in lower

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result status toggles",
        precondition="Inspection Result page is opened",
        steps="Check Waiting for Decision, Approved, Rejected, and In Progress toggles",
        expected="All inspection status toggles should be visible",
        actual=(
            f"Waiting for Decision={waiting_found}; "
            f"Approved={approved_found}; "
            f"Rejected={rejected_found}; "
            f"In Progress={in_progress_found}"
        ),
        status="PASS" if waiting_found and approved_found and rejected_found and in_progress_found else "NEED REVIEW",
    )

    # 3. Filter button
    filter_found = (
        "filter" in lower
        or locator_count("button:has-text('FILTER')") > 0
        or locator_count("button:has-text('Filter')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result filter button",
        precondition="Inspection Result page is opened",
        steps="Check FILTER button",
        expected="FILTER button should be visible",
        actual=f"Filter button visible={filter_found}",
        status="PASS" if filter_found else "NEED REVIEW",
    )

    # 4. Search field
    search_found = (
        "search" in lower
        or locator_count(".v-input:has-text('search')") > 0
        or locator_count("input[type='text']") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result search field",
        precondition="Inspection Result page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 5. Inspection list/card/table
    inspection_list_found = (
        locator_count("#scrollOrder") > 0
        or locator_count(".v-data-table__wrapper") > 0
        or locator_count(".v-card") > 0
        or "inspection info" in lower
        or "inspection type" in lower
        or "document no" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result list/card displayed",
        precondition="Inspection Result page is opened",
        steps="Check inspection list/card/table container",
        expected="Inspection result list/card should be visible",
        actual=f"Inspection list/card visible={inspection_list_found}",
        status="PASS" if inspection_list_found else "FAIL",
    )

    if not inspection_list_found:
        add_bug(
            bugs,
            severity="High",
            title="Inspection Result list/card not displayed",
            actual="Inspection list/card container was not visible",
            expected="Inspection Result should show inspection list or valid empty state",
        )

    # 6. Inspection information sections
    section_markers = {
        "Driver / Inspector": [" - ", "driver", "choose"],
        "Company / Customer": ["pt.", "customer"],
        "Proper Status": ["proper", "not proper"],
        "Score": ["score:"],
        "Vehicle": ["vehicle:"],
        "Chassis No": ["chassis no:"],
        "Odometer": ["odometer:"],
        "Last Maintenance": ["last maintenance:"],
        "Location": ["location:"],
        "Inspection Info": ["inspection info:"],
        "Inspection Type": ["inspection type:"],
        "Document No": ["document no:"],
        "Total Duration": ["total duration:"],
        "Idle Duration": ["idle duration:"],
        "Shipment No": ["shipment no:"],
    }

    matched_sections = []
    missing_sections = []

    for section_name, variants in section_markers.items():
        if any(variant in lower for variant in variants):
            matched_sections.append(section_name)
        else:
            missing_sections.append(section_name)

    sections_valid = len(matched_sections) >= 7

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result information sections",
        precondition="Inspection result card/list is visible",
        steps="Check score, vehicle, location, inspection info, document no, duration, and shipment no sections",
        expected=", ".join(section_markers.keys()),
        actual=(
            f"Matched sections={', '.join(matched_sections) if matched_sections else '-'}; "
            f"Missing sections={', '.join(missing_sections) if missing_sections else '-'}"
        ),
        status="PASS" if sections_valid else "NEED REVIEW",
    )

    # 7. Data or empty state
    inspection_card_count = locator_count(".mx-auto.v-card") + locator_count(".v-card")
    table_count = locator_count(".v-data-table__wrapper")
    empty_state_found = (
        "no data available" in lower
        or "tidak ada data" in lower
    )

    data_valid = inspection_card_count > 0 or table_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result data or empty state",
        precondition="Inspection Result page is opened",
        steps="Check inspection cards/table or valid empty state",
        expected="Inspection Result should show inspection data or valid empty state",
        actual=(
            f"inspection_card_count={inspection_card_count}; "
            f"table_count={table_count}; "
            f"empty_state_visible={empty_state_found}"
        ),
        status="PASS" if data_valid else "NEED REVIEW",
    )

    # 8. CHOOSE/action button presence, read-only only
    choose_button_count = locator_count("button:has-text('CHOOSE')")
    generic_button_count = locator_count("button")
    icon_button_count = locator_count(".v-btn--icon")

    add_test_case(
        test_cases,
        scenario="Verify Inspection Result action buttons presence",
        precondition="Inspection result cards are visible",
        steps="Check CHOOSE/action buttons without clicking",
        expected="Action buttons may be available, but automation should not click them",
        actual=(
            f"choose_button_count={choose_button_count}; "
            f"generic_button_count={generic_button_count}; "
            f"icon_button_count={icon_button_count}"
        ),
        status="PASS" if choose_button_count > 0 or icon_button_count > 0 or empty_state_found else "NEED REVIEW",
    )

    # 9. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Inspection Result safe validation mode",
        precondition="Inspection Result page is opened",
        steps="Validate page without clicking CHOOSE, approve, reject, or submit buttons",
        expected="Automation should not update or mutate inspection result data",
        actual="Safe mode: no CHOOSE clicked, no approve/reject action executed, no data mutation executed",
        status="PASS",
    )
'''

text = text.rstrip() + "\n" + validator_code + "\n"
CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
print("Force appended validate_inspection_result_page to checker.py")
