from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 CSS */"
JS_MARKER = "/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 JS */"

def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)

if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_main_dashboard_monitoring_cleanup_v1_2_{stamp}"
)
shutil.copy2(HTML_PATH, backup_path)
text = HTML_PATH.read_text(encoding="utf-8")

css = r'''
/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 CSS */

body.qa-main-dashboard-active-v11
  .qa-dashboard-header-controls-v12 {
  display: none !important;
}

body.qa-main-dashboard-active-v11
  .qa-main-dashboard-actions-v1 {
  display: none !important;
}

body.qa-main-dashboard-active-v11
  .qa-dashboard-legacy-metric-v12 {
  display: none !important;
}

.qa-dashboard-project-select-v12 {
  width: 100%;
  min-height: 34px;
  padding: 3px 26px 3px 0;
  border: 0;
  border-bottom: 1px solid transparent;
  border-radius: 0;
  background: transparent;
  color: #0f172a;
  cursor: pointer;
  font-size: 18px;
  font-weight: 850;
}

.qa-dashboard-project-select-v12:hover,
.qa-dashboard-project-select-v12:focus {
  border-bottom-color: #93c5fd;
  outline: none;
}

.qa-dashboard-project-hint-v12 {
  margin-top: 3px;
  color: #64748b;
  font-size: 9px;
}

.qa-dashboard-context-status-v12 {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.qa-dashboard-context-pill-v12 {
  display: inline-flex;
  min-height: 22px;
  align-items: center;
  padding: 3px 7px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #475569;
  font-size: 9px;
  font-weight: 800;
}

.qa-dashboard-context-pill-v12.connected {
  background: #dcfce7;
  color: #166534;
}

.qa-dashboard-context-pill-v12.running {
  background: #dbeafe;
  color: #1d4ed8;
}

.qa-dashboard-flow-help-v12 {
  width: 34px !important;
  min-width: 34px !important;
  height: 34px !important;
  min-height: 34px !important;
  padding: 0 !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 50% !important;
  background: #fff !important;
  color: #334155 !important;
  box-shadow: none !important;
  font-size: 15px !important;
  font-weight: 900 !important;
}

.qa-dashboard-help-overlay-v12 {
  position: fixed;
  z-index: 1600;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, .52);
}

.qa-dashboard-help-overlay-v12.open {
  display: flex;
}

.qa-dashboard-help-dialog-v12 {
  width: min(620px, 100%);
  max-height: calc(100vh - 40px);
  overflow-y: auto;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 24px 80px rgba(15, 23, 42, .25);
}

.qa-dashboard-help-head-v12 {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 18px;
  border-bottom: 1px solid #e2e8f0;
}

.qa-dashboard-help-head-v12 h2 {
  margin: 0;
  color: #0f172a;
  font-size: 15px;
}

.qa-dashboard-help-close-v12 {
  width: 30px;
  min-width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid #cbd5e1;
  border-radius: 50%;
  background: #fff;
  cursor: pointer;
}

.qa-dashboard-help-body-v12 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 16px 18px 18px;
}

.qa-dashboard-help-step-v12 {
  padding: 11px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}

.qa-dashboard-help-step-v12 strong {
  display: block;
  color: #0f172a;
  font-size: 10px;
}

.qa-dashboard-help-step-v12 span {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 9px;
  line-height: 1.45;
}

@media (max-width: 620px) {
  .qa-dashboard-help-body-v12 {
    grid-template-columns: 1fr;
  }
}
'''

