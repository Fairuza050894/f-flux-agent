from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_fix_menu_text_syntax_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

# Fix malformed line:
# menu_text = str(module_name or "") if menu_opened else
pattern = r'(\s*)menu_text = str\(module_name or ""\) if menu_opened else\s*$'

fixed_text, count = re.subn(
    pattern,
    r'\1menu_text = str(module_name or "") if menu_opened else ""',
    text,
    flags=re.MULTILINE,
)

CHECKER_PATH.write_text(fixed_text)

print(f"Fixed malformed menu_text line count: {count}")
print(f"Backup created: {backup_path}")
