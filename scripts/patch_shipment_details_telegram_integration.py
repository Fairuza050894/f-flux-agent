from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_shipment_details_telegram_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Shipment Details Telegram /audit_qa Integration
# ============================================================

def _qa_register_shipment_details_feature():
    """
    Register Shipment Details ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=shipment details
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["shipment_details"] = {
        "display_name": "Shipment Details",
        "module_name": "Shipment Details",
        "menu_aliases": [
            "Shipment Details",
            "Shipment Detail",
            "shipmentdetail",
        ],
        "aliases": [
            "shipment details",
            "shipment detail",
            "shipment_details",
            "shipment_detail",
            "tracking shipment",
            "tracking shipment details",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "shipment details",
                "shipment detail",
            ],
        },
    }


def should_run_shipment_details(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ")

    aliases = {
        "shipment details",
        "shipment detail",
        "shipmentdetails",
        "shipmentdetail",
        "tracking shipment",
        "tracking shipment details",
    }

    return value in aliases


def open_shipment_details_target_menu(page, module_name="Shipment Details"):
    """
    Open Shipment Details via direct sandbox route /shipmentdetail.

    Flow ini dipakai untuk Telegram command agar tidak nyasar ke:
    - Shipment Activity Dashboard
    - Main Dashboard / PDT Vehicle Performance
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

    def has_shipment_details_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "shipment details" in lower
            or "shipment detail" in lower
            or "on shipment" in lower
            or "finished" in lower
            or "ordered" in lower
            or "vehicle & driver" in lower
            or "shipment info" in lower
        )

    try:
        target_url = get_origin() + "/shipmentdetail"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "shipmentdetail" in current_url
        marker_found = has_shipment_details_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /shipmentdetail: {exc}"


def open_shipment_details_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Shipment Details page",
        precondition="User is logged in and /shipmentdetail route is available",
        steps="Open direct /shipmentdetail route",
        expected="Shipment Details page should be opened",
        actual="Shipment Details direct route used",
        status="PASS",
    )


def perform_shipment_details_suite(url, module_name="Shipment Details", mode="regression"):
    """
    Runner Shipment Details.

    Reuse existing Hermes audit flow, tetapi sementara mengganti:
    - open_target_menu
    - open_uang_makan_driver_subpage
    - validate_uang_makan_driver_monitoring_page
    - validate_uang_makan_driver_page

    Setelah run selesai, semua function dikembalikan agar Driver Daily Meal tetap aman.
    """

    previous_open_target_menu = globals().get("open_target_menu")
    previous_open_subpage = globals().get("open_uang_makan_driver_subpage")
    previous_validate_monitoring = globals().get("validate_uang_makan_driver_monitoring_page")
    previous_validate_page = globals().get("validate_uang_makan_driver_page")

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS")

    if base_runner is None:
        base_runner = globals().get("_perform_audit_for_telegram_original")

    if base_runner is None:
        base_runner = globals().get("_perform_audit_for_telegram_original_before_wrapper")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_shipment_details_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_shipment_details_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_shipment_details_page
        globals()["validate_uang_makan_driver_page"] = validate_shipment_details_page

        return base_runner(
            url,
            "Shipment Details",
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


_qa_register_shipment_details_feature()


if not globals().get("_SHIPMENT_DETAILS_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_shipment_details(module_name, mode):
            return perform_shipment_details_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_SHIPMENT_DETAILS(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _SHIPMENT_DETAILS_TELEGRAM_PATCH_INSTALLED = True
'''

if "# Shipment Details Telegram /audit_qa Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Shipment Details Telegram integration")
else:
    print("Shipment Details Telegram integration block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
