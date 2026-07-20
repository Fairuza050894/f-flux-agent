from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(f"dashboard.html.backup_before_agent_flow_panel_{timestamp}")
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text()

css = r'''
    .agent-flow-grid {
      display: grid;
      grid-template-columns: repeat(7, 1fr);
      gap: 10px;
      margin-top: 12px;
    }

    .agent-step {
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 12px;
      background: #f9fafb;
      min-height: 108px;
      position: relative;
    }

    .agent-step-number {
      width: 24px;
      height: 24px;
      border-radius: 999px;
      background: #e5e7eb;
      color: #374151;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: bold;
      margin-bottom: 8px;
    }

    .agent-step-title {
      font-weight: 700;
      font-size: 13px;
      margin-bottom: 6px;
    }

    .agent-step-desc {
      color: #6b7280;
      font-size: 11px;
      line-height: 1.35;
      min-height: 30px;
    }

    .agent-step-status {
      display: inline-block;
      margin-top: 8px;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      background: #e5e7eb;
      color: #374151;
    }

    .agent-step.completed {
      border-color: #bbf7d0;
      background: #f0fdf4;
    }

    .agent-step.completed .agent-step-number,
    .agent-step.completed .agent-step-status {
      background: #dcfce7;
      color: #166534;
    }

    .agent-step.running {
      border-color: #bfdbfe;
      background: #eff6ff;
    }

    .agent-step.running .agent-step-number,
    .agent-step.running .agent-step-status {
      background: #dbeafe;
      color: #1d4ed8;
    }

    .agent-step.failed {
      border-color: #fecaca;
      background: #fef2f2;
    }

    .agent-step.failed .agent-step-number,
    .agent-step.failed .agent-step-status {
      background: #fee2e2;
      color: #991b1b;
    }

    .agent-step.review {
      border-color: #fde68a;
      background: #fffbeb;
    }

    .agent-step.review .agent-step-number,
    .agent-step.review .agent-step-status {
      background: #fef3c7;
      color: #92400e;
    }

    .agent-step.manual {
      border-color: #ddd6fe;
      background: #f5f3ff;
    }

    .agent-step.manual .agent-step-number,
    .agent-step.manual .agent-step-status {
      background: #ede9fe;
      color: #5b21b6;
    }

    .agent-flow-note {
      margin-top: 12px;
      padding: 10px 12px;
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      color: #4b5563;
      font-size: 13px;
    }

    @media (max-width: 1100px) {
      .agent-flow-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }
'''

if ".agent-flow-grid" not in text:
    text = text.replace("</style>", css + "\n  </style>", 1)
    print("Inserted Agent Flow CSS")
else:
    print("Agent Flow CSS already exists")


html = r'''
    <section class="section" id="agentFlowPanel">
      <h2>QA Agent Flow Status</h2>
      <p class="muted">Visual status alur autonomous QA: planning, scenario, execution, evidence, analysis, dan report.</p>

      <div class="agent-flow-grid">
        <div class="agent-step" id="agent-step-planning">
          <div class="agent-step-number">1</div>
          <div class="agent-step-title">Planning</div>
          <div class="agent-step-desc">Menentukan scope, strategy, dan risk.</div>
          <span class="agent-step-status">Not Started</span>
        </div>

        <div class="agent-step" id="agent-step-scenario">
          <div class="agent-step-number">2</div>
          <div class="agent-step-title">Scenario</div>
          <div class="agent-step-desc">Menentukan scenario, case type, dan expected result.</div>
          <span class="agent-step-status">Not Started</span>
        </div>

        <div class="agent-step" id="agent-step-template">
          <div class="agent-step-number">3</div>
          <div class="agent-step-title">Template</div>
          <div class="agent-step-desc">Template / manual input siap dijalankan.</div>
          <span class="agent-step-status">Not Started</span>
        </div>

        <div class="agent-step" id="agent-step-execution">
          <div class="agent-step-number">4</div>
          <div class="agent-step-title">Execution</div>
          <div class="agent-step-desc">Menjalankan UI/API automation.</div>
          <span class="agent-step-status">Not Started</span>
        </div>

        <div class="agent-step" id="agent-step-evidence">
          <div class="agent-step-number">5</div>
          <div class="agent-step-title">Evidence</div>
          <div class="agent-step-desc">Mengumpulkan screenshot, response, log, dan artifact.</div>
          <span class="agent-step-status">Not Started</span>
        </div>

        <div class="agent-step" id="agent-step-analysis">
          <div class="agent-step-number">6</div>
          <div class="agent-step-title">Analysis</div>
          <div class="agent-step-desc">Menganalisis PASS, FAILED, atau NEED REVIEW.</div>
          <span class="agent-step-status">Not Started</span>
        </div>

        <div class="agent-step" id="agent-step-report">
          <div class="agent-step-number">7</div>
          <div class="agent-step-title">Report</div>
          <div class="agent-step-desc">Membuat report, error log, standard JSON, dan history.</div>
          <span class="agent-step-status">Not Started</span>
        </div>
      </div>

      <div class="agent-flow-note" id="agentFlowNote">
        Ready. Pilih runner atau template untuk memulai QA Agent Flow.
      </div>
    </section>

'''

if 'id="agentFlowPanel"' not in text:
    text = text.replace('    <div class="tabs">', html + '    <div class="tabs">', 1)
    print("Inserted Agent Flow HTML")
else:
    print("Agent Flow HTML already exists")


