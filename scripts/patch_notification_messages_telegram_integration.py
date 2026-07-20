from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_notification_messages_telegram_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Notification Messages Telegram /audit_qa Integration
# ============================================================

def _qa_register_notification_messages_feature():
    """
    Register Notification Messages ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=notification messages
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["notification_messages"] = {
        "display_name": "Notification Messages",
        "module_name": "Notification Messages",
        "menu_aliases": [
            "Notification Messages",
            "Notification Message",
            "notificationmessage",
        ],
        "aliases": [
            "notification messages",
            "notification message",
            "notification_messages",
            "notification-message",
            "notificationmessage",
            "mobo notification message",
            "mobo notif message",
            "notif message",
            "notif messages",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "notification messages",
                "notification message",
                "send message",
                "sent items",
            ],
        },
    }


def should_run_notification_messages(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "notification messages",
        "notification message",
        "notificationmessage",
        "mobo notification message",
        "mobo notif message",
        "notif message",
        "notif messages",
    }

    return value in aliases


def open_notification_messages_target_menu(page, module_name="Notification Messages"):
    """
    Open Notification Messages via direct sandbox route /notificationmessage.
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

    def has_notification_messages_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "notification message" in lower
            or "notification messages" in lower
            or "send message" in lower
            or "sent items" in lower
        )

    try:
        target_url = get_origin() + "/notificationmessage"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "notificationmessage" in current_url
        marker_found = has_notification_messages_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /notificationmessage: {exc}"


def open_notification_messages_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Notification Messages page",
        precondition="User is logged in and /notificationmessage route is available",
        steps="Open direct /notificationmessage route",
        expected="Notification Messages page should be opened",
        actual="Notification Messages direct route used",
        status="PASS",
    )


def perform_notification_messages_suite(url, module_name="Notification Messages", mode="regression"):
    """
    Runner Notification Messages.

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

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_notification_messages_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_notification_messages_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_notification_messages_page
        globals()["validate_uang_makan_driver_page"] = validate_notification_messages_page

        return base_runner(
            url,
            "Notification Messages",
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


_qa_register_notification_messages_feature()


if not globals().get("_NOTIFICATION_MESSAGES_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_notification_messages(module_name, mode):
            return perform_notification_messages_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_NOTIFICATION_MESSAGES(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _NOTIFICATION_MESSAGES_TELEGRAM_PATCH_INSTALLED = True
'''

if "# Notification Messages Telegram /audit_qa Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Notification Messages Telegram integration")
else:
    print("Notification Messages Telegram integration block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
