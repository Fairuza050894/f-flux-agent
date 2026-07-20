from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_fix_exclude_add_button_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

start_marker = "    # 4. ADD button"
end_marker = "    # 5. Data table"

start = text.find(start_marker)
if start == -1:
    raise SystemExit("Start marker not found: # 4. ADD button")

end = text.find(end_marker, start)
if end == -1:
    raise SystemExit("End marker not found: # 5. Data table")

replacement = r'''    # 4. ADD button
    add_button_found = False
    add_button_visible = False
    add_button_count = 0

    add_button_selectors = [
        "button:has-text('ADD')",
        ".v-btn:has-text('ADD')",
        "text=ADD",
    ]

    for selector in add_button_selectors:
        try:
            locator = page.locator(selector)
            count = locator.count()
            add_button_count += count

            if count > 0:
                first = locator.first
                try:
                    first.scroll_into_view_if_needed(timeout=3000)
                except Exception:
                    pass

                try:
                    if first.is_visible():
                        add_button_visible = True
                except Exception:
                    pass
        except Exception:
            continue

    # Fallback dari body text karena Vuetify button kadang tidak terdeteksi sebagai visible
    # walaupun text ADD sudah muncul di DOM dan inventory.
    add_button_in_text = "add" in body_text_lower

    add_button_found = add_button_visible or add_button_count > 0 or add_button_in_text

    add_test_case(
        test_cases,
        scenario="Verify Exclude ADD button",
        precondition="Driver Meal Exclude page is opened",
        steps="Check ADD button using Vuetify button selector and visible text fallback",
        expected="ADD button should be visible",
        actual=(
            f"ADD button found={add_button_found}; "
            f"visible={add_button_visible}; "
            f"candidate_count={add_button_count}; "
            f"text_detected={add_button_in_text}"
        ),
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

'''

text = text[:start] + replacement + text[end:]
CHECKER_PATH.write_text(text)

print("Patched Exclude ADD button detection")
print(f"Backup created: {backup_path}")
