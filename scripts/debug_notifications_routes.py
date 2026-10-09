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


def _click_label(page, label: str) -> bool:
    scopes = [
        page.locator(".v-navigation-drawer, .v-navigation-drawer__content, .v-list, nav, aside").first,
        page.locator("body"),
    ]

    for scope in scopes:
        candidates = [
            scope.get_by_text(label, exact=True).first,
            page.locator(f".v-list-item:has-text('{label}')").last,
            page.locator(f"[role='button']:has-text('{label}')").last,
            scope.get_by_text(label, exact=False).first,
            page.get_by_text(label, exact=True).last,
            page.get_by_text(label, exact=False).last,
        ]

        for candidate in candidates:
            try:
                if candidate.count() <= 0:
                    continue

                candidate.scroll_into_view_if_needed(timeout=3000)
                candidate.wait_for(state="visible", timeout=4000)
                candidate.click(timeout=5000)

                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                page.wait_for_timeout(1500)
                return True

            except Exception:
                continue

    return False


def print_notification_debug(page):
    try:
        # Coba expand menu Notifications di sidebar.
        for label in [
            "Notifications",
            "Notification",
            "MoboNotif",
        ]:
            try:
                _click_label(page, label)
                page.wait_for_timeout(1500)
            except Exception:
                pass

        info = page.evaluate("""
        () => {
            const elements = Array.from(document.querySelectorAll(
                'a, button, .v-list-item, .v-card, .homeContainer, [class*="homeContainer"], [role="button"], div'
            ));

            return elements
                .map((el, index) => {
                    const text = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
                    const href = el.getAttribute('href');
                    const to = el.getAttribute('to');
                    const role = el.getAttribute('role');
                    const id = el.getAttribute('id');
                    const cls = el.getAttribute('class');
                    const tag = el.tagName;
                    const onclick = el.getAttribute('onclick');
                    const parentHref = el.closest('a') ? el.closest('a').getAttribute('href') : null;
                    const parentClass = el.parentElement ? el.parentElement.getAttribute('class') : null;

                    return {
                        index,
                        tag,
                        text,
                        href,
                        to,
                        role,
                        id,
                        class: cls,
                        onclick,
                        parentHref,
                        parentClass
                    };
                })
                .filter((item) => {
                    const t = (item.text || '').toLowerCase();
                    const h = (item.href || '').toLowerCase();
                    return (
                        t.includes('notification') ||
                        t.includes('notif') ||
                        t.includes('message') ||
                        t.includes('template') ||
                        t.includes('context') ||
                        t.includes('group') ||
                        t.includes('contact') ||
                        h.includes('notification') ||
                        h.includes('notif') ||
                        h.includes('message') ||
                        h.includes('template') ||
                        h.includes('context') ||
                        h.includes('group') ||
                        h.includes('contact')
                    );
                });
        }
        """)

        print("\n=== NOTIFICATIONS ROUTE DEBUG JSON ===")
        print(json.dumps(info, indent=2, ensure_ascii=False))

    except Exception as exc:
        print("\n=== NOTIFICATIONS ROUTE DEBUG ERROR ===")
        print(str(exc))


def debug_open_target_menu(page, module_name):
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    page.wait_for_timeout(2500)
    print_notification_debug(page)

    return True, "Notification route metadata captured"


def noop_subpage(page, test_cases, preferred_subpage=""):
    checker.add_test_case(
        test_cases,
        scenario="Debug Notifications route",
        precondition="User is logged in",
        steps="Inspect notification-related menu/card metadata",
        expected="Notification route metadata should be printed in terminal",
        actual="Notification route metadata captured",
        status="PASS",
    )


def noop_validate(page, test_cases, bugs):
    checker.add_test_case(
        test_cases,
        scenario="Validate notification route debug",
        precondition="Debug mode",
        steps="No UI validation",
        expected="Debug run should complete",
        actual="Debug completed",
        status="PASS",
    )


def main():
    checker.open_target_menu = debug_open_target_menu
    checker.open_uang_makan_driver_subpage = noop_subpage
    checker.validate_uang_makan_driver_monitoring_page = noop_validate
    checker.validate_uang_makan_driver_page = noop_validate

    result = checker.perform_audit_for_telegram(
        URL,
        "Notifications",
        "smoke",
    )

    print("\n=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:3000])

    print("\n=== ARTIFACTS ===")
    print("Selector Inventory:", result.get("selector_inventory_path"))
    print("Screenshot:", result.get("screenshot_path"))
    print("Report:", result.get("report_path"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=== ERROR TRACEBACK ===")
        traceback.print_exc()
