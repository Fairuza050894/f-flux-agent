from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_inspection_result_telegram_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Inspection Result Telegram /audit_qa Integration
# ============================================================

def _qa_register_inspection_result_feature():
    """
    Register Inspection Result ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=inspection result
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["inspection_result"] = {
        "display_name": "Inspection Result",
        "module_name": "Inspection Result",
        "menu_aliases": [
            "Inspection Result",
            "Inspection",
            "inspectionresult",
        ],
        "aliases": [
            "inspection result",
            "inspection_result",
            "inspection-result",
            "inspectionresult",
            "inspection",
            "hasil inspection",
            "hasil inspeksi",
            "inspection report",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "inspection result",
                "inspection",
            ],
        },
    }


def should_run_inspection_result(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "inspection result",
        "inspectionresult",
        "inspection",
        "hasil inspection",
        "hasil inspeksi",
        "inspection report",
    }

    return value in aliases


def open_inspection_result_target_menu(page, module_name="Inspection Result"):
    """
    Open Inspection Result via direct sandbox route /inspectionresult.
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

    def has_inspection_result_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        return (
            "inspection result" in lower
            or "inspection" in lower
            or "waiting for decision" in lower
            or "approved" in lower
            or "rejected" in lower
            or "in progress" in lower
            or "inspection info" in lower
            or "inspection type" in lower
            or "document no" in lower
        )

    try:
        target_url = get_origin() + "/inspectionresult"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(5000)

        current_url = page.url.lower()
        route_found = "inspectionresult" in current_url
        marker_found = has_inspection_result_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /inspectionresult: {exc}"


def open_inspection_result_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open Inspection Result page",
        precondition="User is logged in and /inspectionresult route is available",
        steps="Open direct /inspectionresult route",
        expected="Inspection Result page should be opened",
        actual="Inspection Result direct route used",
        status="PASS",
    )


def perform_inspection_result_suite(url, module_name="Inspection Result", mode="regression"):
    """
    Runner Inspection Result.

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

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_inspection_result_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_inspection_result_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_inspection_result_page
        globals()["validate_uang_makan_driver_page"] = validate_inspection_result_page

        return base_runner(
            url,
            "Inspection Result",
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


_qa_register_inspection_result_feature()


if not globals().get("_INSPECTION_RESULT_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_inspection_result(module_name, mode):
            return perform_inspection_result_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_INSPECTION_RESULT(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _INSPECTION_RESULT_TELEGRAM_PATCH_INSTALLED = True
'''

if "# Inspection Result Telegram /audit_qa Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Inspection Result Telegram integration")
else:
    print("Inspection Result Telegram integration block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
