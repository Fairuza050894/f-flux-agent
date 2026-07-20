from pathlib import Path
from datetime import datetime
import ast
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA UI TESTING EXECUTION BRIDGE V2.2.2 CSS */"
JS_MARKER = "/* QA UI TESTING EXECUTION BRIDGE V2.2.2 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


text = HTML_PATH.read_text(encoding="utf-8")

required_markers = [
    "/* QA UI TESTING PANEL SCOPE V2.1.2 PATCHED */",
    "/* QA UI TESTING DRAFT PERSISTENCE V2.1.3 JS */",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing:
    fail(
        "Required UI Testing frontend markers were not found: "
        + ", ".join(missing)
    )


stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_ui_testing_execution_bridge_v2_2_2_{stamp}"
)
shutil.copy2(HTML_PATH, backup_path)


css = r'''
/* QA UI TESTING EXECUTION BRIDGE V2.2.2 CSS */

.qa-ui-run-session-v222 {
  display: none;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  margin: 0 0 14px;
  padding: 13px 14px;
  border: 1px solid #bfdbfe;
  border-radius: 11px;
  background: #f8fbff;
}

.qa-ui-run-session-v222.visible {
  display: block;
}

.qa-ui-run-session-head-v222 {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.qa-ui-run-session-copy-v222 {
  min-width: 0;
}

.qa-ui-run-session-eyebrow-v222 {
  color: #64748b;
  font-size: 9px;
  font-weight: 850;
  letter-spacing: .07em;
  text-transform: uppercase;
}

.qa-ui-run-session-title-v222 {
  margin-top: 3px;
  overflow: hidden;
  color: #0f172a;
  font-size: 12px;
  font-weight: 850;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-ui-run-session-meta-v222 {
  margin-top: 4px;
  color: #64748b;
  font-size: 9px;
  line-height: 1.45;
}

.qa-ui-run-status-v222 {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  flex: 0 0 auto;
  padding: 4px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 9px;
  font-weight: 850;
  text-transform: uppercase;
}

.qa-ui-run-status-v222.passed,
.qa-ui-run-status-v222.completed {
  background: #dcfce7;
  color: #166534;
}

.qa-ui-run-status-v222.failed {
  background: #fee2e2;
  color: #b91c1c;
}

.qa-ui-run-status-v222.need_review {
  background: #fef3c7;
  color: #92400e;
}

.qa-ui-run-progress-track-v222 {
  overflow: hidden;
  height: 7px;
  margin-top: 11px;
  border-radius: 999px;
  background: #dbe3ee;
}

.qa-ui-run-progress-bar-v222 {
  width: 0;
  height: 100%;
  border-radius: inherit;
  background: #2563eb;
  transition: width 180ms ease;
}

.qa-ui-run-grid-v222 {
  display: grid;
  grid-template-columns:
    minmax(0, 1.4fr)
    repeat(3, minmax(80px, .55fr));
  gap: 8px;
  margin-top: 10px;
}

.qa-ui-run-detail-v222,
.qa-ui-run-count-v222 {
  min-width: 0;
  padding: 9px 10px;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  background: #ffffff;
}

.qa-ui-run-field-label-v222 {
  color: #64748b;
  font-size: 8px;
  font-weight: 850;
  letter-spacing: .05em;
  text-transform: uppercase;
}

.qa-ui-run-field-value-v222 {
  margin-top: 3px;
  overflow: hidden;
  color: #0f172a;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-ui-run-count-v222
  .qa-ui-run-field-value-v222 {
  font-size: 14px;
  font-weight: 900;
}

.qa-ui-run-session-foot-v222 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
  color: #64748b;
  font-size: 8px;
  line-height: 1.4;
}

.qa-ui-run-refresh-v222 {
  min-height: 30px;
  padding: 6px 9px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
  font-size: 9px;
  font-weight: 800;
}

.qa-ui-run-refresh-v222:hover {
  border-color: #93c5fd;
  color: #1d4ed8;
}

.qa-ui-run-bridge-warning-v222 {
  display: none;
  margin: 0 0 12px;
  padding: 9px 10px;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  background: #fff7ed;
  color: #9a3412;
  font-size: 9px;
  line-height: 1.45;
}

.qa-ui-run-bridge-warning-v222.visible {
  display: block;
}

@media (max-width: 760px) {
  .qa-ui-run-grid-v222 {
    grid-template-columns:
      repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .qa-ui-run-session-head-v222,
  .qa-ui-run-session-foot-v222 {
    align-items: stretch;
    flex-direction: column;
  }

  .qa-ui-run-grid-v222 {
    grid-template-columns: 1fr;
  }

  .qa-ui-run-status-v222 {
    align-self: flex-start;
  }
}
'''


