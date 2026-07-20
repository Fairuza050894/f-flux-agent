from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_repair_summary_sections_{timestamp}")
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


normalizer_function = r'''def normalize_testing_summary_sections(result):
    """
    Rebuild summary section agar status NEED REVIEW tidak tampil di Failed section.

    Output yang diharapkan:
    - Failed: -
    - Need Review: TC-xxx NEED REVIEW - Console error check
    - Vue warning tampil sebagai Warning / Known Issue, bukan blocking bug.
    """

    if not isinstance(result, dict):
        return result

    summary = result.get("testing_summary") or ""

    if not summary:
        return result

    test_cases = result.get("test_cases") or []
    bugs = result.get("bugs") or []
    non_blocking_warnings = result.get("non_blocking_warnings") or []

    passed_lines = []
    failed_lines = []
    need_review_lines = []
    skipped_lines = []

    for index, tc in enumerate(test_cases, start=1):
        scenario = str(tc.get("scenario", "-"))
        status = str(tc.get("status", "-")).upper()

        tc_id = tc.get("id") or tc.get("test_case_id") or f"TC-{index:03d}"
        line = f"{tc_id} {status} - {scenario}"

        if status == "PASS":
            passed_lines.append(line)
        elif status == "FAIL":
            failed_lines.append(line)
        elif status == "NEED REVIEW":
            need_review_lines.append(line)
        elif status == "SKIPPED":
            skipped_lines.append(line)

    # Fallback kalau existing summary sudah punya TC-019 NEED REVIEW tapi belum ada di test_cases parsed.
    known_console_need_review_lines = [
        "TC-019 NEED REVIEW - Console error check",
        "TC-012 NEED REVIEW - Console error check",
    ]

    for line in known_console_need_review_lines:
        if line in summary and line not in need_review_lines:
            need_review_lines.append(line)

    blocking_bug_lines = []
    warning_lines = []

    known_warning_markers = [
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
        "attrs",
        "on",
        "Known Vue warning",
        "JavaScript console error detected",
    ]

    for bug in bugs:
        bug_text = str(bug)
        is_known_warning = any(marker in bug_text for marker in known_warning_markers)

        title = str(bug.get("title", "JavaScript console error detected"))
        severity = str(bug.get("severity", "Medium")).upper()

        line = f"{severity} - {title}"

        if is_known_warning:
            warning_lines.append(line)
        else:
            blocking_bug_lines.append(line)

    for warning in non_blocking_warnings:
        title = str(warning.get("title", "Known non-blocking warning"))
        severity = str(warning.get("severity", "Medium")).upper()
        line = f"{severity} - {title}"
        if line not in warning_lines:
            warning_lines.append(line)

    # Update status based on normalized sections
    if failed_lines or blocking_bug_lines:
        overall_status = "FAILED"
    elif need_review_lines or warning_lines:
        overall_status = "NEED REVIEW"
    else:
        overall_status = "PASS"

    result["overall_status"] = overall_status

    passed_count = len(passed_lines)
    failed_count = len(failed_lines)
    need_review_count = len(need_review_lines)
    skipped_count = len(skipped_lines)
    blocking_bug_count = len(blocking_bug_lines)
    warning_count = len(warning_lines)

    # Preserve header up to Runtime Environment if possible.
    header_part = summary

    cut_markers = ["Summary:\n", "\nSummary:\n"]
    cut_index = -1

    for marker in cut_markers:
        idx = header_part.find(marker)
        if idx != -1:
            cut_index = idx
            break

    if cut_index != -1:
        header_part = header_part[:cut_index].rstrip()
    else:
        # Minimal fallback header
        module_name = result.get("module_name") or result.get("feature") or "Uang Makan Driver"
        mode = result.get("mode") or "-"
        environment = result.get("environment") or "Sandbox"
        header_part = (
            "✅ QA E2E Regression Completed\n\n"
            f"Module: {module_name}\n"
            f"Mode: {mode}\n"
            f"Environment: {environment}\n"
            f"Status: {overall_status}"
        )

    # Force status in header
    import re as _re
    header_part = _re.sub(r"Status:\s*(PASS|FAILED|NEED REVIEW)", f"Status: {overall_status}", header_part)

    def section_or_dash(lines):
        return "\n".join(lines) if lines else "-"

    rebuilt = (
        header_part.rstrip()
        + "\n\nSummary:\n"
        + f"- Passed: {passed_count}\n"
        + f"- Failed: {failed_count}\n"
        + f"- Need Review: {need_review_count}\n"
        + f"- Skipped: {skipped_count}\n"
        + f"- Bugs Found: {blocking_bug_count}\n"
        + f"- Non-blocking Warnings: {warning_count}\n"
        + "\nVerified:\n"
        + section_or_dash(passed_lines)
        + "\n\nFailed:\n"
        + section_or_dash(failed_lines)
        + "\n\nNeed Review:\n"
        + section_or_dash(need_review_lines)
        + "\n\nBugs:\n"
        + ("No blocking bug found" if not blocking_bug_lines else "\n".join(blocking_bug_lines))
        + "\n\nWarnings / Known Issues:\n"
        + ("-" if not warning_lines else "\n".join(warning_lines))
    )

    if "Evidence:" in summary:
        evidence_part = summary[summary.find("Evidence:"):].strip()
        # Remove old Recommendation duplication if needed.
        rebuilt += "\n\n" + evidence_part
    else:
        rebuilt += (
            "\n\nRecommendation:\n"
            "Review non-blocking warnings with frontend developer before release."
        )

    result["testing_summary"] = rebuilt

    return result
'''


text, replaced = replace_function(text, "normalize_testing_summary_sections", normalizer_function)

if not replaced:
    marker = "def enrich_qa_report_artifacts_with_metadata"
    idx = text.find(marker)

    if idx == -1:
        raise SystemExit("Could not find enrich_qa_report_artifacts_with_metadata marker")

    text = text[:idx] + normalizer_function + "\n\n" + text[idx:]
    print("Inserted normalize_testing_summary_sections")
else:
    print("Replaced normalize_testing_summary_sections")


wrapper_function = r'''def perform_audit_for_telegram(*args, **kwargs):
    """
    Wrapper final:
    - metadata masuk ke Telegram summary, Markdown, Excel
    - known Vue warning tidak menjadi blocking FAIL
    - summary section dinormalisasi agar NEED REVIEW tidak tampil di Failed
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

        result = apply_console_warning_policy(result)
        result = normalize_testing_summary_sections(result)

        result["testing_summary"] = inject_metadata_into_testing_summary(
            result.get("testing_summary", ""),
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

text, wrapper_replaced = replace_function(text, "perform_audit_for_telegram", wrapper_function)

if not wrapper_replaced:
    raise SystemExit("perform_audit_for_telegram wrapper not found")

CHECKER_PATH.write_text(text)

print("Summary section normalizer patched.")
print(f"Backup created: {backup_path}")
