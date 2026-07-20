from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_generic_ui_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Generic UI Runner V2
# ============================================================

def _custom_smoke_build_target_url_v2(base_url, route):
    base = str(base_url or "").rstrip("/")
    route_value = str(route or "").strip()

    if route_value.startswith("http://") or route_value.startswith("https://"):
        return route_value, route_value

    if not route_value.startswith("/"):
        route_value = "/" + route_value

    return base + route_value, route_value


def _custom_smoke_resolve_credentials_v2():
    import os
    from pathlib import Path

    if "_custom_smoke_resolve_credentials_flexible" in globals():
        try:
            return _custom_smoke_resolve_credentials_flexible()
        except Exception:
            pass

    root = Path(__file__).resolve().parents[2]

    try:
        from dotenv import load_dotenv
        load_dotenv(root / ".env")
        load_dotenv(root / "skills" / "qa_automation" / ".env")
    except Exception:
        pass

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

    workspace = (
        os.getenv("QA_WORKSPACE")
        or os.getenv("QA_COMPANY")
        or os.getenv("MOBOSPACE_WORKSPACE")
        or os.getenv("MOBOSPACE_COMPANY")
        or os.getenv("WORKSPACE")
        or os.getenv("COMPANY")
        or ""
    )

    return {
        "username": username,
        "password": password,
        "workspace": workspace,
        "username_key": "",
        "password_key": "",
        "workspace_key": "",
    }


def _custom_smoke_click_text_v2(page, texts, timeout=3500):
    import re

    for value in texts:
        try:
            page.get_by_text(re.compile(str(value), re.I)).first().click(timeout=timeout)
            page.wait_for_timeout(1200)
            return True, str(value)
        except Exception:
            pass

    return False, ""


def _custom_smoke_click_selector_v2(page, selectors, timeout=3500):
    for selector in selectors:
        try:
            loc = page.locator(selector).first()
            if loc.count() > 0:
                loc.click(timeout=timeout)
                page.wait_for_timeout(1200)
                return True, selector
        except Exception:
            pass

    return False, ""


def _custom_smoke_fill_selector_v2(page, selectors, value, timeout=3500):
    for selector in selectors:
        try:
            loc = page.locator(selector).first()
            if loc.count() > 0:
                loc.fill(str(value), timeout=timeout)
                return True, selector
        except Exception:
            pass

    return False, ""


def _custom_smoke_fill_visible_input_by_type_v2(page, username, password):
    user_ok = False
    pass_ok = False

    try:
        inputs = page.locator("input:visible")
        total = inputs.count()
    except Exception:
        total = 0

    for index in range(total):
        try:
            item = inputs.nth(index)
            input_type = (item.get_attribute("type") or "").lower()
            name = (item.get_attribute("name") or "").lower()
            placeholder = (item.get_attribute("placeholder") or "").lower()
            aria = (item.get_attribute("aria-label") or "").lower()

            marker = " ".join([input_type, name, placeholder, aria])

            if "password" in marker or input_type == "password":
                if not pass_ok:
                    item.fill(str(password), timeout=3000)
                    pass_ok = True
            else:
                if not user_ok:
                    item.fill(str(username), timeout=3000)
                    user_ok = True

        except Exception:
            pass

    return user_ok, pass_ok


def _custom_smoke_has_login_fields_v2(page):
    try:
        password_count = page.locator('input[type="password"]:visible').count()
        visible_input_count = page.locator("input:visible").count()
        return password_count > 0 and visible_input_count >= 2
    except Exception:
        return False


