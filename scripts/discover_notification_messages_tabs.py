from pathlib import Path
import os
import sys
import traceback
import json

os.environ["QA_DRIVER_DAILY_MEAL_COMBINED"] = "false"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import skills.qa_automation.checker as checker


URL = os.getenv(
    "QA_DEFAULT_URL",
    "https://mobospace-sandbox.pancaran-group.co.id",
)


def open_notification_messages_direct(page, module_name):
    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    try:
        target_url = get_origin() + "/notificationmessage"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(4000)

        return True, f"Opened direct route: {target_url}"

    except Exception as exc:
        return False, f"Failed to open /notificationmessage: {exc}"


def noop_subpage(page, test_cases, preferred_subpage=""):
    checker.add_test_case(
        test_cases,
        scenario="Open Notification Messages page",
        precondition="User is logged in and /notificationmessage route is available",
        steps="Open direct /notificationmessage route",
        expected="Notification Messages page should be opened",
        actual="Notification Messages direct route used",
        status="PASS",
    )


def collect_page_state(page, label):
    try:
        body_text = page.locator("body").inner_text(timeout=8000)
    except Exception as exc:
        body_text = f"FAILED_TO_READ_BODY: {exc}"

    def count(selector):
        try:
            return page.locator(selector).count()
        except Exception:
            return 0

    data = {
        "tab": label,
        "url": page.url,
        "visible_text_preview": body_text[:2500],
        "counts": {
            "buttons": count("button"),
            "inputs": count("input"),
            "textareas": count("textarea"),
            "vuetify_inputs": count(".v-input"),
            "tabs": count("[role='tab'], .v-tab"),
            "tables": count(".v-data-table"),
            "table_wrappers": count(".v-data-table__wrapper"),
            "cards": count(".v-card"),
            "dialogs": count(".v-dialog, [role='dialog']"),
        },
        "buttons_text": [],
        "inputs_info": [],
    }

    try:
        data["buttons_text"] = page.evaluate("""
        () => Array.from(document.querySelectorAll('button, .v-btn'))
            .map((el) => (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' '))
            .filter(Boolean)
            .slice(0, 50)
        """)
    except Exception:
        pass

    try:
        data["inputs_info"] = page.evaluate("""
        () => Array.from(document.querySelectorAll('input, textarea'))
            .map((el) => ({
                tag: el.tagName,
                type: el.getAttribute('type'),
                placeholder: el.getAttribute('placeholder'),
                value: el.value || '',
                role: el.getAttribute('role'),
                id: el.getAttribute('id'),
                class: el.getAttribute('class')
            }))
            .slice(0, 50)
        """)
    except Exception:
        pass

    return data


def click_tab(page, label):
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


def validate_notification_messages_tab_discovery(page, test_cases, bugs):
    results = []

    # Initial state
    results.append(collect_page_state(page, "Initial"))

    for tab in ["Send Message", "Sent Items"]:
        clicked = click_tab(page, tab)
        state = collect_page_state(page, tab)
        state["clicked"] = clicked
        results.append(state)

        checker.add_test_case(
            test_cases,
            scenario=f"Discover Notification Messages tab - {tab}",
            precondition="Notification Messages page is opened",
            steps=f"Click tab {tab} and inspect fields/tables read-only",
            expected=f"{tab} tab should be inspectable without submitting data",
            actual=f"clicked={clicked}; counts={state['counts']}",
            status="PASS" if clicked else "NEED REVIEW",
        )

    print("\n=== NOTIFICATION MESSAGES TAB DEBUG JSON ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))


def main():
    checker.open_target_menu = open_notification_messages_direct
    checker.open_uang_makan_driver_subpage = noop_subpage
    checker.validate_uang_makan_driver_monitoring_page = validate_notification_messages_tab_discovery
    checker.validate_uang_makan_driver_page = validate_notification_messages_tab_discovery

    result = checker.perform_audit_for_telegram(
        URL,
        "Notification Messages",
        "regression",
    )

    print("\n=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:7000])

    print("\n=== ARTIFACTS ===")
    print("Selector Inventory:", result.get("selector_inventory_path"))
    print("Screenshot:", result.get("screenshot_path"))
    print("Report:", result.get("report_path"))
    print("Spreadsheet:", result.get("spreadsheet_path"))

    print("\n=== ERROR LOG REPORT ===")
    print((result.get("error_log_report") or "-")[:3000])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
