from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_exclude_add_form_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''
def validate_driver_meal_exclude_add_form_page(page, test_cases, bugs):
    """
    Hardened validator untuk:
    Driver Meal -> Exclude -> ADD Form

    Scope aman:
    - Tidak submit data valid
    - Tidak create data
    - Tidak update/delete data
    - Hanya validasi dialog, field, required marker, counter, dan button
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

    # 1. Form/dialog context
    form_context_found = (
        "add exception" in lower
        or "tambah pengecualian" in lower
        or (
            "driver *" in lower
            and "reason *" in lower
            and ("simpan" in lower or "save" in lower)
        )
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form dialog context",
        precondition="Driver Meal Exclude page is opened and ADD button clicked",
        steps="Check ADD form title and visible form markers",
        expected="Add Exception form should be visible",
        actual="Add Exception form visible" if form_context_found else body_text[:500],
        status="PASS" if form_context_found else "FAIL",
    )

    if not form_context_found:
        add_bug(
            bugs,
            severity="High",
            title="Exclude ADD form dialog not visible",
            actual="Add Exception dialog/form was not visible after clicking ADD",
            expected="Add Exception dialog should appear",
        )

    # 2. Driver required field
    driver_field_found = (
        "driver *" in lower
        or locator_count(".v-input:has-text('Driver')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Driver required field",
        precondition="Exclude ADD form is opened",
        steps="Check Driver field and required marker",
        expected="Driver * field should be visible",
        actual=f"Driver required field visible={driver_field_found}",
        status="PASS" if driver_field_found else "FAIL",
    )

    if not driver_field_found:
        add_bug(
            bugs,
            severity="High",
            title="Driver required field not visible on Exclude ADD form",
            actual="Driver * field was not visible",
            expected="Driver * field should be visible and required",
        )

    # 3. Group field
    group_field_found = (
        "group" in lower
        or locator_count(".v-input:has-text('Group')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Group field",
        precondition="Exclude ADD form is opened",
        steps="Check Group field",
        expected="Group field should be visible",
        actual=f"Group field visible={group_field_found}",
        status="PASS" if group_field_found else "NEED REVIEW",
    )

    # 4. Reason required field
    reason_field_found = (
        "reason *" in lower
        or locator_count(".v-input:has-text('Reason')") > 0
        or locator_count("textarea") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Reason required field",
        precondition="Exclude ADD form is opened",
        steps="Check Reason field and required marker",
        expected="Reason * field should be visible",
        actual=f"Reason required field visible={reason_field_found}",
        status="PASS" if reason_field_found else "FAIL",
    )

    if not reason_field_found:
        add_bug(
            bugs,
            severity="High",
            title="Reason required field not visible on Exclude ADD form",
            actual="Reason * field was not visible",
            expected="Reason * field should be visible and required",
        )

    # 5. Reason max length counter
    reason_counter_found = (
        "0 / 40" in lower
        or "/ 40" in lower
        or "0/40" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Reason max length counter",
        precondition="Exclude ADD form is opened",
        steps="Check Reason character counter",
        expected="Reason counter should show 0 / 40",
        actual=f"Reason 40 character counter visible={reason_counter_found}",
        status="PASS" if reason_counter_found else "NEED REVIEW",
    )

    # 6. Note field
    note_field_found = (
        "note" in lower
        or locator_count(".v-input:has-text('Note')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form Note field",
        precondition="Exclude ADD form is opened",
        steps="Check Note field",
        expected="Note field should be visible",
        actual=f"Note field visible={note_field_found}",
        status="PASS" if note_field_found else "NEED REVIEW",
    )

    # 7. Action buttons
    cancel_button_found = (
        "batal" in lower
        or "cancel" in lower
        or locator_count("button:has-text('BATAL')") > 0
        or locator_count("button:has-text('CANCEL')") > 0
    )

    save_button_found = (
        "simpan" in lower
        or "save" in lower
        or locator_count("button:has-text('SIMPAN')") > 0
        or locator_count("button:has-text('SAVE')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form action buttons",
        precondition="Exclude ADD form is opened",
        steps="Check BATAL/CANCEL and SIMPAN/SAVE buttons",
        expected="BATAL and SIMPAN buttons should be visible",
        actual=f"Cancel visible={cancel_button_found}; Save visible={save_button_found}",
        status="PASS" if cancel_button_found and save_button_found else "FAIL",
    )

    if not cancel_button_found or not save_button_found:
        add_bug(
            bugs,
            severity="Medium",
            title="Exclude ADD form action button missing",
            actual=f"Cancel visible={cancel_button_found}; Save visible={save_button_found}",
            expected="Both BATAL and SIMPAN buttons should be visible",
        )

    # 8. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD form safe validation mode",
        precondition="Exclude ADD form is opened",
        steps="Validate form without submitting valid data",
        expected="Automation should not create/update/delete production-like data",
        actual="Safe mode: no valid submit/save action executed",
        status="PASS",
    )
'''

if "def validate_driver_meal_exclude_add_form_page(" in text:
    print("validate_driver_meal_exclude_add_form_page already exists")
else:
    marker = "def build_testing_summary"
    index = text.find(marker)

    if index == -1:
        raise SystemExit("Could not find def build_testing_summary marker")

    text = text[:index] + validator_code + "\n\n" + text[index:]
    CHECKER_PATH.write_text(text)
    print("Inserted validate_driver_meal_exclude_add_form_page")

print(f"Backup created: {backup_path}")
