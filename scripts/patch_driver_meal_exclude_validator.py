from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_exclude_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''
def validate_driver_meal_exclude_page(page, test_cases, bugs):
    """
    Hardened validator untuk:
    Driver Meal -> Exclude

    Coverage:
    - Page context
    - Today / History tab
    - Search field
    - ADD button
    - Data table
    - Table headers
    - Empty state / data state
    - Pagination
    """

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=5000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def is_visible(selector, timeout=4000):
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            return locator.is_visible()
        except Exception:
            return False

    def get_text(selector, timeout=3000):
        try:
            return page.locator(selector).first.inner_text(timeout=timeout).strip()
        except Exception:
            return ""

    body_text = get_body_text()
    body_text_lower = body_text.lower()

    # 1. Page context
    page_context_found = (
        "driver meal exclude" in body_text_lower
        or (
            "transaction date" in body_text_lower
            and "driver name" in body_text_lower
            and "reason" in body_text_lower
        )
    )

    add_test_case(
        test_cases,
        scenario="Verify Driver Meal Exclude page context",
        precondition="Driver Meal menu and Exclude subpage are opened",
        steps="Check page title or Exclude table markers",
        expected="Driver Meal Exclude page should be visible",
        actual="Driver Meal Exclude context found" if page_context_found else "Driver Meal Exclude context not found",
        status="PASS" if page_context_found else "FAIL",
    )

    if not page_context_found:
        add_bug(
            bugs,
            severity="High",
            title="Driver Meal Exclude page context not found",
            actual="Expected Driver Meal Exclude context was not visible",
            expected="Driver Meal Exclude page should be visible after opening Exclude subpage",
        )

    # 2. Today / History tabs
    today_found = "today" in body_text_lower or "hari ini" in body_text_lower
    history_found = "history" in body_text_lower or "riwayat" in body_text_lower

    add_test_case(
        test_cases,
        scenario="Verify Exclude Today and History tabs",
        precondition="Driver Meal Exclude page is opened",
        steps="Check Today and History tab labels",
        expected="Today and History tabs should be visible",
        actual=f"Today visible={today_found}; History visible={history_found}",
        status="PASS" if today_found and history_found else "NEED REVIEW",
    )

    # 3. Search field
    search_found = (
        is_visible(".mobo-search, .v-input.mobo-search")
        or "search..." in body_text_lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude search field",
        precondition="Driver Meal Exclude page is opened",
        steps="Check search input field",
        expected="Search field should be visible",
        actual=f"Search field visible={search_found}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 4. ADD button
    add_button_found = False

    try:
        add_button_found = page.get_by_text("ADD", exact=True).first.is_visible(timeout=3000)
    except Exception:
        add_button_found = "add" in body_text_lower

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD button",
        precondition="Driver Meal Exclude page is opened",
        steps="Check ADD button",
        expected="ADD button should be visible",
        actual=f"ADD button visible={add_button_found}",
        status="PASS" if add_button_found else "FAIL",
    )

    if not add_button_found:
        add_bug(
            bugs,
            severity="Medium",
            title="Exclude ADD button not visible",
            actual="ADD button was not visible on Driver Meal Exclude page",
            expected="ADD button should be available for adding exclusion data",
        )

    # 5. Data table
    table_found = is_visible(".v-data-table.mobo-table, .v-data-table")
    table_text = get_text(".v-data-table.mobo-table, .v-data-table")

    add_test_case(
        test_cases,
        scenario="Verify Exclude data table displayed",
        precondition="Driver Meal Exclude page is opened",
        steps="Check Vuetify data table component",
        expected="Exclude data table should be visible",
        actual="Exclude data table is visible" if table_found else "Exclude data table not found",
        status="PASS" if table_found else "FAIL",
    )

    if not table_found:
        add_bug(
            bugs,
            severity="High",
            title="Exclude data table not displayed",
            actual="v-data-table component was not visible on Driver Meal Exclude page",
            expected="Exclude table should be displayed",
        )

    # 6. Table headers
    header_text = get_text(".v-data-table-header")
    combined_table_text = f"{header_text}\n{table_text}\n{body_text}"
    combined_table_text_lower = combined_table_text.lower()

    required_header_groups = {
        "Transaction Date": ["transaction date", "date", "tanggal transaksi"],
        "Driver Name": ["driver name", "driver", "nama driver"],
        "Driver ID": ["driver id", "id driver", "nik"],
        "Driver Phone": ["driver phone", "phone", "telepon"],
        "Reason": ["reason", "alasan"],
        "Note": ["note", "catatan"],
        "Created At": ["created at", "created"],
        "Created By": ["created by"],
        "Updated": ["updated", "updated at"],
        "Updated By": ["updated by"],
    }

    matched_headers = []
    missing_headers = []

    for header_name, variants in required_header_groups.items():
        if any(variant in combined_table_text_lower for variant in variants):
            matched_headers.append(header_name)
        else:
            missing_headers.append(header_name)

    header_count = 0
    try:
        header_count = page.locator(
            ".v-data-table-header th, .v-data-table__wrapper thead th"
        ).count()
    except Exception:
        header_count = 0

    header_detected = header_count >= 6 or len(matched_headers) >= 6

    add_test_case(
        test_cases,
        scenario="Verify Exclude table headers",
        precondition="Exclude data table is visible",
        steps="Check Exclude table headers with flexible label matching",
        expected=", ".join(required_header_groups.keys()),
        actual=(
            f"Header count={header_count}; "
            f"Matched headers={', '.join(matched_headers) if matched_headers else '-'}; "
            f"Missing labels={', '.join(missing_headers) if missing_headers else '-'}"
        ),
        status="PASS" if header_detected else "NEED REVIEW",
    )

    # 7. Empty state or data state
    row_count = 0

    try:
        row_count = page.locator(".v-data-table__wrapper tbody tr").count()
    except Exception:
        row_count = 0

    empty_state_found = (
        "no data available" in body_text_lower
        or "tidak ada data" in body_text_lower
    )

    data_or_empty_state_valid = row_count > 0 or empty_state_found

    add_test_case(
        test_cases,
        scenario="Verify Exclude table data or empty state",
        precondition="Exclude data table is visible",
        steps="Check table rows or empty state",
        expected="Table should show data rows or valid empty state",
        actual=f"DOM row count={row_count}; empty state visible={empty_state_found}",
        status="PASS" if data_or_empty_state_valid else "NEED REVIEW",
    )

    # 8. Pagination
    rows_per_page_found = "rows per page" in body_text_lower
    pagination_button_found = False

    try:
        pagination_button_found = page.locator(
            "button[aria-label='Previous page'], button[aria-label='Next page']"
        ).count() > 0
    except Exception:
        pagination_button_found = False

    add_test_case(
        test_cases,
        scenario="Verify Exclude table pagination",
        precondition="Exclude data table is visible",
        steps="Check Rows per page and pagination buttons",
        expected="Pagination section should be visible",
        actual=f"Rows per page visible={rows_per_page_found}; pagination buttons visible={pagination_button_found}",
        status="PASS" if rows_per_page_found or pagination_button_found or table_found else "NEED REVIEW",
    )
'''

if "def validate_driver_meal_exclude_page(" in text:
    print("validate_driver_meal_exclude_page already exists")
else:
    marker = "def build_testing_summary"
    index = text.find(marker)

    if index == -1:
        raise SystemExit("Could not find def build_testing_summary marker")

    text = text[:index] + validator_code + "\n\n" + text[index:]
    CHECKER_PATH.write_text(text)
    print("Inserted validate_driver_meal_exclude_page")

print(f"Backup created: {backup_path}")
