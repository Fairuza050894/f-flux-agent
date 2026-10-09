from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_force_notification_messages_validator_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

validator_code = r'''

# ============================================================
# Notification Messages Validator
# ============================================================

def validate_notification_messages_page(page, test_cases, bugs):
    """
    Hardened validator untuk Notification Messages.

    Scope aman:
    - Tidak klik SEND
    - Tidak submit message
    - Tidak create/edit/delete data
    - Hanya validasi tab, form field, Sent Items table/list, dan evidence
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
        "notification message" in lower
        or "notification messages" in lower
    ) and (
        "send message" in lower
        or "sent items" in lower
    )

    add_test_case(
        test_cases,
        scenario="Verify Notification Messages page context",
        precondition="Notification Messages route is opened",
        steps="Check page title and main tabs",
        expected="Notification Message page should show Send Message and Sent Items tabs",
        actual="Notification Messages context found" if context_found else body_text[:500],
        status="PASS" if context_found else "FAIL",
    )

    if not context_found:
        add_bug(
            bugs,
            severity="High",
            title="Notification Messages page context not found",
            actual="Notification Message page markers were not visible",
            expected="Notification Message page should show Send Message and Sent Items tabs",
        )

    # 2. Tabs visible
    send_tab_found = "send message" in lower or locator_count(".v-tab:has-text('Send Message')") > 0
    sent_items_tab_found = "sent items" in lower or locator_count(".v-tab:has-text('Sent Items')") > 0

    add_test_case(
        test_cases,
        scenario="Verify Notification Messages tabs",
        precondition="Notification Messages page is opened",
        steps="Check Send Message and Sent Items tabs",
        expected="Send Message and Sent Items tabs should be visible",
        actual=f"Send Message={send_tab_found}; Sent Items={sent_items_tab_found}",
        status="PASS" if send_tab_found and sent_items_tab_found else "NEED REVIEW",
    )

    # 3. Send Message tab form
    send_clicked = click_tab("Send Message")
    send_text = get_body_text()
    send_lower = send_text.lower()

    send_fields = {
        "Contact Groups": "contact groups" in send_lower,
        "Contacts": "contacts" in send_lower,
        "Channels": "channels" in send_lower,
        "Select All": "select all" in send_lower,
        "Signature": "signature" in send_lower,
        "Title / Subject": "title / subject" in send_lower or "subject" in send_lower,
        "Body / Notification Message": "body / notification message" in send_lower or "notification message" in send_lower,
        "Title Counter 0 / 60": "0 / 60" in send_lower,
        "Body Counter 0 / 500": "0 / 500" in send_lower,
    }

    send_form_count = (
        locator_count("input")
        + locator_count("textarea")
        + locator_count(".v-input")
    )

    send_button_visible = (
        "send" in send_lower
        or locator_count("button:has-text('SEND')") > 0
        or locator_count("button:has-text('Send')") > 0
    )

    matched_send_fields = [name for name, found in send_fields.items() if found]
    missing_send_fields = [name for name, found in send_fields.items() if not found]

    send_form_valid = send_clicked and len(matched_send_fields) >= 5 and send_form_count > 0

    add_test_case(
        test_cases,
        scenario="Verify Send Message form fields",
        precondition="Send Message tab is opened",
        steps="Check recipient/channel/signature/title/body fields without filling or submitting",
        expected="Send Message form fields should be visible",
        actual=(
            f"clicked={send_clicked}; "
            f"form_count={send_form_count}; "
            f"send_button_visible={send_button_visible}; "
            f"matched={matched_send_fields}; "
            f"missing={missing_send_fields}"
        ),
        status="PASS" if send_form_valid else "NEED REVIEW",
    )

    # 4. SEND button read-only presence
    add_test_case(
        test_cases,
        scenario="Verify Send Message action button presence",
        precondition="Send Message tab is opened",
        steps="Check SEND button visibility without clicking",
        expected="SEND button may be visible but automation must not click it",
        actual=f"SEND button visible={send_button_visible}",
        status="PASS" if send_button_visible else "NEED REVIEW",
    )

    # 5. Sent Items tab
    sent_clicked = click_tab("Sent Items")
    sent_text = get_body_text()
    sent_lower = sent_text.lower()

    sent_markers = {
        "ACTION": "action" in sent_lower,
        "Search": "search" in sent_lower,
        "Title": "title" in sent_lower,
        "Body": "body" in sent_lower,
        "Number Of Contact": "number of contact" in sent_lower,
        "Channels": "channels" in sent_lower,
        "Message Sent": "message sent" in sent_lower,
        "No Data Available": "no data available" in sent_lower,
    }

    sent_table_count = locator_count(".v-data-table") + locator_count(".v-data-table__wrapper")
    sent_input_count = locator_count("input[type='text']") + locator_count(".v-input")

    matched_sent_markers = [name for name, found in sent_markers.items() if found]
    missing_sent_markers = [name for name, found in sent_markers.items() if not found]

    sent_items_valid = sent_clicked and (
        sent_table_count > 0
        or len(matched_sent_markers) >= 4
    )

    add_test_case(
        test_cases,
        scenario="Verify Sent Items table/list",
        precondition="Sent Items tab is opened",
        steps="Check Sent Items table/search/headers or empty state",
        expected="Sent Items should show search, table headers, message history, or valid empty state",
        actual=(
            f"clicked={sent_clicked}; "
            f"table_count={sent_table_count}; "
            f"input_count={sent_input_count}; "
            f"matched={matched_sent_markers}; "
            f"missing={missing_sent_markers}"
        ),
        status="PASS" if sent_items_valid else "NEED REVIEW",
    )

    # 6. Safe mode confirmation
    add_test_case(
        test_cases,
        scenario="Verify Notification Messages safe validation mode",
        precondition="Notification Messages page is opened",
        steps="Validate tabs and fields without clicking SEND or submitting data",
        expected="Automation should not send notification or mutate notification data",
        actual="Safe mode: no SEND clicked, no message submitted, no edit/delete action executed",
        status="PASS",
    )
'''

text = text.rstrip() + "\n" + validator_code + "\n"
CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
print("Force appended validate_notification_messages_page to checker.py")
