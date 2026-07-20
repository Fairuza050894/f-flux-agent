from pathlib import Path
from datetime import datetime
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = (
    ROOT
    / "qa_dashboard"
    / "frontend"
    / "dashboard.html"
)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_path = HTML_PATH.with_name(
    "dashboard.html.backup_before_run_detail_"
    + timestamp
)

shutil.copy2(
    HTML_PATH,
    backup_path,
)

text = HTML_PATH.read_text(
    encoding="utf-8"
)


css = r'''
    .run-detail-toolbar {
      display: grid;
      grid-template-columns: minmax(240px, 1fr) auto auto;
      gap: 10px;
      align-items: end;
      margin: 12px 0 18px;
      padding: 14px;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      background: #f9fafb;
    }

    .run-detail-section {
      margin-top: 18px;
      border-top: 1px solid #e5e7eb;
      padding-top: 18px;
    }

    .run-detail-summary-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin: 12px 0;
    }

    .run-detail-card {
      border: 1px solid #e5e7eb;
      background: #ffffff;
      border-radius: 10px;
      padding: 12px;
      min-width: 0;
    }

    .run-detail-card-label {
      color: #6b7280;
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .run-detail-card-value {
      font-size: 14px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .run-detail-two-column {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 14px;
    }

    .run-detail-content-card {
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      background: #ffffff;
      padding: 14px;
    }

    .run-detail-content-card h3 {
      margin: 0 0 12px;
      font-size: 15px;
    }

    .run-detail-timeline {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .run-detail-timeline li {
      position: relative;
      padding: 0 0 18px 24px;
      font-size: 13px;
    }

    .run-detail-timeline li::before {
      content: "";
      position: absolute;
      left: 3px;
      top: 5px;
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: #2563eb;
    }

    .run-detail-timeline li::after {
      content: "";
      position: absolute;
      left: 7px;
      top: 17px;
      bottom: 0;
      width: 2px;
      background: #dbeafe;
    }

    .run-detail-timeline li:last-child::after {
      display: none;
    }

    .run-detail-time {
      color: #6b7280;
      font-size: 11px;
      margin-bottom: 3px;
    }

    .run-detail-event-title {
      font-weight: 700;
      margin-bottom: 3px;
    }

    .run-detail-feature {
      display: grid;
      grid-template-columns: 1.7fr repeat(7, minmax(70px, 1fr));
      gap: 8px;
      align-items: center;
      border-bottom: 1px solid #e5e7eb;
      padding: 9px 0;
      font-size: 12px;
    }

    .run-detail-feature:last-child {
      border-bottom: none;
    }

    .run-detail-artifact {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      border-bottom: 1px solid #e5e7eb;
      padding: 10px 0;
      font-size: 13px;
    }

    .run-detail-artifact:last-child {
      border-bottom: none;
    }

    .run-detail-artifact-meta {
      color: #6b7280;
      font-size: 11px;
      margin-top: 3px;
    }

    .run-detail-analysis-list {
      margin: 8px 0 0;
      padding-left: 20px;
      font-size: 13px;
      line-height: 1.5;
    }

    .run-detail-availability {
      border-left: 4px solid #f59e0b;
      background: #fffbeb;
      padding: 12px;
      border-radius: 8px;
      font-size: 13px;
      line-height: 1.5;
    }

    .run-detail-empty {
      color: #6b7280;
      font-size: 13px;
      padding: 12px 0;
    }

    @media (max-width: 1000px) {
      .run-detail-summary-grid,
      .run-detail-two-column {
        grid-template-columns: 1fr 1fr;
      }

      .run-detail-feature {
        grid-template-columns: 1fr 1fr;
      }
    }

    @media (max-width: 700px) {
      .run-detail-toolbar,
      .run-detail-summary-grid,
      .run-detail-two-column {
        grid-template-columns: 1fr;
      }
    }
'''


if ".run-detail-toolbar" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print("Inserted Run Detail CSS")
else:
    print("Run Detail CSS already exists")


