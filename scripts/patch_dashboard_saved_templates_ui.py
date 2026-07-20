from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_saved_templates_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

custom_template_block = r'''
      <div class="form-row">
        <div>
          <label>Saved Custom Smoke Template</label>
          <select id="customTemplateSelect">
            <option value="">No template loaded</option>
          </select>
        </div>
        <div>
          <label>&nbsp;</label>
          <button class="secondary" onclick="loadSelectedTemplate('custom_smoke')">Load Template</button>
          <button onclick="saveCustomSmokeTemplate()">Save Current Form</button>
        </div>
      </div>

'''

if 'id="customTemplateSelect"' not in text:
    text = text.replace(
        '      <h2>Custom Smoke Test</h2>\n',
        '      <h2>Custom Smoke Test</h2>\n' + custom_template_block,
        1,
    )
    print("Inserted Custom Smoke template UI")
else:
    print("Custom Smoke template UI already exists")

curl_template_block = r'''
      <div class="form-row">
        <div>
          <label>Saved API cURL Template</label>
          <select id="curlTemplateSelect">
            <option value="">No template loaded</option>
          </select>
        </div>
        <div>
          <label>&nbsp;</label>
          <button class="secondary" onclick="loadSelectedTemplate('api_curl')">Load Template</button>
          <button onclick="saveCurlTemplate()">Save Current Form</button>
        </div>
      </div>

'''

if 'id="curlTemplateSelect"' not in text:
    text = text.replace(
        '      <h2>API cURL Test</h2>\n',
        '      <h2>API cURL Test</h2>\n' + curl_template_block,
        1,
    )
    print("Inserted API cURL template UI")
else:
    print("API cURL template UI already exists")

