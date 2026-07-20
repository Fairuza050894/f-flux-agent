from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA ACTIVE EXECUTION MONITORING V1.3 CSS */"
JS_MARKER = "/* QA ACTIVE EXECUTION MONITORING V1.3 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


required_base_markers = [
    "/* QA MAIN DASHBOARD V1 JS */",
    "/* QA MAIN DASHBOARD MONITORING BUGFIX V1.2.1 CSS */",
]

text = HTML_PATH.read_text(encoding="utf-8")

missing_base = [
    marker
    for marker in required_base_markers
    if marker not in text
]

if missing_base:
    fail(
        "Required stable dashboard markers were not found: "
        + ", ".join(missing_base)
    )


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_active_execution_monitoring_v1_3_{timestamp}"
)

shutil.copy2(
    HTML_PATH,
    backup_path
)


css = r'''
/* QA ACTIVE EXECUTION MONITORING V1.3 CSS */

.qa-active-run-v13 {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-active-run-summary-v13 {
  display: grid;
  grid-template-columns:
    minmax(0, 1.4fr)
    repeat(3, minmax(105px, .65fr));
  gap: 9px;
}

.qa-active-run-main-v13,
.qa-active-run-stat-v13 {
  min-width: 0;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.qa-active-run-label-v13 {
  margin-bottom: 4px;
  color: #64748b;
  font-size: 9px;
  font-weight: 850;
  letter-spacing: .07em;
  text-transform: uppercase;
}

.qa-active-run-title-v13 {
  overflow: hidden;
  color: #0f172a;
  font-size: 12px;
  font-weight: 850;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-active-run-meta-v13 {
  margin-top: 4px;
  color: #64748b;
  font-size: 9px;
  line-height: 1.45;
}

.qa-active-run-value-v13 {
  color: #0f172a;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.2;
}

.qa-active-run-progress-v13 {
  overflow: hidden;
  height: 7px;
  border-radius: 999px;
  background: #e2e8f0;
}

.qa-active-run-progress-bar-v13 {
  width: 0;
  height: 100%;
  border-radius: inherit;
  background: #2563eb;
  transition: width 180ms ease;
}

.qa-active-run-footer-v13 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.qa-active-run-evidence-v13 {
  min-width: 0;
  color: #64748b;
  font-size: 9px;
  line-height: 1.45;
}

.qa-active-run-detail-v13 {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  padding: 8px 12px;
  border: 1px solid #2563eb;
  border-radius: 9px;
  background: #2563eb;
  color: #ffffff;
  cursor: pointer;
  font-size: 10px;
  font-weight: 850;
}

.qa-active-run-detail-v13:hover {
  border-color: #1d4ed8;
  background: #1d4ed8;
}

.qa-active-run-detail-v13[disabled] {
  border-color: #cbd5e1;
  background: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
}

.qa-active-run-empty-v13 {
  padding: 20px 14px;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  color: #64748b;
  font-size: 10px;
  line-height: 1.55;
  text-align: center;
}

@media (max-width: 900px) {
  .qa-active-run-summary-v13 {
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .qa-active-run-summary-v13 {
    grid-template-columns: 1fr;
  }

  .qa-active-run-footer-v13 {
    align-items: stretch;
    flex-direction: column;
  }

  .qa-active-run-detail-v13 {
    width: 100%;
  }
}
'''


