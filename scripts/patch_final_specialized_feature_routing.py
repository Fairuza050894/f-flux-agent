from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_final_specialized_routing_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

patch_code = r'''

# ============================================================
# Final Specialized Feature Routing Override
# ============================================================
#
# Tujuan:
# Memastikan command individual selalu masuk ke specialized suite,
# bukan fallback ke generic open_target_menu.
#
# Contoh:
# Notification Management -> perform_notification_management_suite()
# Notification Messages   -> perform_notification_messages_suite()
# MoboMap                 -> perform_mobomap_suite()
# Shipment Details        -> perform_shipment_details_suite()
# Inspection Result       -> perform_inspection_result_suite()
# Driver Daily Meal       -> perform_driver_daily_meal_combined_suite()
# ============================================================

def _qa_final_call_suite(fn, url, module_name, mode):
    try:
        return fn(url, module_name, mode)
    except TypeError:
        try:
            return fn(url=url, module_name=module_name, mode=mode)
        except TypeError:
            try:
                return fn(url, module_name)
            except TypeError:
                return fn(url)


def _qa_final_enrich_and_history(result, url, module_name, mode):
    try:
        enrich_fn = globals().get("enrich_qa_result_with_standard_json")
        if enrich_fn:
            result = enrich_fn(result, url, module_name, mode)
    except Exception as exc:
        if isinstance(result, dict):
            result["standard_json_error"] = str(exc)

    try:
        append_history_fn = globals().get("append_qa_run_history")
        if append_history_fn:
            result = append_history_fn(result, url, module_name, mode)
    except Exception as exc:
        if isinstance(result, dict):
            result["history_error"] = str(exc)

    return result


def _qa_final_match_specialized_suite(module_name, mode=None):
    checks = [
        ("should_run_driver_daily_meal_combined", "perform_driver_daily_meal_combined_suite", "Uang Makan Driver"),
        ("should_run_shipment_details", "perform_shipment_details_suite", "Shipment Details"),
        ("should_run_mobomap", "perform_mobomap_suite", "MoboMap"),
        ("should_run_inspection_result", "perform_inspection_result_suite", "Inspection Result"),
        ("should_run_notification_messages", "perform_notification_messages_suite", "Notification Messages"),
        ("should_run_notification_management", "perform_notification_management_suite", "Notification Management"),
    ]

    for checker_name, suite_name, canonical_module_name in checks:
        checker_fn = globals().get(checker_name)
        suite_fn = globals().get(suite_name)

        if not checker_fn or not suite_fn:
            continue

        try:
            if checker_fn(module_name, mode):
                return suite_fn, canonical_module_name
        except TypeError:
            try:
                if checker_fn(module_name):
                    return suite_fn, canonical_module_name
            except Exception:
                pass
        except Exception:
            pass

    return None, None


if not globals().get("_FINAL_SPECIALIZED_FEATURE_ROUTING_PATCH_INSTALLED"):
    _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING = globals().get("perform_audit_for_telegram")

    def perform_audit_for_telegram(url, module_name="Uang Makan Driver", mode="regression", *args, **kwargs):
        # Utility command tetap ikut wrapper sebelumnya:
        # /audit_qa help
        # /audit_qa list
        # /audit_qa history
        # /audit_qa fitur=all
        utility_checkers = [
            globals().get("should_run_qa_help"),
            globals().get("should_run_qa_list"),
            globals().get("should_run_qa_history"),
            globals().get("should_run_all_features"),
        ]

        for checker_fn in utility_checkers:
            try:
                if checker_fn and checker_fn(module_name, mode):
                    if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING is None:
                        raise RuntimeError("Previous perform_audit_for_telegram runner not found")

                    return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING(
                        url,
                        module_name,
                        mode,
                        *args,
                        **kwargs,
                    )
            except Exception:
                pass

        suite_fn, canonical_module_name = _qa_final_match_specialized_suite(module_name, mode)

        if suite_fn:
            result = _qa_final_call_suite(
                suite_fn,
                url,
                canonical_module_name or module_name,
                mode,
            )

            return _qa_final_enrich_and_history(
                result,
                url,
                canonical_module_name or module_name,
                mode,
            )

        if _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING is None:
            raise RuntimeError("Previous perform_audit_for_telegram runner not found")

        return _PERFORM_AUDIT_FOR_TELEGRAM_BEFORE_FINAL_SPECIALIZED_ROUTING(
            url,
            module_name,
            mode,
            *args,
            **kwargs,
        )

    _FINAL_SPECIALIZED_FEATURE_ROUTING_PATCH_INSTALLED = True
'''

if "# Final Specialized Feature Routing Override" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    CHECKER_PATH.write_text(text)
    print("Inserted Final Specialized Feature Routing Override")
else:
    print("Final Specialized Feature Routing Override already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
