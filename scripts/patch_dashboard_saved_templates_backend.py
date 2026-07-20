from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_saved_templates_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

route_code = r'''

# ============================================================
# Saved QA Test Case Templates
# ============================================================

from typing import Optional as _TemplateOptional, Dict as _TemplateDict, Any as _TemplateAny
from pydantic import BaseModel as _TemplateBaseModel


class QATestTemplateRequest(_TemplateBaseModel):
    id: _TemplateOptional[str] = None
    type: str
    name: str
    description: _TemplateOptional[str] = ""
    payload: _TemplateDict[str, _TemplateAny]


def _qa_templates_root():
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    target = root / "skills" / "qa_automation" / "artifacts" / "templates"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _qa_templates_path():
    return _qa_templates_root() / "qa_test_templates.json"


def _qa_template_slug(value):
    import re
    from datetime import datetime

    base = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "template").lower()).strip("_")
    base = base or "template"
    return base + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")


def _qa_read_templates():
    import json

    path = _qa_templates_path()

    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("templates"), list):
            return data.get("templates")
    except Exception:
        pass

    return []


def _qa_write_templates(items):
    import json

    path = _qa_templates_path()
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


@app.get("/test-templates")
def list_test_templates(type: str = "all"):
    items = _qa_read_templates()

    type_value = str(type or "all").strip().lower()

    if type_value != "all":
        items = [item for item in items if str(item.get("type", "")).lower() == type_value]

    return {
        "ok": True,
        "total": len(items),
        "items": items,
        "path": str(_qa_templates_path()),
    }


@app.post("/test-templates")
def save_test_template(request: QATestTemplateRequest):
    from datetime import datetime

    template_type = str(request.type or "").strip().lower()
    name = str(request.name or "").strip()

    if template_type not in ["custom_smoke", "api_curl"]:
        raise HTTPException(status_code=400, detail="type must be custom_smoke or api_curl")

    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    items = _qa_read_templates()

    template_id = str(request.id or "").strip()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S WIB")

    if not template_id:
        template_id = _qa_template_slug(name)

    existing_index = None

    for index, item in enumerate(items):
        if str(item.get("id")) == template_id:
            existing_index = index
            break

    new_item = {
        "id": template_id,
        "type": template_type,
        "name": name,
        "description": request.description or "",
        "payload": request.payload or {},
        "updated_at": now,
    }

    if existing_index is not None:
        created_at = items[existing_index].get("created_at") or now
        new_item["created_at"] = created_at
        items[existing_index] = new_item
        action = "updated"
    else:
        new_item["created_at"] = now
        items.insert(0, new_item)
        action = "created"

    path = _qa_write_templates(items)

    return {
        "ok": True,
        "action": action,
        "template": new_item,
        "path": str(path),
    }


@app.delete("/test-templates/{template_id}")
def delete_test_template(template_id: str):
    items = _qa_read_templates()
    before = len(items)
    items = [item for item in items if str(item.get("id")) != str(template_id)]
    path = _qa_write_templates(items)

    return {
        "ok": True,
        "deleted": before - len(items),
        "path": str(path),
    }
'''

if '@app.get("/test-templates")' not in text:
    text = text.rstrip() + "\n" + route_code + "\n"
    APP_PATH.write_text(text)
    print("Inserted saved template endpoints")
else:
    print("Saved template endpoints already exist")

print(f"Backup created: {backup_path}")
