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


def noop_open_target_menu(page, module_name):
    """
    Jangan klik Shipment Activity.
    Kita ingin lihat landing/launcher setelah login.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass

    page.wait_for_timeout(2000)
    return True, "Debug launcher only"


def noop_subpage(page, test_cases, preferred_subpage=""):
    checker.add_test_case(
        test_cases,
        scenario="Debug Shipment Activity card launcher",
        precondition="User is logged in",
        steps="Do not navigate; inspect current launcher/cards",
        expected="Launcher/card page should be inspectable",
        actual="Debug mode",
        status="PASS",
    )


def inspect_cards(page, test_cases, bugs):
    try:
        info = page.evaluate("""
        () => {
            const elements = Array.from(document.querySelectorAll('a, button, .v-card, .homeContainer, [class*="homeContainer"], [role="button"], div'));

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
                        t.includes('Shipment Details') ||
                        t.includes('Shipment Activity Dashboard') ||
                        t.includes('MoboMap') ||
                        t.includes('Verify Activities') ||
                        t.includes('Operational Dashboard')
                    );
                });
        }
        """)

        print("=== CARD DEBUG JSON ===")
        print(json.dumps(info, indent=2, ensure_ascii=False))

        checker.add_test_case(
            test_cases,
            scenario="Inspect Shipment Activity cards",
            precondition="Launcher page is visible",
            steps="Extract DOM metadata for Shipment Details card",
            expected="Shipment Details card metadata should be available",
            actual=json.dumps(info[:5], ensure_ascii=False),
            status="PASS" if info else "NEED REVIEW",
        )

    except Exception as exc:
        checker.add_test_case(
            test_cases,
            scenario="Inspect Shipment Activity cards",
            precondition="Launcher page is visible",
            steps="Extract DOM metadata for Shipment Details card",
            expected="Shipment Details card metadata should be available",
            actual=str(exc),
            status="FAIL",
        )


def main():
    checker.open_target_menu = noop_open_target_menu
    checker.open_uang_makan_driver_subpage = noop_subpage
    checker.validate_uang_makan_driver_monitoring_page = inspect_cards
    checker.validate_uang_makan_driver_page = inspect_cards

    result = checker.perform_audit_for_telegram(
        URL,
        "Shipment Details",
        "smoke",
    )

    print("\n=== TESTING SUMMARY ===")
    print(result.get("testing_summary", "")[:4000])

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
