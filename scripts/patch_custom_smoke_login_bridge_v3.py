from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_login_bridge_v3_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Generic Login Bridge V3
# Reuse registered QA login helper: fill_login_form + is_still_on_login_page
# ============================================================

if not globals().get("_CUSTOM_SMOKE_LOGIN_BRIDGE_V3_INSTALLED"):
    _CUSTOM_SMOKE_PREVIOUS_PERFORM_LOGIN_V2 = globals().get("_custom_smoke_perform_login_v2")

    def _custom_smoke_perform_login_v2(page, username, password, add_tc):
        if not username or not password:
            raise RuntimeError("Credential username/password tidak ditemukan di .env")

        registered_login_helper = globals().get("fill_login_form")
        still_login_helper = globals().get("is_still_on_login_page")

        if registered_login_helper:
            try:
                registered_login_helper(page, username, password)

                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    pass

                page.wait_for_timeout(3000)

                add_tc("TC-003", "PASS", "Login using registered helper: fill_login_form")

                still_on_login = False

                try:
                    if still_login_helper:
                        still_on_login = bool(still_login_helper(page))
                    else:
                        still_on_login = "/login" in str(page.url).lower()
                except Exception:
                    still_on_login = "/login" in str(page.url).lower()

                # Fallback kecil kalau helper hanya mengisi form tapi belum submit.
                if still_on_login:
                    try:
                        clicked = False

                        if "_custom_smoke_click_selector_v2" in globals():
                            clicked, marker = _custom_smoke_click_selector_v2(
                                page,
                                [
                                    'button[type="submit"]',
                                    'button:has-text("Login")',
                                    'button:has-text("Masuk")',
                                    'button:has-text("Sign In")',
                                    'button:has-text("Submit")',
                                    '[role="button"]:has-text("Login")',
                                    '[role="button"]:has-text("Masuk")',
                                ],
                                timeout=5000,
                            )

                        if not clicked:
                            page.keyboard.press("Enter")

                        try:
                            page.wait_for_load_state("networkidle", timeout=30000)
                        except Exception:
                            pass

                        page.wait_for_timeout(3000)
                    except Exception:
                        pass

                try:
                    if still_login_helper:
                        still_on_login = bool(still_login_helper(page))
                    else:
                        still_on_login = "/login" in str(page.url).lower()
                except Exception:
                    still_on_login = "/login" in str(page.url).lower()

                if still_on_login:
                    diagnostics = ""
                    try:
                        if "_custom_smoke_collect_page_diagnostics_v2" in globals():
                            diagnostics = _custom_smoke_collect_page_diagnostics_v2(page)
                    except Exception:
                        diagnostics = ""

                    raise RuntimeError(
                        "Registered login helper executed but page is still on login page\n" + diagnostics
                    )

                add_tc("TC-004", "PASS", "Authenticated session established")
                return

            except Exception as exc:
                add_tc("TC-003B", "NEED REVIEW", "Registered login helper fallback: " + str(exc))

        if _CUSTOM_SMOKE_PREVIOUS_PERFORM_LOGIN_V2:
            return _CUSTOM_SMOKE_PREVIOUS_PERFORM_LOGIN_V2(page, username, password, add_tc)

        raise RuntimeError("No login helper available for Custom Smoke Generic UI Runner")

    _CUSTOM_SMOKE_LOGIN_BRIDGE_V3_INSTALLED = True
'''

if "# Custom Smoke Generic Login Bridge V3" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Custom Smoke Generic Login Bridge V3")
else:
    print("Custom Smoke Generic Login Bridge V3 already exists")

print(f"Backup created: {backup_path}")
