from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_template_add_custom_ui_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

css_patch = r'''
    .mode-switch {
      display: flex;
      gap: 8px;
      margin: 8px 0 18px;
      padding: 6px;
      background: #f3f4f6;
      border-radius: 10px;
      width: fit-content;
    }

    .mode-switch button {
      background: transparent;
      color: #374151;
      border: 1px solid transparent;
    }

    .mode-switch button.active {
      background: #2563eb;
      color: white;
    }

    .inline-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 12px;
      margin-bottom: 12px;
    }

    .hidden {
      display: none !important;
    }
'''

if ".mode-switch" not in text:
    text = text.replace("    @media (max-width: 900px) {", css_patch + "\n    @media (max-width: 900px) {", 1)
    print("Inserted mode switch CSS")
else:
    print("Mode switch CSS already exists")

js_patch = r'''
    function setupCustomTemplateModes() {
      setupCustomSmokeModeUi();
      setupCurlModeUi();
    }

    function setupCustomSmokeModeUi() {
      const section = document.getElementById("tab-custom");
      if (!section || document.getElementById("customSmokeModeSwitch")) return;

      const h2 = section.querySelector("h2");
      const switcher = document.createElement("div");
      switcher.id = "customSmokeModeSwitch";
      switcher.className = "mode-switch";
      switcher.innerHTML = `
        <button id="customSmokeTemplateModeBtn" class="active" onclick="showCustomSmokeMode('template')">From Template</button>
        <button id="customSmokeAddModeBtn" onclick="showCustomSmokeMode('add')">Add Custom</button>
      `;
      h2.insertAdjacentElement("afterend", switcher);

      const resultBox = document.getElementById("customResult");

      if (!document.getElementById("customAddActions")) {
        const actions = document.createElement("div");
        actions.id = "customAddActions";
        actions.className = "inline-actions";
        actions.innerHTML = `
          <button onclick="runCustomSmoke()">Run Custom Smoke</button>
          <button class="secondary" onclick="saveCustomSmokeTemplate()">Save as Template</button>
        `;
        resultBox.insertAdjacentElement("beforebegin", actions);
      }

      const originalRunButton = document.getElementById("runCustomBtn");
      if (originalRunButton) {
        originalRunButton.classList.add("hidden");
      }

      showCustomSmokeMode("template");
    }

    function showCustomSmokeMode(mode) {
      const templateRow = document.getElementById("customTemplateSelect")
        ? document.getElementById("customTemplateSelect").closest(".form-row")
        : null;

      const featureRow = document.getElementById("customFeatureName")
        ? document.getElementById("customFeatureName").closest(".form-row")
        : null;

      const routeRow = document.getElementById("customRoute")
        ? document.getElementById("customRoute").closest(".form-row")
        : null;

      const expectedBlock = document.getElementById("expectedTexts")
        ? document.getElementById("expectedTexts").parentElement
        : null;

      const addActions = document.getElementById("customAddActions");
      const templateBtn = document.getElementById("customSmokeTemplateModeBtn");
      const addBtn = document.getElementById("customSmokeAddModeBtn");

      const isTemplate = mode === "template";

      [templateRow].forEach(el => el && el.classList.toggle("hidden", !isTemplate));
      [featureRow, routeRow, expectedBlock, addActions].forEach(el => el && el.classList.toggle("hidden", isTemplate));

      if (templateBtn) templateBtn.classList.toggle("active", isTemplate);
      if (addBtn) addBtn.classList.toggle("active", !isTemplate);
    }

    function setupCurlModeUi() {
      const section = document.getElementById("tab-curl");
      if (!section || document.getElementById("curlModeSwitch")) return;

      const h2 = section.querySelector("h2");
      const switcher = document.createElement("div");
      switcher.id = "curlModeSwitch";
      switcher.className = "mode-switch";
      switcher.innerHTML = `
        <button id="curlTemplateModeBtn" class="active" onclick="showCurlMode('template')">From Template</button>
        <button id="curlAddModeBtn" onclick="showCurlMode('add')">Add Custom</button>
      `;
      h2.insertAdjacentElement("afterend", switcher);

      const resultBox = document.getElementById("curlResult");

      if (!document.getElementById("curlAddActions")) {
        const actions = document.createElement("div");
        actions.id = "curlAddActions";
        actions.className = "inline-actions";
        actions.innerHTML = `
          <button onclick="runCurlTest()">Run cURL Test</button>
          <button class="secondary" onclick="saveCurlTemplate()">Save as Template</button>
        `;
        resultBox.insertAdjacentElement("beforebegin", actions);
      }

      const originalRunButton = document.getElementById("runCurlBtn");
      if (originalRunButton) {
        originalRunButton.classList.add("hidden");
      }

      showCurlMode("template");
    }

    function showCurlMode(mode) {
      const templateRow = document.getElementById("curlTemplateSelect")
        ? document.getElementById("curlTemplateSelect").closest(".form-row")
        : null;

      const featureRow = document.getElementById("curlFeatureName")
        ? document.getElementById("curlFeatureName").closest(".form-row")
        : null;

      const caseRow = document.getElementById("curlCaseType")
        ? document.getElementById("curlCaseType").closest(".form-row")
        : null;

      const commandBlock = document.getElementById("curlCommand")
        ? document.getElementById("curlCommand").parentElement
        : null;

      const expectedContainsBlock = document.getElementById("curlExpectedContains")
        ? document.getElementById("curlExpectedContains").parentElement
        : null;

      const expectedErrorBlock = document.getElementById("curlExpectedErrorContains")
        ? document.getElementById("curlExpectedErrorContains").parentElement
        : null;

      const addActions = document.getElementById("curlAddActions");
      const templateBtn = document.getElementById("curlTemplateModeBtn");
      const addBtn = document.getElementById("curlAddModeBtn");

      const isTemplate = mode === "template";

      [templateRow].forEach(el => el && el.classList.toggle("hidden", !isTemplate));
      [featureRow, caseRow, commandBlock, expectedContainsBlock, expectedErrorBlock, addActions].forEach(el => el && el.classList.toggle("hidden", isTemplate));

      if (templateBtn) templateBtn.classList.toggle("active", isTemplate);
      if (addBtn) addBtn.classList.toggle("active", !isTemplate);
    }

'''

if "function setupCustomTemplateModes()" not in text:
    text = text.replace("    async function init() {", js_patch + "\n    async function init() {", 1)
    print("Inserted From Template / Add Custom JS")
else:
    print("From Template / Add Custom JS already exists")

if "setupCustomTemplateModes();" not in text:
    text = text.replace(
        "      await loadTemplates();",
        "      await loadTemplates();\n      setupCustomTemplateModes();",
        1,
    )
    print("Patched init to setup custom template modes")
else:
    print("init already calls setupCustomTemplateModes()")

HTML_PATH.write_text(text)
print(f"Backup created: {backup_path}")
