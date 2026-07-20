from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_analysis_agent_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")

css = r'''
    .analysis-summary-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 14px 0;
    }

    .analysis-summary-card {
      border: 1px solid #e5e7eb;
      background: #f9fafb;
      border-radius: 10px;
      padding: 12px;
    }

    .analysis-summary-label {
      color: #6b7280;
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .analysis-summary-value {
      font-size: 14px;
      font-weight: 700;
      word-break: break-word;
    }

    .analysis-detail-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }

    .analysis-detail-card {
      border: 1px solid #e5e7eb;
      background: white;
      border-radius: 10px;
      padding: 14px;
    }

    .analysis-detail-card h3 {
      margin: 0 0 10px;
      font-size: 14px;
    }

    .analysis-detail-card p,
    .analysis-detail-card li {
      font-size: 13px;
      line-height: 1.5;
    }

    .analysis-detail-card ul {
      padding-left: 20px;
      margin: 0;
    }

    .severity-low {
      color: #166534;
    }

    .severity-medium {
      color: #92400e;
    }

    .severity-high {
      color: #991b1b;
    }

    @media (max-width: 900px) {
      .analysis-summary-grid,
      .analysis-detail-grid {
        grid-template-columns: 1fr;
      }
    }
'''

if ".analysis-summary-grid" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )
    print("Inserted Analysis Agent CSS")
else:
    print("Analysis Agent CSS already exists")


html = r'''
    <section class="section hidden" id="analysisAgentPanel">
      <h2>Analysis Agent</h2>
      <p class="muted">
        Rule-based analysis of root cause, impact, retry decision,
        and release recommendation.
      </p>

      <div class="analysis-summary-grid">
        <div class="analysis-summary-card">
          <div class="analysis-summary-label">Category</div>
          <div class="analysis-summary-value" id="analysisCategory">-</div>
        </div>

        <div class="analysis-summary-card">
          <div class="analysis-summary-label">Severity</div>
          <div class="analysis-summary-value" id="analysisSeverity">-</div>
        </div>

        <div class="analysis-summary-card">
          <div class="analysis-summary-label">Confidence</div>
          <div class="analysis-summary-value" id="analysisConfidence">-</div>
        </div>

        <div class="analysis-summary-card">
          <div class="analysis-summary-label">Release</div>
          <div class="analysis-summary-value" id="analysisRelease">-</div>
        </div>
      </div>

      <div class="analysis-detail-grid">
        <div class="analysis-detail-card">
          <h3>Possible Root Cause</h3>
          <p id="analysisRootCause">-</p>
        </div>

        <div class="analysis-detail-card">
          <h3>Impact</h3>
          <p id="analysisImpact">-</p>
        </div>

        <div class="analysis-detail-card">
          <h3>Evidence</h3>
          <ul id="analysisEvidence">
            <li>-</li>
          </ul>
        </div>

        <div class="analysis-detail-card">
          <h3>Recommendations</h3>
          <ul id="analysisRecommendations">
            <li>-</li>
          </ul>
        </div>

        <div class="analysis-detail-card">
          <h3>Retry Decision</h3>
          <p id="analysisRetry">-</p>
        </div>

        <div class="analysis-detail-card">
          <h3>Analysis Artifact</h3>
          <p id="analysisArtifact">-</p>
        </div>
      </div>
    </section>

'''

if 'id="analysisAgentPanel"' not in text:
    text = text.replace(
        '    <div class="tabs">',
        html + '    <div class="tabs">',
        1,
    )
    print("Inserted Analysis Agent HTML")
else:
    print("Analysis Agent HTML already exists")