js = r'''
/* QA ACTIVE EXECUTION MONITORING V1.3 JS */
(function () {
  "use strict";

  let refreshTimerV13 = null;
  let refreshIntervalV13 = null;
  let lastRenderedSignatureV13 = "";

  function textV13(value) {
    return String(value ?? "");
  }

  function escapeV13(value) {
    const element = document.createElement("div");
    element.textContent = textV13(value);
    return element.innerHTML;
  }

  function normalizeStatusV13(value) {
    return textV13(value || "UNKNOWN")
      .trim()
      .replace(/[_-]+/g, " ")
      .toUpperCase();
  }

  function isActiveStatusV13(value) {
    const status = normalizeStatusV13(value);

    return (
      status.includes("RUNNING")
      || status.includes("IN PROGRESS")
      || status.includes("QUEUED")
      || status.includes("STARTED")
      || status.includes("EXECUTING")
    );
  }

  function currentProjectIdV13() {
    const proxy = document.getElementById(
      "qaDashboardProjectSelectV12"
    );

    if (proxy && proxy.value) {
      return textV13(proxy.value);
    }

    const original = document.querySelector(
      "[data-qa-project-selector],"
      + "#qaProjectSelector,"
      + "select[id*='Project'],"
      + "select[name*='project' i]"
    );

    return original && original.value
      ? textV13(original.value)
      : "";
  }

  function currentProjectNameV13() {
    const proxy = document.getElementById(
      "qaDashboardProjectSelectV12"
    );

    if (
      proxy
      && proxy.selectedOptions
      && proxy.selectedOptions.length
    ) {
      return textV13(
        proxy.selectedOptions[0].textContent
      ).trim();
    }

    return "Selected project";
  }

  function normalizeHistoryV13(payload) {
    if (Array.isArray(payload)) {
      return payload;
    }

    const candidates = [
      payload && payload.history,
      payload && payload.runs,
      payload && payload.items,
      payload && payload.data,
      payload && payload.results
    ];

    return (
      candidates.find(Array.isArray)
      || []
    );
  }

  function runDateV13(run) {
    return (
      run.started_at
      || run.executed_at
      || run.created_at
      || run.timestamp
      || run.updated_at
      || ""
    );
  }

  function runTimestampV13(run) {
    const parsed = Date.parse(
      textV13(runDateV13(run))
    );

    return Number.isFinite(parsed)
      ? parsed
      : 0;
  }

  function runIdV13(run) {
    return (
      run.run_id
      || run.id
      || run.execution_id
      || ""
    );
  }

  function runFeatureV13(run) {
    return (
      run.feature
      || run.feature_name
      || run.module
      || run.suite_name
      || run.name
      || "Unnamed execution"
    );
  }

  function runTypeV13(run) {
    return (
      run.test_type
      || run.type
      || run.mode
      || run.execution_mode
      || "Test"
    );
  }

  function numberFromV13(object, keys) {
    if (!object || typeof object !== "object") {
      return null;
    }

    for (const key of keys) {
      const value = object[key];

      if (
        typeof value === "number"
        && Number.isFinite(value)
      ) {
        return value;
      }

      if (
        typeof value === "string"
        && value.trim()
        && Number.isFinite(Number(value))
      ) {
        return Number(value);
      }
    }

    return null;
  }

  function summaryV13(run) {
    if (!run || typeof run !== "object") {
      return {};
    }

    const candidates = [
      run.summary,
      run.counts,
      run.metrics,
      run.result && run.result.summary,
      run.output && run.output.summary,
      run.report && run.report.summary,
      run.standard_json
        && run.standard_json.summary,
      run
    ].filter(Boolean);

    for (const candidate of candidates) {
      const passed = numberFromV13(
        candidate,
        [
          "passed",
          "pass",
          "passed_count",
          "total_passed"
        ]
      );

      const failed = numberFromV13(
        candidate,
        [
          "failed",
          "fail",
          "failed_count",
          "total_failed"
        ]
      );

      const review = numberFromV13(
        candidate,
        [
          "need_review",
          "needReview",
          "review",
          "review_count",
          "total_need_review"
        ]
      );

      if (
        passed !== null
        || failed !== null
        || review !== null
      ) {
        return {
          passed,
          failed,
          review
        };
      }
    }

    return {};
  }

  function progressV13(run, summary) {
    const explicit = numberFromV13(
      run,
      [
        "progress",
        "progress_percent",
        "percentage",
        "percent_complete"
      ]
    );

    if (explicit !== null) {
      return Math.max(
        0,
        Math.min(100, explicit)
      );
    }

    const total = numberFromV13(
      run,
      [
        "total",
        "total_tests",
        "test_count",
        "total_cases"
      ]
    );

    const completed = [
      summary.passed,
      summary.failed,
      summary.review
    ]
      .filter(value => value !== null && value !== undefined)
      .reduce((sum, value) => sum + value, 0);

    if (total && total > 0 && completed >= 0) {
      return Math.max(
        0,
        Math.min(
          100,
          (completed / total) * 100
        )
      );
    }

    return null;
  }

  function formatDateV13(value) {
    if (!value) {
      return "Not available";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return textV13(value);
    }

    return new Intl.DateTimeFormat(
      undefined,
      {
        dateStyle: "medium",
        timeStyle: "short"
      }
    ).format(date);
  }

  function dashboardVisibleV13() {
    const panel = document.getElementById(
      "tab-dashboard"
    );

    if (!panel) {
      return false;
    }

    const style = window.getComputedStyle(panel);

    return (
      style.display !== "none"
      && style.visibility !== "hidden"
    );
  }

  function findActiveCardV13() {
    const root = document.getElementById(
      "qaMainDashboardRootV1"
    );

    if (!root) {
      return null;
    }

    const titles = Array.from(
      root.querySelectorAll(
        ".qa-main-dashboard-card-title-v1"
      )
    );

    const title = titles.find(
      element =>
        textV13(element.textContent)
          .trim()
          .toLowerCase()
        === "active executions"
    );

    if (!title) {
      return null;
    }

    return title.closest(
      ".qa-main-dashboard-card-v1"
    );
  }

  function openHistoryForRunV13(run) {
    const id = textV13(
      runIdV13(run)
    ).trim();

    if (
      typeof window.showTab === "function"
    ) {
      window.showTab("history");
    }

    window.setTimeout(
      function () {
        const knownFunctions = [
          "openHistoryDetail",
          "showHistoryDetail",
          "viewHistoryDetail",
          "openRunDetail",
          "openHistoryDrawer"
        ];

        for (const name of knownFunctions) {
          if (
            typeof window[name] === "function"
            && id
          ) {
            try {
              window[name](id, run);
              return;
            } catch (_) {}
          }
        }

        const historyPanel =
          document.getElementById(
            "tab-history"
          );

        if (!historyPanel) {
          return;
        }

        const inputs = Array.from(
          historyPanel.querySelectorAll(
            "input[type='search'],"
            + "input[id*='search' i],"
            + "input[placeholder*='search' i]"
          )
        );

        const search = inputs[0];

        if (search && id) {
          search.value = id;

          search.dispatchEvent(
            new Event(
              "input",
              { bubbles: true }
            )
          );

          search.dispatchEvent(
            new Event(
              "change",
              { bubbles: true }
            )
          );
        }

        window.setTimeout(
          function () {
            const rows = Array.from(
              historyPanel.querySelectorAll(
                "tbody tr, [data-run-id], .history-item"
              )
            );

            const matchingRow = rows.find(
              row =>
                id
                && textV13(row.textContent)
                  .includes(id)
            );

            if (matchingRow) {
              matchingRow.scrollIntoView({
                behavior: "smooth",
                block: "center"
              });

              matchingRow.click();
            }
          },
          250
        );
      },
      160
    );
  }

  function renderV13(run, isActive, projectName) {
    const card = findActiveCardV13();

    if (!card) {
      return;
    }

    const title = card.querySelector(
      ".qa-main-dashboard-card-title-v1"
    );

    const help = card.querySelector(
      ".qa-main-dashboard-card-help-v1"
    );

    const body = card.querySelector(
      ".qa-main-dashboard-live-v1"
    );

    if (!body) {
      return;
    }

    if (!run) {
      if (title) {
        title.textContent =
          "Active Execution";
      }

      if (help) {
        help.textContent =
          "Live monitoring for the selected project.";
      }

      body.innerHTML = `
        <div class="qa-active-run-empty-v13">
          No active or recent project execution
          was found.
        </div>
      `;

      lastRenderedSignatureV13 = "empty";
      return;
    }

    const summary = summaryV13(run);
    const progress = progressV13(
      run,
      summary
    );

    const status =
      normalizeStatusV13(run.status);

    const id =
      textV13(runIdV13(run)).trim();

    const signature = JSON.stringify({
      id,
      status,
      progress,
      passed: summary.passed,
      failed: summary.failed,
      review: summary.review,
      projectName
    });

    if (
      signature === lastRenderedSignatureV13
      && body.querySelector(
        ".qa-active-run-v13"
      )
    ) {
      return;
    }

    lastRenderedSignatureV13 =
      signature;

    if (title) {
      title.textContent =
        isActive
          ? "Active Execution"
          : "Latest Execution";
    }

    if (help) {
      help.textContent =
        isActive
          ? "Current execution state from project history."
          : "No run is active; showing the latest recorded execution.";
    }

    const stats = [
      ["Passed", summary.passed],
      ["Failed", summary.failed],
      ["Need Review", summary.review]
    ];

    body.innerHTML = `
      <div class="qa-active-run-v13">
        <div class="qa-active-run-summary-v13">
          <div class="qa-active-run-main-v13">
            <div class="qa-active-run-label-v13">
              ${isActive ? "Running Test" : "Latest Test"}
            </div>

            <div
              class="qa-active-run-title-v13"
              title="${escapeV13(runFeatureV13(run))}"
            >
              ${escapeV13(runFeatureV13(run))}
            </div>

            <div class="qa-active-run-meta-v13">
              ${escapeV13(runTypeV13(run))}
              ·
              ${escapeV13(projectName)}
              ·
              ${escapeV13(status)}
            </div>
          </div>

          ${stats.map(function (item) {
            return `
              <div class="qa-active-run-stat-v13">
                <div class="qa-active-run-label-v13">
                  ${item[0]}
                </div>

                <div class="qa-active-run-value-v13">
                  ${
                    item[1] === null
                    || item[1] === undefined
                      ? "—"
                      : escapeV13(item[1])
                  }
                </div>
              </div>
            `;
          }).join("")}
        </div>

        ${
          progress === null
            ? ""
            : `
              <div>
                <div class="qa-active-run-meta-v13">
                  Progress: ${escapeV13(progress.toFixed(0))}%
                </div>

                <div class="qa-active-run-progress-v13">
                  <div
                    class="qa-active-run-progress-bar-v13"
                    style="width: ${escapeV13(progress)}%"
                  ></div>
                </div>
              </div>
            `
        }

        <div class="qa-active-run-footer-v13">
          <div class="qa-active-run-evidence-v13">
            Run ID:
            ${escapeV13(id || "Not available")}
            ·
            ${escapeV13(formatDateV13(runDateV13(run)))}
          </div>

          <button
            type="button"
            class="qa-active-run-detail-v13"
            ${id ? "" : "disabled"}
          >
            ${
              isActive
                ? "View Run Details"
                : "View Latest Run"
            }
          </button>
        </div>
      </div>
    `;

    const button = body.querySelector(
      ".qa-active-run-detail-v13"
    );

    if (button && id) {
      button.addEventListener(
        "click",
        function () {
          openHistoryForRunV13(run);
        }
      );
    }
  }

  async function refreshV13() {
    if (!dashboardVisibleV13()) {
      return;
    }

    const projectId =
      currentProjectIdV13();

    if (!projectId) {
      renderV13(
        null,
        false,
        currentProjectNameV13()
      );

      return;
    }

    try {
      const response = await fetch(
        `/history?limit=200&_=${Date.now()}`,
        {
          cache: "no-store"
        }
      );

      if (!response.ok) {
        throw new Error(
          `History request failed: ${response.status}`
        );
      }

      const history = normalizeHistoryV13(
        await response.json()
      );

      const projectRuns = history
        .filter(function (run) {
          return (
            run
            && textV13(
              run.project_id || ""
            ) === projectId
          );
        })
        .sort(
          (left, right) =>
            runTimestampV13(right)
            - runTimestampV13(left)
        );

      const active = projectRuns.find(
        run => isActiveStatusV13(run.status)
      );

      const selected =
        active || projectRuns[0] || null;

      renderV13(
        selected,
        Boolean(active),
        currentProjectNameV13()
      );

    } catch (error) {
      console.warn(
        "Active execution monitoring unavailable:",
        error
      );
    }
  }

  function scheduleRefreshV13() {
    window.clearTimeout(
      refreshTimerV13
    );

    refreshTimerV13 =
      window.setTimeout(
        refreshV13,
        120
      );
  }

  function initializeV13() {
    scheduleRefreshV13();

    if (!refreshIntervalV13) {
      refreshIntervalV13 =
        window.setInterval(
          function () {
            if (dashboardVisibleV13()) {
              refreshV13();
            }
          },
          15000
        );
    }
  }

  window.qaRefreshActiveExecutionV13 =
    refreshV13;

  window.addEventListener(
    "qa-project-changed",
    scheduleRefreshV13
  );

  window.addEventListener(
    "load",
    function () {
      initializeV13();

      window.setTimeout(
        initializeV13,
        500
      );
    }
  );

  document.addEventListener(
    "visibilitychange",
    function () {
      if (
        !document.hidden
        && dashboardVisibleV13()
      ) {
        scheduleRefreshV13();
      }
    }
  );

  if (
    document.readyState === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      initializeV13
    );
  } else {
    initializeV13();
  }
})();
'''


