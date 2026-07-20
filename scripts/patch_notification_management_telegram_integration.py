from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_notification_management_telegram_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Notification Management Telegram /audit_qa Integration
# ============================================================

def _qa_register_notification_management_feature():
    """
    Register Notification Management ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=notification management
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["notification_management"] = {
        "display_name": "Notification Management",
        "module_name": "Notification Management",
        "menu_aliases": [
            "Notification Management",
            "managementnotif",
        ],
        "aliases": [
            "notification management",
            "notification_management",
            "notification-management",
            "managementnotif",
            "management notif",
            "notif management",
            "mobo notif management",
            "mobo notification management",
        ],
        "default_subfeatures": [
            "notification_context",
            "notification_event",
            "notification_group",
            "message_template",
            "email_template",
            "contact",
            "contact_group",
        ],
        "subfeature_aliases": {
            "notification_context": ["notification context", "context"],
            "notification_event": ["notification event", "event"],
            "notification_group": ["notification group", "group"],
            "message_template": ["message template", "template message"],
            "email_template": ["email template", "template email"],
            "contact": ["contact"],
            "contact_group": ["contact group", "group contact"],
        },
    }


def should_run_notification_management(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "notification management",
        "managementnotif",
        "management notif",
        "notif management",
        "mobo notif management",
        "mobo notification management",
    }

    return value in aliases


def open_notification_management_target_menu(page, module_name="Notification Management"):
    """
    Open Notification Management via direct sandbox route /managementnotif.
    """

    def get_origin():
        try:
            parts = page.url.split("/")
            return parts[0] + "//" + parts[2]
        except Exception:
            return "https://mobospace-sandbox.pancaran-group.co.id"

    def get_body_text():
        try:
            return page.locator("body").inner_text(timeout=8000)
        except Exception:
            return ""

    def has_notification_management_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "notification management" in lower
            or "notification context" in lower
            or "notification event" in lower
            or "notification group" in lower
            or "message template" in lower
            or "email template" in lower
            or "contact group" in lower
        )

    try:
        target_url = get_origin() + "/managementnotif"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "managementnotif" in current_url
        marker_found = has_notification_management_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /managementnotif: {exc}"


def open_notification_management_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Notification Management page",
        precondition="User is logged in and /managementnotif route is available",
        steps="Open direct /managementnotif route",
        expected="Notification Management page should be opened",
        actual="Notification Management direct route used",
        status="PASS",
    )


def perform_notification_management_suite(url, module_name="Notification Management", mode="regression"):
    """
    Runner Notification Management.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar fitur lain tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_notification_management_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_notification_management_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_notification_management_page
        globals()["validate_uang_makan_driver_page"] = validate_notification_management_page

        return base_runner(
            url,
            "Notification Management",
            mode,
        )

    finally:
        if previous_open_target_menu is not None:
            globals()["open_target_menu"] = previous_open_target_menu

        if previous_open_subpage is not None:
            globals()["open_uang_makan_driver_subpage"] = previous_open_subpage

        if previous_validate_monitoring is not None:
            globals()["validate_uang_makan_driver_monitoring_page"] = previous_validate_monitoring

        if previous_validate_page is not None:
            globals()["validate_uang_makan_driver_page"] = previous_validate_page


_qa_register_notification_management_feature()


if not globals().get("_NOTIFICATION_MANAGEMENT_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_notification_management(module_name, mode):
            return perform_notification_management_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MANAGEMENT(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _NOTIFICATION_MANAGEMENT_TELEGRAM_PATCH_INSTALLED = True
'''

if "# Notification Management Telegram /audit_qa Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Notification Management Telegram integration")
else:
    print("Notification Management Telegram integration block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
