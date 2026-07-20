from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_open_target_menu_tuple_safe_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

old_line = "            menu_opened, menu_text = open_target_menu(page, module_name)"

new_block = """            menu_result = open_target_menu(page, module_name)

            if isinstance(menu_result, (tuple, list)):
                menu_opened = bool(menu_result[0]) if len(menu_result) > 0 else False
                menu_text = str(menu_result[1]) if len(menu_result) > 1 and menu_result[1] is not None else str(module_name or "")
            else:
                menu_opened = bool(menu_result)
                menu_text = str(module_name or "") if menu_opened else """""

if old_line in text:
    text = text.replace(old_line, new_block, 1)
    print("Patched perform_structured_audit tuple-safe menu handling")
else:
    print("Tuple-safe menu handling line already patched or not found")

patch_code = r'''

# ============================================================
# Notification Management Direct Route for open_target_menu
# ============================================================

def _qa_is_notification_management_module(module_name):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    return value in {
        "notification management",
        "management notif",
        "management notification",
        "notification manage",
        "notif management",
    }


def _qa_direct_open_notification_management_from_generic_menu(page):
    import os
    from urllib.parse import urlparse

    try:
        current_url = page.url or ""
        parsed = urlparse(current_url)

        if parsed.scheme and parsed.netloc:
            base_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            base_url = os.getenv(
                "QA_DEFAULT_URL",
                "https://mobospace-sandbox.pancaran-group.co.id",
            ).rstrip("/")
    except Exception:
        base_url = os.getenv(
            "QA_DEFAULT_URL",
            "https://mobospace-sandbox.pancaran-group.co.id",
        ).rstrip("/")

    target_urls = [
        f"{base_url}/managementnotif",
        f"{base_url}/managementnotif/",
    ]

    markers = [
        "notification management",
        "notification context",
        "notification event",
        "notification group",
        "message template",
        "email template",
        "contact group",
    ]

    for target_url in target_urls:
        try:
            page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )

            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            page.wait_for_timeout(3000)

            try:
                body_text = page.locator("body").inner_text(timeout=15000)
            except Exception:
                body_text = ""

            lowered = str(body_text or "").lower()

            if any(marker in lowered for marker in markers):
                return True, "Notification Management"

        except Exception:
            continue

    return False, ""


if not globals().get("_OPEN_TARGET_MENU_NOTIFICATION_MANAGEMENT_DIRECT_PATCH_INSTALLED"):
    _OPEN_TARGET_MENU_BEFORE_NOTIFICATION_MANAGEMENT_DIRECT = globals().get("open_target_menu")

    def open_target_menu(page, module_name):
        if _qa_is_notification_management_module(module_name):
            opened, menu_text = _qa_direct_open_notification_management_from_generic_menu(page)

            if opened:
                return opened, menu_text

        if _OPEN_TARGET_MENU_BEFORE_NOTIFICATION_MANAGEMENT_DIRECT:
            return _OPEN_TARGET_MENU_BEFORE_NOTIFICATION_MANAGEMENT_DIRECT(page, module_name)

        return False, ""

    _OPEN_TARGET_MENU_NOTIFICATION_MANAGEMENT_DIRECT_PATCH_INSTALLED = True
'''

if "# Notification Management Direct Route for open_target_menu" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    print("Inserted Notification Management direct route for open_target_menu")
else:
    print("Notification Management direct route for open_target_menu already exists")

CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