js = r'''
    function setAgentStep(step, status, label) {
      const el = document.getElementById("agent-step-" + step);
      if (!el) return;

      el.classList.remove("completed", "running", "failed", "review", "manual");

      if (status) {
        el.classList.add(status);
      }

      const statusEl = el.querySelector(".agent-step-status");
      if (statusEl) {
        statusEl.textContent = label || "Not Started";
      }
    }

    function resetAgentFlow(note) {
      const steps = ["planning", "scenario", "template", "execution", "evidence", "analysis", "report"];

      steps.forEach(step => {
        setAgentStep(step, "", "Not Started");
      });

      const noteEl = document.getElementById("agentFlowNote");
      if (noteEl) {
        noteEl.textContent = note || "Ready. Pilih runner atau template untuk memulai QA Agent Flow.";
      }
    }

    function startAgentFlow(runnerType) {
      const typeLabel = runnerType || "QA Runner";

      setAgentStep("planning", "completed", "Completed");
      setAgentStep("scenario", "completed", "Completed");

      if (typeLabel === "registered") {
        setAgentStep("template", "completed", "Registered");
      } else if (typeLabel === "template") {
        setAgentStep("template", "completed", "Template");
      } else {
        setAgentStep("template", "manual", "Manual");
      }

      setAgentStep("execution", "running", "Running");
      setAgentStep("evidence", "", "Waiting");
      setAgentStep("analysis", "", "Waiting");
      setAgentStep("report", "", "Waiting");

      const noteEl = document.getElementById("agentFlowNote");
      if (noteEl) {
        noteEl.textContent = "QA Agent Flow running via " + typeLabel + "...";
      }
    }

    function completeAgentFlow(result, runnerType) {
      const status = String(result && result.status ? result.status : "UNKNOWN").toUpperCase();

      setAgentStep("execution", status === "FAILED" ? "failed" : "completed", status === "FAILED" ? "Failed" : "Completed");
      setAgentStep("evidence", "completed", "Collected");

      if (status === "PASS") {
        setAgentStep("analysis", "completed", "PASS");
      } else if (status === "NEED REVIEW") {
        setAgentStep("analysis", "review", "Need Review");
      } else if (status === "FAILED") {
        setAgentStep("analysis", "failed", "Failed");
      } else {
        setAgentStep("analysis", "review", status);
      }

      setAgentStep("report", "completed", "Generated");

      const featureName =
        (result && result.feature && result.feature.name) ||
        (result && result.feature_name) ||
        "-";

      const noteEl = document.getElementById("agentFlowNote");
      if (noteEl) {
        noteEl.textContent = "Completed: " + featureName + " | Status: " + status;
      }
    }

    function failAgentFlow(errorMessage) {
      setAgentStep("execution", "failed", "Failed");
      setAgentStep("evidence", "review", "Partial");
      setAgentStep("analysis", "failed", "Failed");
      setAgentStep("report", "review", "Partial");

      const noteEl = document.getElementById("agentFlowNote");
      if (noteEl) {
        noteEl.textContent = "QA Agent Flow failed: " + errorMessage;
      }
    }

'''

if "function setAgentStep(step, status, label)" not in text:
    text = text.replace("    async function runRegisteredQA() {", js + "\n    async function runRegisteredQA() {", 1)
    print("Inserted Agent Flow JS")
else:
    print("Agent Flow JS already exists")


def patch_function(text, fn_name, runner_type, running_text):
    marker = f"async function {fn_name}()"
    start = text.find(marker)
    if start == -1:
      print(f"{fn_name} not found")
      return text

    next_fn = text.find("\n    async function ", start + len(marker))
    if next_fn == -1:
      next_fn = text.find("\n    function ", start + len(marker))
    if next_fn == -1:
      next_fn = text.find("\n    init();", start + len(marker))
    if next_fn == -1:
      next_fn = len(text)

    chunk = text[start:next_fn]

    if f'startAgentFlow("{runner_type}")' not in chunk:
        chunk = chunk.replace(
            f'resultBox.textContent = "{running_text}";',
            f'resultBox.textContent = "{running_text}";\n      startAgentFlow("{runner_type}");',
            1,
        )
        print(f"Patched {fn_name}: startAgentFlow")

    if f'completeAgentFlow(data, "{runner_type}")' not in chunk:
        chunk = chunk.replace(
            "resultBox.textContent = formatResult(data);",
            f'resultBox.textContent = formatResult(data);\n        completeAgentFlow(data, "{runner_type}");',
            1,
        )
        print(f"Patched {fn_name}: completeAgentFlow")

    if "failAgentFlow(error.message)" not in chunk:
        chunk = chunk.replace(
            'resultBox.textContent = "Error: " + error.message;',
            'resultBox.textContent = "Error: " + error.message;\n        failAgentFlow(error.message);',
            1,
        )
        print(f"Patched {fn_name}: failAgentFlow")

    return text[:start] + chunk + text[next_fn:]


text = patch_function(text, "runRegisteredQA", "registered", "Running registered QA... Please wait.")
text = patch_function(text, "runCustomSmoke", "custom_smoke", "Running custom smoke test... Please wait.")
text = patch_function(text, "runCurlTest", "api_curl", "Running API cURL test... Please wait.")


# Patch runSelectedTemplate agar Agent Flow tahu ini dari template.
if 'startAgentFlow("template");' not in text:
    text = text.replace(
        "      loadSelectedTemplate(type);\n\n      if (type === \"custom_smoke\") {",
        "      loadSelectedTemplate(type);\n      startAgentFlow(\"template\");\n\n      if (type === \"custom_smoke\") {",
        1,
    )
    print("Patched runSelectedTemplate with template flow marker")
else:
    print("runSelectedTemplate already has template flow marker")


HTML_PATH.write_text(text)
print(f"Backup created: {backup_path}")
