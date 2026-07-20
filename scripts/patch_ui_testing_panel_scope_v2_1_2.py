from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

PATCH_MARKER = "/* QA UI TESTING PANEL SCOPE V2.1.2 PATCHED */"
CSS_MARKER = "/* QA UI TESTING PANEL SCOPE V2.1.2 CSS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


text = HTML_PATH.read_text(encoding="utf-8")

required = [
    "/* QA UI TESTING WORKSPACE V2.1 JS */",
    "function findUiPanelV21()",
    "function ensureHeadingStatusV21(panel)",
]

missing = [item for item in required if item not in text]

if missing:
    fail(
        "UI Testing Workspace V2.1 code was not found: "
        + ", ".join(missing)
    )


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_ui_testing_panel_scope_v2_1_2_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)


new_find_panel = r'''  function findUiPanelV21() {
    /*
      Start from the actual execution-mode button instead of a text
      heading. "UI Testing" also exists in the sidebar and previously
      caused the whole application shell to be selected as the panel.
    */
    const fromTemplateButtons = Array.from(
      document.querySelectorAll("button")
    ).filter(function (button) {
      if (
        textV21(button) !== "From Template"
      ) {
        return false;
      }

      if (
        button.closest(
          "nav,aside,[role='navigation'],"
          + "#sidebar,.sidebar,[class*='sidebar']"
        )
      ) {
        return false;
      }

      return true;
    });

    for (const button of fromTemplateButtons) {
      const modeContainer =
        button.parentElement;

      const hasAddCustom =
        modeContainer
        && Array.from(
          modeContainer.querySelectorAll(
            "button"
          )
        ).some(function (candidate) {
          return (
            textV21(candidate)
            === "Add Custom"
          );
        });

      if (!hasAddCustom) {
        continue;
      }

      let current =
        modeContainer;

      for (
        let depth = 0;
        current && depth < 9;
        depth += 1
      ) {
        const content =
          textV21(current);

        const hasForm =
          current.querySelectorAll(
            "input,select,textarea"
          ).length >= 2;

        const isWorkspace =
          content.includes("From Template")
          && content.includes("Add Custom")
          && content.includes("Test Information")
          && content.includes("Target")
          && content.includes("Validation")
          && content.includes("Execution Result")
          && hasForm;

        const isTooBroad =
          content.includes("API Status")
          || content.includes(
            "Autonomous QA Flow"
          )
          || content.includes(
            "Test Planning"
          )
          || content.includes(
            "Collapse sidebar"
          );

        if (
          isWorkspace
          && !isTooBroad
        ) {
          return current;
        }

        current =
          current.parentElement;
      }
    }

    return null;
  }

'''


new_heading_status = r'''  function ensureHeadingStatusV21(panel) {
    /*
      Remove titlebars created by earlier panel-detection patches.
      A valid titlebar is recreated only inside the scoped workspace.
    */
    Array.from(
      document.querySelectorAll(
        ".qa-ui-testing-titlebar-v211,"
        + ".qa-ui-testing-titlebar-v211a,"
        + ".qa-ui-testing-titlebar-v212"
      )
    ).forEach(function (titlebar) {
      titlebar.remove();
    });

    Array.from(
      document.querySelectorAll(
        ".qa-ui-testing-draft-status-v21"
      )
    ).forEach(function (badge) {
      badge.remove();
    });

    Array.from(
      document.querySelectorAll(
        ".qa-ui-testing-original-heading-v211,"
        + ".qa-ui-testing-original-heading-v211a"
      )
    ).forEach(function (heading) {
      heading.classList.remove(
        "qa-ui-testing-original-heading-v211"
      );

      heading.classList.remove(
        "qa-ui-testing-original-heading-v211a"
      );
    });

    if (!panel) {
      return;
    }

    const titlebar =
      document.createElement("div");

    titlebar.className =
      "qa-ui-testing-titlebar-v212";

    titlebar.innerHTML = `
      <div class="qa-ui-testing-title-copy-v212">
        <h2>UI Testing</h2>

        <p>
          Configure and run route-level UI checks
          for the active project.
        </p>
      </div>

      <span
        class="qa-ui-testing-draft-status-v21"
        aria-live="polite"
      >
        Draft ready
      </span>
    `;

    panel.insertBefore(
      titlebar,
      panel.firstChild
    );
  }

'''


def replace_function(
    source: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    name: str,
) -> str:
    start = source.find(start_marker)
    end = source.find(end_marker, start)

    if start == -1 or end == -1 or end <= start:
        shutil.copy2(backup_path, HTML_PATH)
        fail(
            f"Could not locate {name}. Dashboard restored."
        )

    return (
        source[:start]
        + replacement
        + source[end:]
    )