js = r'''
    function renderAnalysisList(elementId, items) {
      const element = document.getElementById(elementId);
      if (!element) return;

      const values = Array.isArray(items) && items.length
        ? items
        : ["-"];

      element.innerHTML = values
        .map(item => "<li>" + escapeHtml(item) + "</li>")
        .join("");
    }

    function renderAnalysisAgent(responseData) {
      const panel = document.getElementById("analysisAgentPanel");
      const analysis = responseData && responseData.analysis
        ? responseData.analysis
        : {};

      if (!panel) return;

      panel.classList.remove("hidden");

      document.getElementById("analysisCategory").textContent =
        analysis.category || "-";

      const severityEl = document.getElementById("analysisSeverity");
      severityEl.textContent = analysis.severity || "-";
      severityEl.classList.remove(
        "severity-low",
        "severity-medium",
        "severity-high"
      );

      const severity = String(analysis.severity || "").toLowerCase();

      if (severity) {
        severityEl.classList.add("severity-" + severity);
      }

      document.getElementById("analysisConfidence").textContent =
        analysis.confidence || "-";

      document.getElementById("analysisRelease").textContent =
        analysis.release_recommendation || "-";

      document.getElementById("analysisRootCause").textContent =
        analysis.root_cause || "-";

      document.getElementById("analysisImpact").textContent =
        analysis.impact || "-";

      document.getElementById("analysisRetry").textContent =
        analysis.retry_decision || "-";

      document.getElementById("analysisArtifact").textContent =
        responseData.analysis_path || "-";

      renderAnalysisList(
        "analysisEvidence",
        analysis.evidence
      );

      renderAnalysisList(
        "analysisRecommendations",
        analysis.recommendations
      );
    }

    async function runAnalysisAgent(result) {
      setAgentStep("analysis", "running", "Analyzing");

      try {
        const response = await fetch("/analysis/generate", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({result})
        });

        const data = await response.json();

        if (!response.ok || !data.ok) {
          throw new Error(JSON.stringify(data));
        }

        result.analysis = data.analysis;
        result.analysis_path = data.analysis_path;

        renderAnalysisAgent(data);

        const severity = String(
          data.analysis && data.analysis.severity
            ? data.analysis.severity
            : "medium"
        ).toLowerCase();

        const testStatus = String(
          data.analysis && data.analysis.test_status
            ? data.analysis.test_status
            : result.status || "UNKNOWN"
        ).toUpperCase();

        if (testStatus === "PASS") {
          setAgentStep("analysis", "completed", "PASS");
        } else if (
          testStatus === "NEED REVIEW"
          || severity === "medium"
        ) {
          setAgentStep("analysis", "review", "Need Review");
        } else {
          setAgentStep("analysis", "failed", "Failed");
        }

        setAgentStep("report", "completed", "Enriched");

        const noteEl = document.getElementById("agentFlowNote");

        if (noteEl) {
          noteEl.textContent =
            "Analysis completed: "
            + (data.analysis.category || "-")
            + " | Release: "
            + (data.analysis.release_recommendation || "-");
        }

        return data;

      } catch (error) {
        setAgentStep("analysis", "failed", "Analysis Failed");

        const noteEl = document.getElementById("agentFlowNote");

        if (noteEl) {
          noteEl.textContent =
            "Analysis Agent failed: " + error.message;
        }

        console.error("Analysis Agent error:", error);
        return null;
      }
    }

'''

if "async function runAnalysisAgent(result)" not in text:
    text = text.replace(
        "    async function runRegisteredQA() {",
        js + "\n    async function runRegisteredQA() {",
        1,
    )
    print("Inserted Analysis Agent JS")
else:
    print("Analysis Agent JS already exists")


replacements = [
    (
        'completeAgentFlow(data, "registered");',
        'completeAgentFlow(data, "registered");\n'
        '        await runAnalysisAgent(data);',
    ),
    (
        'completeAgentFlow(data, "custom_smoke");',
        'completeAgentFlow(data, "custom_smoke");\n'
        '        await runAnalysisAgent(data);',
    ),
    (
        'completeAgentFlow(data, "api_curl");',
        'completeAgentFlow(data, "api_curl");\n'
        '        await runAnalysisAgent(data);',
    ),
]

for old, new in replacements:
    if new not in text and old in text:
        text = text.replace(old, new, 1)
        print("Patched automatic Analysis Agent:", old)

HTML_PATH.write_text(text, encoding="utf-8")
print(f"Backup created: {backup_path}")
