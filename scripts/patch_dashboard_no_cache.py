from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_dashboard_no_cache_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

old = '''@app.get("/dashboard")
def dashboard_page():
    if not DASHBOARD_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(DASHBOARD_HTML_PATH, media_type="text/html")'''

new = '''@app.get("/dashboard")
def dashboard_page():
    if not DASHBOARD_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(
        DASHBOARD_HTML_PATH,
        media_type="text/html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )'''

if old in text:
    text = text.replace(old, new, 1)
    print("Patched /dashboard with no-cache headers")
elif '"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"' in text:
    print("/dashboard no-cache headers already exist")
else:
    raise RuntimeError("Could not find /dashboard route block to patch")

APP_PATH.write_text(text)

print(f"Backup created: {backup_path}")