def _custom_smoke_open_login_form_v2(page):
    if _custom_smoke_has_login_fields_v2(page):
        return True, "login_fields_already_visible"

    login_texts = [
        "Internal User",
        "Internal",
        "LDAP",
        "Username",
        "Password",
        "Login",
        "Log In",
        "Masuk",
        "Sign In",
        "SSO",
    ]

    clicked, marker = _custom_smoke_click_text_v2(page, login_texts, timeout=3000)
    if clicked:
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        page.wait_for_timeout(1500)

        if _custom_smoke_has_login_fields_v2(page):
            return True, marker

    login_selectors = [
        'button:has-text("Login")',
        'button:has-text("Masuk")',
        'button:has-text("Sign In")',
        'button',
        '[role="button"]',
        '.v-card',
        '.card',
        'a',
    ]

    clicked, marker = _custom_smoke_click_selector_v2(page, login_selectors, timeout=3000)
    if clicked:
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        page.wait_for_timeout(1500)

        if _custom_smoke_has_login_fields_v2(page):
            return True, marker

    return _custom_smoke_has_login_fields_v2(page), "generic_login_attempt"


def _custom_smoke_collect_page_diagnostics_v2(page):
    diagnostics = []

    try:
        diagnostics.append("Current URL: " + str(page.url))
    except Exception:
        pass

    try:
        diagnostics.append("Visible input count: " + str(page.locator("input:visible").count()))
    except Exception:
        pass

    try:
        diagnostics.append("Password input count: " + str(page.locator('input[type="password"]:visible').count()))
    except Exception:
        pass

    try:
        button_texts = []
        buttons = page.locator("button")
        total = min(buttons.count(), 10)

        for index in range(total):
            try:
                text_value = buttons.nth(index).inner_text(timeout=1000).strip()
                if text_value:
                    button_texts.append(text_value)
            except Exception:
                pass

        diagnostics.append("Visible button texts: " + ", ".join(button_texts))
    except Exception:
        pass

    try:
        body_text = page.locator("body").inner_text(timeout=3000)
        diagnostics.append("Body preview: " + body_text[:1200].replace("\n", " | "))
    except Exception:
        pass

    return "\n".join(diagnostics)


def _custom_smoke_perform_login_v2(page, username, password, add_tc):
    if not username or not password:
        raise RuntimeError("Credential username/password tidak ditemukan di .env")

    opened, marker = _custom_smoke_open_login_form_v2(page)

    if opened:
        add_tc("TC-003", "PASS", "Open login form: " + str(marker))
    else:
        diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
        raise RuntimeError("Login form tidak ditemukan\n" + diagnostics)

    user_selectors = [
        'input[type="email"]:visible',
        'input[type="text"]:visible',
        'input[name*="email" i]:visible',
        'input[name*="user" i]:visible',
        'input[name*="username" i]:visible',
        'input[placeholder*="email" i]:visible',
        'input[placeholder*="user" i]:visible',
        'input[placeholder*="username" i]:visible',
        'input[placeholder*="NIK" i]:visible',
    ]

    password_selectors = [
        'input[type="password"]:visible',
        'input[name*="password" i]:visible',
        'input[name*="pass" i]:visible',
        'input[placeholder*="password" i]:visible',
    ]

    user_ok, user_marker = _custom_smoke_fill_selector_v2(page, user_selectors, username)
    pass_ok, pass_marker = _custom_smoke_fill_selector_v2(page, password_selectors, password)

    if not user_ok or not pass_ok:
        fallback_user_ok, fallback_pass_ok = _custom_smoke_fill_visible_input_by_type_v2(page, username, password)
        user_ok = user_ok or fallback_user_ok
        pass_ok = pass_ok or fallback_pass_ok

    if not user_ok or not pass_ok:
        diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
        raise RuntimeError("Login field username/password tidak ditemukan\n" + diagnostics)

    add_tc("TC-004", "PASS", "Fill username/password")

    login_selectors = [
        'button[type="submit"]',
        'button:has-text("Login")',
        'button:has-text("Masuk")',
        'button:has-text("Sign In")',
        'button:has-text("Submit")',
        '[role="button"]:has-text("Login")',
        '[role="button"]:has-text("Masuk")',
    ]

    clicked, marker = _custom_smoke_click_selector_v2(page, login_selectors, timeout=5000)

    if not clicked:
        try:
            page.keyboard.press("Enter")
            clicked = True
            marker = "keyboard_enter"
        except Exception:
            pass

    if not clicked:
        diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
        raise RuntimeError("Tombol login tidak ditemukan\n" + diagnostics)

    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass

    page.wait_for_timeout(3000)
    add_tc("TC-005", "PASS", "Submit login: " + str(marker))


