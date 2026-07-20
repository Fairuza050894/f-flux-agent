from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_notification_management_direct_route_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Notification Management Direct Route Override
# ============================================================
#
# Problem:
# Runner kadang gagal menemukan menu "Notification Management"
# walaupun route valid adalah /managementnotif.
#
# Fix:
# Setelah login, langsung buka /managementnotif.
# ============================================================

def _qa_notification_management_get_base_url(page):
    import os
    from urllib.parse import urlparse

    try:
        current_url = page.url or ""
        parsed = urlparse(current_url)

        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass

    return os.getenv(
        "QA_DEFAULT_URL",
        "https://mobospace-sandbox.pancaran-group.co.id",
    ).rstrip("/")


if not globals().get("_NOTIFICATION_MANAGEMENT_DIRECT_ROUTE_PATCH_INSTALLED"):
    _ORIGINAL_OPEN_NOTIFICATION_MANAGEMENT_TARGET_MENU = globals().get(
        "open_notification_management_target_menu"
    )

    def open_notification_management_target_menu(page, *args, **kwargs):
        base_url = _qa_notification_management_get_base_url(page).rstrip("/")

        direct_routes = [
            f"{base_url}/managementnotif",
            f"{base_url}/managementnotif/",
        ]

        page_markers = [
            "NOTIFICATION MANAGEMENT",
            "Notification Management",
            "Notification Context",
            "Notification Event",
            "Notification Group",
            "Message Template",
            "Email Template",
            "Contact Group",
        ]

        last_error = None

        for target_url in direct_routes:
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

                body_text = ""
                try:
                    body_text = page.locator("body").inner_text(timeout=15000)
                except Exception:
                    body_text = ""

                lowered = body_text.lower()

                if any(marker.lower() in lowered for marker in page_markers):
                    return True

            except Exception as exc:
                last_error = exc

        # Fallback ke opener lama kalau direct route gagal.
        if _ORIGINAL_OPEN_NOTIFICATION_MANAGEMENT_TARGET_MENU:
            try:
                return _ORIGINAL_OPEN_NOTIFICATION_MANAGEMENT_TARGET_MENU(
                    page,
                    *args,
                    **kwargs,
                )
            except Exception as exc:
                last_error = exc

        return False

    _NOTIFICATION_MANAGEMENT_DIRECT_ROUTE_PATCH_INSTALLED = True
'''

if "# Notification Management Direct Route Override" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Notification Management direct route override")
else:
    print("Notification Management direct route override already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
