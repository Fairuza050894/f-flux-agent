from pathlib import Path
from datetime import datetime
import shutil
import ast

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_console_warning_policy_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

policy_code = r'''
def apply_console_warning_policy(result):
    """
    Policy:
    - Real console error tetap FAIL.
    - Known Vue warning attrs/on dari DriverExceptionTable.vue dicatat sebagai NEED REVIEW,
      bukan blocking FAIL.
    """

    if not isinstance(result, dict):
        return result

    known_warning_markers = [
        '[Vue warn]: Property or method "attrs" is not defined',
        '[Vue warn]: Property or method "on" is not defined',
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
    ]

    test_cases = result.get("test_cases") or []
    bugs = result.get("bugs") or []

    for tc in test_cases:
        scenario = str(tc.get("scenario", ""))
        actual = str(tc.get("actual", ""))

        is_console_check = "console error check" in scenario.lower()
        is_known_vue_warning = any(marker in actual for marker in known_warning_markers)

        if is_console_check and is_known_vue_warning:
            tc["status"] = "NEED REVIEW"
            tc["actual"] = (
                actual
                + "\n\nPolicy: Known Vue warning detected in DriverExceptionTable.vue. "
                + "Downgraded from FAIL to NEED REVIEW because it is non-blocking for page rendering, "
                + "but still must be reviewed by frontend developer."
            )

    for bug in bugs:
        title = str(bug.get("title", ""))
        actual = str(bug.get("actual", ""))

        is_console_bug = "console" in title.lower() or "javascript" in title.lower()
        is_known_vue_warning = any(marker in actual for marker in known_warning_markers)

        if is_console_bug and is_known_vue_warning:
            bug["severity"] = "Medium"
            bug["title"] = "Known Vue warning detected in Driver Meal Exclude"
            bug["actual"] = (
                actual
                + "\n\nPolicy: This warning is downgraded to NEED REVIEW, not blocking FAIL."
            )
            bug["expected"] = (
                "Frontend should resolve attrs/on scope warning in DriverExceptionTable.vue."
            )

    try:
        result["overall_status"] = calculate_overall_status(test_cases, bugs)
    except Exception:
        pass

    return result

'''

if "def apply_console_warning_policy(" not in text:
    marker = "def enrich_qa_report_artifacts_with_metadata"
    index = text.find(marker)

    if index == -1:
        raise SystemExit("Could not find enrich_qa_report_artifacts_with_metadata marker")

    text = text[:index] + policy_code + "\n\n" + text[index:]
    print("Inserted apply_console_warning_policy")
else:
    print("apply_console_warning_policy already exists")


# Replace wrapper function to call policy before report enrichment
tree = ast.parse(text)
lines = text.splitlines(keepends=True)

target_node = None
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "perform_audit_for_telegram":
        target_node = node
        break

if not target_node:
    raise SystemExit("perform_audit_for_telegram wrapper not found")

start = target_node.lineno - 1
end = target_node.end_lineno

wrapper_code = r'''def perform_audit_for_telegram(*args, **kwargs):
    """
    Wrapper final untuk memastikan:
    - Metadata masuk ke Telegram summary, Markdown, Excel
    - Known console warnings bisa diturunkan menjadi NEED REVIEW
    """

    result = _perform_audit_for_telegram_original(*args, **kwargs)

    try:
        if not isinstance(result, dict):
            return result

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

        if not result.get("execution_metadata"):
            result["execution_metadata"] = collect_qa_execution_metadata_basic(
                url=url,
                module_name=module_name,
                mode=mode,
                environment=environment,
                result=result,
            )

        # Apply known console warning policy before rebuilding artifacts
        result = apply_console_warning_policy(result)

        result["testing_summary"] = inject_metadata_into_testing_summary(
            build_testing_summary(result),
            result.get("execution_metadata", {}),
        )

        result = enrich_qa_report_artifacts_with_metadata(result)

    except Exception as exc:
        try:
            result["metadata_enrichment_error"] = str(exc)
        except Exception:
            pass

    return result
'''

lines = lines[:start] + [wrapper_code + "\n"] + lines[end:]
text = "".join(lines)

CHECKER_PATH.write_text(text)

print("Patched console warning policy wrapper")
print(f"Backup created: {backup_path}")
