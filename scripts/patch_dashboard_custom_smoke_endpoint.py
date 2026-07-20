from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_custom_smoke_endpoint_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

if "import skills.qa_automation.checker as qa_checker" not in text:
    text = text.replace(
        "from skills.qa_automation import perform_audit_for_telegram",
        "from skills.qa_automation import perform_audit_for_telegram\nimport skills.qa_automation.checker as qa_checker",
        1,
    )

model_code = r'''

class CustomSmokeRequest(BaseModel):
    url: Optional[str] = None
    route: str
    feature_name: str = "Custom Smoke Test"
    expected_texts: Optional[list[str]] = None
    mode: str = "smoke"
'''

endpoint_code = r'''

@app.post("/custom-smoke")
def create_custom_smoke(request: CustomSmokeRequest):
    mode = normalize_text(request.mode or "smoke")

    if mode not in {"smoke", "regression"}:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Unsupported mode",
                "requested_mode": request.mode,
                "supported_modes": ["smoke", "regression"],
            },
        )

    if not request.route:
        raise HTTPException(
            status_code=400,
            detail="route is required",
        )

    url = request.url or DEFAULT_BASE_URL

    if not hasattr(qa_checker, "perform_custom_smoke_test"):
        raise HTTPException(
            status_code=500,
            detail="perform_custom_smoke_test is not available in checker.py",
        )

    result = qa_checker.perform_custom_smoke_test(
        url=url,
        route=request.route,
        expected_texts=request.expected_texts or [],
        feature_name=request.feature_name or "Custom Smoke Test",
        mode=mode,
    )

    standard_json = load_standard_json_from_result(result)

    return {
        "ok": True,
        "type": "custom_smoke",
        "feature_name": request.feature_name,
        "mode": mode,
        "url": url,
        "route": request.route,
        "status": result.get("status"),
        "testing_summary": result.get("testing_summary"),
        "standard_json_path": result.get("standard_json_path"),
        "history_path": result.get("history_path"),
        "report_path": result.get("report_path") or result.get("documentation_path"),
        "screenshot_path": result.get("screenshot_path"),
        "error_log_path": result.get("error_log_path"),
        "standard_json": standard_json,
    }
'''

if "class CustomSmokeRequest(BaseModel):" not in text:
    marker = "class RunRequest(BaseModel):"
    index = text.find(marker)

    if index == -1:
        raise RuntimeError("RunRequest model marker not found")

    next_marker = text.find("\n\napp = FastAPI", index)

    if next_marker == -1:
        raise RuntimeError("FastAPI app marker not found")

    text = text[:next_marker] + model_code + text[next_marker:]
    print("Inserted CustomSmokeRequest model")
else:
    print("CustomSmokeRequest model already exists")

if '@app.post("/custom-smoke")' not in text:
    text = text.rstrip() + "\n" + endpoint_code + "\n"
    print("Inserted /custom-smoke endpoint")
else:
    print("/custom-smoke endpoint already exists")

APP_PATH.write_text(text)

print(f"Backup created: {backup_path}")
