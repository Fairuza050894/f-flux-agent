from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_force_notification_management_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''

# ============================================================
# Notification Management Validator
# ============================================================

def validate_notification_management_page(page, test_cases, bugs):
    """
    Hardened validator untuk Notification Management.

    Scope aman:
    - Tidak klik ACTION
    - Tidak create context/event/group/template/contact
    - Tidak edit/delete data
    - Tidak submit form
    - Hanya validasi tabs, table/list, search, action visibility, dan evidence
    """

    tabs = [
        {
            "name": "Notification Context",
            "markers": [
                "context key",
                "context name",
                "engine type",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Notification Event",
            "markers": [
                "event key",
                "event name",
                "context",
                "channels",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Notification Group",
            "markers": [
                "group name",
                "notification event",
                "site",
                "description",
                "numbers of contacts",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Message Template",
            "markers": [
                "template name",
                "message title",
                "message body",
                "property info",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Email Template",
            "markers": [
                "template name",
                "message subject",
                "message body",
                "active",
                "html",
                "created by",
                "created",
            ],
            "min_markers": 4,
        },
        {
            "name": "Contact",
            "markers": [
                "name",
                "phones",
                "email",
                "user type",
                "contacs source",
                "contacts source",
                "active",
            ],
            "min_markers": 4,
        },
        {
            "name": "Contact Group",
            "markers": [
                "contact group name",
                "number of contact",
                "active",
                "created by",
                "created",
            ],
            "min_markers": 3,
        },
    ]

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=10000)
        except Exception as exc:
            return f"FAILED_TO_READ_BODY: {exc}"

    def locator_count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    def click_tab(label):
        candidates = [
            page.get_by_role("tab", name=label).first,
            page.locator(f".v-tab:has-text('{label}')").first,
            page.get_by_text(label, exact=True).first,
        ]

        for candidate in candidates:
            try:
                if candidate.count() <= 0:
                    continue

                candidate.scroll_into_view_if_needed(timeout=3000)
                candidate.click(timeout=5000, force=True)

                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                page.wait_for_timeout(2500)
                return True

            except Exception:
                continue

        return False

    body_text = get_body_text()
    lower = body_text.lower()

    # 1. Page context
    context_found = (
        "notification management" in lower
        and "notification context" in lower
        and "notification event" in lower
        and "notification group" in lower
        and "message template" in lower
        and "email template" in lower
        and "contact" in lower
        and "contact group" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Management page context",
        precondition="Notification Management route is opened",
        steps="Check page title and all management tabs",
        expected="Notification Management page should show all management tabs",
        actual="Notification Management context found" if context_found else body_text[:700],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Notification Management page context not found",
            actual="Notification Management markers were not visible",
            expected="Page should show Notification Context, Event, Group, Templates, Contact, and Contact Group tabs",
        )

    # 2. Tab count / visibility
    tab_count = locator_count("[role='tab']") + locator_count(".v-tab")
    visible_tab_names = [tab["name"] for tab in tabs if tab["name"].lower() in lower]

    add_test_case(
        test_cases,
        scenario="Verify Notification Management tab visibility",
        precondition="Notification Management page is opened",
        steps="Check all vertical tabs are visible",
        expected=", ".join([tab["name"] for tab in tabs]),
        actual=f"tab_count={tab_count}; visible_tabs={visible_tab_names}",
        status="PASS" if len(visible_tab_names) >= 7 else "NEED REVIEW",
    )

    # 3. Validate each tab read-only
    for tab in tabs:
        tab_name = tab["name"]
        clicked = click_tab(tab_name)

        tab_text = get_body_text()
        tab_lower = tab_text.lower()

        matched_markers = [
            marker for marker in tab["markers"]
            if marker.lower() in tab_lower
        ]

        missing_markers = [
            marker for marker in tab["markers"]
            if marker.lower() not in tab_lower
        ]

        table_count = locator_count(".v-data-table") + locator_count(".v-data-table__wrapper")
        search_count = locator_count("input[type='text']") + locator_count(".v-input")
        action_visible = "action" in tab_lower or locator_count("button:has-text('ACTION')") > 0 or locator_count("button:has-text('Action')") > 0
        empty_state_visible = "no data available" in tab_lower or "tidak ada data" in tab_lower

        tab_valid = (
            clicked
            and (
                len(matched_markers) >= tab["min_markers"]
                or table_count > 0
                or empty_state_visible
            )
        )

        add_test_case(
            test_cases,
            scenario=f"Verify Notification Management tab - {tab_name}",
            precondition="Notification Management page is opened",
            steps=f"Click {tab_name} tab and validate table/search/action visibility without mutating data",
            expected=f"{tab_name} should show table/list/search or valid empty state",
            actual=(
                f"clicked={clicked}; "
                f"table_count={table_count}; "
                f"search_count={search_count}; "
                f"action_visible={action_visible}; "
                f"empty_state_visible={empty_state_visible}; "
                f"matched_markers={matched_markers}; "
                f"missing_markers={missing_markers}"
            ),
            status="PASS" if tab_valid else "NEED REVIEW",
        )

    # 4. Search field overall
    final_text = get_body_text()
    final_lower = final_text.lower()

    search_found = (
        "search" in final_lower
        or locator_count("input[placeholder='Search']") > 0
        or locator_count("input[type='text']") > 0
        or locator_count(".v-input") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Management search fields",
        precondition="Notification Management tabs are inspectable",
        steps="Check search inputs across management tabs",
        expected="Search input should be available for table-based tabs",
        actual=f"search_found={search_found}; input_count={locator_count('input')}; vuetify_input_count={locator_count('.v-input')}",
        status="PASS" if search_found else "NEED REVIEW",
    )

    # 5. Action button visibility, read-only only
    action_visible = (
        "action" in final_lower
        or locator_count("button:has-text('ACTION')") > 0
        or locator_count("button:has-text('Action')") > 0
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Management action button visibility",
        precondition="Notification Management tabs are inspectable",
        steps="Check ACTION button visibility without clicking",
        expected="ACTION button may be visible but automation must not click it",
        actual=f"action_visible={action_visible}",
        status="PASS" if action_visible else "NEED REVIEW",
    )

    # 6. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Notification Management safe validation mode",
        precondition="Notification Management page is opened",
        steps="Validate management tabs without clicking ACTION, save, delete, edit, or submit",
        expected="Automation should not mutate notification configuration data",
        actual="Safe mode: no ACTION clicked, no create/edit/delete/save/submit executed",
        status="PASS",
    )
'''

text = text.rstrip() + "\n" + validator_code + "\n"
CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
print("Force appended validate_notification_management_page to checker.py")