js = r'''
/* QA UI TESTING EXECUTION BRIDGE V2.2.2 JS */
(function () {
  "use strict";

  const RUN_ID_PREFIX_V222 =
    "qa.ui-testing.active-run.v222";

  const SENSITIVE_PATTERN_V222 =
    /(password|passwd|secret|token|cookie|authorization|credential|api.?key|session)/i;

  const ACTIVE_STATUSES_V222 =
    new Set([
      "queued",
      "running",
      "in_progress",
      "started",
      "executing"
    ]);

  const TERMINAL_STATUSES_V222 =
    new Set([
      "completed",
      "passed",
      "failed",
      "need_review",
      "cancelled"
    ]);

  let panelV222 = null;
  let runV222 = null;
  let pollTimerV222 = null;
  let createPromiseV222 = null;
  let resultObserverV222 = null;
  let resultCheckTimerV222 = null;
  let lastProgressSignatureV222 = "";

  function normalizeTextV222(value) {
    return String(value ?? "")
      .trim()
      .replace(/\s+/g, " ");
  }

  function normalizeStatusV222(value) {
    return normalizeTextV222(value)
      .toLowerCase()
      .replace(/[\s-]+/g, "_");
  }

  function escapeHtmlV222(value) {
    const element =
      document.createElement("div");

    element.textContent =
      String(value ?? "");

    return element.innerHTML;
  }

  function findPanelV222() {
    const buttons = Array.from(
      document.querySelectorAll("button")
    ).filter(function (button) {
      return (
        normalizeTextV222(
          button.textContent
        ) === "From Template"
        && !button.closest(
          "nav,aside,[role='navigation'],"
          + "#sidebar,.sidebar,[class*='sidebar']"
        )
      );
    });

    for (const button of buttons) {
      let current =
        button.parentElement;

      for (
        let depth = 0;
        current && depth < 9;
        depth += 1
      ) {
        const content =
          normalizeTextV222(
            current.textContent
          );

        const valid =
          content.includes(
            "From Template"
          )
          && content.includes(
            "Add Custom"
          )
          && content.includes(
            "Test Information"
          )
          && content.includes(
            "Execution Result"
          )
          && current.querySelectorAll(
            "input,select,textarea"
          ).length >= 2;

        const tooBroad =
          content.includes(
            "API Status"
          )
          || content.includes(
            "Autonomous QA Flow"
          )
          || content.includes(
            "Collapse sidebar"
          );

        if (
          valid
          && !tooBroad
        ) {
          return current;
        }

        current =
          current.parentElement;
      }
    }

    return null;
  }

  function visibleV222(element) {
    if (
      !element
      || !element.isConnected
    ) {
      return false;
    }

    const style =
      window.getComputedStyle(
        element
      );

    return (
      !element.hidden
      && style.display !== "none"
      && style.visibility !== "hidden"
      && element.getClientRects().length > 0
    );
  }

  function projectSelectV222() {
    const selectors = [
      "#qaDashboardProjectSelectV12",
      "[data-qa-project-selector]",
      "#qaProjectSelector",
      "select[id*='Project']",
      "select[name*='project' i]"
    ];

    for (const selector of selectors) {
      const element =
        document.querySelector(selector);

      if (
        element
        && element.tagName === "SELECT"
        && element.value
      ) {
        return element;
      }
    }

    return null;
  }

  function projectIdV222() {
    const select =
      projectSelectV222();

    return normalizeTextV222(
      select && select.value
    ) || "default";
  }

  function projectNameV222() {
    const select =
      projectSelectV222();

    if (
      select
      && select.selectedOptions
      && select.selectedOptions.length
    ) {
      return normalizeTextV222(
        select.selectedOptions[0]
          .textContent
      );
    }

    return projectIdV222();
  }

  function environmentV222() {
    const headerText =
      normalizeTextV222(
        document.body.textContent
      );

    const match =
      headerText.match(
        /Environment:\s*([A-Za-z0-9 _-]+)/i
      );

    return match
      ? normalizeTextV222(
          match[1]
        )
      : "";
  }

  function runStorageKeyV222() {
    return (
      RUN_ID_PREFIX_V222
      + "."
      + projectIdV222()
    );
  }

  function saveRunIdV222(runId) {
    if (!runId) {
      return;
    }

    sessionStorage.setItem(
      runStorageKeyV222(),
      String(runId)
    );
  }

  function storedRunIdV222() {
    return sessionStorage.getItem(
      runStorageKeyV222()
    ) || "";
  }

  function controlLabelV222(
    control,
    panel
  ) {
    if (control.id) {
      try {
        const explicit =
          panel.querySelector(
            `label[for="${CSS.escape(control.id)}"]`
          );

        if (explicit) {
          return normalizeTextV222(
            explicit.textContent
          );
        }
      } catch (_) {}
    }

    const wrapping =
      control.closest("label");

    if (wrapping) {
      return normalizeTextV222(
        wrapping.textContent
      );
    }

    let current =
      control.parentElement;

    for (
      let depth = 0;
      current
      && current !== panel
      && depth < 4;
      depth += 1
    ) {
      const directLabels =
        Array.from(
          current.querySelectorAll(
            ":scope > label"
          )
        );

      if (directLabels.length) {
        return normalizeTextV222(
          directLabels[0]
            .textContent
        );
      }

      current =
        current.parentElement;
    }

    return "";
  }

  function semanticKeyV222(
    control,
    panel
  ) {
    const candidates = [
      control.getAttribute(
        "data-qa-draft-key"
      ),
      control.name,
      control.id,
      control.getAttribute(
        "aria-label"
      ),
      controlLabelV222(
        control,
        panel
      ),
      control.placeholder
    ]
      .map(normalizeTextV222)
      .filter(Boolean);

    return (
      candidates[0]
      || (
        control.tagName.toLowerCase()
        + "-"
        + String(control.type || "")
      )
    )
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function safeControlV222(
    control,
    panel
  ) {
    const descriptor = [
      semanticKeyV222(
        control,
        panel
      ),
      control.name,
      control.id,
      control.placeholder,
      control.type
    ].join(" ");

    return !(
      control.disabled
      || control.type === "password"
      || control.type === "hidden"
      || control.type === "file"
      || control.type === "submit"
      || control.type === "button"
      || control.type === "reset"
      || SENSITIVE_PATTERN_V222.test(
        descriptor
      )
    );
  }

  function sanitizeUrlV222(value) {
    const raw =
      normalizeTextV222(value);

    if (!raw) {
      return raw;
    }

    try {
      const url =
        new URL(raw);

      url.username = "";
      url.password = "";

      Array.from(
        url.searchParams.keys()
      ).forEach(function (key) {
        if (
          SENSITIVE_PATTERN_V222.test(
            key
          )
        ) {
          url.searchParams.set(
            key,
            "[REDACTED]"
          );
        }
      });

      return url.toString();
    } catch (_) {
      return raw;
    }
  }

  function snapshotV222(panel) {
    const fields = {};

    Array.from(
      panel.querySelectorAll(
        "input,select,textarea"
      )
    ).forEach(function (control) {
      if (
        !safeControlV222(
          control,
          panel
        )
      ) {
        return;
      }

      const key =
        semanticKeyV222(
          control,
          panel
        );

      if (!key) {
        return;
      }

      let value;

      if (
        control.type === "checkbox"
        || control.type === "radio"
      ) {
        value = {
          kind: control.type,
          checked:
            Boolean(control.checked),
          value:
            String(control.value || "")
        };
      } else if (
        control.tagName === "SELECT"
        && control.multiple
      ) {
        value = {
          kind: "select-multiple",
          values:
            Array.from(
              control.selectedOptions
            ).map(function (option) {
              return String(option.value);
            })
        };
      } else {
        const raw =
          String(control.value || "");

        value = {
          kind:
            control.tagName
              .toLowerCase(),
          value:
            /url|route|endpoint/i.test(
              key
            )
              ? sanitizeUrlV222(raw)
              : raw
        };
      }

      fields[key] = {
        label:
          controlLabelV222(
            control,
            panel
          ),
        name:
          String(
            control.name || ""
          ),
        id:
          String(
            control.id || ""
          ),
        value
      };
    });

    return {
      version: "2.2.2",
      mode:
        activeModeV222(panel),
      fields
    };
  }

  function activeModeV222(panel) {
    const buttons = Array.from(
      panel.querySelectorAll("button")
    ).filter(function (button) {
      const label =
        normalizeTextV222(
          button.textContent
        );

      return (
        label === "From Template"
        || label === "Add Custom"
      );
    });

    const active =
      buttons.find(function (button) {
        return (
          button.getAttribute(
            "aria-pressed"
          ) === "true"
          || button.classList.contains(
            "active"
          )
          || button.classList.contains(
            "selected"
          )
          || button.classList.contains(
            "primary"
          )
        );
      });

    return normalizeTextV222(
      active && active.textContent
    ) || normalizeTextV222(
      buttons[0] && buttons[0].textContent
    ) || "From Template";
  }

  function restoreSnapshotV222(
    panel,
    snapshot
  ) {
    if (
      !panel
      || !snapshot
      || !snapshot.fields
    ) {
      return 0;
    }

    const controls =
      Array.from(
        panel.querySelectorAll(
          "input,select,textarea"
        )
      );

    let restored = 0;

    controls.forEach(function (control) {
      if (
        !safeControlV222(
          control,
          panel
        )
        || document.activeElement
          === control
      ) {
        return;
      }

      const key =
        semanticKeyV222(
          control,
          panel
        );

      const saved =
        snapshot.fields[key];

      if (
        !saved
        || !saved.value
      ) {
        return;
      }

      const value =
        saved.value;

      let changed = false;

      if (
        control.type === "checkbox"
        || control.type === "radio"
      ) {
        const next =
          Boolean(value.checked);

        if (
          control.checked !== next
        ) {
          control.checked = next;
          changed = true;
        }
      } else if (
        control.tagName === "SELECT"
        && control.multiple
        && Array.isArray(
          value.values
        )
      ) {
        const selected =
          new Set(
            value.values.map(String)
          );

        Array.from(
          control.options
        ).forEach(function (option) {
          const next =
            selected.has(
              String(option.value)
            );

          if (
            option.selected !== next
          ) {
            option.selected = next;
            changed = true;
          }
        });
      } else {
        const next =
          String(
            value.value ?? ""
          );

        if (
          control.value !== next
        ) {
          control.value = next;
          changed = true;
        }
      }

      if (changed) {
        control.dispatchEvent(
          new Event(
            "input",
            { bubbles: true }
          )
        );

        control.dispatchEvent(
          new Event(
            "change",
            { bubbles: true }
          )
        );

        restored += 1;
      }
    });

    return restored;
  }

  function findFieldValueV222(
    snapshot,
    patterns
  ) {
    if (
      !snapshot
      || !snapshot.fields
    ) {
      return "";
    }

    for (
      const [key, entry]
      of Object.entries(
        snapshot.fields
      )
    ) {
      const descriptor = [
        key,
        entry.label,
        entry.name,
        entry.id
      ].join(" ");

      if (
        patterns.some(
          pattern =>
            pattern.test(
              descriptor
            )
        )
      ) {
        return normalizeTextV222(
          entry.value
          && entry.value.value
        );
      }
    }

    return "";
  }

  function featureNameV222(
    snapshot
  ) {
    return (
      findFieldValueV222(
        snapshot,
        [
          /test.?name/i,
          /scenario.?name/i,
          /feature/i,
          /template/i
        ]
      )
      || "UI Testing"
    );
  }

  async function apiV222(
    path,
    options
  ) {
    const response =
      await fetch(
        path,
        {
          cache: "no-store",
          ...options,
          headers: {
            "Content-Type":
              "application/json",
            ...(
              options
              && options.headers
                ? options.headers
                : {}
            )
          }
        }
      );

    if (!response.ok) {
      let detail = "";

      try {
        const payload =
          await response.json();

        detail =
          payload.detail
          || JSON.stringify(
            payload
          );
      } catch (_) {
        detail =
          await response.text();
      }

      throw new Error(
        `${response.status} ${detail}`
      );
    }

    return response.json();
  }

  async function createRunV222(
    panel
  ) {
    if (createPromiseV222) {
      return createPromiseV222;
    }

    const snapshot =
      snapshotV222(panel);

    createPromiseV222 =
      apiV222(
        "/runs",
        {
          method: "POST",
          body: JSON.stringify({
            project_id:
              projectIdV222(),
            source:
              "ui_testing",
            feature:
              featureNameV222(
                snapshot
              ),
            test_type:
              "ui",
            environment:
              environmentV222(),
            request_snapshot:
              snapshot
          })
        }
      )
      .then(async function (run) {
        runV222 = run;

        saveRunIdV222(
          run.run_id
        );

        renderRunV222(
          run
        );

        try {
          runV222 =
            await apiV222(
              `/runs/${encodeURIComponent(
                run.run_id
              )}/progress`,
              {
                method: "PATCH",
                body:
                  JSON.stringify({
                    status:
                      "running",
                    progress: 5,
                    current_stage:
                      "execution",
                    current_step:
                      "UI test started"
                  })
              }
            );

          renderRunV222(
            runV222
          );
        } catch (error) {
          console.warn(
            "Run progress initialization failed:",
            error
          );
        }

        return runV222;
      })
      .catch(function (error) {
        showBridgeWarningV222(
          "Execution Store is unavailable. "
          + "The UI test may still run, but its "
          + "active state cannot be restored."
        );

        console.warn(
          "UI execution bridge create failed:",
          error
        );

        throw error;
      })
      .finally(function () {
        createPromiseV222 =
          null;
      });

    return createPromiseV222;
  }

  function ensureSessionUiV222(
    panel
  ) {
    if (!panel) {
      return null;
    }

    let warning =
      panel.querySelector(
        ".qa-ui-run-bridge-warning-v222"
      );

    if (!warning) {
      warning =
        document.createElement(
          "div"
        );

      warning.className =
        "qa-ui-run-bridge-warning-v222";

      panel.insertBefore(
        warning,
        panel.firstChild
      );
    }

    let card =
      panel.querySelector(
        ".qa-ui-run-session-v222"
      );

    if (!card) {
      card =
        document.createElement(
          "section"
        );

      card.className =
        "qa-ui-run-session-v222";

      const titlebar =
        panel.querySelector(
          ".qa-ui-testing-titlebar-v212"
        );

      if (
        titlebar
        && titlebar.nextSibling
      ) {
        panel.insertBefore(
          card,
          titlebar.nextSibling
        );
      } else {
        panel.insertBefore(
          card,
          panel.firstChild
        );
      }
    }

    return card;
  }

  function showBridgeWarningV222(
    message
  ) {
    const panel =
      panelV222
      || findPanelV222();

    if (!panel) {
      return;
    }

    ensureSessionUiV222(panel);

    const warning =
      panel.querySelector(
        ".qa-ui-run-bridge-warning-v222"
      );

    warning.textContent =
      message;

    warning.classList.add(
      "visible"
    );
  }

  function hideBridgeWarningV222() {
    const panel =
      panelV222
      || findPanelV222();

    const warning =
      panel
      && panel.querySelector(
        ".qa-ui-run-bridge-warning-v222"
      );

    if (warning) {
      warning.classList.remove(
        "visible"
      );
    }
  }

  function statusClassV222(status) {
    const normalized =
      normalizeStatusV222(
        status
      );

    return TERMINAL_STATUSES_V222.has(
      normalized
    )
      ? normalized
      : "";
  }

  function renderRunV222(run) {
    const panel =
      panelV222
      || findPanelV222();

    if (
      !panel
      || !run
    ) {
      return;
    }

    panelV222 =
      panel;

    const card =
      ensureSessionUiV222(
        panel
      );

    const progress =
      Math.max(
        0,
        Math.min(
          100,
          Number(
            run.progress || 0
          )
        )
      );

    const status =
      normalizeStatusV222(
        run.status
      ) || "unknown";

    card.innerHTML = `
      <div class="qa-ui-run-session-head-v222">
        <div class="qa-ui-run-session-copy-v222">
          <div class="qa-ui-run-session-eyebrow-v222">
            Execution Session
          </div>

          <div
            class="qa-ui-run-session-title-v222"
            title="${escapeHtmlV222(
              run.feature || "UI Testing"
            )}"
          >
            ${escapeHtmlV222(
              run.feature || "UI Testing"
            )}
          </div>

          <div class="qa-ui-run-session-meta-v222">
            ${escapeHtmlV222(
              projectNameV222()
            )}
            ·
            ${escapeHtmlV222(
              run.environment
              || environmentV222()
              || "Environment not set"
            )}
            ·
            ${escapeHtmlV222(
              run.run_id || ""
            )}
          </div>
        </div>

        <span
          class="qa-ui-run-status-v222 ${escapeHtmlV222(
            statusClassV222(
              status
            )
          )}"
        >
          ${escapeHtmlV222(
            status.replace(
              /_/g,
              " "
            )
          )}
        </span>
      </div>

      <div class="qa-ui-run-progress-track-v222">
        <div
          class="qa-ui-run-progress-bar-v222"
          style="width:${escapeHtmlV222(
            progress
          )}%"
        ></div>
      </div>

      <div class="qa-ui-run-grid-v222">
        <div class="qa-ui-run-detail-v222">
          <div class="qa-ui-run-field-label-v222">
            Current Activity
          </div>

          <div
            class="qa-ui-run-field-value-v222"
            title="${escapeHtmlV222(
              run.current_step
              || run.current_stage
              || "Waiting for update"
            )}"
          >
            ${escapeHtmlV222(
              run.current_step
              || run.current_stage
              || "Waiting for update"
            )}
          </div>
        </div>

        ${[
          ["Passed", run.passed],
          ["Failed", run.failed],
          ["Need Review", run.need_review]
        ].map(function (item) {
          return `
            <div class="qa-ui-run-count-v222">
              <div class="qa-ui-run-field-label-v222">
                ${item[0]}
              </div>

              <div class="qa-ui-run-field-value-v222">
                ${escapeHtmlV222(
                  item[1] ?? 0
                )}
              </div>
            </div>
          `;
        }).join("")}
      </div>

      <div class="qa-ui-run-session-foot-v222">
        <span>
          Progress ${escapeHtmlV222(
            progress.toFixed(0)
          )}%
          · Updated
          ${escapeHtmlV222(
            formatDateV222(
              run.updated_at
              || run.created_at
            )
          )}
        </span>

        <button
          type="button"
          class="qa-ui-run-refresh-v222"
        >
          Refresh status
        </button>
      </div>
    `;

    card.classList.add(
      "visible"
    );

    card.querySelector(
      ".qa-ui-run-refresh-v222"
    ).addEventListener(
      "click",
      function () {
        rehydrateV222(true);
      }
    );

    hideBridgeWarningV222();
  }

  function formatDateV222(value) {
    if (!value) {
      return "not available";
    }

    const date =
      new Date(value);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return String(value);
    }

    return new Intl.DateTimeFormat(
      undefined,
      {
        dateStyle: "medium",
        timeStyle: "short"
      }
    ).format(date);
  }

  async function activeRunV222() {
    const payload =
      await apiV222(
        "/runs/active?"
        + new URLSearchParams({
          project_id:
            projectIdV222(),
          source:
            "ui_testing"
        }).toString(),
        {
          method: "GET"
        }
      );

    return (
      Array.isArray(
        payload.runs
      )
      && payload.runs.length
        ? payload.runs[0]
        : null
    );
  }

  async function storedRunV222() {
    const runId =
      storedRunIdV222();

    if (!runId) {
      return null;
    }

    try {
      return await apiV222(
        `/runs/${encodeURIComponent(
          runId
        )}`,
        {
          method: "GET"
        }
      );
    } catch (error) {
      if (
        String(error.message)
          .startsWith("404")
      ) {
        sessionStorage.removeItem(
          runStorageKeyV222()
        );

        return null;
      }

      throw error;
    }
  }

  async function rehydrateV222(
    force
  ) {
    const panel =
      findPanelV222();

    if (
      !panel
      || !visibleV222(panel)
    ) {
      return null;
    }

    panelV222 =
      panel;

    ensureSessionUiV222(
      panel
    );

    try {
      let run =
        await activeRunV222();

      if (!run) {
        run =
          await storedRunV222();
      }

      if (!run) {
        return null;
      }

      runV222 =
        run;

      saveRunIdV222(
        run.run_id
      );

      renderRunV222(
        run
      );

      const snapshot =
        run.request_snapshot;

      if (
        snapshot
        && (
          force
          || ACTIVE_STATUSES_V222.has(
            normalizeStatusV222(
              run.status
            )
          )
        )
      ) {
        [
          0,
          100,
          350,
          800,
          1400
        ].forEach(function (delay) {
          window.setTimeout(
            function () {
              const current =
                findPanelV222();

              if (current) {
                restoreSnapshotV222(
                  current,
                  snapshot
                );
              }
            },
            delay
          );
        });
      }

      return run;
    } catch (error) {
      showBridgeWarningV222(
        "Could not read the active UI execution "
        + "from the backend."
      );

      console.warn(
        "UI execution bridge rehydrate failed:",
        error
      );

      return null;
    }
  }

  function runButtonV222(panel) {
    if (!panel) {
      return null;
    }

    const candidates =
      Array.from(
        panel.querySelectorAll(
          "button,input[type='submit']"
        )
      );

    const exactLabels = [
      "run ui test",
      "run test",
      "execute ui test",
      "start ui test",
      "start test"
    ];

    return (
      candidates.find(function (element) {
        const label =
          normalizeTextV222(
            element.value
            || element.textContent
          ).toLowerCase();

        return exactLabels.includes(
          label
        );
      })
      || candidates.find(function (element) {
        const label =
          normalizeTextV222(
            element.value
            || element.textContent
          ).toLowerCase();

        return (
          label.includes("run")
          && label.includes("test")
          && !label.includes(
            "detail"
          )
          && !label.includes(
            "history"
          )
        );
      })
      || null
    );
  }

  function executionResultTextV222(
    panel
  ) {
    const headings =
      Array.from(
        panel.querySelectorAll(
          "h1,h2,h3,h4,h5,strong,div,span,p"
        )
      );

    const heading =
      headings.find(function (element) {
        return (
          normalizeTextV222(
            element.textContent
          ) === "Execution Result"
        );
      });

    if (!heading) {
      return "";
    }

    const containers = [
      heading.nextElementSibling,
      heading.parentElement,
      heading.closest(
        ".qa-ui-testing-section-v21"
      )
    ].filter(Boolean);

    for (const container of containers) {
      const text =
        normalizeTextV222(
          container.textContent
        );

      if (
        text
        && text !== "Execution Result"
      ) {
        return text.slice(
          0,
          4000
        );
      }
    }

    return "";
  }

  function extractCountV222(
    text,
    label
  ) {
    const patterns = [
      new RegExp(
        `${label}\\s*[:=-]?\\s*(\\d+)`,
        "i"
      ),
      new RegExp(
        `(\\d+)\\s*${label}`,
        "i"
      )
    ];

    for (const pattern of patterns) {
      const match =
        text.match(pattern);

      if (match) {
        return Number(
          match[1]
        );
      }
    }

    return null;
  }

  function deriveResultV222(
    panel
  ) {
    const text =
      executionResultTextV222(
        panel
      );

    if (
      !text
      || /no result/i.test(text)
      || /waiting for/i.test(text)
    ) {
      return null;
    }

    let status = "";

    if (
      /\bneed review\b/i.test(
        text
      )
    ) {
      status =
        "need_review";
    } else if (
      /\bfailed\b/i.test(
        text
      )
    ) {
      status =
        "failed";
    } else if (
      /\bpassed\b/i.test(
        text
      )
    ) {
      status =
        "passed";
    } else if (
      /\bcompleted\b/i.test(
        text
      )
    ) {
      status =
        "completed";
    }

    if (!status) {
      return null;
    }

    return {
      status,
      passed:
        extractCountV222(
          text,
          "passed"
        ),
      failed:
        extractCountV222(
          text,
          "failed"
        ),
      need_review:
        extractCountV222(
          text,
          "need\\s*review"
        ),
      summary: text
    };
  }

  async function completeFromDomV222(
    result
  ) {
    if (
      !runV222
      || !runV222.run_id
      || TERMINAL_STATUSES_V222.has(
        normalizeStatusV222(
          runV222.status
        )
      )
    ) {
      return;
    }

    try {
      runV222 =
        await apiV222(
          `/runs/${encodeURIComponent(
            runV222.run_id
          )}/complete`,
          {
            method: "POST",
            body: JSON.stringify({
              status:
                result.status,
              progress: 100,
              passed:
                result.passed,
              failed:
                result.failed,
              need_review:
                result.need_review,
              result_summary: {
                source:
                  "ui_testing_dom",
                text:
                  result.summary
                    .slice(0, 3000)
              },
              artifacts: []
            })
          }
        );

      renderRunV222(
        runV222
      );
    } catch (error) {
      console.warn(
        "UI execution completion update failed:",
        error
      );
    }
  }

  function inspectResultV222() {
    window.clearTimeout(
      resultCheckTimerV222
    );

    resultCheckTimerV222 =
      window.setTimeout(
        function () {
          const panel =
            findPanelV222();

          if (
            !panel
            || !runV222
          ) {
            return;
          }

          const result =
            deriveResultV222(
              panel
            );

          if (result) {
            completeFromDomV222(
              result
            );
          }
        },
        120
      );
  }

  async function updateProgressFromDomV222() {
    if (
      !runV222
      || !runV222.run_id
      || !ACTIVE_STATUSES_V222.has(
        normalizeStatusV222(
          runV222.status
        )
      )
    ) {
      return;
    }

    const panel =
      findPanelV222();

    if (!panel) {
      return;
    }

    const text =
      normalizeTextV222(
        panel.textContent
      );

    const progressMatch =
      text.match(
        /\b(\d{1,3})\s*%/
      );

    if (!progressMatch) {
      return;
    }

    const progress =
      Math.max(
        5,
        Math.min(
          99,
          Number(
            progressMatch[1]
          )
        )
      );

    const signature =
      `${runV222.run_id}:${progress}`;

    if (
      signature ===
      lastProgressSignatureV222
    ) {
      return;
    }

    lastProgressSignatureV222 =
      signature;

    try {
      runV222 =
        await apiV222(
          `/runs/${encodeURIComponent(
            runV222.run_id
          )}/progress`,
          {
            method: "PATCH",
            body: JSON.stringify({
              status:
                "running",
              progress,
              current_stage:
                "execution",
              current_step:
                "UI test is running"
            })
          }
        );

      renderRunV222(
        runV222
      );
    } catch (error) {
      console.warn(
        "UI execution progress update failed:",
        error
      );
    }
  }

  function observeResultV222() {
    if (resultObserverV222) {
      return;
    }

    resultObserverV222 =
      new MutationObserver(
        function () {
          inspectResultV222();
          updateProgressFromDomV222();
        }
      );

    resultObserverV222.observe(
      document.body,
      {
        childList: true,
        subtree: true,
        characterData: true
      }
    );
  }

  function handleRunClickV222(
    event
  ) {
    const panel =
      findPanelV222();

    if (!panel) {
      return;
    }

    const button =
      event.target.closest(
        "button,input[type='submit']"
      );

    if (
      !button
      || button !== runButtonV222(
        panel
      )
    ) {
      return;
    }

    /*
      Capture the request snapshot before the existing UI runner
      replaces or clears the form. The original runner click is not
      prevented and continues normally.
    */
    createRunV222(
      panel
    ).catch(function () {});

    window.setTimeout(
      inspectResultV222,
      300
    );

    window.setTimeout(
      inspectResultV222,
      1200
    );
  }

  function pollV222() {
    window.clearInterval(
      pollTimerV222
    );

    pollTimerV222 =
      window.setInterval(
        function () {
          const panel =
            findPanelV222();

          if (
            panel
            && visibleV222(
              panel
            )
          ) {
            panelV222 =
              panel;

            rehydrateV222(false);
            inspectResultV222();
          }
        },
        2500
      );
  }

  document.addEventListener(
    "click",
    handleRunClickV222,
    true
  );

  document.addEventListener(
    "pointerdown",
    function () {
      if (
        panelV222
        && visibleV222(
          panelV222
        )
        && typeof window
          .qaSaveUiTestingDraftV213
          === "function"
      ) {
        window
          .qaSaveUiTestingDraftV213();
      }
    },
    true
  );

  window.addEventListener(
    "qa-project-changed",
    function () {
      runV222 = null;
      panelV222 = null;

      window.setTimeout(
        function () {
          rehydrateV222(true);
        },
        120
      );
    }
  );

  document.addEventListener(
    "visibilitychange",
    function () {
      if (!document.hidden) {
        rehydrateV222(true);
      }
    }
  );

  window.qaRehydrateUiRunV222 =
    function () {
      return rehydrateV222(
        true
      );
    };

  window.qaCurrentUiRunV222 =
    function () {
      return runV222;
    };

  function initializeV222() {
    panelV222 =
      findPanelV222();

    if (panelV222) {
      ensureSessionUiV222(
        panelV222
      );
    }

    observeResultV222();
    pollV222();

    window.setTimeout(
      function () {
        rehydrateV222(true);
      },
      100
    );

    window.setTimeout(
      function () {
        rehydrateV222(true);
      },
      700
    );
  }

  if (
    document.readyState
    === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      initializeV222
    );
  } else {
    initializeV222();
  }

  window.addEventListener(
    "load",
    initializeV222
  );
})();
'''


