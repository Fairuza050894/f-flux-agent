from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

PATCH_MARKER = "/* QA UI TESTING LAYOUT BUGFIX V2.1.1A PATCHED */"
CSS_MARKER = "/* QA UI TESTING LAYOUT BUGFIX V2.1.1A CSS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")


text = HTML_PATH.read_text(encoding="utf-8")

required_base_markers = [
    "/* QA UI TESTING WORKSPACE V2.1 JS */",
    "function findUiPanelV21()",
    "function ensureHeadingStatusV21(panel)",
]

missing_base = [
    marker
    for marker in required_base_markers
    if marker not in text
]

if missing_base:
    fail(
        "UI Testing Workspace V2.1 was not found: "
        + ", ".join(missing_base)
    )


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_ui_testing_layout_bugfix_v2_1_1a_{timestamp}"
)

shutil.copy2(
    HTML_PATH,
    backup_path,
)


new_find_panel = r'''  function findUiPanelV21() {
    const explicitSelectors = [
      "#tab-ui-testing",
      "#tab-ui",
      "[data-tab-panel='ui-testing']",
      "[data-panel='ui-testing']",
      "[data-view='ui-testing']"
    ];

    for (const selector of explicitSelectors) {
      const candidate =
        document.querySelector(selector);

      if (
        candidate
        && textV21(candidate).includes("From Template")
        && textV21(candidate).includes("Execution Result")
      ) {
        return candidate;
      }
    }

    const headings = Array.from(
      document.querySelectorAll(
        "h1,h2,h3,h4,h5,strong,span,div,p"
      )
    ).filter(function (element) {
      if (textV21(element) !== "UI Testing") {
        return false;
      }

      if (
        element.closest(
          "button,a,nav,aside,[role='navigation'],"
          + "#sidebar,.sidebar,[class*='sidebar']"
        )
      ) {
        return false;
      }

      return true;
    });

    for (const heading of headings) {
      let current =
        heading.parentElement;

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
          && content.includes("Test Information")
          && content.includes("Execution Result")
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
    if (!panel) {
      return;
    }

    Array.from(
      document.querySelectorAll(
        ".qa-ui-testing-draft-status-v21"
      )
    ).forEach(function (badge) {
      if (
        !panel.contains(badge)
        || !badge.closest(
          ".qa-ui-testing-titlebar-v211a"
        )
      ) {
        badge.remove();
      }
    });

    Array.from(
      document.querySelectorAll(
        ".qa-ui-testing-heading-row-v21"
      )
    ).forEach(function (row) {
      row.classList.remove(
        "qa-ui-testing-heading-row-v21"
      );
    });

    let titlebar =
      panel.querySelector(
        ".qa-ui-testing-titlebar-v211a"
      );

    if (!titlebar) {
      const originalHeading =
        Array.from(
          panel.querySelectorAll(
            "h1,h2,h3,h4,h5,strong,span,div,p"
          )
        ).find(function (element) {
          return (
            textV21(element) === "UI Testing"
            && !element.closest(
              "button,a,nav,aside,[role='navigation']"
            )
          );
        });

      if (originalHeading) {
        originalHeading.classList.add(
          "qa-ui-testing-original-heading-v211a"
        );
      }

      const modeButton =
        Array.from(
          panel.querySelectorAll("button")
        ).find(function (button) {
          return (
            textV21(button)
            === "From Template"
          );
        });

      const modeContainer =
        modeButton
          ? modeButton.parentElement
          : null;

      titlebar =
        document.createElement("div");

      titlebar.className =
        "qa-ui-testing-titlebar-v211a";

      titlebar.innerHTML = `
        <div class="qa-ui-testing-title-copy-v211a">
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

      if (
        modeContainer
        && modeContainer.parentElement
      ) {
        modeContainer.parentElement.insertBefore(
          titlebar,
          modeContainer
        );
      } else {
        panel.insertBefore(
          titlebar,
          panel.firstChild
        );
      }
    }

    const badges =
      titlebar.querySelectorAll(
        ".qa-ui-testing-draft-status-v21"
      );

    Array.from(badges)
      .slice(1)
      .forEach(function (badge) {
        badge.remove();
      });
  }

'''


def replace_function_block(
    source: str,
    start_marker: str,
    end_marker: str,
    replacement: str,
    name: str,
) -> str:
    start = source.find(start_marker)
    end = source.find(end_marker, start)

    if start == -1 or end == -1 or end <= start:
        shutil.copy2(
            backup_path,
            HTML_PATH,
        )

        fail(
            f"Could not locate {name}. Dashboard restored."
        )

    return (
        source[:start]
        + replacement
        + source[end:]
    )


