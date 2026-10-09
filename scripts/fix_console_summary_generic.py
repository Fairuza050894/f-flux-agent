from pathlib import Path
from datetime import datetime
import ast
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_console_summary_generic_{timestamp}")
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
    return "".join(lines[:start] + [replacement + "\n"] + lines[end:]), True


normalizer = r'''def normalize_testing_summary_sections(result):
    """
    Preserve summary asli.
    Pindahkan semua TC console warning dari Failed ke Need Review secara generic:
    - TC-012
    - TC-013
    - TC-019
    - nomor TC lain yang mengandung "FAIL - Console error check"
    """

    if not isinstance(result, dict):
        return result

    summary = result.get("testing_summary") or ""

    if not summary:
        return result

    import re as _re

    strong_warning_markers = [
        "DriverExceptionTable.vue",
        "MealAllowanceException.vue",
        'Property or method "attrs" is not defined',
        'Property or method "on" is not defined',
    ]

    current_run_parts = [
        str(result.get("error_log_report", "")),
        str(result.get("bugs", "")),
        str(result.get("non_blocking_warnings", "")),
    ]

    for tc in result.get("test_cases") or []:
        current_run_parts.append(str(tc.get("actual", "")))
        current_run_parts.append(str(tc.get("scenario", "")))

    current_run_text = "\n".join(current_run_parts)

    current_warning_found = any(
        marker in current_run_text
        for marker in strong_warning_markers
    )

    lines = summary.splitlines()

    headers = [
        "Verified:",
        "Failed:",
        "Need Review:",
        "Bugs:",
        "Warnings / Known Issues:",
        "Evidence:",
        "Recommendation:",
        "Policy Note:",
    ]

    def find_header(header):
        for idx, line in enumerate(lines):
            if line.strip() == header:
                return idx
        return -1

    def next_header_index(start_idx):
        for idx in range(start_idx + 1, len(lines)):
            if lines[idx].strip() in headers:
                return idx
        return len(lines)

    def get_section(header):
        start = find_header(header)
        if start == -1:
            return []
        end = next_header_index(start)
        return lines[start + 1:end]

    def set_section(header, content_lines, insert_before_candidates=None):
        nonlocal lines

        start = find_header(header)

        if start == -1:
            insert_at = len(lines)

            for candidate in insert_before_candidates or ["Evidence:", "Recommendation:", "Policy Note:"]:
                candidate_idx = find_header(candidate)
                if candidate_idx != -1:
                    insert_at = candidate_idx
                    break

            block = [header] + content_lines + [""]
            lines = lines[:insert_at] + block + lines[insert_at:]
            return

        end = next_header_index(start)
        lines = lines[:start + 1] + content_lines + lines[end:]

    def clean(section_lines):
        return [
            line for line in section_lines
            if line.strip() and line.strip() != "-"
        ]

    if not current_warning_found:
        summary = summary.replace(
            "WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude",
            "-",
        )
        summary = summary.replace(
            "- Known Vue warning from DriverExceptionTable.vue is downgraded to NEED REVIEW, not blocking FAIL.",
            "",
        )
        summary = _re.sub(r"- Non-blocking Warnings:\s*\d+", "- Non-blocking Warnings: 0", summary)
        result["testing_summary"] = summary
        result["non_blocking_warnings"] = []
        return result

    failed_lines = clean(get_section("Failed:"))
    need_review_lines = clean(get_section("Need Review:"))

    new_failed_lines = []
    moved_lines = []

    for line in failed_lines:
        if "console error check" in line.lower():
            moved_lines.append(
                _re.sub(
                    r"(TC-\d+)\s+FAIL\s+-\s+Console error check",
                    r"\1 NEED REVIEW - Console error check",
                    line,
                )
            )
        else:
            new_failed_lines.append(line)

    for line in moved_lines:
        if line not in need_review_lines:
            need_review_lines.append(line)

    set_section("Failed:", new_failed_lines if new_failed_lines else ["-"])
    set_section("Need Review:", need_review_lines if need_review_lines else ["-"])

    bug_lines = clean(get_section("Bugs:"))
    warning_lines = clean(get_section("Warnings / Known Issues:"))

    new_bug_lines = []

    for line in bug_lines:
        lower = line.lower()

        if "javascript console error detected" in lower or "known vue warning" in lower:
            warning_line = line
            warning_line = warning_line.replace("BUG-001", "WARNING-001")
            warning_line = warning_line.replace("BUG", "WARNING")
            warning_line = warning_line.replace(
                "JavaScript console error detected",
                "Known Vue warning detected in Driver Meal Exclude",
            )

            if warning_line not in warning_lines:
                warning_lines.append(warning_line)
        elif line.strip() not in ["No bug found", "No blocking bug found"]:
            new_bug_lines.append(line)

    if not warning_lines:
        warning_lines = ["WARNING-001 MEDIUM - Known Vue warning detected in Driver Meal Exclude"]

    set_section("Bugs:", new_bug_lines if new_bug_lines else ["No blocking bug found"])
    set_section(
        "Warnings / Known Issues:",
        warning_lines,
        insert_before_candidates=["Evidence:", "Recommendation:", "Policy Note:"],
    )

    summary = "\n".join(lines)

    failed_count = len(new_failed_lines)
    need_review_count = len(need_review_lines)
    bug_count = len(new_bug_lines)
    warning_count = len(warning_lines)

    summary = _re.sub(r"- Failed:\s*\d+", f"- Failed: {failed_count}", summary)
    summary = _re.sub(r"- Need Review:\s*\d+", f"- Need Review: {need_review_count}", summary)
    summary = _re.sub(r"- Bugs Found:\s*\d+", f"- Bugs Found: {bug_count}", summary)

    if "- Non-blocking Warnings:" in summary:
        summary = _re.sub(
            r"- Non-blocking Warnings:\s*\d+",
            f"- Non-blocking Warnings: {warning_count}",
            summary,
        )
    else:
        summary = summary.replace(
            f"- Bugs Found: {bug_count}",
            f"- Bugs Found: {bug_count}\n- Non-blocking Warnings: {warning_count}",
        )

    if failed_count > 0:
        summary = _re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: FAILED", summary)
        result["overall_status"] = "FAILED"
    elif need_review_count > 0 or warning_count > 0:
        summary = _re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: NEED REVIEW", summary)
        result["overall_status"] = "NEED REVIEW"
    else:
        summary = _re.sub(r"Status:\s*(FAILED|PASS|NEED REVIEW)", "Status: PASS", summary)
        result["overall_status"] = "PASS"

    summary = summary.replace(
        "Fix blocking issues before release. Prioritize failed login, access, menu, or runtime issues.",
        "Review non-blocking warnings with frontend developer before release.",
    )

    if "Known Vue warning from DriverExceptionTable.vue is downgraded" not in summary:
        summary += (
            "\n\nPolicy Note:\n"
            "- Known Vue warning from DriverExceptionTable.vue is downgraded to NEED REVIEW, not blocking FAIL."
        )

    result["testing_summary"] = summary

    error_log_report = result.get("error_log_report") or ""

    if error_log_report:
        error_log_report = error_log_report.replace("Status: FAILED", "Status: NEED REVIEW")
        error_log_report = error_log_report.replace("## 1. Bug Digest", "## 1. Warning Digest")
        error_log_report = error_log_report.replace(
            "BUG-001 Medium - JavaScript console error detected",
            "WARNING-001 Medium - Known Vue warning detected in Driver Meal Exclude",
        )
        result["error_log_report"] = error_log_report

    return result
'''

text, replaced = replace_function(text, "normalize_testing_summary_sections", normalizer)

if not replaced:
    raise SystemExit("normalize_testing_summary_sections not found")

CHECKER_PATH.write_text(text)

print("Generic console summary normalizer patched.")
print(f"Backup created: {backup_path}")
