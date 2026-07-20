from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_dashboard_frontend_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

route_code = r'''

FRONTEND_DIR = ROOT / "qa_dashboard" / "frontend"
DASHBOARD_HTML_PATH = FRONTEND_DIR / "dashboard.html"


@app.get("/dashboard")
def dashboard_page():
    if not DASHBOARD_HTML_PATH.exists():
        raise HTTPException(status_code=404, detail="dashboard.html not found")

    return FileResponse(DASHBOARD_HTML_PATH, media_type="text/html")
'''

if '@app.get("/dashboard")' not in text:
    text = text.rstrip() + "\n" + route_code + "\n"
    APP_PATH.write_text(text)
    print("Inserted /dashboard route")
else:
    print("/dashboard route already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
