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


def print_card_debug(page):
    try:
        info = page.evaluate("""
        () => {
            const elements = Array.from(document.querySelectorAll(
                'a, button, .v-card, .homeContainer, [class*="homeContainer"], [role="button"], div'
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
                    const t = item.text || '';
                    return (
                        t.includes('Operational Dashboard') ||
                        t.includes('Shipment Activity Dashboard') ||
                        t.includes('Shipment Details') ||
                        t.includes('MoboMap') ||
                        t.includes('Verify Activities') ||
                        t.includes('Mobodrive') ||
                        t.includes('Notification Message') ||
                        t.includes('Inspection Result')
                    );
                });
        }
        """)

        print("\n=== CARD DEBUG JSON ===")
        print(json.dumps(info, indent=2, ensure_ascii=False))

    except Exception as exc:
        print("\n=== CARD DEBUG ERROR ===")
        print(str(exc))


def debug_open_target_menu(page, module_name):
    """
    Dipanggil saat TC-006 Navigate to target module.
    Kita tidak navigasi dulu, hanya inspect card/launcher yang sedang terbuka.
    """

    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    page.wait_for_timeout(2500)

    print_card_debug(page)

    return True, "Debug card metadata captured"


def noop_subpage(page, test_cases, preferred_subpage=""):
    checker.add_test_case(
        test_cases,
        scenario="Debug card launcher",
        precondition="User is logged in",
        steps="Inspect current launcher/card metadata",
        expected="Card metadata should be printed in terminal",
        actual="Debug card metadata captured",
        status="PASS",
    )


def noop_validate(page, test_cases, bugs):
    checker.add_test_case(
        test_cases,
        scenario="Validate debug card metadata capture",
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
        "Shipment Details",
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
