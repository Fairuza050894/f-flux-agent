from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA UI TESTING WORKSPACE V2.1 CSS */"
JS_MARKER = "/* QA UI TESTING WORKSPACE V2.1 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


text = HTML_PATH.read_text(encoding="utf-8")

required_base_markers = [
    "/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 JS */",
    "/* QA MAIN DASHBOARD MONITORING BUGFIX V1.2.1 CSS */",
]

missing_base = [
    marker
    for marker in required_base_markers
    if marker not in text
]

if missing_base:
    fail(
        "Required stable Main Dashboard V1.2.1 markers were not found: "
        + ", ".join(missing_base)
    )


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_ui_testing_workspace_v2_1_{timestamp}"
)

shutil.copy2(
    HTML_PATH,
    backup_path,
)


css = r'''
/* QA UI TESTING WORKSPACE V2.1 CSS */

/*
  UI Testing is an execution workspace. Dashboard summary cards
  and the global flow are hidden only while this workspace is active.
*/
body.qa-ui-testing-active-v21
  .qa-dashboard-legacy-metric-v12,
body.qa-ui-testing-active-v21
  .qa-ui-testing-global-flow-v21 {
  display: none !important;
}

body.qa-ui-testing-active-v21
  .qa-ui-testing-panel-v21 {
  max-width: 100% !important;
  min-width: 0 !important;
  overflow-x: hidden !important;
}

.qa-ui-testing-panel-v21 {
  --qa-ui-border-v21: #dbe3ee;
  --qa-ui-muted-v21: #64748b;
  --qa-ui-text-v21: #0f172a;
  --qa-ui-soft-v21: #f8fafc;
  --qa-ui-blue-v21: #2563eb;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-heading-row-v21 {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-heading-row-v21
  h1,
.qa-ui-testing-panel-v21
  .qa-ui-testing-heading-row-v21
  h2,
.qa-ui-testing-panel-v21
  .qa-ui-testing-heading-row-v21
  h3 {
  margin: 0 !important;
}

.qa-ui-testing-draft-status-v21 {
  display: inline-flex;
  min-height: 24px;
  align-items: center;
  gap: 6px;
  flex: 0 0 auto;
  padding: 4px 8px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 9px;
  font-weight: 800;
  white-space: nowrap;
}

.qa-ui-testing-draft-status-v21::before {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  content: "";
}

.qa-ui-testing-mode-v21 {
  display: inline-flex !important;
  width: fit-content;
  max-width: 100%;
  gap: 4px !important;
  padding: 4px !important;
  border: 1px solid var(--qa-ui-border-v21) !important;
  border-radius: 10px !important;
  background: #f1f5f9 !important;
}

.qa-ui-testing-mode-v21 button {
  min-height: 34px !important;
  padding: 7px 13px !important;
  border-radius: 7px !important;
  font-size: 10px !important;
  font-weight: 800 !important;
}

.qa-ui-testing-context-v21 {
  margin-top: 10px !important;
  padding: 13px 14px !important;
  border: 1px solid #bfdbfe !important;
  border-left: 3px solid var(--qa-ui-blue-v21) !important;
  border-radius: 10px !important;
  background: #eff6ff !important;
}

.qa-ui-testing-context-v21 strong,
.qa-ui-testing-context-v21 h3,
.qa-ui-testing-context-v21 h4 {
  color: #1e3a8a !important;
}

.qa-ui-testing-section-v21 {
  min-width: 0 !important;
  margin-top: 10px !important;
  padding: 14px !important;
  border: 1px solid var(--qa-ui-border-v21) !important;
  border-radius: 11px !important;
  background: #ffffff !important;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .03);
}

.qa-ui-testing-section-v21:hover {
  border-color: #cbd5e1 !important;
}

.qa-ui-testing-section-heading-v21 {
  margin: 0 0 3px !important;
  color: var(--qa-ui-text-v21) !important;
  font-size: 11px !important;
  font-weight: 850 !important;
}

.qa-ui-testing-panel-v21 label {
  color: #334155 !important;
  font-size: 9px !important;
  font-weight: 800 !important;
}

.qa-ui-testing-panel-v21
  input:not([type="checkbox"]):not([type="radio"]),
.qa-ui-testing-panel-v21
  select,
.qa-ui-testing-panel-v21
  textarea {
  width: 100% !important;
  min-width: 0 !important;
  min-height: 38px !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 8px !important;
  background: #ffffff !important;
  color: var(--qa-ui-text-v21) !important;
  font-size: 10px !important;
}

.qa-ui-testing-panel-v21
  input:not([type="checkbox"]):not([type="radio"]):focus,
.qa-ui-testing-panel-v21
  select:focus,
.qa-ui-testing-panel-v21
  textarea:focus {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, .10) !important;
  outline: none !important;
}

.qa-ui-testing-panel-v21
  input::placeholder,
.qa-ui-testing-panel-v21
  textarea::placeholder {
  color: #94a3b8 !important;
}

.qa-ui-testing-target-preview-v21 {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 9px 10px;
  border: 1px dashed #bfdbfe;
  border-radius: 8px;
  background: #f8fbff;
}

.qa-ui-testing-target-preview-label-v21 {
  flex: 0 0 auto;
  color: #64748b;
  font-size: 9px;
  font-weight: 800;
}

.qa-ui-testing-target-preview-value-v21 {
  min-width: 0;
  overflow: hidden;
  color: #1d4ed8;
  font-family:
    ui-monospace,
    SFMono-Regular,
    Menlo,
    Monaco,
    Consolas,
    monospace;
  font-size: 9px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-ui-testing-validation-note-v21 {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 8px;
  padding: 9px 10px;
  border-radius: 8px;
  background: #f8fafc;
  color: #475569;
  font-size: 9px;
  line-height: 1.5;
}

.qa-ui-testing-validation-note-v21::before {
  display: inline-flex;
  width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  flex: 0 0 18px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #475569;
  content: "i";
  font-size: 9px;
  font-weight: 900;
}

.qa-ui-testing-result-empty-v21 {
  padding: 18px 14px !important;
  border: 1px dashed #cbd5e1 !important;
  border-radius: 9px !important;
  background: #f8fafc !important;
  color: #64748b !important;
  font-size: 10px !important;
  line-height: 1.55 !important;
  text-align: center !important;
}

.qa-ui-testing-template-library-v21 {
  margin-top: 10px !important;
  border-radius: 9px !important;
}

@media (max-width: 720px) {
  .qa-ui-testing-panel-v21
    .qa-ui-testing-heading-row-v21 {
    align-items: flex-start;
    flex-direction: column;
  }

  .qa-ui-testing-draft-status-v21 {
    align-self: flex-start;
  }

  .qa-ui-testing-target-preview-v21 {
    align-items: flex-start;
    flex-direction: column;
  }
}
'''