js = r'''
/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 JS */
(function () {
  "use strict";

  let timer = null;
  let observer = null;

  function textOf(element) {
    return String(element?.textContent || "")
      .trim()
      .replace(/\s+/g, " ");
  }

  function findProjectSelect() {
    return document.querySelector(
      "[data-qa-project-selector],"
      + "#qaProjectSelector,"
      + "select[id*='Project'],"
      + "select[name*='project' i]"
    );
  }

  function findHeaderGroup(projectSelect) {
    let current = projectSelect?.parentElement || null;

    for (let depth = 0; current && depth < 7; depth += 1) {
      const text = textOf(current);

      if (
        /PROJECT/i.test(text)
        && /Environment:/i.test(text)
        && /Backend:/i.test(text)
        && /Run:/i.test(text)
      ) {
        return current;
      }

      current = current.parentElement;
    }

    return projectSelect?.parentElement || null;
  }

  function exactText(value) {
    return Array.from(
      document.querySelectorAll(
        "h1,h2,h3,h4,div,span,strong,p,button"
      )
    ).find(function (element) {
      return textOf(element) === value;
    }) || null;
  }

  function markLegacyMetrics() {
    [
      "API Status",
      "Total Runs",
      "PASS",
      "FAILED / REVIEW"
    ].forEach(function (label) {
      const node = exactText(label);

      if (!node) return;

      let current = node;

      for (let depth = 0; current && depth < 4; depth += 1) {
        const text = textOf(current);

        if (
          text.includes(label)
          && text.length < 120
          && current.children.length
        ) {
          current.classList.add(
            "qa-dashboard-legacy-metric-v12"
          );
        }

        current = current.parentElement;
      }
    });
  }

  function ensureHelpDialog() {
    let overlay = document.getElementById(
      "qaDashboardFlowHelpV12"
    );

    if (overlay) return overlay;

    overlay = document.createElement("div");
    overlay.id = "qaDashboardFlowHelpV12";
    overlay.className =
      "qa-dashboard-help-overlay-v12";

    const steps = [
      ["Planning", "Define target, scope, objective, and risk."],
      ["Scenario", "Prepare test scenarios and expected behavior."],
      ["Template", "Load or build reusable execution configuration."],
      ["Execution", "Run UI, API, or regression checks."],
      ["Evidence", "Capture screenshots, responses, console, and network logs."],
      ["Analysis", "Evaluate failures, warnings, anomalies, and likely causes."],
      ["Report", "Store results, history, and generated artifacts."]
    ];

    overlay.innerHTML = `
      <div class="qa-dashboard-help-dialog-v12">
        <div class="qa-dashboard-help-head-v12">
          <div>
            <h2>Autonomous QA Flow</h2>
          </div>
          <button
            type="button"
            class="qa-dashboard-help-close-v12"
            aria-label="Close help"
          >×</button>
        </div>
        <div class="qa-dashboard-help-body-v12">
          ${steps.map(function (step, index) {
            return `
              <div class="qa-dashboard-help-step-v12">
                <strong>${index + 1}. ${step[0]}</strong>
                <span>${step[1]}</span>
              </div>
            `;
          }).join("")}
        </div>
      </div>
    `;

    overlay.querySelector(
      ".qa-dashboard-help-close-v12"
    ).addEventListener("click", function () {
      overlay.classList.remove("open");
    });

    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) {
        overlay.classList.remove("open");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        overlay.classList.remove("open");
      }
    });

    document.body.appendChild(overlay);
    return overlay;
  }

  function refineFlowButton() {
    const flowTitle = exactText(
      "Autonomous QA Flow"
    );

    if (!flowTitle) return;

    let container = flowTitle.parentElement;

    for (let depth = 0; container && depth < 5; depth += 1) {
      const text = textOf(container);

      if (
        text.includes("Planning")
        && text.includes("Report")
      ) break;

      container = container.parentElement;
    }

    const button = Array.from(
      container?.querySelectorAll("button") || []
    ).find(function (candidate) {
      return textOf(candidate) === "Detail Flow";
    });

    if (!button) return;

    button.textContent = "?";
    button.classList.add(
      "qa-dashboard-flow-help-v12"
    );
    button.setAttribute(
      "aria-label",
      "About Autonomous QA Flow"
    );
    button.setAttribute(
      "title",
      "About Autonomous QA Flow"
    );

    if (!button.dataset.qaHelpBoundV12) {
      button.dataset.qaHelpBoundV12 = "true";
      button.addEventListener("click", function () {
        ensureHelpDialog().classList.add("open");
      });
    }
  }

  function cloneOptions(target, source) {
    const currentValue = source.value;
    target.innerHTML = "";

    Array.from(source.options).forEach(function (option) {
      target.appendChild(option.cloneNode(true));
    });

    target.value = currentValue;
  }

  function enhanceProjectOverview(
    projectSelect,
    headerGroup
  ) {
    const root = document.getElementById(
      "qaMainDashboardRootV1"
    );

    if (!root || !projectSelect) return;

    const title = root.querySelector(
      ".qa-main-dashboard-title-v1"
    );

    if (title) {
      title.textContent = "Project Overview";
    }

    const subtitle = root.querySelector(
      ".qa-main-dashboard-subtitle-v1"
    );

    if (subtitle) {
      subtitle.textContent =
        "Monitoring context and real execution data for the selected project.";
    }

    const firstCard = root.querySelector(
      ".qa-main-dashboard-context-card-v1"
    );

    if (!firstCard) return;

    const oldValue = firstCard.querySelector(
      ".qa-main-dashboard-value-v1.large"
    );

    if (oldValue) {
      oldValue.style.display = "none";
    }

    let proxy = document.getElementById(
      "qaDashboardProjectSelectV12"
    );

    if (!proxy) {
      proxy = document.createElement("select");
      proxy.id = "qaDashboardProjectSelectV12";
      proxy.className =
        "qa-dashboard-project-select-v12";

      const hint = document.createElement("div");
      hint.className =
        "qa-dashboard-project-hint-v12";
      hint.textContent =
        "Change the monitored project";

      if (oldValue) {
        oldValue.insertAdjacentElement(
          "afterend",
          proxy
        );
        proxy.insertAdjacentElement(
          "afterend",
          hint
        );
      } else {
        firstCard.appendChild(proxy);
        firstCard.appendChild(hint);
      }

      proxy.addEventListener("change", function () {
        if (projectSelect.value !== proxy.value) {
          projectSelect.value = proxy.value;
          projectSelect.dispatchEvent(
            new Event("input", { bubbles: true })
          );
          projectSelect.dispatchEvent(
            new Event("change", { bubbles: true })
          );
        }
      });
    }

    cloneOptions(proxy, projectSelect);

    let statusRow = firstCard.querySelector(
      ".qa-dashboard-context-status-v12"
    );

    if (!statusRow) {
      statusRow = document.createElement("div");
      statusRow.className =
        "qa-dashboard-context-status-v12";
      firstCard.appendChild(statusRow);
    }

    statusRow.innerHTML = "";

    const headerText = textOf(headerGroup);
    const backendMatch = headerText.match(
      /Backend:\s*[^|]+?(?=Run:|$)/i
    );
    const runMatch = headerText.match(
      /Run:\s*[^|]+$/i
    );

    [
      {
        text: backendMatch?.[0]?.trim() || "",
        css: /connected/i.test(
          backendMatch?.[0] || ""
        ) ? "connected" : ""
      },
      {
        text: runMatch?.[0]?.trim() || "",
        css: /running|progress/i.test(
          runMatch?.[0] || ""
        ) ? "running" : ""
      }
    ].forEach(function (item) {
      if (!item.text) return;

      const badge = document.createElement("span");
      badge.className =
        "qa-dashboard-context-pill-v12 "
        + item.css;
      badge.textContent = item.text;
      statusRow.appendChild(badge);
    });
  }

  function applyCleanup() {
    const projectSelect = findProjectSelect();
    const headerGroup = findHeaderGroup(projectSelect);

    if (headerGroup) {
      headerGroup.classList.add(
        "qa-dashboard-header-controls-v12"
      );
    }

    markLegacyMetrics();
    refineFlowButton();
    enhanceProjectOverview(
      projectSelect,
      headerGroup
    );
  }

  function scheduleCleanup() {
    window.clearTimeout(timer);
    timer = window.setTimeout(applyCleanup, 80);
  }

  window.qaApplyMainDashboardMonitoringCleanupV12 =
    applyCleanup;

  window.addEventListener(
    "qa-project-changed",
    scheduleCleanup
  );

  window.addEventListener("load", function () {
    applyCleanup();
    window.setTimeout(applyCleanup, 300);
    window.setTimeout(applyCleanup, 1000);
  });

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      applyCleanup
    );
  } else {
    applyCleanup();
  }

  if (!observer) {
    observer = new MutationObserver(
      scheduleCleanup
    );

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
})();
'''