controls_html = r'''
      <div class="run-detail-toolbar" id="runDetailToolbar">
        <div>
          <label>Run Detail</label>
          <select id="runDetailExecutionSelect">
            <option value="">Loading run history...</option>
          </select>
        </div>

        <button type="button" onclick="openSelectedRunDetail()">
          View Detail
        </button>

        <button type="button" class="secondary" onclick="loadRunDetailOptions()">
          Refresh Runs
        </button>
      </div>

      <div class="run-detail-section hidden" id="runDetailPanel">
        <h2>Run Detail</h2>
        <p class="muted" id="runDetailSubtitle">
          Select a run to inspect its stored data.
        </p>

        <div class="run-detail-summary-grid" id="runDetailSummary"></div>

        <div class="run-detail-two-column">
          <div class="run-detail-content-card">
            <h3>Execution Timeline</h3>
            <ul class="run-detail-timeline" id="runDetailTimeline"></ul>
          </div>

          <div class="run-detail-content-card">
            <h3>Analysis Agent</h3>
            <div id="runDetailAnalysis"></div>
          </div>
        </div>

        <div class="run-detail-content-card" style="margin-top:14px;">
          <h3>Feature Results</h3>
          <div id="runDetailFeatures"></div>
        </div>

        <div class="run-detail-two-column">
          <div class="run-detail-content-card">
            <h3>Artifacts</h3>
            <div id="runDetailArtifacts"></div>
          </div>

          <div class="run-detail-content-card">
            <h3>Data Availability</h3>
            <div id="runDetailAvailability"></div>
          </div>
        </div>

        <details style="margin-top:14px;">
          <summary>Stored Testing Summary</summary>
          <div class="result-box" id="runDetailTestingSummary">
            No stored summary.
          </div>
        </details>
      </div>
'''


if 'id="runDetailToolbar"' not in text:
    history_heading_pattern = re.compile(
        r'('
        r'<section[^>]*id=["\']tab-history["\'][^>]*>'
        r'.*?'
        r'<h2[^>]*>.*?</h2>'
        r')',
        flags=re.IGNORECASE | re.DOTALL,
    )

    match = history_heading_pattern.search(text)

    if match:
        text = (
            text[:match.end()]
            + "\n"
            + controls_html
            + text[match.end():]
        )

        print(
            "Inserted Run Detail controls into Run History"
        )
    else:
        section_pattern = re.compile(
            r'(<section[^>]*id=["\']tab-history["\'][^>]*>)',
            flags=re.IGNORECASE,
        )

        match = section_pattern.search(text)

        if not match:
            raise RuntimeError(
                "Could not find tab-history section"
            )

        text = (
            text[:match.end()]
            + "\n"
            + controls_html
            + text[match.end():]
        )

        print(
            "Inserted Run Detail controls using fallback"
        )
else:
    print("Run Detail controls already exist")


