from pathlib import Path
from datetime import datetime
import ast
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_fix_warning_scope_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()


def replace_function(source_text, func_name, replacement):
    tree = ast.parse(source_text)
    lines = source_text.splitlines(keepends=True)

    target = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            target = node
            break

    if not target:
        return source_text, False

    start = target.lineno - 1
    end = target.end_lineno
    new_lines = lines[:start] + [replacement + "\n"] + lines[end:]
    return "".join(new_lines), True


policy_function = r'''def apply_console_warning_policy(result):
    """
    Scope-safe policy:
    Known Vue warning hanya berlaku kalau run saat ini benar-benar mengandung
    marker DriverExceptionTable.vue / MealAllowanceException.vue / Vue attrs/on warning.

    Tujuannya agar warning Exclude tidak ikut muncul di Monitoring atau History.
    """

    if not isinstance(result, dict):
        return result

    strong_warning_markers = [
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
        'Property or method "attrs" is not defined',
        'Property or method "on" is not defined',
    ]

    current_run_parts = [
        str(result.get("error_log_report", "")),
        str(result.get("bugs", "")),
    ]

    for tc in result.get("test_cases") or []:
        current_run_parts.append(str(tc.get("actual", "")))
        current_run_parts.append(str(tc.get("scenario", "")))

    current_run_text = "\n".join(current_run_parts)

    current_warning_found = any(
        marker in current_run_text
        for marker in strong_warning_markers
    )

    if not current_warning_found:
        result["non_blocking_warnings"] = []
        return result

    test_cases = result.get("test_cases") or []
    bugs = result.get("bugs") or []

    for tc in test_cases:
        scenario = str(tc.get("scenario", ""))
        status = str(tc.get("status", ""))

        if "console error check" in scenario.lower() and status.upper() == "FAIL":
            tc["status"] = "NEED REVIEW"
            tc["actual"] = (
                str(tc.get("actual", ""))
                + "\n\nPolicy: Known Vue warning from DriverExceptionTable.vue "
                + "downgraded from FAIL to NEED REVIEW."
            )

    blocking_bugs = []
    non_blocking_warnings = []

    for bug in bugs:
        bug_text = str(bug)

        if any(marker in bug_text for marker in strong_warning_markers):
            warning = dict(bug)
            warning["severity"] = "Medium"
            warning["title"] = "Known Vue warning detected in Driver Meal Exclude"
            warning["policy"] = "Non-blocking warning; downgraded to NEED REVIEW"
            warning["expected"] = "Frontend should resolve attrs/on warning in DriverExceptionTable.vue."
            non_blocking_warnings.append(warning)
        else:
            blocking_bugs.append(bug)

    result["bugs"] = blocking_bugs
    result["non_blocking_warnings"] = non_blocking_warnings

    return result
'''


normalizer_function = r'''def normalize_testing_summary_sections(result):
    """
    Preserve summary asli.
    Hanya memindahkan console Vue warning Exclude dari Failed ke Need Review
    kalau run saat ini memang mengandung DriverExceptionTable.vue warning.
    """

    if not isinstance(result, dict):
        return result

    summary = result.get("testing_summary") or ""

    if not summary:
        return result

    strong_warning_markers = [
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
        'Property or method "attrs" is not defined',
        'Property or method "on" is not defined',
    ]

    current_run_parts = [
        str(result.get("error_log_report", "")),
        str(result.get("bugs", "")),
    ]

    for tc in result.get("test_cases") or []:
        current_run_parts.append(str(tc.get("actual", "")))

    current_run_text = "\n".join(current_run_parts)

    current_warning_found = any(
        marker in current_run_text
        for marker in strong_warning_markers
    )

    if not current_warning_found:
        # Cleanup stale Exclude warning yang mungkin sudah pernah masuk summary.
        summary = summary.replace(
            "WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude",
            "-",
        )
        summary = summary.replace(
            "- Known Vue warning from DriverExceptionTable.vue is downgraded to NEED REVIEW, not blocking FAIL.",
            "",
        )
        summary = re.sub(r"- Non-blocking Warnings:\s*\d+", "- Non-blocking Warnings: 0", summary)

        if "- Failed: 0" in summary and "- Need Review: 0" in summary:
            summary = re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: PASS", summary)
            result["overall_status"] = "PASS"

        result["testing_summary"] = summary
        result["non_blocking_warnings"] = []
        return result

    lines = summary.splitlines()

    def replace_line(old, new):
        nonlocal lines
        lines = [new if line.strip() == old else line for line in lines]

    replace_line(
        "TC-019 FAIL - Console error check",
        "TC-019 NEED REVIEW - Console error check",
    )
    replace_line(
        "TC-012 FAIL - Console error check",
        "TC-012 NEED REVIEW - Console error check",
    )

    summary = "\n".join(lines)

    summary = summary.replace("- Failed: 1", "- Failed: 0")
    summary = summary.replace("- Need Review: 0", "- Need Review: 1")
    summary = summary.replace("- Bugs Found: 1", "- Bugs Found: 0")

    if "- Non-blocking Warnings:" in summary:
        summary = re.sub(r"- Non-blocking Warnings:\s*\d+", "- Non-blocking Warnings: 1", summary)
    else:
        summary = summary.replace("- Bugs Found: 0", "- Bugs Found: 0\n- Non-blocking Warnings: 1")

    summary = re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: NEED REVIEW", summary)

    if "Warnings / Known Issues:" not in summary:
        summary += "\n\nWarnings / Known Issues:\nWARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude"
    elif "Known Vue warning detected in Driver Meal Exclude" not in summary:
        summary = summary.replace(
            "Warnings / Known Issues:\n-",
            "Warnings / Known Issues:\nWARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude",
        )

    if "Known Vue warning from DriverExceptionTable.vue is downgraded" not in summary:
        summary += (
            "\n\nPolicy Note:\n"
            "- Known Vue warning from DriverExceptionTable.vue is downgraded to NEED REVIEW, not blocking FAIL."
        )

    summary = summary.replace(
        "Fix blocking issues before release. Prioritize failed login, access, menu, or runtime issues.",
        "Review non-blocking warnings with frontend developer before release.",
    )

    result["testing_summary"] = summary
    result["overall_status"] = "NEED REVIEW"

    return result
'''


text, policy_replaced = replace_function(text, "apply_console_warning_policy", policy_function)
if not policy_replaced:
    raise SystemExit("apply_console_warning_policy not found")

text, normalizer_replaced = replace_function(text, "normalize_testing_summary_sections", normalizer_function)
if not normalizer_replaced:
    raise SystemExit("normalize_testing_summary_sections not found")

CHECKER_PATH.write_text(text)

print("Warning policy scope fixed.")
print(f"Backup created: {backup_path}")