if CSS_MARKER not in text:
    style_close = text.rfind("</style>")

    if style_close == -1:
        shutil.copy2(
            backup_path,
            HTML_PATH
        )
        fail("Closing </style> tag was not found")

    text = (
        text[:style_close]
        + "\n"
        + css
        + "\n"
        + text[style_close:]
    )

    print(
        "[OK] UI Testing Execution Bridge V2.2.2 CSS inserted"
    )
else:
    print(
        "[SKIP] UI Testing Execution Bridge V2.2.2 CSS already exists"
    )


if JS_MARKER not in text:
    script_close = text.rfind("</script>")

    if script_close == -1:
        shutil.copy2(
            backup_path,
            HTML_PATH
        )
        fail("Closing </script> tag was not found")

    text = (
        text[:script_close]
        + "\n"
        + js
        + "\n"
        + text[script_close:]
    )

    print(
        "[OK] UI Testing Execution Bridge V2.2.2 JavaScript inserted"
    )
else:
    print(
        "[SKIP] UI Testing Execution Bridge V2.2.2 JavaScript already exists"
    )


verification = [
    CSS_MARKER,
    JS_MARKER,
    "async function createRunV222(",
    "async function rehydrateV222(",
    "function restoreSnapshotV222(",
    "qaRehydrateUiRunV222",
]

missing_verification = [
    marker
    for marker in verification
    if marker not in text
]

if missing_verification:
    shutil.copy2(
        backup_path,
        HTML_PATH
    )

    fail(
        "Verification failed. Dashboard restored. Missing markers: "
        + ", ".join(missing_verification)
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8"
)

print(f"[OK] Backup created: {backup_path}")
print(f"[OK] Updated: {HTML_PATH}")
print()
print(
    "[SUCCESS] UI Testing Execution Bridge V2.2.2 installed"
)
