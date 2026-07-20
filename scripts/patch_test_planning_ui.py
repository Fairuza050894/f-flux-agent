from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_test_planning_ui_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

css = r'''
    .plan-output {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }

    .plan-card {
      border: 1px solid #e5e7eb;
      background: #f9fafb;
      border-radius: 12px;
      padding: 14px;
    }

    .plan-card h3 {
      margin: 0 0 10px;
      font-size: 15px;
    }

    .plan-card ul,
    .plan-card ol {
      margin: 0;
      padding-left: 20px;
      font-size: 13px;
      line-height: 1.5;
    }

    .scenario-item {
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      background: white;
      padding: 10px;
      margin-bottom: 10px;
      font-size: 13px;
    }

    .scenario-title {
      font-weight: 700;
      margin-bottom: 4px;
    }

    .scenario-meta {
      color: #6b7280;
      font-size: 12px;
      margin-bottom: 6px;
    }

    @media (max-width: 900px) {
      .plan-output {
        grid-template-columns: 1fr;
      }
    }
'''

if ".plan-output" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)
    print("Inserted Test Planning CSS")
else:
    print("Test Planning CSS already exists")


tab_button = '      <button class="tab-btn" onclick="showTab(\'planning\')">Test Planning</button>\n'

if "showTab('planning')" not in text:
    text = text.replace(
        '    <div class="tabs">\n',
        '    <div class="tabs">\n' + tab_button,
        1,
    )
    print("Inserted Test Planning tab button")
else:
    print("Test Planning tab button already exists")


planning_panel = r'''
    <section class="section tab-panel" id="tab-planning">
      <h2>Test Planning & Scenario Generator</h2>
      <p class="muted">Generate scope, scenario, acceptance criteria, dan recommended template dari requirement, route, atau cURL.</p>

      <div class="form-row">
        <div>
          <label>Input Type</label>
          <select id="planInputType">
            <option value="requirement">Requirement / User Story</option>
            <option value="route">Mobospace UI Route</option>
            <option value="api_curl">API cURL</option>
            <option value="mixed">Mixed Requirement + Route + API</option>
          </select>
        </div>
        <div>
          <label>Risk Level</label>
          <select id="planRiskLevel">
            <option value="low">Low</option>
            <option value="medium" selected>Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      <div class="form-row">
        <div>
          <label>Feature Name</label>
          <input id="planFeatureName" placeholder="Example: Driver Meal Exclude Today" />
        </div>
        <div>
          <label>Target Route, optional</label>
          <input id="planTargetRoute" placeholder="Example: /driver-meal or /managementnotif" />
        </div>
      </div>

      <div>
        <label>Requirement / Description</label>
        <textarea id="planRequirement" placeholder="Paste requirement, user story, acceptance criteria, or deployment note here."></textarea>
      </div>

      <br />

      <div>
        <label>API cURL, optional</label>
        <textarea id="planApiCurl" placeholder='Example: curl -X GET "https://..."'></textarea>
      </div>

      <br />

      <button id="generatePlanBtn" onclick="generateTestPlan()">Generate Test Plan</button>

      <div id="planResult" class="plan-output"></div>

      <div class="result-box" id="planRawResult">No test plan generated yet.</div>
    </section>

'''

if 'id="tab-planning"' not in text:
    text = text.replace(
        '    <section class="section tab-panel active" id="tab-registered">',
        planning_panel + '\n    <section class="section tab-panel active" id="tab-registered">',
        1,
    )
    print("Inserted Test Planning panel")
else:
    print("Test Planning panel already exists")


