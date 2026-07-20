from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_curl_negative_case_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

case_type_block = r'''
      <div class="form-row">
        <div>
          <label>Case Type</label>
          <select id="curlCaseType" onchange="onCurlCaseTypeChange()">
            <option value="positive">Positive Case</option>
            <option value="negative">Negative Case</option>
          </select>
        </div>
        <div>
          <label>Negative Case Scenario</label>
          <input id="curlNegativeCaseTitle" placeholder="Optional, isi kalau Negative Case" />
        </div>
      </div>

'''

if 'id="curlCaseType"' not in text:
    text = text.replace(
        '      <div>\n        <label>cURL Command</label>',
        case_type_block + '      <div>\n        <label>cURL Command</label>',
        1,
    )
    print("Inserted Case Type UI")
else:
    print("Case Type UI already exists")

expected_error_block = r'''
      <br />

      <div>
        <label>Expected Error Contains, one per line, optional for negative case</label>
        <textarea id="curlExpectedErrorContains"></textarea>
      </div>

'''

if 'id="curlExpectedErrorContains"' not in text:
    text = text.replace(
        '      <br />\n      <button id="runCurlBtn" onclick="runCurlTest()">Run cURL Test</button>',
        expected_error_block + '      <br />\n      <button id="runCurlBtn" onclick="runCurlTest()">Run cURL Test</button>',
        1,
    )
    print("Inserted Expected Error Contains UI")
else:
    print("Expected Error Contains UI already exists")

case_type_js = r'''
    function onCurlCaseTypeChange() {
      const caseType = document.getElementById("curlCaseType").value;
      const expectedStatus = document.getElementById("curlExpectedStatus");
      const scenario = document.getElementById("curlNegativeCaseTitle");

      if (caseType === "negative") {
        if (expectedStatus.value === "200" || expectedStatus.value.trim() === "") {
          expectedStatus.value = "400";
        }
        scenario.placeholder = "Example: Invalid driver ID should return 404";
      } else {
        if (expectedStatus.value === "400") {
          expectedStatus.value = "200";
        }
        scenario.placeholder = "Optional, isi kalau Negative Case";
      }
    }

'''

if "function onCurlCaseTypeChange()" not in text:
    text = text.replace(
        '    async function runCurlTest() {',
        case_type_js + '    async function runCurlTest() {',
        1,
    )
    print("Inserted Case Type JS")
else:
    print("Case Type JS already exists")

old_payload = '''      const expectedContains = document.getElementById("curlExpectedContains").value
        .split("\\n")
        .map(item => item.trim())
        .filter(Boolean);

      const payload = {
        feature_name: document.getElementById("curlFeatureName").value,
        mode: "api",
        curl: document.getElementById("curlCommand").value,
        expected_status: parseInt(document.getElementById("curlExpectedStatus").value || "200", 10),
        expected_contains: expectedContains
      };'''

new_payload = '''      const expectedContains = document.getElementById("curlExpectedContains").value
        .split("\\n")
        .map(item => item.trim())
        .filter(Boolean);

      const expectedErrorContains = document.getElementById("curlExpectedErrorContains").value
        .split("\\n")
        .map(item => item.trim())
        .filter(Boolean);

      const payload = {
        feature_name: document.getElementById("curlFeatureName").value,
        mode: "api",
        curl: document.getElementById("curlCommand").value,
        expected_status: parseInt(document.getElementById("curlExpectedStatus").value || "200", 10),
        expected_contains: expectedContains,
        test_case_type: document.getElementById("curlCaseType").value,
        negative_case_title: document.getElementById("curlNegativeCaseTitle").value,
        expected_error_contains: expectedErrorContains
      };'''

if "expected_error_contains: expectedErrorContains" not in text:
    text = text.replace(old_payload, new_payload, 1)
    print("Patched runCurlTest payload")
else:
    print("runCurlTest payload already patched")

HTML_PATH.write_text(text)
print(f"Backup created: {backup_path}")