def _custom_smoke_select_workspace_v2(page, workspace, add_tc):
    workspace_value = str(workspace or "").strip()

    if workspace_value:
        clicked, marker = _custom_smoke_click_text_v2(page, [workspace_value], timeout=5000)

        if clicked:
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            page.wait_for_timeout(1500)

            _custom_smoke_click_text_v2(
                page,
                ["Select", "Pilih", "Continue", "Lanjut", "Masuk", "OK"],
                timeout=3000,
            )

            add_tc("TC-006", "PASS", "Select workspace/company: " + workspace_value)
            return True

    # Fallback: kalau sudah masuk dashboard atau tidak ada halaman pilihan company, skip sebagai PASS.
    try:
        body = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        body = ""

    selection_markers = [
        "select company",
        "choose company",
        "pilih company",
        "pilih perusahaan",
        "workspace",
    ]

    if any(marker in body for marker in selection_markers):
        clicked, marker = _custom_smoke_click_text_v2(
            page,
            ["Pancaran", "Sandbox", "Mobospace", "Pilih", "Select", "Continue"],
            timeout=4000,
        )

        if clicked:
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            page.wait_for_timeout(1500)
            add_tc("TC-006", "PASS", "Select workspace/company fallback")
            return True

        add_tc("TC-006", "NEED REVIEW", "Workspace/company page detected but no option clicked")
        return False

    add_tc("TC-006", "PASS", "Workspace/company selection skipped")
    return True


