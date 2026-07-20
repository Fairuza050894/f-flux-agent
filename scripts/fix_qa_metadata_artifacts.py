from pathlib import Path
from datetime import datetime
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_fix_metadata_artifacts_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

if "def enrich_qa_report_artifacts_with_metadata(" not in text:
    raise SystemExit("enrich_qa_report_artifacts_with_metadata() not found. Run patch_qa_metadata_reports.py first.")

start = text.find("def enrich_qa_report_artifacts_with_metadata(")
end = text.find("\ndef ", start + 1)

if end == -1:
    end = len(text)

replacement = r'''def enrich_qa_report_artifacts_with_metadata(result):
    """
    Final enrichment untuk memastikan metadata masuk ke:
    - Markdown report file
    - result["documentation_report"]
    - Excel spreadsheet sheet "Execution Metadata"

    Dibuat idempotent:
    - Markdown tidak duplicate jika metadata sudah ada.
    - Excel sheet metadata akan direcreate agar selalu terbaru.
    """

    result = result or {}
    metadata = result.get("execution_metadata") or {}

    if not metadata:
        return result

    try:
        from pathlib import Path as _Path
    except Exception:
        return result

    report_path = (
        result.get("report_path")
        or result.get("documentation_path")
    )

    documentation_report = result.get("documentation_report")

    if not documentation_report and report_path and report_path != "-":
        try:
            path = _Path(report_path)
            if path.exists():
                documentation_report = path.read_text(encoding="utf-8")
        except Exception:
            documentation_report = None

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
        except Exception:
            pass

    spreadsheet_path = result.get("spreadsheet_path")

    if spreadsheet_path and spreadsheet_path != "-":
        try:
            update_spreadsheet_with_metadata(spreadsheet_path, metadata)
        except Exception:
            pass

    return result


'''

text = text[:start] + replacement + text[end:]

# Insert final enrichment call before return result in perform_audit_for_telegram
lines = text.splitlines(keepends=True)

func_start = None
for i, line in enumerate(lines):
    if line.startswith("def perform_audit_for_telegram("):
        func_start = i
        break

if func_start is None:
    raise SystemExit("def perform_audit_for_telegram not found")

func_end = len(lines)
for i in range(func_start + 1, len(lines)):
    if lines[i].startswith("def "):
        func_end = i
        break

func_block = "".join(lines[func_start:func_end])

if "Final artifact metadata enrichment before returning to Telegram" not in func_block:
    return_indexes = [
        i for i in range(func_start, func_end)
        if lines[i].strip() == "return result"
    ]

    if not return_indexes:
        raise SystemExit("return result not found inside perform_audit_for_telegram")

    # Insert before the last return result
    idx = return_indexes[-1]
    indent = re.match(r"^(\s*)", lines[idx]).group(1)

    injection = f'''
{indent}# Final artifact metadata enrichment before returning to Telegram
{indent}result = enrich_qa_report_artifacts_with_metadata(result)

'''

    lines = lines[:idx] + [injection] + lines[idx:]
    text = "".join(lines)
    print("Inserted final metadata enrichment before return result")
else:
    text = "".join(lines)
    print("Final metadata enrichment already exists")

CHECKER_PATH.write_text(text)

print("Patch completed")
print(f"Backup created: {backup_path}")
