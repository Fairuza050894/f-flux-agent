from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_include_exclude_add_form_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

helper_code = r'''
def _qa_make_driver_meal_open_exclude_add_form():
    """
    Open sequence untuk combined suite:
    Driver Meal -> Exclude -> ADD Form

    Scope aman:
    - hanya buka form
    - tidak submit data valid
    - tidak create/update/delete data
    """

    def open_subpage(page, test_cases, preferred_subpage="Monitoring"):
        opened_exclude = False

        for label in ["Exclude", "Pengecualian", "Exception", "Exceptions"]:
            if _qa_click_label(page, label):
                opened_exclude = True
                break

        add_test_case(
            test_cases,
            scenario="Open Driver Meal Exclude subpage",
            precondition="Driver Meal menu group is visible",
            steps="Click Exclude submenu",
            expected="Driver Meal Exclude subpage should be opened",
            actual="Exclude opened" if opened_exclude else "Exclude not opened",
            status="PASS" if opened_exclude else "FAIL",
        )

        if not opened_exclude:
            return

        opened_add = False

        for selector in ["button:has-text('ADD')", ".v-btn:has-text('ADD')", "text=ADD"]:
            try:
                locator = page.locator(selector).first

                if locator.count() <= 0:
                    continue

                locator.scroll_into_view_if_needed(timeout=3000)
                locator.click(timeout=5000)
                page.wait_for_timeout(1500)
                opened_add = True
                break
            except Exception:
                continue

        add_test_case(
            test_cases,
            scenario="Open Exclude ADD form",
            precondition="Driver Meal Exclude page is opened",
            steps="Click ADD button",
            expected="ADD form/dialog should be opened",
            actual="ADD form opened" if opened_add else "ADD form not opened",
            status="PASS" if opened_add else "FAIL",
        )

    return open_subpage

'''

if "def _qa_make_driver_meal_open_exclude_add_form(" not in text:
    marker = "def perform_driver_daily_meal_combined_suite"
    idx = text.find(marker)

    if idx == -1:
        raise SystemExit("perform_driver_daily_meal_combined_suite marker not found")

    text = text[:idx] + helper_code + "\n\n" + text[idx:]
    print("Inserted Exclude ADD Form opener helper")
else:
    print("Exclude ADD Form opener helper already exists")


old_suites = '''    suites = [
        {
            "name": "Monitoring",
            "open": _qa_make_driver_meal_open_subpage("Monitoring", ["Monitoring"]),
            "validator": validate_uang_makan_driver_monitoring_page,
        },
        {
            "name": "Exclude",
            "open": _qa_make_driver_meal_open_subpage("Exclude", ["Exclude", "Pengecualian", "Exception", "Exceptions"]),
            "validator": validate_driver_meal_exclude_page,
        },
        {
            "name": "History / Inquiry",
            "open": _qa_make_driver_meal_open_subpage("History / Inquiry", ["History", "Inquiry", "Riwayat"]),
            "validator": validate_driver_meal_history_page,
        },
    ]

    sub_results = []
'''

new_suites = '''    suites = [
        {
            "name": "Monitoring",
            "open": _qa_make_driver_meal_open_subpage("Monitoring", ["Monitoring"]),
            "validator": validate_uang_makan_driver_monitoring_page,
        },
        {
            "name": "Exclude",
            "open": _qa_make_driver_meal_open_subpage("Exclude", ["Exclude", "Pengecualian", "Exception", "Exceptions"]),
            "validator": validate_driver_meal_exclude_page,
        },
        {
            "name": "Exclude ADD Form",
            "open": _qa_make_driver_meal_open_exclude_add_form(),
            "validator": validate_driver_meal_exclude_add_form_page,
        },
        {
            "name": "History / Inquiry",
            "open": _qa_make_driver_meal_open_subpage("History / Inquiry", ["History", "Inquiry", "Riwayat"]),
            "validator": validate_driver_meal_history_page,
        },
    ]

    sub_results = []
'''

if old_suites in text:
    text = text.replace(old_suites, new_suites)
    print("Updated combined suite list to include Exclude ADD Form")
else:
    print("Exact old suites block not found. Trying fallback insert...")

    if '"name": "Exclude ADD Form"' not in text:
        target = '''        {
            "name": "History / Inquiry",
            "open": _qa_make_driver_meal_open_subpage("History / Inquiry", ["History", "Inquiry", "Riwayat"]),
            "validator": validate_driver_meal_history_page,
        },'''

        insert = '''        {
            "name": "Exclude ADD Form",
            "open": _qa_make_driver_meal_open_exclude_add_form(),
            "validator": validate_driver_meal_exclude_add_form_page,
        },
'''

        if target not in text:
            raise SystemExit("Fallback target History / Inquiry block not found")

        text = text.replace(target, insert + target)
        print("Fallback inserted Exclude ADD Form before History / Inquiry")
    else:
        print("Exclude ADD Form already exists in suite list")


# Dedupe known warning count in combined result because Exclude List and Exclude ADD Form
# can trigger the same DriverExceptionTable.vue Vue warning.
old_warning_block = '''    warnings = []

    for item in sub_results:
        section = _qa_extract_section(item["result"].get("testing_summary", ""), "Warnings / Known Issues:")
        if section and section != "-":
            warnings.append(f"{item['name']}:\\n{section}")

    warning_text = "\\n\\n".join(warnings) if warnings else "-"
'''

new_warning_block = '''    raw_warnings = []

    for item in sub_results:
        section = _qa_extract_section(item["result"].get("testing_summary", ""), "Warnings / Known Issues:")
        if section and section != "-":
            raw_warnings.append(f"{item['name']}:\\n{section}")

    known_vue_warning_found = any(
        "Known Vue warning detected in Driver Meal Exclude" in warning
        or "DriverExceptionTable.vue" in warning
        for warning in raw_warnings
    )

    if known_vue_warning_found:
        warning_text = (
            "Exclude / Exclude ADD Form:\\n"
            "WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude"
        )
        total_counts["warnings"] = 1
    else:
        warning_text = "\\n\\n".join(raw_warnings) if raw_warnings else "-"
'''

if old_warning_block in text:
    text = text.replace(old_warning_block, new_warning_block)
    print("Patched combined warning deduplication")
else:
    print("Warning block not replaced. It may already be patched or has different formatting.")

CHECKER_PATH.write_text(text)

print("Patch completed")
print(f"Backup created: {backup_path}")
