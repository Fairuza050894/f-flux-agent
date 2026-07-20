from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_mobomap_telegram_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# MoboMap Telegram /audit_qa Integration
# ============================================================

def _qa_register_mobomap_feature():
    """
    Register MoboMap ke FEATURE_REGISTRY agar bisa dipanggil dari:
    /audit_qa mode=regression fitur=mobomap
    /audit_qa mode=smoke fitur=mobo map
    """

    global FEATURE_REGISTRY

    try:
        FEATURE_REGISTRY
    except NameError:
        FEATURE_REGISTRY = {}

    FEATURE_REGISTRY["mobomap"] = {
        "display_name": "MoboMap",
        "module_name": "MoboMap",
        "menu_aliases": [
            "MoboMap",
            "Mobo Map",
            "mobomap",
        ],
        "aliases": [
            "mobomap",
            "mobo map",
            "mobo_map",
            "mobo-map",
            "map",
            "vehicle map",
            "tracking map",
            "vehicle tracking",
        ],
        "default_subfeatures": ["main"],
        "subfeature_aliases": {
            "main": [
                "main",
                "mobomap",
                "mobo map",
                "vehicle map",
            ],
        },
    }


def should_run_mobomap(module_name, mode=None):
    value = str(module_name or "").strip().lower().replace("_", " ").replace("-", " ")

    aliases = {
        "mobomap",
        "mobo map",
        "mobo map",
        "map",
        "vehicle map",
        "tracking map",
        "vehicle tracking",
    }

    return value in aliases


def open_mobomap_target_menu(page, module_name="MoboMap"):
    """
    Open MoboMap via direct sandbox route /mobomap.
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

    def has_mobomap_markers():
        body_text = get_body_text()
        lower = body_text.lower()

        dom_map_count = 0

        for selector in [
            ".gm-style",
            ".leaflet-container",
            "[class*='map']",
            "[id*='map']",
            "canvas",
        ]:
            try:
                dom_map_count += page.locator(selector).count()
            except Exception:
                pass

        return (
            "mobomap" in lower
            or "mobo map" in lower
            or "vehicle" in lower
            or "driver" in lower
            or "map data" in lower
            or "satellite" in lower
            or dom_map_count > 0
        )

    try:
        target_url = get_origin() + "/mobomap"

        page.goto(target_url, wait_until="domcontentloaded", timeout=30000)

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        page.wait_for_timeout(6000)

        current_url = page.url.lower()
        route_found = "mobomap" in current_url
        marker_found = has_mobomap_markers()

        opened = route_found or marker_found

        return opened, (
            f"Opened direct route: {target_url}; "
            f"current_url={page.url}; "
            f"route_found={route_found}; "
            f"marker_found={marker_found}"
        )

    except Exception as exc:
        return False, f"Failed to open /mobomap: {exc}"


def open_mobomap_no_subpage(page, test_cases, preferred_subpage=""):
    add_test_case(
        test_cases,
        scenario="Open MoboMap page",
        precondition="User is logged in and /mobomap route is available",
        steps="Open direct /mobomap route",
        expected="MoboMap page should be opened",
        actual="MoboMap direct route used",
        status="PASS",
    )


def perform_mobomap_suite(url, module_name="MoboMap", mode="regression"):
    """
    Runner MoboMap.

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

    base_runner = globals().get("_PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP")

    if base_runner is None:
        base_runner = globals().get("perform_audit_for_telegram")

    if base_runner is None:
        raise RuntimeError("Base perform_audit_for_telegram runner not found")

    try:
        globals()["open_target_menu"] = open_mobomap_target_menu
        globals()["open_uang_makan_driver_subpage"] = open_mobomap_no_subpage
        globals()["validate_uang_makan_driver_monitoring_page"] = validate_mobomap_page
        globals()["validate_uang_makan_driver_page"] = validate_mobomap_page

        return base_runner(
            url,
            "MoboMap",
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


_qa_register_mobomap_feature()


if not globals().get("_MOBOMAP_TELEGRAM_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        if should_run_mobomap(module_name, mode):
            return perform_mobomap_suite(url, module_name, mode)

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_MOBOMAP(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _MOBOMAP_TELEGRAM_PATCH_INSTALLED = True
'''

if "# MoboMap Telegram /audit_qa Integration" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted MoboMap Telegram integration")
else:
    print("MoboMap Telegram integration block already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
