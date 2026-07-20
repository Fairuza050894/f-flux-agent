from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA MAIN DASHBOARD MONITORING BUGFIX V1.2.1 CSS */"
PATCH_MARKER = "/* QA MAIN DASHBOARD MONITORING BUGFIX V1.2.1 PATCHED */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_monitoring_bugfix_v1_2_1_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")

if (
    "/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 JS */"
    not in text
):
    fail(
        "Main Dashboard Monitoring Cleanup V1.2 was not found. "
        "The bugfix was not applied."
    )


old_clone_options = r'''  function cloneOptions(target, source) {
    const currentValue = source.value;
    target.innerHTML = "";

    Array.from(source.options).forEach(function (option) {
      target.appendChild(option.cloneNode(true));
    });

    target.value = currentValue;
  }
'''

new_clone_options = r'''  function cloneOptions(target, source) {
    const currentValue = String(source.value || "");

    const sourceSignature = Array.from(
      source.options
    ).map(function (option) {
      return [
        option.value,
        option.textContent,
        option.disabled,
        option.hidden
      ].join("::");
    }).join("||");

    if (
      target.dataset.qaOptionsSignatureV121
      !== sourceSignature
    ) {
      const fragment =
        document.createDocumentFragment();

      Array.from(source.options).forEach(
        function (option) {
          fragment.appendChild(
            option.cloneNode(true)
          );
        }
      );

      target.replaceChildren(fragment);

      target.dataset.qaOptionsSignatureV121 =
        sourceSignature;
    }

    if (target.value !== currentValue) {
      target.value = currentValue;
    }
  }
'''

old_status_block = r'''    statusRow.innerHTML = "";

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
'''

new_status_block = r'''    const headerText = textOf(headerGroup);
    const backendMatch = headerText.match(
      /Backend:\s*[^|]+?(?=Run:|$)/i
    );
    const runMatch = headerText.match(
      /Run:\s*[^|]+$/i
    );

    const statusItems = [
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
    ].filter(function (item) {
      return Boolean(item.text);
    });

    const statusSignature =
      JSON.stringify(statusItems);

    if (
      statusRow.dataset.qaStatusSignatureV121
      !== statusSignature
    ) {
      const fragment =
        document.createDocumentFragment();

      statusItems.forEach(function (item) {
        const badge =
          document.createElement("span");

        badge.className =
          "qa-dashboard-context-pill-v12 "
          + item.css;

        badge.textContent = item.text;
        fragment.appendChild(badge);
      });

      statusRow.replaceChildren(fragment);

      statusRow.dataset.qaStatusSignatureV121 =
        statusSignature;
    }
'''

old_dialog_start = r'''    overlay = document.createElement("div");
    overlay.id = "qaDashboardFlowHelpV12";
    overlay.className =
      "qa-dashboard-help-overlay-v12";
'''

new_dialog_start = r'''    overlay = document.createElement("div");
    overlay.id = "qaDashboardFlowHelpV12";
    overlay.className =
      "qa-dashboard-help-overlay-v12";
    overlay.hidden = true;
    overlay.setAttribute(
      "aria-hidden",
      "true"
    );
'''

old_dialog_close = r'''    overlay.querySelector(
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
'''

new_dialog_close = r'''    function closeFlowHelp() {
      overlay.classList.remove("open");
      overlay.hidden = true;
      overlay.setAttribute(
        "aria-hidden",
        "true"
      );
    }

    overlay.querySelector(
      ".qa-dashboard-help-close-v12"
    ).addEventListener(
      "click",
      closeFlowHelp
    );

    overlay.addEventListener(
      "click",
      function (event) {
        if (event.target === overlay) {
          closeFlowHelp();
        }
      }
    );

    document.addEventListener(
      "keydown",
      function (event) {
        if (
          event.key === "Escape"
          && !overlay.hidden
        ) {
          closeFlowHelp();
        }
      }
    );
'''

old_dialog_open = r'''      button.addEventListener("click", function () {
        ensureHelpDialog().classList.add("open");
      });
'''

new_dialog_open = r'''      button.addEventListener(
        "click",
        function () {
          const overlay =
            ensureHelpDialog();

          overlay.hidden = false;
          overlay.setAttribute(
            "aria-hidden",
            "false"
          );

          window.requestAnimationFrame(
            function () {
              overlay.classList.add("open");
            }
          );
        }
      );
'''

old_observer = r'''  if (!observer) {
    observer = new MutationObserver(
      scheduleCleanup
    );

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
'''

