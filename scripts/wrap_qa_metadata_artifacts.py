from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_wrap_metadata_artifacts_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

if "def enrich_qa_report_artifacts_with_metadata(" not in text:
    raise SystemExit("enrich_qa_report_artifacts_with_metadata() not found. Run scripts/patch_qa_metadata_reports.py first.")

if "def _perform_audit_for_telegram_original(" in text:
    print("perform_audit_for_telegram is already wrapped")
    raise SystemExit(0)

target = "def perform_audit_for_telegram("
start = text.find(target)

if start == -1:
    raise SystemExit("def perform_audit_for_telegram not found")

# Find end of perform_audit_for_telegram function by next top-level def
next_def = text.find("\ndef ", start + len(target))

if next_def == -1:
    next_def = len(text)

original_block = text[start:next_def]

# Rename original function
renamed_block = original_block.replace(
    "def perform_audit_for_telegram(",
    "def _perform_audit_for_telegram_original(",
    1,
)

wrapper_code = '''

def perform_audit_for_telegram(*args, **kwargs):
    """
    Wrapper untuk memastikan artifact report selalu diperkaya metadata
    sebelum dikirim ke Telegram.

    Ini sengaja dibuat sebagai wrapper agar tidak perlu edit isi function lama.
    """
    result = _perform_audit_for_telegram_original(*args, **kwargs)

    try:
        result = enrich_qa_report_artifacts_with_metadata(result)
    except Exception:
        pass

    return result

'''

new_text = text[:start] + renamed_block + wrapper_code + text[next_def:]

CHECKER_PATH.write_text(new_text)

print("Wrapped perform_audit_for_telegram with metadata artifact enrichment")
print(f"Backup created: {backup_path}")