js = r'''
/* QA UI TESTING WORKSPACE V2.1 JS */
(function () {
  "use strict";

  const STORAGE_PREFIX_V21 =
    "qa.ui-testing.workspace.v21";

  const SENSITIVE_PATTERN_V21 =
    /(password|passwd|secret|token|cookie|authorization|credential|api.?key)/i;

  let activePanelV21 = null;
  let wasVisibleV21 = false;
  let restoreTimerV21 = null;
  let autosaveTimerV21 = null;
  let rerenderGuardV21 = false;

  function textV21(element) {
    return String(
      element && element.textContent || ""
    )
      .trim()
      .replace(/\s+/g, " ");
  }

  function exactTextV21(value, root) {
    const scope = root || document;

    return Array.from(
      scope.querySelectorAll(
        "h1,h2,h3,h4,h5,div,span,strong,p,label,button"
      )
    ).find(function (element) {
      return textV21(element) === value;
    }) || null;
  }

  function findUiPanelV21() {
    const heading = exactTextV21(
      "UI Testing"
    );

    if (!heading) {
      return null;
    }

    let current = heading;

    for (
      let depth = 0;
      current && depth < 9;
      depth += 1
    ) {
      const content =
        textV21(current);

      if (
        content.includes("From Template")
        && content.includes("Add Custom")
        && content.includes("Execution Result")
      ) {
        return current;
      }

      current =
        current.parentElement;
    }

    return heading.parentElement;
  }

  function panelVisibleV21(panel) {
    if (!panel) {
      return false;
    }

    const style =
      window.getComputedStyle(panel);

    return (
      !panel.hidden
      && style.display !== "none"
      && style.visibility !== "hidden"
      && panel.getClientRects().length > 0
    );
  }

  function currentProjectV21() {
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
        return String(
          element.value
        );
      }
    }

    return "default";
  }

  function activeModeV21(panel) {
    const saved = sessionStorage.getItem(
      STORAGE_PREFIX_V21
      + "."
      + currentProjectV21()
      + ".active-mode"
    );

    const buttons = Array.from(
      panel.querySelectorAll("button")
    ).filter(function (button) {
      const value = textV21(button);

      return (
        value === "From Template"
        || value === "Add Custom"
      );
    });

    const active = buttons.find(
      function (button) {
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
      }
    );

    return (
      textV21(active)
      || saved
      || textV21(buttons[0])
      || "From Template"
    );
  }

  function storageKeyV21(panel) {
    return [
      STORAGE_PREFIX_V21,
      currentProjectV21(),
      activeModeV21(panel)
        .toLowerCase()
        .replace(/\s+/g, "-")
    ].join(".");
  }

  function associatedLabelV21(control) {
    if (control.id) {
      const explicit =
        document.querySelector(
          `label[for="${CSS.escape(control.id)}"]`
        );

      if (explicit) {
        return textV21(explicit);
      }
    }

    let current =
      control.parentElement;

    for (
      let depth = 0;
      current && depth < 3;
      depth += 1
    ) {
      const label =
        current.querySelector("label");

      if (label) {
        return textV21(label);
      }

      current =
        current.parentElement;
    }

    return "";
  }

  function fieldKeyV21(
    control,
    index
  ) {
    const key = [
      control.name,
      control.id,
      associatedLabelV21(control),
      control.placeholder,
      control.getAttribute("aria-label"),
      control.tagName,
      index
    ].filter(Boolean).join("|");

    return key;
  }

  function isPersistableV21(
    control,
    index
  ) {
    if (
      !control
      || control.disabled
      || control.type === "password"
      || control.type === "file"
      || control.type === "submit"
      || control.type === "button"
      || control.type === "reset"
    ) {
      return false;
    }

    const key =
      fieldKeyV21(control, index);

    return !SENSITIVE_PATTERN_V21.test(
      key
    );
  }

  function collectStateV21(panel) {
    const state = {
      saved_at:
        new Date().toISOString(),
      fields: {}
    };

    Array.from(
      panel.querySelectorAll(
        "input,select,textarea"
      )
    ).forEach(
      function (control, index) {
        if (
          !isPersistableV21(
            control,
            index
          )
        ) {
          return;
        }

        const key =
          fieldKeyV21(
            control,
            index
          );

        if (
          control.type === "checkbox"
          || control.type === "radio"
        ) {
          state.fields[key] = {
            kind: control.type,
            checked:
              Boolean(control.checked),
            value:
              String(control.value || "")
          };
        } else {
          state.fields[key] = {
            kind:
              control.tagName.toLowerCase(),
            value:
              String(control.value || "")
          };
        }
      }
    );

    return state;
  }

  function setDraftStatusV21(
    panel,
    message
  ) {
    const badge =
      panel.querySelector(
        ".qa-ui-testing-draft-status-v21"
      );

    if (badge) {
      badge.textContent =
        message;
    }
  }

  function saveStateV21(panel) {
    if (!panel) {
      return;
    }

    const state =
      collectStateV21(panel);

    try {
      sessionStorage.setItem(
        storageKeyV21(panel),
        JSON.stringify(state)
      );

      setDraftStatusV21(
        panel,
        "Draft saved"
      );
    } catch (error) {
      console.warn(
        "UI Testing draft could not be saved:",
        error
      );

      setDraftStatusV21(
        panel,
        "Draft not saved"
      );
    }
  }

  function scheduleSaveV21(panel) {
    window.clearTimeout(
      autosaveTimerV21
    );

    setDraftStatusV21(
      panel,
      "Saving draft…"
    );

    autosaveTimerV21 =
      window.setTimeout(
        function () {
          saveStateV21(panel);
        },
        180
      );
  }

  function restoreStateV21(panel) {
    if (!panel) {
      return;
    }

    let state = null;

    try {
      const raw =
        sessionStorage.getItem(
          storageKeyV21(panel)
        );

      state =
        raw
          ? JSON.parse(raw)
          : null;
    } catch (error) {
      console.warn(
        "UI Testing draft could not be restored:",
        error
      );
    }

    if (
      !state
      || !state.fields
    ) {
      setDraftStatusV21(
        panel,
        "Draft ready"
      );

      return;
    }

    let restored = 0;

    Array.from(
      panel.querySelectorAll(
        "input,select,textarea"
      )
    ).forEach(
      function (control, index) {
        if (
          !isPersistableV21(
            control,
            index
          )
        ) {
          return;
        }

        const key =
          fieldKeyV21(
            control,
            index
          );

        const saved =
          state.fields[key];

        if (!saved) {
          return;
        }

        if (
          control.type === "checkbox"
          || control.type === "radio"
        ) {
          if (
            control.checked
            !== Boolean(saved.checked)
          ) {
            control.checked =
              Boolean(saved.checked);

            control.dispatchEvent(
              new Event(
                "change",
                { bubbles: true }
              )
            );
          }
        } else if (
          control.value
          !== String(saved.value ?? "")
        ) {
          control.value =
            String(saved.value ?? "");

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
        }

        restored += 1;
      }
    );

    setDraftStatusV21(
      panel,
      restored
        ? "Draft restored"
        : "Draft ready"
    );
  }

  function joinUrlV21(
    base,
    route
  ) {
    const baseValue =
      String(base || "").trim();

    const routeValue =
      String(route || "").trim();

    if (!baseValue && !routeValue) {
      return "Target URL will appear here";
    }

    if (!baseValue) {
      return routeValue;
    }

    if (!routeValue) {
      return baseValue;
    }

    return (
      baseValue.replace(/\/+$/, "")
      + "/"
      + routeValue.replace(/^\/+/, "")
    );
  }

  function fieldByLabelV21(
    panel,
    labelText
  ) {
    const labels =
      Array.from(
        panel.querySelectorAll("label")
      );

    const label =
      labels.find(function (candidate) {
        return textV21(candidate)
          .toLowerCase()
          .startsWith(
            labelText.toLowerCase()
          );
      });

    if (!label) {
      return null;
    }

    if (
      label.htmlFor
      && document.getElementById(
        label.htmlFor
      )
    ) {
      return document.getElementById(
        label.htmlFor
      );
    }

    const parent =
      label.parentElement;

    return parent
      ? parent.querySelector(
          "input,select,textarea"
        )
      : null;
  }

  function updateTargetPreviewV21(panel) {
    const preview =
      panel.querySelector(
        ".qa-ui-testing-target-preview-value-v21"
      );

    if (!preview) {
      return;
    }

    const base =
      fieldByLabelV21(
        panel,
        "Base URL"
      );

    const route =
      fieldByLabelV21(
        panel,
        "Route"
      );

    const value =
      joinUrlV21(
        base && base.value,
        route && route.value
      );

    preview.textContent =
      value;

    preview.title =
      value;
  }

  function closestSectionV21(
    heading,
    panel
  ) {
    let current =
      heading && heading.parentElement;

    for (
      let depth = 0;
      current
      && current !== panel
      && depth < 5;
      depth += 1
    ) {
      const content =
        textV21(current);

      if (
        content.length > 0
        && current.querySelector(
          "input,select,textarea"
        )
      ) {
        return current;
      }

      if (
        heading
        && textV21(heading)
          === "Validation"
        && content.includes(
          "Credential menggunakan"
        )
      ) {
        return current;
      }

      current =
        current.parentElement;
    }

    return (
      heading
      && heading.parentElement
    );
  }

  function markGlobalFlowV21() {
    const heading =
      exactTextV21(
        "Autonomous QA Flow"
      );

    if (!heading) {
      return;
    }

    let current =
      heading.parentElement;

    for (
      let depth = 0;
      current && depth < 6;
      depth += 1
    ) {
      const content =
        textV21(current);

      if (
        content.includes("Planning")
        && content.includes("Report")
        && content.includes("Ready.")
      ) {
        current.classList.add(
          "qa-ui-testing-global-flow-v21"
        );

        return;
      }

      current =
        current.parentElement;
    }
  }

  function markLegacyMetricsV21() {
    [
      "API Status",
      "Total Runs",
      "PASS",
      "FAILED / REVIEW"
    ].forEach(function (label) {
      const node =
        exactTextV21(label);

      if (!node) {
        return;
      }

      let current =
        node.parentElement;

      for (
        let depth = 0;
        current && depth < 4;
        depth += 1
      ) {
        const content =
          textV21(current);

        if (
          content.includes(label)
          && content.length < 120
        ) {
          current.classList.add(
            "qa-dashboard-legacy-metric-v12"
          );
        }

        current =
          current.parentElement;
      }
    });
  }

  function ensureHeadingStatusV21(panel) {
    const heading =
      exactTextV21(
        "UI Testing",
        panel
      );

    if (!heading) {
      return;
    }

    let row =
      heading.parentElement;

    if (
      row
      && !row.classList.contains(
        "qa-ui-testing-heading-row-v21"
      )
    ) {
      row.classList.add(
        "qa-ui-testing-heading-row-v21"
      );
    }

    if (
      row
      && !row.querySelector(
        ".qa-ui-testing-draft-status-v21"
      )
    ) {
      const badge =
        document.createElement("span");

      badge.className =
        "qa-ui-testing-draft-status-v21";

      badge.textContent =
        "Draft ready";

      row.appendChild(
        badge
      );
    }
  }

  function markModeV21(panel) {
    const buttons = Array.from(
      panel.querySelectorAll("button")
    ).filter(function (button) {
      const value =
        textV21(button);

      return (
        value === "From Template"
        || value === "Add Custom"
      );
    });

    if (!buttons.length) {
      return;
    }

    const parent =
      buttons[0].parentElement;

    if (parent) {
      parent.classList.add(
        "qa-ui-testing-mode-v21"
      );
    }
  }

  function markContextV21(panel) {
    const title =
      exactTextV21(
        "Mobospace UI Testing",
        panel
      );

    if (!title) {
      return;
    }

    let current =
      title.parentElement;

    for (
      let depth = 0;
      current
      && current !== panel
      && depth < 4;
      depth += 1
    ) {
      const content =
        textV21(current);

      if (
        content.includes(
          "Environment:"
        )
        && content.includes(
          "registered features"
        )
      ) {
        current.classList.add(
          "qa-ui-testing-context-v21"
        );

        return;
      }

      current =
        current.parentElement;
    }
  }

  function markTemplateLibraryV21(panel) {
    const library =
      exactTextV21(
        "Template Library",
        panel
      );

    if (library) {
      (
        library.closest("details")
        || library.parentElement
      )?.classList.add(
        "qa-ui-testing-template-library-v21"
      );
    }
  }

  function markSectionsV21(panel) {
    [
      "Test Information",
      "Target",
      "Validation"
    ].forEach(function (title) {
      const heading =
        exactTextV21(
          title,
          panel
        );

      if (!heading) {
        return;
      }

      heading.classList.add(
        "qa-ui-testing-section-heading-v21"
      );

      const section =
        closestSectionV21(
          heading,
          panel
        );

      if (section) {
        section.classList.add(
          "qa-ui-testing-section-v21"
        );
      }
    });

    const executionHeading =
      exactTextV21(
        "Execution Result",
        panel
      );

    if (executionHeading) {
      executionHeading.classList.add(
        "qa-ui-testing-section-heading-v21"
      );

      const resultContainer =
        executionHeading.nextElementSibling;

      if (
        resultContainer
        && textV21(resultContainer)
          .toLowerCase()
          .includes("no result")
      ) {
        resultContainer.classList.add(
          "qa-ui-testing-result-empty-v21"
        );
      }
    }
  }

  function ensureTargetPreviewV21(panel) {
    const targetHeading =
      exactTextV21(
        "Target",
        panel
      );

    if (!targetHeading) {
      return;
    }

    const section =
      closestSectionV21(
        targetHeading,
        panel
      );

    if (
      !section
      || section.querySelector(
        ".qa-ui-testing-target-preview-v21"
      )
    ) {
      updateTargetPreviewV21(panel);
      return;
    }

    const preview =
      document.createElement("div");

    preview.className =
      "qa-ui-testing-target-preview-v21";

    preview.innerHTML = `
      <span
        class="qa-ui-testing-target-preview-label-v21"
      >
        Target URL Preview
      </span>

      <span
        class="qa-ui-testing-target-preview-value-v21"
      >
        Target URL will appear here
      </span>
    `;

    section.appendChild(
      preview
    );

    updateTargetPreviewV21(panel);
  }

  function ensureValidationNoteV21(panel) {
    const heading =
      exactTextV21(
        "Validation",
        panel
      );

    if (!heading) {
      return;
    }

    const section =
      closestSectionV21(
        heading,
        panel
      );

    if (
      !section
      || section.querySelector(
        ".qa-ui-testing-validation-note-v21"
      )
    ) {
      return;
    }

    const note =
      document.createElement("div");

    note.className =
      "qa-ui-testing-validation-note-v21";

    note.textContent =
      "Validation currently follows the selected project or template configuration. Additional validation controls will be exposed only after they are mapped to the runner payload.";

    section.appendChild(
      note
    );
  }

  function ensureFormRenderedV21(panel) {
    const hasTestInformation =
      Boolean(
        exactTextV21(
          "Test Information",
          panel
        )
      );

    const fieldCount =
      panel.querySelectorAll(
        "input,select,textarea"
      ).length;

    if (
      hasTestInformation
      && fieldCount >= 2
    ) {
      return false;
    }

    if (rerenderGuardV21) {
      return false;
    }

    const preferredMode =
      sessionStorage.getItem(
        STORAGE_PREFIX_V21
        + "."
        + currentProjectV21()
        + ".active-mode"
      )
      || "From Template";

    const button =
      Array.from(
        panel.querySelectorAll("button")
      ).find(function (candidate) {
        return (
          textV21(candidate)
          === preferredMode
        );
      })
      || Array.from(
        panel.querySelectorAll("button")
      ).find(function (candidate) {
        return (
          textV21(candidate)
          === "From Template"
        );
      });

    if (!button) {
      return false;
    }

    rerenderGuardV21 = true;

    button.click();

    window.setTimeout(
      function () {
        rerenderGuardV21 =
          false;

        enhanceV21();
        restoreStateV21(
          activePanelV21
        );
      },
      120
    );

    return true;
  }

  function enhanceV21() {
    const panel =
      findUiPanelV21();

    activePanelV21 =
      panel;

    const visible =
      panelVisibleV21(panel);

    document.body.classList.toggle(
      "qa-ui-testing-active-v21",
      visible
    );

    if (!panel) {
      wasVisibleV21 =
        false;

      return;
    }

    panel.classList.add(
      "qa-ui-testing-panel-v21"
    );

    markGlobalFlowV21();
    markLegacyMetricsV21();
    ensureHeadingStatusV21(panel);
    markModeV21(panel);
    markContextV21(panel);
    markTemplateLibraryV21(panel);
    markSectionsV21(panel);
    ensureTargetPreviewV21(panel);
    ensureValidationNoteV21(panel);

    if (
      visible
      && !wasVisibleV21
    ) {
      const rerendered =
        ensureFormRenderedV21(panel);

      if (!rerendered) {
        window.clearTimeout(
          restoreTimerV21
        );

        restoreTimerV21 =
          window.setTimeout(
            function () {
              restoreStateV21(panel);
              updateTargetPreviewV21(panel);
            },
            80
          );
      }
    }

    wasVisibleV21 =
      visible;
  }

  document.addEventListener(
    "input",
    function (event) {
      const panel =
        activePanelV21
        || findUiPanelV21();

      if (
        !panel
        || !panel.contains(
          event.target
        )
      ) {
        return;
      }

      updateTargetPreviewV21(
        panel
      );

      scheduleSaveV21(
        panel
      );
    },
    true
  );

  document.addEventListener(
    "change",
    function (event) {
      const panel =
        activePanelV21
        || findUiPanelV21();

      if (
        !panel
        || !panel.contains(
          event.target
        )
      ) {
        return;
      }

      updateTargetPreviewV21(
        panel
      );

      scheduleSaveV21(
        panel
      );
    },
    true
  );

  document.addEventListener(
    "click",
    function (event) {
      const panel =
        activePanelV21
        || findUiPanelV21();

      if (
        panel
        && panelVisibleV21(panel)
      ) {
        saveStateV21(panel);
      }

      const button =
        event.target.closest("button");

      const mode =
        textV21(button);

      if (
        panel
        && (
          mode === "From Template"
          || mode === "Add Custom"
        )
      ) {
        sessionStorage.setItem(
          STORAGE_PREFIX_V21
          + "."
          + currentProjectV21()
          + ".active-mode",
          mode
        );

        window.setTimeout(
          function () {
            enhanceV21();
            restoreStateV21(
              findUiPanelV21()
            );
          },
          100
        );
      } else {
        window.setTimeout(
          enhanceV21,
          80
        );

        window.setTimeout(
          enhanceV21,
          220
        );
      }
    },
    true
  );

  window.addEventListener(
    "qa-project-changed",
    function () {
      if (activePanelV21) {
        saveStateV21(
          activePanelV21
        );
      }

      wasVisibleV21 =
        false;

      window.setTimeout(
        enhanceV21,
        100
      );
    }
  );

  window.addEventListener(
    "beforeunload",
    function () {
      if (activePanelV21) {
        saveStateV21(
          activePanelV21
        );
      }
    }
  );

  document.addEventListener(
    "visibilitychange",
    function () {
      if (
        document.hidden
        && activePanelV21
      ) {
        saveStateV21(
          activePanelV21
        );
      } else {
        enhanceV21();
      }
    }
  );

  window.qaEnhanceUiTestingV21 =
    enhanceV21;

  window.qaSaveUiTestingDraftV21 =
    function () {
      const panel =
        activePanelV21
        || findUiPanelV21();

      saveStateV21(panel);
    };

  window.qaRestoreUiTestingDraftV21 =
    function () {
      const panel =
        activePanelV21
        || findUiPanelV21();

      restoreStateV21(panel);
    };

  if (
    document.readyState
    === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      enhanceV21
    );
  } else {
    enhanceV21();
  }

  window.addEventListener(
    "load",
    function () {
      enhanceV21();

      window.setTimeout(
        enhanceV21,
        300
      );

      window.setTimeout(
        enhanceV21,
        900
      );
    }
  );

  window.setInterval(
    enhanceV21,
    700
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
        "[OK] UI Testing Workspace V2.1 CSS inserted"
    )
else:
    print(
        "[SKIP] UI Testing Workspace V2.1 CSS already exists"
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
        "[OK] UI Testing Workspace V2.1 JavaScript inserted"
    )
else:
    print(
        "[SKIP] UI Testing Workspace V2.1 JavaScript already exists"
    )


required_markers = [
    CSS_MARKER,
    JS_MARKER,
    "function saveStateV21(panel)",
    "function restoreStateV21(panel)",
    "function ensureFormRenderedV21(panel)",
    "qaEnhanceUiTestingV21",
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

print(
    f"[OK] Backup created: {backup_path}"
)

print(
    f"[OK] Updated: {HTML_PATH}"
)

print()

print(
    "[SUCCESS] UI Testing Workspace V2.1 installed"
)