new_observer = r'''  if (!observer) {
    observer = new MutationObserver(
      function (mutations) {
        const relevantMutation =
          mutations.some(
            function (mutation) {
              const target =
                mutation.target
                && mutation.target.nodeType === 1
                  ? mutation.target
                  : mutation.target?.parentElement;

              if (!target) {
                return false;
              }

              if (
                target.closest(
                  "#qaDashboardProjectSelectV12,"
                  + ".qa-dashboard-context-status-v12,"
                  + "#qaDashboardFlowHelpV12"
                )
              ) {
                return false;
              }

              return true;
            }
          );

        if (relevantMutation) {
          scheduleCleanup();
        }
      }
    );

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
'''

replacements = [
    (
        "stable project option synchronization",
        old_clone_options,
        new_clone_options,
    ),
    (
        "stable monitoring status rendering",
        old_status_block,
        new_status_block,
    ),
    (
        "help dialog hidden initialization",
        old_dialog_start,
        new_dialog_start,
    ),
    (
        "help dialog close lifecycle",
        old_dialog_close,
        new_dialog_close,
    ),
    (
        "help dialog open lifecycle",
        old_dialog_open,
        new_dialog_open,
    ),
    (
        "filtered mutation observer",
        old_observer,
        new_observer,
    ),
]

if PATCH_MARKER not in text:
    for name, old, new in replacements:
        count = text.count(old)

        if count != 1:
            shutil.copy2(backup_path, HTML_PATH)
            fail(
                f"Expected exactly one block for {name}, "
                f"but found {count}. Dashboard restored."
            )

        text = text.replace(old, new, 1)
        print(f"[OK] Patched: {name}")

    script_marker_position = text.find(
        "/* QA MAIN DASHBOARD MONITORING CLEANUP V1.2 JS */"
    )

    if script_marker_position == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Monitoring Cleanup V1.2 JS marker not found")

    text = (
        text[:script_marker_position]
        + PATCH_MARKER
        + "\n"
        + text[script_marker_position:]
    )
else:
    print(
        "[SKIP] Main Dashboard Monitoring Bugfix "
        "V1.2.1 JavaScript is already patched"
    )


css = r'''
/* QA MAIN DASHBOARD MONITORING BUGFIX V1.2.1 CSS */

body.qa-main-dashboard-active-v11
  #tab-dashboard,
body.qa-main-dashboard-active-v11
  #qaMainDashboardRootV1,
body.qa-main-dashboard-active-v11
  .qa-main-dashboard-v1 {
  max-width: 100% !important;
  min-width: 0 !important;
  overflow-x: clip !important;
}

.qa-dashboard-project-select-v12 {
  max-width: 100%;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.qa-dashboard-help-overlay-v12[hidden] {
  display: none !important;
}

.qa-dashboard-help-overlay-v12.open:not([hidden]) {
  display: flex !important;
}

.qa-dashboard-help-dialog-v12 {
  width: min(620px, calc(100vw - 32px)) !important;
  max-width: calc(100vw - 32px) !important;
  min-width: 0 !important;
  overflow-x: hidden !important;
}

.qa-dashboard-help-head-v12,
.qa-dashboard-help-body-v12,
.qa-dashboard-help-step-v12 {
  min-width: 0 !important;
  max-width: 100% !important;
}

.qa-dashboard-help-step-v12 strong,
.qa-dashboard-help-step-v12 span {
  overflow-wrap: anywhere !important;
  word-break: normal !important;
  white-space: normal !important;
}

@media (max-width: 620px) {
  .qa-dashboard-help-overlay-v12 {
    padding: 12px !important;
  }

  .qa-dashboard-help-dialog-v12 {
    width: calc(100vw - 24px) !important;
    max-width: calc(100vw - 24px) !important;
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
        "[OK] Main Dashboard Monitoring Bugfix "
        "V1.2.1 CSS inserted"
    )
else:
    print(
        "[SKIP] Main Dashboard Monitoring Bugfix "
        "V1.2.1 CSS already exists"
    )


required_markers = [
    CSS_MARKER,
    PATCH_MARKER,
    "qaOptionsSignatureV121",
    "qaStatusSignatureV121",
    "function closeFlowHelp()",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

if missing:
    shutil.copy2(backup_path, HTML_PATH)
    fail(
        "Verification failed. Dashboard restored. "
        "Missing markers: "
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
    "[SUCCESS] Main Dashboard Monitoring "
    "Bugfix V1.2.1 installed"
)
