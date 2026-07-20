from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
GATEWAY_PATH = ROOT / "gateway" / "run.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = GATEWAY_PATH.with_name(f"run.py.backup_before_audit_history_parser_{timestamp}")
shutil.copy2(GATEWAY_PATH, backup_path)

text = GATEWAY_PATH.read_text()

patch_code = r'''

# ============================================================
# /audit_qa history Parser Patch
# ============================================================

if not globals().get("_AUDIT_QA_HISTORY_PARSE_PATCH_INSTALLED"):
    _ORIGINAL_PARSE_AUDIT_QA_COMMAND_FOR_HISTORY = globals().get("_parse_audit_qa_command")

    def _parse_audit_qa_command(text: str) -> dict:
        if _ORIGINAL_PARSE_AUDIT_QA_COMMAND_FOR_HISTORY is not None:
            result = _ORIGINAL_PARSE_AUDIT_QA_COMMAND_FOR_HISTORY(text)
        else:
            result = {"mode": "regression", "feature": ""}

        raw = str(text or "").strip()
        lowered = raw.lower().replace("_", "-")

        parts = lowered.split()
        args = parts[1:] if parts and parts[0].startswith("/") else parts
        arg_text = " ".join(args).strip()

        has_explicit_feature = (
            "fitur=" in lowered
            or "feature=" in lowered
            or "module=" in lowered
            or "module_name=" in lowered
        )

        if not has_explicit_feature:
            if arg_text in {
                "history",
                "qa history",
                "run history",
                "riwayat",
                "histori",
                "riwayat qa",
            }:
                result["mode"] = "history"
                result["feature"] = "history"

        return result

    _AUDIT_QA_HISTORY_PARSE_PATCH_INSTALLED = True
'''

if "# /audit_qa history Parser Patch" not in text:
    text = text.rstrip() + "\n" + patch_code + "\n"
    GATEWAY_PATH.write_text(text)
    print("Inserted /audit_qa history parser patch")
else:
    print("/audit_qa history parser patch already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
