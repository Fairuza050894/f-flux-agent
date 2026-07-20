from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_template_run_delete_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

old_custom_buttons = '''          <button class="secondary" onclick="loadSelectedTemplate('custom_smoke')">Load Template</button>
          <button onclick="saveCustomSmokeTemplate()">Save Current Form</button>'''

new_custom_buttons = '''          <button class="secondary" onclick="loadSelectedTemplate('custom_smoke')">Load Template</button>
          <button class="secondary" onclick="runSelectedTemplate('custom_smoke')">Run Template</button>
          <button class="secondary" onclick="deleteSelectedTemplate('custom_smoke')">Delete Template</button>
          <button onclick="saveCustomSmokeTemplate()">Save Current Form</button>'''

if "runSelectedTemplate('custom_smoke')" not in text:
    text = text.replace(old_custom_buttons, new_custom_buttons, 1)
    print("Inserted Custom Smoke Run/Delete buttons")
else:
    print("Custom Smoke Run/Delete buttons already exist")


old_curl_buttons = '''          <button class="secondary" onclick="loadSelectedTemplate('api_curl')">Load Template</button>
          <button onclick="saveCurlTemplate()">Save Current Form</button>'''

new_curl_buttons = '''          <button class="secondary" onclick="loadSelectedTemplate('api_curl')">Load Template</button>
          <button class="secondary" onclick="runSelectedTemplate('api_curl')">Run Template</button>
          <button class="secondary" onclick="deleteSelectedTemplate('api_curl')">Delete Template</button>
          <button onclick="saveCurlTemplate()">Save Current Form</button>'''

if "runSelectedTemplate('api_curl')" not in text:
    text = text.replace(old_curl_buttons, new_curl_buttons, 1)
    print("Inserted API cURL Run/Delete buttons")
else:
    print("API cURL Run/Delete buttons already exist")


template_action_js = r'''
    async function runSelectedTemplate(type) {
      const template = getSelectedTemplate(type);
      if (!template) return;

      loadSelectedTemplate(type);

      if (type === "custom_smoke") {
        await runCustomSmoke();
      }

      if (type === "api_curl") {
        await runCurlTest();
      }
    }

    async function deleteSelectedTemplate(type) {
      const template = getSelectedTemplate(type);
      if (!template) return;

      const confirmed = confirm("Hapus template ini?\n\n" + template.name);
      if (!confirmed) return;

      try {
        const response = await fetch("/test-templates/" + encodeURIComponent(template.id), {
          method: "DELETE"
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
          alert("Gagal menghapus template: " + JSON.stringify(data));
          return;
        }

        await loadTemplates();
        alert("Template berhasil dihapus: " + template.name);
      } catch (error) {
        alert("Gagal menghapus template: " + error.message);
      }
    }

'''

if "async function runSelectedTemplate(type)" not in text:
    text = text.replace(
        '    async function saveCustomSmokeTemplate() {',
        template_action_js + '    async function saveCustomSmokeTemplate() {',
        1,
    )
    print("Inserted Run/Delete template JS")
else:
    print("Run/Delete template JS already exists")

HTML_PATH.write_text(text)
print(f"Backup created: {backup_path}")