if PATCH_MARKER not in text:
    text = replace_function(
        text,
        "  function findUiPanelV21() {",
        "  function panelVisibleV21(panel) {",
        new_find_panel,
        "findUiPanelV21",
    )

    text = replace_function(
        text,
        "  function ensureHeadingStatusV21(panel) {",
        "  function markModeV21(panel) {",
        new_heading_status,
        "ensureHeadingStatusV21",
    )

    marker_position = text.find(
        "/* QA UI TESTING WORKSPACE V2.1 JS */"
    )

    if marker_position == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail(
            "UI Testing Workspace V2.1 marker was not found. "
            "Dashboard restored."
        )

    text = (
        text[:marker_position]
        + PATCH_MARKER
        + "\n"
        + text[marker_position:]
    )

    print(
        "[OK] UI Testing panel scoped from execution controls"
    )
    print(
        "[OK] Misplaced titlebar and draft badges cleanup installed"
    )
else:
    print(
        "[SKIP] UI Testing Panel Scope V2.1.2 "
        "JavaScript already patched"
    )


css = r'''
/* QA UI TESTING PANEL SCOPE V2.1.2 CSS */

/* Hide any stale titlebar while JavaScript replaces it. */
body > .qa-ui-testing-titlebar-v211,
body > .qa-ui-testing-titlebar-v211a,
body > .qa-ui-testing-titlebar-v212,
#app > .qa-ui-testing-titlebar-v211,
#app > .qa-ui-testing-titlebar-v211a {
  display: none !important;
}

.qa-ui-testing-titlebar-v212 {
  display: flex;
  width: 100%;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  box-sizing: border-box;
  margin: 0 0 14px;
  padding: 0 0 12px;
  border-bottom: 1px solid #e2e8f0;
}

.qa-ui-testing-title-copy-v212 {
  min-width: 0;
}

.qa-ui-testing-title-copy-v212 h2 {
  margin: 0 !important;
  color: #0f172a !important;
  font-size: 18px !important;
  font-weight: 850 !important;
  line-height: 1.2 !important;
}

.qa-ui-testing-title-copy-v212 p {
  margin: 4px 0 0 !important;
  color: #64748b !important;
  font-size: 10px !important;
  line-height: 1.45 !important;
}

.qa-ui-testing-titlebar-v212
  .qa-ui-testing-draft-status-v21 {
  display: inline-flex !important;
  position: static !important;
  inset: auto !important;
  align-self: center;
  flex: 0 0 auto;
  margin: 0 !important;
  transform: none !important;
}

/*
  A draft badge is valid only inside the scoped UI Testing titlebar.
*/
body
  .qa-ui-testing-draft-status-v21:not(
    .qa-ui-testing-titlebar-v212
      .qa-ui-testing-draft-status-v21
  ) {
  display: none !important;
}

body.qa-ui-testing-active-v21
  .qa-dashboard-legacy-metric-v12,
body.qa-ui-testing-active-v21
  .qa-ui-testing-global-flow-v21 {
  display: none !important;
}

body.qa-ui-testing-active-v21
  .qa-ui-testing-panel-v21 {
  width: 100% !important;
  max-width: 100% !important;
  min-width: 0 !important;
  box-sizing: border-box !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-mode-v21 {
  margin: 0 0 12px !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-context-v21 {
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box !important;
  margin: 0 0 12px !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-template-library-v21,
.qa-ui-testing-panel-v21
  .qa-ui-testing-section-v21,
.qa-ui-testing-panel-v21
  .qa-ui-testing-result-empty-v21 {
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box !important;
}

@media (max-width: 720px) {
  .qa-ui-testing-titlebar-v212 {
    align-items: stretch;
    flex-direction: column;
  }

  .qa-ui-testing-titlebar-v212
    .qa-ui-testing-draft-status-v21 {
    align-self: flex-start;
  }
}
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
        "[OK] UI Testing Panel Scope V2.1.2 CSS inserted"
    )
else:
    print(
        "[SKIP] UI Testing Panel Scope V2.1.2 CSS already exists"
    )


required_markers = [
    PATCH_MARKER,
    CSS_MARKER,
    "qa-ui-testing-titlebar-v212",
    "Start from the actual execution-mode button",
]

missing_markers = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing_markers:
    shutil.copy2(backup_path, HTML_PATH)
    fail(
        "Verification failed. Dashboard restored. Missing markers: "
        + ", ".join(missing_markers)
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"[OK] Backup created: {backup_path}")
print(f"[OK] Updated: {HTML_PATH}")
print()
print(
    "[SUCCESS] UI Testing Panel Scope V2.1.2 installed"
)