if PATCH_MARKER not in text:
    text = replace_function_block(
        text,
        "  function findUiPanelV21() {",
        "  function panelVisibleV21(panel) {",
        new_find_panel,
        "findUiPanelV21",
    )

    text = replace_function_block(
        text,
        "  function ensureHeadingStatusV21(panel) {",
        "  function markModeV21(panel) {",
        new_heading_status,
        "ensureHeadingStatusV21",
    )

    js_marker_position = text.find(
        "/* QA UI TESTING WORKSPACE V2.1 JS */"
    )

    if js_marker_position == -1:
        shutil.copy2(
            backup_path,
            HTML_PATH,
        )

        fail(
            "UI Testing Workspace V2.1 JS marker was not found. "
            "Dashboard restored."
        )

    text = (
        text[:js_marker_position]
        + PATCH_MARKER
        + "\n"
        + text[js_marker_position:]
    )

    print(
        "[OK] UI Testing panel detection corrected"
    )

    print(
        "[OK] Draft badge isolated from sidebar"
    )

    print(
        "[OK] UI Testing title area rebuilt"
    )
else:
    print(
        "[SKIP] UI Testing Layout Bugfix V2.1.1A "
        "JavaScript already patched"
    )


css = r'''
/* QA UI TESTING LAYOUT BUGFIX V2.1.1A CSS */

.qa-ui-testing-heading-row-v21 {
  display: block !important;
  margin: 0 !important;
}

.qa-ui-testing-original-heading-v211a {
  display: none !important;
}

.qa-ui-testing-titlebar-v211a {
  display: flex;
  width: 100%;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 12px;
  padding: 0 0 12px;
  border-bottom: 1px solid #e2e8f0;
}

.qa-ui-testing-title-copy-v211a {
  min-width: 0;
}

.qa-ui-testing-title-copy-v211a h2 {
  margin: 0 !important;
  color: #0f172a !important;
  font-size: 18px !important;
  font-weight: 850 !important;
  line-height: 1.2 !important;
}

.qa-ui-testing-title-copy-v211a p {
  margin: 4px 0 0 !important;
  color: #64748b !important;
  font-size: 10px !important;
  line-height: 1.45 !important;
}

.qa-ui-testing-titlebar-v211a
  .qa-ui-testing-draft-status-v21 {
  position: static !important;
  inset: auto !important;
  align-self: center;
  margin: 0 !important;
  transform: none !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-mode-v21 {
  display: inline-flex !important;
  margin: 0 0 12px !important;
  vertical-align: top;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-context-v21 {
  width: 100% !important;
  max-width: none !important;
  margin: 0 0 12px !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-template-library-v21 {
  width: 100% !important;
  margin: 0 0 14px !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-section-v21 {
  width: 100% !important;
  max-width: none !important;
  box-sizing: border-box !important;
}

.qa-ui-testing-panel-v21
  .qa-ui-testing-result-empty-v21 {
  width: 100% !important;
  box-sizing: border-box !important;
}

body
  .qa-ui-testing-draft-status-v21:not(
    .qa-ui-testing-titlebar-v211a
      .qa-ui-testing-draft-status-v21
  ) {
  display: none !important;
}

@media (max-width: 720px) {
  .qa-ui-testing-titlebar-v211a {
    align-items: stretch;
    flex-direction: column;
  }

  .qa-ui-testing-titlebar-v211a
    .qa-ui-testing-draft-status-v21 {
    align-self: flex-start;
  }
}
'''


if CSS_MARKER not in text:
    style_close = text.rfind("</style>")

    if style_close == -1:
        shutil.copy2(
            backup_path,
            HTML_PATH,
        )

        fail(
            "Closing </style> tag was not found"
        )

    text = (
        text[:style_close]
        + "\n"
        + css
        + "\n"
        + text[style_close:]
    )

    print(
        "[OK] UI Testing Layout Bugfix V2.1.1A CSS inserted"
    )
else:
    print(
        "[SKIP] UI Testing Layout Bugfix V2.1.1A CSS already exists"
    )


required_markers = [
    PATCH_MARKER,
    CSS_MARKER,
    "qa-ui-testing-titlebar-v211a",
    "qa-ui-testing-original-heading-v211a",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing:
    shutil.copy2(
        backup_path,
        HTML_PATH,
    )

    fail(
        "Verification failed. Dashboard restored. "
        "Missing markers: "
        + ", ".join(missing)
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(
    f"[OK] Backup created: {backup_path}"
)

print(
    f"[OK] Updated: {HTML_PATH}"
)

print()

print(
    "[SUCCESS] UI Testing Layout Bugfix V2.1.1A installed"
)