template_js = r'''
    let templateCache = [];

    async function loadTemplates() {
      try {
        const response = await fetch("/test-templates?type=all");
        const data = await response.json();
        templateCache = data.items || [];
        renderTemplateSelects();
      } catch (error) {
        console.error("Failed to load templates", error);
      }
    }

    function renderTemplateSelects() {
      const customSelect = document.getElementById("customTemplateSelect");
      const curlSelect = document.getElementById("curlTemplateSelect");

      if (customSelect) {
        customSelect.innerHTML = '<option value="">Select custom smoke template</option>';

        templateCache
          .filter(item => item.type === "custom_smoke")
          .forEach(item => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = item.name;
            customSelect.appendChild(option);
          });
      }

      if (curlSelect) {
        curlSelect.innerHTML = '<option value="">Select API cURL template</option>';

        templateCache
          .filter(item => item.type === "api_curl")
          .forEach(item => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = item.name;
            curlSelect.appendChild(option);
          });
      }
    }

    function getSelectedTemplate(type) {
      const selectId = type === "custom_smoke" ? "customTemplateSelect" : "curlTemplateSelect";
      const select = document.getElementById(selectId);
      const templateId = select ? select.value : "";

      if (!templateId) {
        alert("Pilih template terlebih dahulu.");
        return null;
      }

      const template = templateCache.find(item => item.id === templateId);

      if (!template) {
        alert("Template tidak ditemukan.");
        return null;
      }

      return template;
    }

    function loadSelectedTemplate(type) {
      const template = getSelectedTemplate(type);
      if (!template) return;

      const payload = template.payload || {};

      if (type === "custom_smoke") {
        document.getElementById("customFeatureName").value = payload.feature_name || "";
        document.getElementById("customMode").value = payload.mode || "smoke";
        document.getElementById("customUrl").value = payload.url || "";
        document.getElementById("customRoute").value = payload.route || "";
        document.getElementById("expectedTexts").value = (payload.expected_texts || []).join("\n");
      }

      if (type === "api_curl") {
        document.getElementById("curlFeatureName").value = payload.feature_name || "";
        document.getElementById("curlExpectedStatus").value = payload.expected_status || 200;
        document.getElementById("curlCommand").value = payload.curl || "";
        document.getElementById("curlExpectedContains").value = (payload.expected_contains || []).join("\n");

        if (document.getElementById("curlCaseType")) {
          document.getElementById("curlCaseType").value = payload.test_case_type || "positive";
        }

        if (document.getElementById("curlNegativeCaseTitle")) {
          document.getElementById("curlNegativeCaseTitle").value = payload.negative_case_title || "";
        }

        if (document.getElementById("curlExpectedErrorContains")) {
          document.getElementById("curlExpectedErrorContains").value = (payload.expected_error_contains || []).join("\n");
        }

        if (typeof onCurlCaseTypeChange === "function") {
          onCurlCaseTypeChange();
        }
      }
    }

    async function saveTemplate(type, name, description, payload) {
      const response = await fetch("/test-templates", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          type,
          name,
          description,
          payload
        })
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        alert("Gagal menyimpan template: " + JSON.stringify(data));
        return;
      }

      await loadTemplates();
      alert("Template berhasil disimpan: " + data.template.name);
    }

    async function saveCustomSmokeTemplate() {
      const defaultName = document.getElementById("customFeatureName").value || "Custom Smoke Template";
      const name = prompt("Nama template:", defaultName);

      if (!name) return;

      const expectedTexts = document.getElementById("expectedTexts").value
        .split("\n")
        .map(item => item.trim())
        .filter(Boolean);

      const payload = {
        feature_name: document.getElementById("customFeatureName").value,
        mode: document.getElementById("customMode").value,
        url: document.getElementById("customUrl").value,
        route: document.getElementById("customRoute").value,
        expected_texts: expectedTexts
      };

      await saveTemplate("custom_smoke", name, "Saved from Custom Smoke Test form", payload);
    }

    async function saveCurlTemplate() {
      const defaultName = document.getElementById("curlFeatureName").value || "API cURL Template";
      const name = prompt("Nama template:", defaultName);

      if (!name) return;

      const expectedContains = document.getElementById("curlExpectedContains").value
        .split("\n")
        .map(item => item.trim())
        .filter(Boolean);

      const expectedErrorContains = document.getElementById("curlExpectedErrorContains")
        ? document.getElementById("curlExpectedErrorContains").value
            .split("\n")
            .map(item => item.trim())
            .filter(Boolean)
        : [];

      const payload = {
        feature_name: document.getElementById("curlFeatureName").value,
        mode: "api",
        curl: document.getElementById("curlCommand").value,
        expected_status: parseInt(document.getElementById("curlExpectedStatus").value || "200", 10),
        expected_contains: expectedContains,
        test_case_type: document.getElementById("curlCaseType") ? document.getElementById("curlCaseType").value : "positive",
        negative_case_title: document.getElementById("curlNegativeCaseTitle") ? document.getElementById("curlNegativeCaseTitle").value : "",
        expected_error_contains: expectedErrorContains
      };

      const riskyMethods = ["-X POST", "-X PUT", "-X PATCH", "-X DELETE"];
      const curlUpper = payload.curl.toUpperCase();

      if (riskyMethods.some(method => curlUpper.includes(method))) {
        const confirmed = confirm("Template ini berisi method yang dapat mengubah data. Simpan hanya untuk sandbox/dev. Lanjut?");
        if (!confirmed) return;
      }

      await saveTemplate("api_curl", name, "Saved from API cURL Test form", payload);
    }

'''

if "let templateCache = [];" not in text:
    text = text.replace(
        '    async function init() {',
        template_js + '    async function init() {',
        1,
    )
    print("Inserted template JS")
else:
    print("Template JS already exists")

if "await loadTemplates();" not in text:
    text = text.replace(
        '      await loadHealth();\n      await loadFeatures();\n      await loadHistory();',
        '      await loadHealth();\n      await loadFeatures();\n      await loadHistory();\n      await loadTemplates();',
        1,
    )
    print("Patched init to load templates")
else:
    print("init already loads templates")

HTML_PATH.write_text(text)
print(f"Backup created: {backup_path}")
