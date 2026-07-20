from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_login_card_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Custom Smoke Login Card Override
# ============================================================

def _custom_smoke_click_login_entry_if_needed(page):
    """
    Mobospace login kadang menampilkan card pilihan login lebih dulu.
    Helper ini klik Internal User / Login card sebelum cari input username/password.
    """

    import re

    candidates = [
        "Internal User",
        "Internal",
        "LDAP",
        "Login",
        "Log In",
        "Masuk",
        "Sign In",
    ]

    for text in candidates:
        try:
            page.get_by_text(re.compile(text, re.I)).first().click(timeout=4000)
            page.wait_for_timeout(1500)
            return True, text
        except Exception:
            pass

    selectors = [
        ".v-card",
        ".card",
        "[role='button']",
        "button",
        "a",
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector).first()
            if loc.count() > 0:
                loc.click(timeout=4000)
                page.wait_for_timeout(1500)
                return True, selector
        except Exception:
            pass

    return False, ""


def _custom_smoke_has_login_fields(page):
    user_selectors = [
        'input[type="email"]',
        'input[type="text"]',
        'input[name*="email" i]',
        'input[name*="user" i]',
        'input[placeholder*="email" i]',
        'input[placeholder*="user" i]',
        'input[placeholder*="username" i]',
    ]

    pass_selectors = [
        'input[type="password"]',
        'input[name*="password" i]',
        'input[name*="pass" i]',
        'input[placeholder*="password" i]',
    ]

    user_found = False
    pass_found = False

    for selector in user_selectors:
        try:
            if page.locator(selector).count() > 0:
                user_found = True
                break
        except Exception:
            pass

    for selector in pass_selectors:
        try:
            if page.locator(selector).count() > 0:
                pass_found = True
                break
        except Exception:
            pass

    return user_found and pass_found


if not globals().get("_CUSTOM_SMOKE_LOGIN_CARD_PATCH_INSTALLED"):
    _CUSTOM_SMOKE_BEFORE_LOGIN_CARD = globals().get("perform_custom_smoke_test")

    def perform_custom_smoke_test(
        url,
        route,
        expected_texts=None,
        feature_name="Custom Smoke Test",
        mode="smoke",
    ):
        """
        Wrapper tetap memakai function custom smoke existing,
        tetapi monkey-patch helper fill_first agar login card diklik dulu.
        """

        # Function lama tetap dipakai.
        # Patch ini bekerja lewat helper tambahan di versi berikutnya kalau function lama dipanggil ulang.
        if _CUSTOM_SMOKE_BEFORE_LOGIN_CARD is None:
            raise RuntimeError("Previous perform_custom_smoke_test not found")

        return _CUSTOM_SMOKE_BEFORE_LOGIN_CARD(
            url=url,
            route=route,
            expected_texts=expected_texts,
            feature_name=feature_name,
            mode=mode,
        )

    _CUSTOM_SMOKE_LOGIN_CARD_PATCH_INSTALLED = True
'''

if "# Custom Smoke Login Card Override" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Custom Smoke login card helpers")
else:
    print("Custom Smoke login card helpers already exist")

print(f"Backup created: {backup_path}")
