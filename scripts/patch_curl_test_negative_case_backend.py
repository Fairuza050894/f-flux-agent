from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "qa_dashboard" / "backend" / "app.py"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = APP_PATH.with_name(f"app.py.backup_before_curl_negative_case_{timestamp}")
shutil.copy2(APP_PATH, backup_path)

text = APP_PATH.read_text()

# 1. Add request fields
if "test_case_type: str = \"positive\"" not in text:
    text = text.replace(
        "    timeout_seconds: int = 30",
        "    timeout_seconds: int = 30\n"
        "    test_case_type: str = \"positive\"\n"
        "    negative_case_title: _CurlOptional[str] = None\n"
        "    expected_error_contains: _CurlOptional[_CurlList[str]] = None",
        1,
    )
    print("Added negative case fields to CurlTestRequest")
else:
    print("Negative case request fields already exist")

# 2. Add runtime variables
old_expected = "    expected_contains = request.expected_contains or []"
new_expected = """    expected_contains = request.expected_contains or []

    test_case_type = str(getattr(request, "test_case_type", "positive") or "positive").strip().lower()
    if test_case_type not in ["positive", "negative"]:
        test_case_type = "positive"

    negative_case_title = str(getattr(request, "negative_case_title", "") or "").strip()
    expected_error_contains = getattr(request, "expected_error_contains", None) or []

    if test_case_type == "negative":
        for item in expected_error_contains:
            if item not in expected_contains:
                expected_contains.append(item)
"""

if "negative_case_title = str(getattr(request, \"negative_case_title\"" not in text:
    text = text.replace(old_expected, new_expected, 1)
    print("Added negative case runtime variables")
else:
    print("Negative case runtime variables already exist")

# 3. Add test marker
old_parse = '        add_tc("TC-001", "PASS", "Parse cURL command")'
new_parse = '''        add_tc("TC-001", "PASS", "Parse cURL command")

        if test_case_type == "negative":
            scenario_label = negative_case_title or "Negative API scenario"
            add_tc("TC-NEG", "PASS", "Negative case selected: " + scenario_label)
        else:
            add_tc("TC-POS", "PASS", "Positive case selected")'''

if 'add_tc("TC-NEG", "PASS", "Negative case selected:' not in text:
    text = text.replace(old_parse, new_parse, 1)
    print("Added positive/negative case marker")
else:
    print("Positive/negative case marker already exists")

# 4. Add summary info
old_summary = '''        + "- Feature: " + str(feature_name) + "\\n"
        + "- Method: " + str(parsed.get("method", "-")) + "\\n"'''
new_summary = '''        + "- Feature: " + str(feature_name) + "\\n"
        + "- Test Case Type: " + test_case_type.upper() + "\\n"
        + ("- Negative Scenario: " + negative_case_title + "\\n" if test_case_type == "negative" and negative_case_title else "")
        + "- Method: " + str(parsed.get("method", "-")) + "\\n"'''

if '"- Test Case Type: " + test_case_type.upper()' not in text:
    text = text.replace(old_summary, new_summary, 1)
    print("Added case type to testing summary")
else:
    print("Case type already exists in testing summary")

# 5. Add documentation info
old_doc = '''        + "- Status: " + status + "\\n"
        + "- Method: " + str(parsed.get("method", "-")) + "\\n"'''
new_doc = '''        + "- Status: " + status + "\\n"
        + "- Test Case Type: " + test_case_type.upper() + "\\n"
        + ("- Negative Scenario: " + negative_case_title + "\\n" if test_case_type == "negative" and negative_case_title else "")
        + "- Method: " + str(parsed.get("method", "-")) + "\\n"'''

if '"- Test Case Type: " + test_case_type.upper() + "\\\\n"' not in text and '"- Test Case Type: " + test_case_type.upper() + "\\n"' not in text:
    text = text.replace(old_doc, new_doc, 1)
    print("Added case type to documentation report")
else:
    print("Case type already exists in documentation report")

# 6. Add standard JSON fields
old_payload = '''        "mode": mode,
        "status": status,'''
new_payload = '''        "mode": mode,
        "test_case_type": test_case_type,
        "negative_case_title": negative_case_title,
        "expected_error_contains": expected_error_contains,
        "status": status,'''

if '"test_case_type": test_case_type,' not in text:
    text = text.replace(old_payload, new_payload, 1)
    print("Added negative case fields to standard JSON")
else:
    print("Negative case fields already exist in standard JSON")

# 7. Add API response fields
old_result = '''        "mode": mode,
        "testing_summary": testing_summary,'''
new_result = '''        "mode": mode,
        "test_case_type": test_case_type,
        "negative_case_title": negative_case_title,
        "expected_error_contains": expected_error_contains,
        "testing_summary": testing_summary,'''

if '"negative_case_title": negative_case_title,' not in text:
    text = text.replace(old_result, new_result, 1)
    print("Added negative case fields to API response")
else:
    print("Negative case fields already exist in API response")

APP_PATH.write_text(text)
print(f"Backup created: {backup_path}")
