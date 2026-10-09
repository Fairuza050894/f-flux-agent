from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_safe_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Test Function - Safe MVP
# ============================================================

def perform_custom_smoke_test(
    url,
    route,
    expected_texts=None,
    feature_name="Custom Smoke Test",
    mode="smoke",
):
    from pathlib import Path
    from datetime import datetime
    import json
    import os
    import platform
    import re
    import sys

    root = Path(__file__).resolve().parents[2]

    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
        load_dotenv(root / "skills" / "qa_automation" / ".env")
    except Exception:
        pass

    report_dir = root / "skills" / "qa_automation" / "artifacts" / "reports"
    screenshot_dir = root / "skills" / "qa_automation" / "artifacts" / "screenshots"
    log_dir = root / "skills" / "qa_automation" / "artifacts" / "logs"

    report_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = "QA-CUSTOM-" + run_id
    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    expected_texts = expected_texts or []
    base_url = str(url or "").rstrip("/")
    route_value = str(route or "").strip()

    if route_value.startswith("http://") or route_value.startswith("https://"):
        target_url = route_value
    else:
        if not route_value.startswith("/"):
            route_value = "/" + route_value
        target_url = base_url + route_value

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(feature_name).lower()).strip("_") or "custom_smoke"

    report_path = report_dir / ("qa_documentation_custom_smoke_" + slug + "_" + run_id + ".md")
    error_log_path = log_dir / ("qa_error_log_custom_smoke_" + slug + "_" + run_id + ".md")
    screenshot_path = screenshot_dir / ("custom_smoke_" + slug + "_" + run_id + ".png")

    username = (
        os.getenv("QA_USERNAME")
        or os.getenv("QA_EMAIL")
        or os.getenv("MOBOSPACE_USERNAME")
        or os.getenv("MOBOSPACE_EMAIL")
        or os.getenv("TEST_USERNAME")
        or os.getenv("TEST_EMAIL")
        or os.getenv("USERNAME")
        or os.getenv("EMAIL")
        or ""
    )

    password = (
        os.getenv("QA_PASSWORD")
        or os.getenv("MOBOSPACE_PASSWORD")
        or os.getenv("TEST_PASSWORD")
        or os.getenv("PASSWORD")
        or ""
    )

    test_cases = []
    bugs = []
    page_text = ""

    def add_tc(tc_id, status, title):
        test_cases.append({"id": tc_id, "status": status, "title": title})

    def fill_first(page, selectors, value):
        for selector in selectors:
            try:
                loc = page.locator(selector).first()
                if loc.count() > 0:
                    loc.fill(value, timeout=5000)
                    return True
            except Exception:
                pass
        return False

    def click_first(page, selectors):
        for selector in selectors:
            try:
                loc = page.locator(selector).first()
                if loc.count() > 0:
                    loc.click(timeout=5000)
                    return True
            except Exception:
                pass
        return False

    try:
        add_tc("TC-001", "PASS" if username and password else "FAIL", "Load credential")

        if not username or not password:
            raise RuntimeError("Credential username/password tidak ditemukan di .env")

        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            page.goto(base_url, wait_until="domcontentloaded", timeout=60000)
            add_tc("TC-002", "PASS", "Access base URL")

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            user_ok = fill_first(
                page,
                [
                    'input[type="email"]',
                    'input[type="text"]',
                    'input[name*="email" i]',
                    'input[name*="user" i]',
                    'input[placeholder*="email" i]',
                    'input[placeholder*="user" i]',
                    'input[placeholder*="username" i]',
                ],
                username,
            )

            pass_ok = fill_first(
                page,
                [
                    'input[type="password"]',
                    'input[name*="password" i]',
                    'input[name*="pass" i]',
                    'input[placeholder*="password" i]',
                ],
                password,
            )

            if not user_ok or not pass_ok:
                raise RuntimeError("Login field username/password tidak ditemukan")

            login_ok = click_first(
                page,
                [
                    'button[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Masuk")',
                    'button:has-text("Sign In")',
                    'button',
                    '[role="button"]',
                ],
            )

            if not login_ok:
                raise RuntimeError("Tombol login tidak ditemukan")

            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass

            page.wait_for_timeout(3000)
            add_tc("TC-003", "PASS", "Login attempted")

            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            page.wait_for_timeout(3000)
            add_tc("TC-004", "PASS", "Open custom route " + route_value)

            try:
                page_text = page.locator("body").inner_text(timeout=15000)
            except Exception:
                page_text = ""

            if page_text.strip():
                add_tc("TC-005", "PASS", "Read page content")
            else:
                add_tc("TC-005", "FAIL", "Read page content")
                bugs.append("Page content is empty")

            for index, expected in enumerate(expected_texts, start=1):
                tc_id = "TC-" + str(5 + index).zfill(3)
                if str(expected).lower() in page_text.lower():
                    add_tc(tc_id, "PASS", "Expected text found: " + str(expected))
                else:
                    add_tc(tc_id, "FAIL", "Expected text missing: " + str(expected))
                    bugs.append("Expected text missing: " + str(expected))

            page.screenshot(path=str(screenshot_path), full_page=True)
            add_tc("TC-020", "PASS", "Capture screenshot evidence")

            context.close()
            browser.close()

    except Exception as exc:
        add_tc("TC-999", "FAIL", "Automation runtime")
        bugs.append("Automation runtime error: " + str(exc))

    passed = sum(1 for item in test_cases if item["status"] == "PASS")
    failed = sum(1 for item in test_cases if item["status"] == "FAIL")

    status = "FAILED" if failed > 0 or bugs else "PASS"
    icon = "❌" if status == "FAILED" else "✅"

    verified_lines = []
    failed_lines = []

    for tc in test_cases:
        line = tc["id"] + " " + tc["status"] + " - " + tc["title"]
        if tc["status"] == "PASS":
            verified_lines.append(line)
        elif tc["status"] == "FAIL":
            failed_lines.append(line)

    bug_lines = bugs if bugs else ["No bug found"]

    testing_summary = (
        icon + " QA Custom Smoke Test Completed\n\n"
        + "Module: " + str(feature_name) + "\n"
        + "Mode: " + str(mode) + "\n"
        + "Environment: Sandbox\n"
        + "Status: " + status + "\n\n"
        + "Execution Info:\n"
        + "- Execution ID: " + execution_id + "\n"
        + "- Executed At: " + executed_at + "\n"
        + "- Executed By: Hermes QA Automation\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Suite / Mode: " + str(mode) + "\n"
        + "- Environment: Sandbox\n"
        + "- Base URL: " + base_url + "\n"
        + "- Route: " + route_value + "\n"
        + "- Target URL: " + target_url + "\n\n"
        + "Runtime Environment:\n"
        + "- OS: " + platform.platform() + "\n"
        + "- Machine: " + platform.machine() + "\n"
        + "- Browser: Chromium\n"
        + "- Automation Tool: Playwright\n"
        + "- Runtime: Hermes Agent\n"
        + "- Python Version: " + sys.version.split()[0] + "\n\n"
        + "Summary:\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Need Review: 0\n"
        + "- Skipped: 0\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n"
        + "- Non-blocking Warnings: 0\n\n"
        + "Verified:\n" + ("\n".join(verified_lines) if verified_lines else "-") + "\n\n"
        + "Failed:\n" + ("\n".join(failed_lines) if failed_lines else "-") + "\n\n"
        + "Need Review:\n-\n\n"
        + "Bugs:\n" + "\n".join(bug_lines) + "\n\n"
        + "Evidence:\n"
        + "- Screenshot: " + str(screenshot_path) + "\n"
        + "- Report: " + str(report_path) + "\n"
        + "- Error Log: " + str(error_log_path) + "\n\n"
        + "Recommendation:\n"
        + ("Fix blocking issues before release." if status == "FAILED" else "No blocking issue found from custom smoke result.")
    )

    documentation_report = (
        "# QA Custom Smoke Test Report\n\n"
        + "Execution ID: " + execution_id + "\n"
        + "Feature: " + str(feature_name) + "\n"
        + "Mode: " + str(mode) + "\n"
        + "Status: " + status + "\n"
        + "Base URL: " + base_url + "\n"
        + "Route: " + route_value + "\n"
        + "Target URL: " + target_url + "\n\n"
        + "Summary:\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n\n"
        + "Expected Texts:\n"
        + json.dumps(expected_texts, indent=2, ensure_ascii=False) + "\n\n"
        + "Test Cases:\n"
        + json.dumps(test_cases, indent=2, ensure_ascii=False) + "\n\n"
        + "Bugs:\n"
        + "\n".join(bug_lines) + "\n\n"
        + "Page Text Preview:\n"
        + page_text[:3000]
    )

    error_log_report = (
        "# QA Custom Smoke Error Log\n\n"
        + "Status: " + status + "\n"
        + "Execution ID: " + execution_id + "\n"
        + "Feature: " + str(feature_name) + "\n"
        + "Route: " + route_value + "\n\n"
        + "Bugs:\n"
        + "\n".join(bug_lines)
    )

    report_path.write_text(documentation_report, encoding="utf-8")
    error_log_path.write_text(error_log_report, encoding="utf-8")

    result = {
        "testing_summary": testing_summary,
        "documentation_report": documentation_report,
        "error_log_report": error_log_report,
        "status": status,
        "screenshot_path": str(screenshot_path),
        "report_path": str(report_path),
        "documentation_path": str(report_path),
        "error_log_path": str(error_log_path),
        "feature_name": feature_name,
        "route": route_value,
        "target_url": target_url,
        "custom_smoke": True,
    }

    try:
        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
        if enrich_fn:
            result = enrich_fn(result, base_url, feature_name, mode)
    except Exception as exc:
        result["standard_json_error"] = str(exc)

    try:
        append_history_fn = globals().get("append_qa_run_history")
        if append_history_fn:
            result = append_history_fn(result, base_url, feature_name, mode)
    except Exception as exc:
        result["history_error"] = str(exc)

    return result
'''

if "def perform_custom_smoke_test(" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted perform_custom_smoke_test")
else:
    print("perform_custom_smoke_test already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
