from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_repair_metadata_artifacts_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()
lines = text.splitlines(keepends=True)

tree = ast.parse(text)


def find_function(name):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def replace_function(source_text, func_name, replacement):
    local_tree = ast.parse(source_text)
    local_lines = source_text.splitlines(keepends=True)

    target = None
    for node in local_tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            target = node
            break

    if not target:
        return source_text, False

    start = target.lineno - 1
    end = target.end_lineno

    new_lines = local_lines[:start] + [replacement + "\n"] + local_lines[end:]
    return "".join(new_lines), True


robust_enrich_function = r'''def enrich_qa_report_artifacts_with_metadata(result):
    """
    Final enrichment untuk memastikan metadata masuk ke:
    - Markdown report file
    - result["documentation_report"]
    - Excel spreadsheet sheet "Execution Metadata"

    Idempotent:
    - Markdown tidak duplicate jika metadata sudah ada.
    - Excel sheet metadata direcreate agar selalu terbaru.
    """

    result = result or {}

    if not isinstance(result, dict):
        return result

    metadata = result.get("execution_metadata") or {}

    if not metadata:
        return result

    try:
        from pathlib import Path as _Path
    except Exception:
        return result

    # ------------------------------------------------------------
    # Markdown report enrichment
    # ------------------------------------------------------------
    report_path = (
        result.get("report_path")
        or result.get("documentation_path")
    )

    documentation_report = result.get("documentation_report")

    # Prefer actual file content because report file may be written
    # after documentation_report string was generated.
    if report_path and report_path != "-":
        try:
            path = _Path(report_path)
            if path.exists():
                documentation_report = path.read_text(encoding="utf-8")
        except Exception:
            pass

    if documentation_report:
        try:
            enriched_report = inject_metadata_into_markdown_report(
                documentation_report,
                metadata,
            )

            result["documentation_report"] = enriched_report

            if report_path and report_path != "-":
                path = _Path(report_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(enriched_report, encoding="utf-8")
                result["metadata_markdown_enriched"] = True
        except Exception as exc:
            result["metadata_markdown_enriched"] = False
            result["metadata_markdown_error"] = str(exc)

    # ------------------------------------------------------------
    # Excel report enrichment
    # ------------------------------------------------------------
    spreadsheet_path = result.get("spreadsheet_path")

    if spreadsheet_path and spreadsheet_path != "-":
        try:
            update_spreadsheet_with_metadata(spreadsheet_path, metadata)
            result["metadata_excel_enriched"] = True
        except Exception as exc:
            result["metadata_excel_enriched"] = False
            result["metadata_excel_error"] = str(exc)

    return result
'''


robust_wrapper_function = r'''def perform_audit_for_telegram(*args, **kwargs):
    """
    Wrapper final untuk memastikan metadata masuk ke:
    - Telegram testing_summary
    - Markdown report
    - Excel report

    Wrapper ini sengaja tidak mengubah function asli.
    """

    result = _perform_audit_for_telegram_original(*args, **kwargs)

    try:
        if not isinstance(result, dict):
            return result

        # Resolve call arguments safely
        url = (
            kwargs.get("url")
            or kwargs.get("base_url")
            or (args[0] if len(args) > 0 else None)
            or result.get("base_url")
            or "https://mobospace-sandbox.pancaran-group.co.id"
        )

        module_name = (
            kwargs.get("module_name")
            or (args[1] if len(args) > 1 else None)
            or result.get("module_name")
            or result.get("feature")
            or "Uang Makan Driver"
        )

        mode = (
            kwargs.get("mode")
            or (args[2] if len(args) > 2 else None)
            or result.get("mode")
            or "regression"
        )

        environment = (
            kwargs.get("environment")
            or result.get("environment")
            or "Sandbox"
        )

        # Ensure metadata exists in result
        if not result.get("execution_metadata"):
            result["execution_metadata"] = collect_qa_execution_metadata_basic(
                url=url,
                module_name=module_name,
                mode=mode,
                environment=environment,
                result=result,
            )

        # Ensure Telegram summary has metadata
        result["testing_summary"] = inject_metadata_into_testing_summary(
            result.get("testing_summary", ""),
            result.get("execution_metadata", {}),
        )

        # Ensure Markdown and Excel artifacts have metadata
        result = enrich_qa_report_artifacts_with_metadata(result)

    except Exception as exc:
        try:
            result["metadata_enrichment_error"] = str(exc)
        except Exception:
            pass

    return result
'''


# 1. Replace enrich function if exists
text, replaced = replace_function(text, "enrich_qa_report_artifacts_with_metadata", robust_enrich_function)

if not replaced:
    marker = "def build_testing_summary"
    idx = text.find(marker)
    if idx == -1:
        raise SystemExit("Could not find build_testing_summary marker to insert enrich function.")
    text = text[:idx] + robust_enrich_function + "\n\n" + text[idx:]


# 2. Ensure original function exists
tree = ast.parse(text)
has_original = any(
    isinstance(node, ast.FunctionDef) and node.name == "_perform_audit_for_telegram_original"
    for node in tree.body
)

has_wrapper = any(
    isinstance(node, ast.FunctionDef) and node.name == "perform_audit_for_telegram"
    for node in tree.body
)

if has_original:
    # Replace current wrapper with robust wrapper
    text, wrapper_replaced = replace_function(text, "perform_audit_for_telegram", robust_wrapper_function)
    if not wrapper_replaced:
        text += "\n\n" + robust_wrapper_function + "\n"
else:
    # Rename existing perform_audit_for_telegram to original, then append wrapper
    tree = ast.parse(text)
    node = None
    for item in tree.body:
        if isinstance(item, ast.FunctionDef) and item.name == "perform_audit_for_telegram":
            node = item
            break

    if not node:
        raise SystemExit("perform_audit_for_telegram not found")

    local_lines = text.splitlines(keepends=True)
    def_line_idx = node.lineno - 1

    local_lines[def_line_idx] = local_lines[def_line_idx].replace(
        "def perform_audit_for_telegram(",
        "def _perform_audit_for_telegram_original(",
        1,
    )

    insert_at = node.end_lineno
    local_lines = local_lines[:insert_at] + ["\n\n" + robust_wrapper_function + "\n"] + local_lines[insert_at:]

    text = "".join(local_lines)


CHECKER_PATH.write_text(text)

print("Repair completed.")
print(f"Backup created: {backup_path}")