js = r'''
    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderList(items) {
      if (!items || !items.length) return "<p class='muted'>No data.</p>";
      return "<ul>" + items.map(item => "<li>" + escapeHtml(item) + "</li>").join("") + "</ul>";
    }

    function renderScenarios(scenarios) {
      if (!scenarios || !scenarios.length) return "<p class='muted'>No scenario generated.</p>";

      return scenarios.map(item => {
        const steps = item.steps || [];

        return `
          <div class="scenario-item">
            <div class="scenario-title">${escapeHtml(item.id)} - ${escapeHtml(item.title)}</div>
            <div class="scenario-meta">
              Type: ${escapeHtml(item.type)} |
              Case: ${escapeHtml(item.case_type)} |
              Priority: ${escapeHtml(item.priority)} |
              Runner: ${escapeHtml(item.recommended_runner)}
            </div>
            <div><strong>Steps:</strong></div>
            <ol>${steps.map(step => `<li>${escapeHtml(step)}</li>`).join("")}</ol>
            <div style="margin-top:6px;"><strong>Expected:</strong> ${escapeHtml(item.expected_result)}</div>
          </div>
        `;
      }).join("");
    }

    function renderRecommendedTemplates(templates) {
      if (!templates || !templates.length) return "<p class='muted'>No recommended template.</p>";

      return templates.map((item, index) => {
        return `
          <div class="scenario-item">
            <div class="scenario-title">${escapeHtml(item.name)}</div>
            <div class="scenario-meta">Type: ${escapeHtml(item.type)}</div>
            <div>${escapeHtml(item.description || "")}</div>
            <div class="inline-actions">
              <button type="button" onclick="applyRecommendedTemplate(${index})">Apply to Form</button>
              <button type="button" class="secondary" onclick="saveRecommendedTemplate(${index})">Save Template</button>
            </div>
          </div>
        `;
      }).join("");
    }

    let latestGeneratedPlan = null;

    async function generateTestPlan() {
      const button = document.getElementById("generatePlanBtn");
      const resultBox = document.getElementById("planRawResult");
      const resultPanel = document.getElementById("planResult");

      button.disabled = true;
      resultBox.textContent = "Generating test plan...";
      resultPanel.innerHTML = "";

      setAgentStep("planning", "running", "Running");
      setAgentStep("scenario", "", "Waiting");
      setAgentStep("template", "", "Waiting");
      setAgentStep("execution", "", "Not Started");
      setAgentStep("evidence", "", "Not Started");
      setAgentStep("analysis", "", "Not Started");
      setAgentStep("report", "", "Not Started");

      const payload = {
        input_type: document.getElementById("planInputType").value,
        feature_name: document.getElementById("planFeatureName").value,
        requirement: document.getElementById("planRequirement").value,
        target_route: document.getElementById("planTargetRoute").value,
        api_curl: document.getElementById("planApiCurl").value,
        risk_level: document.getElementById("planRiskLevel").value
      };

      try {
        const response = await fetch("/test-plan/generate", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
          throw new Error(JSON.stringify(data));
        }

        latestGeneratedPlan = data;

        resultPanel.innerHTML = `
          <div class="plan-card">
            <h3>Test Scope</h3>
            ${renderList(data.test_scope)}
          </div>

          <div class="plan-card">
            <h3>Acceptance Criteria</h3>
            ${renderList(data.acceptance_criteria)}
          </div>

          <div class="plan-card">
            <h3>Suggested Scenarios</h3>
            ${renderScenarios(data.scenarios)}
          </div>

          <div class="plan-card">
            <h3>Recommended Templates</h3>
            ${renderRecommendedTemplates(data.recommended_templates)}
          </div>
        `;

        resultBox.textContent = JSON.stringify(data, null, 2);

        setAgentStep("planning", "completed", "Completed");
        setAgentStep("scenario", "completed", "Generated");
        setAgentStep("template", data.recommended_templates && data.recommended_templates.length ? "completed" : "review", data.recommended_templates && data.recommended_templates.length ? "Suggested" : "Need Input");
        setAgentStep("report", "completed", "Plan Generated");

        const noteEl = document.getElementById("agentFlowNote");
        if (noteEl) {
          noteEl.textContent = "Test plan generated for: " + data.input.feature_name;
        }

      } catch (error) {
        resultBox.textContent = "Error: " + error.message;
        failAgentFlow(error.message);
      } finally {
        button.disabled = false;
      }
    }

    function applyRecommendedTemplate(index) {
      if (!latestGeneratedPlan || !latestGeneratedPlan.recommended_templates) {
        alert("No generated template available.");
        return;
      }

      const template = latestGeneratedPlan.recommended_templates[index];

      if (!template) {
        alert("Template not found.");
        return;
      }

      const payload = template.payload || {};

      if (template.type === "custom_smoke") {
        showTab("custom");
        showCustomSmokeMode("add");

        document.getElementById("customFeatureName").value = payload.feature_name || "";
        document.getElementById("customMode").value = payload.mode || "smoke";
        document.getElementById("customUrl").value = payload.url || "https://mobospace-sandbox.pancaran-group.co.id";
        document.getElementById("customRoute").value = payload.route || "";
        document.getElementById("expectedTexts").value = (payload.expected_texts || []).join("\n");
      }

      if (template.type === "api_curl") {
        showTab("curl");
        showCurlMode("add");

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

    async function saveRecommendedTemplate(index) {
      if (!latestGeneratedPlan || !latestGeneratedPlan.recommended_templates) {
        alert("No generated template available.");
        return;
      }

      const template = latestGeneratedPlan.recommended_templates[index];

      if (!template) {
        alert("Template not found.");
        return;
      }

      await saveTemplate(
        template.type,
        template.name,
        template.description || "Generated from Test Planning",
        template.payload || {}
      );
    }

'''

if "async function generateTestPlan()" not in text:
    text = text.replace(
        "    async function runRegisteredQA() {",
        js + "\n    async function runRegisteredQA() {",
        1,
    )
    print("Inserted Test Planning JS")
else:
    print("Test Planning JS already exists")


HTML_PATH.write_text(text)
print(f"Backup created: {backup_path}")