if CSS_MARKER not in text:
    style_close = text.rfind("</style>")
    if style_close == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Closing </style> tag was not found")
    text = text[:style_close] + "\n" + css + "\n" + text[style_close:]
    print("[OK] Main Dashboard Monitoring Cleanup V1.2 CSS inserted")
else:
    print("[SKIP] Main Dashboard Monitoring Cleanup V1.2 CSS already exists")

if JS_MARKER not in text:
    script_close = text.rfind("</script>")
    if script_close == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Closing </script> tag was not found")
    text = text[:script_close] + "\n" + js + "\n" + text[script_close:]
    print("[OK] Main Dashboard Monitoring Cleanup V1.2 JavaScript inserted")
else:
    print("[SKIP] Main Dashboard Monitoring Cleanup V1.2 JavaScript already exists")

required = [
    CSS_MARKER,
    JS_MARKER,
    "function applyCleanup()",
    "qaApplyMainDashboardMonitoringCleanupV12",
]

missing = [item for item in required if item not in text]

if missing:
    shutil.copy2(backup_path, HTML_PATH)
    fail(
        "Verification failed. Dashboard restored. Missing markers: "
        + ", ".join(missing)
    )

HTML_PATH.write_text(text, encoding="utf-8")

print(f"[OK] Backup created: {backup_path}")
print(f"[OK] Updated: {HTML_PATH}")
print()
print("[SUCCESS] Main Dashboard Monitoring Cleanup V1.2 installed")
