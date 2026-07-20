from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_curl_test_ui_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

if "API cURL Test" not in text:
    text = text.replace(
        '<button class="tab-btn" onclick="showTab(\'custom\')">Custom Smoke Test</button>',
        '<button class="tab-btn" onclick="showTab(\'custom\')">Custom Smoke Test</button>\n'
        '      <button class="tab-btn" onclick="showTab(\'curl\')">API cURL Test</button>',
        1,
    )

    curl_panel = r'''
    <section class="section tab-panel" id="tab-curl">
      <h2>API cURL Test</h2>
      <p class="muted">Paste cURL command untuk testing API atau endpoint di luar registered QA.</p>

      <div class="form-row">
        <div>
          <label>Feature Name</label>
          <input id="curlFeatureName" value="Custom API cURL Test" />
        </div>
        <div>
          <label>Expected Status</label>
          <input id="curlExpectedStatus" value="200" />
        </div>
      </div>

      <div>
        <label>cURL Command</label>
        <textarea id="curlCommand">curl -X GET "https://mobospace-sandbox.pancaran-group.co.id"</textarea>
      </div>

      <br />

      <div>
        <label>Expected Response Contains, one per line, optional</label>
        <textarea id="curlExpectedContains"></textarea>
      </div>

      <br />
      <button id="runCurlBtn" onclick="runCurlTest()">Run cURL Test</button>

      <div class="result-box" id="curlResult">No result yet.</div>
    </section>

'''

    text = text.replace(
        '    <section class="section tab-panel" id="tab-history">',
        curl_panel + '    <section class="section tab-panel" id="tab-history">',
        1,
    )

    curl_function = r'''
    async function runCurlTest() {
      const button = document.getElementById("runCurlBtn");
      const resultBox = document.getElementById("curlResult");

      button.disabled = true;
      resultBox.textContent = "Running API cURL test... Please wait.";

      const expectedContains = document.getElementById("curlExpectedContains").value
        .split("\n")
        .map(item => item.trim())
        .filter(Boolean);

      const payload = {
        feature_name: document.getElementById("curlFeatureName").value,
        mode: "api",
        curl: document.getElementById("curlCommand").value,
        expected_status: parseInt(document.getElementById("curlExpectedStatus").value || "200", 10),
        expected_contains: expectedContains
      };

      try {
        const response = await fetch("/curl-test", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });

        const data = await response.json();
        resultBox.textContent = formatResult(data);
        await loadHistory();
      } catch (error) {
        resultBox.textContent = "Error: " + error.message;
      } finally {
        button.disabled = false;
      }
    }

'''

    text = text.replace(
        '    async function init() {',
        curl_function + '    async function init() {',
        1,
    )

    HTML_PATH.write_text(text)
    print("Inserted API cURL Test UI")
else:
    print("API cURL Test UI already exists. No duplicate inserted.")

print(f"Backup created: {backup_path}")