if CSS_MARKER not in text:
    style_close = text.rfind("</style>")

    if style_close == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Closing </style> tag was not found")

    text = (
        text[:style_close]
        + "\n"
        + css
        + "\n"
        + text[style_close:]
    )

    print(
        "[OK] Active Execution Monitoring V1.3 CSS inserted"
    )
else:
    print(
        "[SKIP] Active Execution Monitoring V1.3 CSS already exists"
    )


if JS_MARKER not in text:
    script_close = text.rfind("</script>")

    if script_close == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Closing </script> tag was not found")

    text = (
        text[:script_close]
        + "\n"
        + js
        + "\n"
        + text[script_close:]
    )

    print(
        "[OK] Active Execution Monitoring V1.3 JavaScript inserted"
    )
else:
    print(
        "[SKIP] Active Execution Monitoring V1.3 JavaScript already exists"
    )


required_markers = [
    CSS_MARKER,
    JS_MARKER,
    "async function refreshV13()",
    "function openHistoryForRunV13(run)",
    "qaRefreshActiveExecutionV13",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. Missing markers: "
        + ", ".join(missing)
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8"
)

print(f"[OK] Backup created: {backup_path}")
print(f"[OK] Updated: {HTML_PATH}")
print()
print(
    "[SUCCESS] Active Execution Monitoring V1.3 installed"
)