def _perform_custom_smoke_generic_ui_v2(
    url,
    route,
    expected_texts=None,
    feature_name="Custom Smoke Test",
    mode="smoke",
):
    from pathlib import Path
    from datetime import datetime
    import json
    import platform
    import re
    import sys

    root = Path(__file__).resolve().parents[2]

    report_dir = root / "skills" / "qa_automation" / "artifacts" / "reports"
    screenshot_dir = root / "skills" / "qa_automation" / "artifacts" / "screenshots"
    log_dir = root / "skills" / "qa_automation" / "artifacts" / "logs"

    report_dir.mkdir(parents=True, exist_ok=True)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    execution_id = "QA-CUSTOM-GENERIC-" + run_id
    executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    expected_texts = expected_texts or []
    base_url = str(url or "").rstrip("/")
    target_url, route_value = _custom_smoke_build_target_url_v2(base_url, route)

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(feature_name).lower()).strip("_") or "custom_smoke"

    report_path = report_dir / ("qa_documentation_custom_smoke_generic_" + slug + "_" + run_id + ".md")
    error_log_path = log_dir / ("qa_error_log_custom_smoke_generic_" + slug + "_" + run_id + ".md")
    screenshot_path = screenshot_dir / ("custom_smoke_generic_" + slug + "_" + run_id + ".png")

    credential = _custom_smoke_resolve_credentials_v2()
    username = credential.get("username") or ""
    password = credential.get("password") or ""
    workspace = credential.get("workspace") or ""

    test_cases = []
    bugs = []
    warnings = []
    page_text = ""
    current_url = ""
    browser = None
    context = None
    page = None

    def add_tc(tc_id, status, title):
        test_cases.append({
            "id": tc_id,
            "status": status,
            "title": title,
        })

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

            _custom_smoke_perform_login_v2(page, username, password, add_tc)
            _custom_smoke_select_workspace_v2(page, workspace, add_tc)

            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass

            page.wait_for_timeout(3000)

            try:
                current_url = str(page.url)
            except Exception:
                current_url = target_url

            add_tc("TC-007", "PASS", "Open custom route: " + str(route_value))

            try:
                page_text = page.locator("body").inner_text(timeout=15000)
            except Exception:
                page_text = ""

            if page_text.strip():
                add_tc("TC-008", "PASS", "Read page content")
            else:
                add_tc("TC-008", "FAIL", "Read page content")
                bugs.append("Page content is empty")

            tc_number = 9

            for expected in expected_texts:
                expected_value = str(expected).strip()

                if not expected_value:
                    continue

                tc_id = "TC-" + str(tc_number).zfill(3)

                if expected_value.lower() in page_text.lower():
                    add_tc(tc_id, "PASS", "Expected text found: " + expected_value)
                else:
                    add_tc(tc_id, "FAIL", "Expected text missing: " + expected_value)
                    bugs.append("Expected text missing: " + expected_value)

                tc_number += 1

            page.screenshot(path=str(screenshot_path), full_page=True)
            add_tc("TC-020", "PASS", "Capture screenshot evidence")

            context.close()
            browser.close()

    except Exception as exc:
        add_tc("TC-999", "FAIL", "Automation runtime")
        bugs.append("Automation runtime error: " + str(exc))

        try:
            if page is not None:
                page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception:
            pass

        try:
            if context is not None:
                context.close()
        except Exception:
            pass

        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass

    passed = sum(1 for tc in test_cases if tc["status"] == "PASS")
    failed = sum(1 for tc in test_cases if tc["status"] == "FAIL")
    need_review = sum(1 for tc in test_cases if tc["status"] == "NEED REVIEW")
    skipped = 0

    if failed > 0 or bugs:
        status = "FAILED"
        icon = "❌"
    elif need_review > 0 or warnings:
        status = "NEED REVIEW"
        icon = "⚠️"
    else:
        status = "PASS"
        icon = "✅"

    verified_lines = []
    failed_lines = []
    review_lines = []

    for tc in test_cases:
        line = tc["id"] + " " + tc["status"] + " - " + tc["title"]

        if tc["status"] == "PASS":
            verified_lines.append(line)
        elif tc["status"] == "FAIL":
            failed_lines.append(line)
        elif tc["status"] == "NEED REVIEW":
            review_lines.append(line)

    bug_lines = bugs if bugs else ["No bug found"]
    warning_lines = warnings if warnings else ["-"]

    testing_summary = (
        icon + " QA Custom Smoke Generic UI Test Completed\n\n"
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
        + "- Strategy: Generic UI Smoke Runner\n"
        + "- Environment: Sandbox\n"
        + "- Base URL: " + base_url + "\n"
        + "- Route: " + route_value + "\n"
        + "- Target URL: " + target_url + "\n"
        + "- Current URL: " + current_url + "\n\n"
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
        + "- Need Review: " + str(need_review) + "\n"
        + "- Skipped: " + str(skipped) + "\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n"
        + "- Non-blocking Warnings: " + str(len(warnings)) + "\n\n"
        + "Verified:\n" + ("\n".join(verified_lines) if verified_lines else "-") + "\n\n"
        + "Failed:\n" + ("\n".join(failed_lines) if failed_lines else "-") + "\n\n"
        + "Need Review:\n" + ("\n".join(review_lines) if review_lines else "-") + "\n\n"
        + "Bugs:\n" + "\n".join(bug_lines) + "\n\n"
        + "Evidence:\n"
        + "- Screenshot: " + str(screenshot_path) + "\n"
        + "- Report: " + str(report_path) + "\n"
        + "- Error Log: " + str(error_log_path) + "\n\n"
        + "Recommendation:\n"
        + ("Fix blocking issues before release." if status == "FAILED" else "No blocking issue found from generic custom smoke result.")
    )

    documentation_report = (
        "# QA Custom Smoke Generic UI Test Report\n\n"
        + "## Execution\n\n"
        + "- Execution ID: " + execution_id + "\n"
        + "- Feature: " + str(feature_name) + "\n"
        + "- Mode: " + str(mode) + "\n"
        + "- Strategy: Generic UI Smoke Runner\n"
        + "- Environment: Sandbox\n"
        + "- Status: " + status + "\n"
        + "- Base URL: " + base_url + "\n"
        + "- Route: " + route_value + "\n"
        + "- Target URL: " + target_url + "\n"
        + "- Current URL: " + current_url + "\n\n"
        + "## Summary\n\n"
        + "- Passed: " + str(passed) + "\n"
        + "- Failed: " + str(failed) + "\n"
        + "- Need Review: " + str(need_review) + "\n"
        + "- Bugs Found: " + str(len(bugs)) + "\n\n"
        + "## Expected Texts\n\n"
        + json.dumps(expected_texts, indent=2, ensure_ascii=False) + "\n\n"
        + "## Test Cases\n\n"
        + json.dumps(test_cases, indent=2, ensure_ascii=False) + "\n\n"
        + "## Bugs\n\n"
        + "\n".join(bug_lines) + "\n\n"
        + "## Page Text Preview\n\n"
        + page_text[:3000]
    )

    error_log_report = (
        "# QA Custom Smoke Generic UI Error Log\n\n"
        + "Status: " + status + "\n"
        + "Execution ID: " + execution_id + "\n"
        + "Feature: " + str(feature_name) + "\n"
        + "Route: " + route_value + "\n"
        + "Target URL: " + target_url + "\n"
        + "Current URL: " + current_url + "\n\n"
        + "## Bugs\n\n"
        + "\n".join(bug_lines) + "\n\n"
        + "## Warnings\n\n"
        + "\n".join(warning_lines)
    )

    report_path.write_text(documentation_report, encoding="utf-8")
    error_log_path.write_text(error_log_report, encoding="utf-8")

    result = {
        "ok": status == "PASS",
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
        "current_url": current_url,
        "custom_smoke": True,
        "custom_smoke_strategy": "generic_ui_runner_v2",
        "passed": passed,
        "failed": failed,
        "need_review": need_review,
        "bugs_found": len(bugs),
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


def _custom_smoke_exact_registered_route_v2(route):
    from urllib.parse import urlparse

    route_raw = str(route or "").strip()

    try:
        if route_raw.startswith("http://") or route_raw.startswith("https://"):
            parsed = urlparse(route_raw)
            path = parsed.path.lower()
            query = parsed.query
        else:
            if not route_raw.startswith("/"):
                route_raw = "/" + route_raw
            parsed = urlparse(route_raw)
            path = parsed.path.lower()
            query = parsed.query
    except Exception:
        path = route_raw.lower()
        query = ""

    # Query sengaja dianggap generic, agar route seperti /managementnotif?genericSmoke=1
    # bisa dipakai untuk test Generic UI Runner tanpa masuk registered fallback.
    if query:
        return None

    route_map = {
        "/managementnotif": "Notification Management",
        "/notificationmessage": "Notification Messages",
        "/shipmentdetail": "Shipment Details",
        "/mobomap": "MoboMap",
        "/inspectionresult": "Inspection Result",
    }

    return route_map.get(path)


if not globals().get("_CUSTOM_SMOKE_GENERIC_UI_V2_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_GENERIC_UI_V2 = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        registered_feature = _custom_smoke_exact_registered_route_v2(route)

        # Untuk route yang sudah registered, tetap pakai flow lama yang sudah stabil.
        if registered_feature and _CUSTOM_SMOKE_BEFORE_GENERIC_UI_V2 is not None:
            return _CUSTOM_SMOKE_BEFORE_GENERIC_UI_V2(
                url=url,
                route=route,
                expected_texts=expected_texts,
                feature_name=feature_name,
                mode=mode,
            )

        # Untuk route baru / unregistered, pakai generic UI smoke runner.
        return _perform_custom_smoke_generic_ui_v2(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

    _CUSTOM_SMOKE_GENERIC_UI_V2_INSTALLED = True
'''

if "# Custom Smoke Generic UI Runner V2" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Custom Smoke Generic UI Runner V2")
else:
    print("Custom Smoke Generic UI Runner V2 already exists")

print(f"Backup created: {backup_path}")
