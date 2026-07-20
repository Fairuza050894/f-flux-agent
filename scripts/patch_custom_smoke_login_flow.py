from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "skills" / "qa_automation" / "checker.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = CHECKER_PATH.with_name(f"checker.py.backup_before_custom_smoke_login_flow_{timestamp}")
shutil.copy2(CHECKER_PATH, backup_path)

text = CHECKER_PATH.read_text()

old = '''            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            user_ok = fill_first('''

new = '''            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass

            # Mobospace login revamp: klik card/login entry dulu jika form belum tampil.
            try:
                if "_custom_smoke_has_login_fields" in globals() and not _custom_smoke_has_login_fields(page):
                    if "_custom_smoke_click_login_entry_if_needed" in globals():
                        _custom_smoke_click_login_entry_if_needed(page)
                        try:
                            page.wait_for_load_state("networkidle", timeout=15000)
                        except Exception:
                            pass
                        page.wait_for_timeout(1500)
            except Exception:
                pass

            user_ok = fill_first('''

if old in text:
    text = text.replace(old, new, 1)
    print("Patched Custom Smoke login flow before username/password fill")
else:
    print("Target block not found. It may already be patched or function layout differs.")

CHECKER_PATH.write_text(text)

print(f"Backup created: {backup_path}")