js = r'''
    function rdEscapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function rdHistoryItems(payload) {
      if (Array.isArray(payload)) {
        return payload;
      }

      if (!payload || typeof payload !== "object") {
        return [];
      }

      for (const key of [
        "runs",
        "history",
        "items",
        "records",
        "data"
      ]) {
        if (Array.isArray(payload[key])) {
          return payload[key];
        }
      }

      return [];
    }

    async function loadRunDetailOptions() {
      const select = document.getElementById(
        "runDetailExecutionSelect"
      );

      if (!select) return;

      select.innerHTML =
        '<option value="">Loading run history...</option>';

      try {
        const response = await fetch("/history");
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(JSON.stringify(payload));
        }

        const runs = rdHistoryItems(payload);

        select.innerHTML = "";

        if (!runs.length) {
          select.innerHTML =
            '<option value="">No run history available</option>';
          return;
        }

        runs.forEach(run => {
          const executionId =
            run.execution_id || "";

          if (!executionId) return;

          const option =
            document.createElement("option");

          option.value = executionId;

          option.textContent = [
            executionId,
            run.feature || "-",
            run.status || "-",
            run.executed_at || run.created_at || "-"
          ].join(" | ");

          select.appendChild(option);
        });

      } catch (error) {
        select.innerHTML =
          '<option value="">Failed to load history</option>';

        console.error(
          "Run Detail history error:",
          error
        );
      }
    }

    function rdSummaryCard(label, value) {
      return `
        <div class="run-detail-card">
          <div class="run-detail-card-label">
            ${rdEscapeHtml(label)}
          </div>
          <div class="run-detail-card-value">
            ${rdEscapeHtml(value ?? "-")}
          </div>
        </div>
      `;
    }

    function rdRenderTimeline(timeline) {
      const target = document.getElementById(
        "runDetailTimeline"
      );

      const items = Array.isArray(timeline)
        ? timeline
        : [];

      if (!items.length) {
        target.innerHTML = `
          <li>
            <div class="run-detail-empty">
              No structured timestamp stored.
            </div>
          </li>
        `;
        return;
      }

      target.innerHTML = items.map(item => `
        <li>
          <div class="run-detail-time">
            ${rdEscapeHtml(item.timestamp || "-")}
          </div>
          <div class="run-detail-event-title">
            ${rdEscapeHtml(item.label || "-")}
          </div>
          <div>
            ${rdEscapeHtml(item.description || "")}
          </div>
        </li>
      `).join("");
    }

    function rdRenderAnalysis(analysis) {
      const target = document.getElementById(
        "runDetailAnalysis"
      );

      if (!analysis || typeof analysis !== "object") {
        target.innerHTML = `
          <div class="run-detail-empty">
            Analysis is not available for this historical run.
          </div>
        `;
        return;
      }

      const recommendations = Array.isArray(
        analysis.recommendations
      )
        ? analysis.recommendations
        : [];

      target.innerHTML = `
        <p>
          <strong>Category:</strong>
          ${rdEscapeHtml(analysis.category || "-")}
        </p>

        <p>
          <strong>Severity:</strong>
          ${rdEscapeHtml(analysis.severity || "-")}
        </p>

        <p>
          <strong>Confidence:</strong>
          ${rdEscapeHtml(analysis.confidence || "-")}
        </p>

        <p>
          <strong>Root Cause:</strong><br />
          ${rdEscapeHtml(analysis.root_cause || "-")}
        </p>

        <p>
          <strong>Retry Decision:</strong><br />
          ${rdEscapeHtml(analysis.retry_decision || "-")}
        </p>

        <p>
          <strong>Release Recommendation:</strong><br />
          ${rdEscapeHtml(
            analysis.release_recommendation || "-"
          )}
        </p>

        ${
          recommendations.length
            ? `
              <strong>Recommendations:</strong>
              <ul class="run-detail-analysis-list">
                ${recommendations.map(item =>
                  `<li>${rdEscapeHtml(item)}</li>`
                ).join("")}
              </ul>
            `
            : ""
        }
      `;
    }

    function rdRenderFeatures(features) {
      const target = document.getElementById(
        "runDetailFeatures"
      );

      const items = Array.isArray(features)
        ? features
        : [];

      if (!items.length) {
        target.innerHTML = `
          <div class="run-detail-empty">
            No structured feature result stored.
          </div>
        `;
        return;
      }

      const header = `
        <div class="run-detail-feature">
          <strong>Feature</strong>
          <strong>Status</strong>
          <strong>Passed</strong>
          <strong>Failed</strong>
          <strong>Review</strong>
          <strong>Skipped</strong>
          <strong>Warnings</strong>
          <strong>Bugs</strong>
        </div>
      `;

      const rows = items.map(item => `
        <div class="run-detail-feature">
          <span>${rdEscapeHtml(item.name || "-")}</span>
          <span>${rdEscapeHtml(item.status || "-")}</span>
          <span>${rdEscapeHtml(item.passed ?? 0)}</span>
          <span>${rdEscapeHtml(item.failed ?? 0)}</span>
          <span>${rdEscapeHtml(item.need_review ?? 0)}</span>
          <span>${rdEscapeHtml(item.skipped ?? 0)}</span>
          <span>${rdEscapeHtml(item.warnings ?? 0)}</span>
          <span>${rdEscapeHtml(item.bugs_found ?? 0)}</span>
        </div>
      `).join("");

      target.innerHTML = header + rows;
    }

    function rdFormatBytes(value) {
      const bytes = Number(value);

      if (!Number.isFinite(bytes) || bytes < 0) {
        return "-";
      }

      if (bytes < 1024) {
        return bytes + " B";
      }

      if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(1) + " KB";
      }

      return (
        bytes / (1024 * 1024)
      ).toFixed(1) + " MB";
    }

    function rdRenderArtifacts(artifacts) {
      const target = document.getElementById(
        "runDetailArtifacts"
      );

      const items = Array.isArray(artifacts)
        ? artifacts
        : [];

      if (!items.length) {
        target.innerHTML = `
          <div class="run-detail-empty">
            No artifact metadata stored.
          </div>
        `;
        return;
      }

      target.innerHTML = items.map(item => `
        <div class="run-detail-artifact">
          <div>
            <strong>${rdEscapeHtml(item.label || "-")}</strong>

            <div class="run-detail-artifact-meta">
              ${
                item.available
                  ? (
                    rdEscapeHtml(item.filename || "-")
                    + " | "
                    + rdEscapeHtml(
                      rdFormatBytes(item.size_bytes)
                    )
                    + " | "
                    + rdEscapeHtml(
                      item.modified_at || "-"
                    )
                  )
                  : "Artifact not available"
              }
            </div>
          </div>

          ${
            item.available && item.open_url
              ? `
                <a
                  href="${rdEscapeHtml(item.open_url)}"
                  target="_blank"
                  rel="noopener"
                >
                  Open
                </a>
              `
              : '<span class="muted">Unavailable</span>'
          }
        </div>
      `).join("");
    }

    function rdRenderAvailability(availability) {
      const target = document.getElementById(
        "runDetailAvailability"
      );

      const data = availability || {};
      const notes = Array.isArray(data.notes)
        ? data.notes
        : [];

      target.innerHTML = `
        <div class="run-detail-availability">
          <div>
            <strong>Structured feature results:</strong>
            ${data.structured_feature_results ? "Available" : "Unavailable"}
          </div>

          <div>
            <strong>Individual test cases:</strong>
            ${data.structured_test_cases ? "Available" : "Not stored"}
          </div>

          <div>
            <strong>Request / response:</strong>
            ${data.request_response ? "Available" : "Not stored"}
          </div>

          <div>
            <strong>Per-step timestamps:</strong>
            ${data.per_step_timestamps ? "Available" : "Not stored"}
          </div>

          <div>
            <strong>Analysis Agent:</strong>
            ${data.analysis ? "Available" : "Unavailable"}
          </div>

          ${
            notes.length
              ? `
                <ul>
                  ${notes.map(note =>
                    `<li>${rdEscapeHtml(note)}</li>`
                  ).join("")}
                </ul>
              `
              : ""
          }
        </div>
      `;
    }

    function renderRunDetail(data) {
      const panel = document.getElementById(
        "runDetailPanel"
      );

      const run = data.run || {};
      const summary = data.summary || {};

      panel.classList.remove("hidden");

      document.getElementById(
        "runDetailSubtitle"
      ).textContent = [
        run.execution_id || "-",
        run.feature || "-",
        run.status || "-"
      ].join(" | ");

      document.getElementById(
        "runDetailSummary"
      ).innerHTML = [
        rdSummaryCard(
          "Execution ID",
          run.execution_id
        ),
        rdSummaryCard(
          "Feature",
          run.feature
        ),
        rdSummaryCard(
          "Environment",
          run.environment
        ),
        rdSummaryCard(
          "Mode",
          run.mode
        ),
        rdSummaryCard(
          "Status",
          run.status
        ),
        rdSummaryCard(
          "Executed At",
          run.executed_at
        ),
        rdSummaryCard(
          "Passed",
          summary.passed ?? 0
        ),
        rdSummaryCard(
          "Failed",
          summary.failed ?? 0
        ),
        rdSummaryCard(
          "Need Review",
          summary.need_review ?? 0
        ),
        rdSummaryCard(
          "Skipped",
          summary.skipped ?? 0
        ),
        rdSummaryCard(
          "Warnings",
          summary.warnings ?? 0
        ),
        rdSummaryCard(
          "Bugs Found",
          summary.bugs_found ?? 0
        )
      ].join("");

      rdRenderTimeline(data.timeline);
      rdRenderAnalysis(data.analysis);
      rdRenderFeatures(data.feature_results);
      rdRenderArtifacts(data.artifacts);
      rdRenderAvailability(
        data.data_availability
      );

      document.getElementById(
        "runDetailTestingSummary"
      ).textContent =
        data.testing_summary
        || "No stored testing summary.";

      panel.scrollIntoView({
        behavior: "smooth",
        block: "start"
      });
    }

    async function openSelectedRunDetail() {
      const select = document.getElementById(
        "runDetailExecutionSelect"
      );

      const executionId = select
        ? select.value
        : "";

      if (!executionId) {
        alert("Select a run first.");
        return;
      }

      const panel = document.getElementById(
        "runDetailPanel"
      );

      panel.classList.remove("hidden");

      document.getElementById(
        "runDetailSubtitle"
      ).textContent =
        "Loading run detail...";

      try {
        const response = await fetch(
          "/history/"
          + encodeURIComponent(executionId)
        );

        const data = await response.json();

        if (!response.ok || !data.ok) {
          throw new Error(
            JSON.stringify(data)
          );
        }

        renderRunDetail(data);

      } catch (error) {
        document.getElementById(
          "runDetailSubtitle"
        ).textContent =
          "Failed to load run detail: "
          + error.message;

        console.error(
          "Run Detail error:",
          error
        );
      }
    }

    window.addEventListener("load", function () {
      setTimeout(function () {
        loadRunDetailOptions();
      }, 500);
    });

'''


if "async function openSelectedRunDetail()" not in text:
    text = text.replace(
        "    async function runRegisteredQA() {",
        js + "\n    async function runRegisteredQA() {",
        1,
    )

    print("Inserted Run Detail JS")
else:
    print("Run Detail JS already exists")


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
