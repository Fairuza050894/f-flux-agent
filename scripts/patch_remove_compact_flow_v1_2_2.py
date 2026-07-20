from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA REMOVE COMPACT FLOW V1.2.2 CSS */"
JS_MARKER = "/* QA REMOVE COMPACT FLOW V1.2.2 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_remove_compact_flow_v1_2_2_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")


css = r'''
/* QA REMOVE COMPACT FLOW V1.2.2 CSS */

[data-qa-compact-flow-hidden-v122="true"],
.qa-compact-flow-hidden-v122 {
  display: none !important;
  width: 0 !important;
  min-width: 0 !important;
  max-width: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  border: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
}
'''


js = r'''
/* QA REMOVE COMPACT FLOW V1.2.2 JS */
(function () {
  "use strict";

  let compactFlowObserverV122 = null;
  let compactFlowCleanupScheduledV122 = false;

  function normalizedTextV122(element) {
    return String(
      element && element.textContent || ""
    )
      .trim()
      .replace(/\s+/g, " ");
  }

  function hideCompactFlowControlV122(element) {
    if (!element) {
      return;
    }

    const interactive =
      element.closest(
        "button, a, [role='button']"
      );

    const target =
      interactive || element;

    target.classList.add(
      "qa-compact-flow-hidden-v122"
    );

    target.setAttribute(
      "data-qa-compact-flow-hidden-v122",
      "true"
    );

    target.setAttribute(
      "aria-hidden",
      "true"
    );

    target.hidden = true;

    target.style.setProperty(
      "display",
      "none",
      "important"
    );

    /*
      Some legacy controls wrap the button inside a
      one-child container. Hide that wrapper only when
      its complete visible label is also Compact Flow.
    */
    const parent =
      target.parentElement;

    if (
      parent
      && normalizedTextV122(parent)
        .toLowerCase() === "compact flow"
      && parent.children.length <= 2
    ) {
      parent.classList.add(
        "qa-compact-flow-hidden-v122"
      );

      parent.setAttribute(
        "data-qa-compact-flow-hidden-v122",
        "true"
      );

      parent.setAttribute(
        "aria-hidden",
        "true"
      );

      parent.hidden = true;

      parent.style.setProperty(
        "display",
        "none",
        "important"
      );
    }
  }

  function removeCompactFlowV122(root) {
    const scope =
      root && root.querySelectorAll
        ? root
        : document;

    const candidates =
      scope.querySelectorAll(
        "button, a, [role='button'], span, div"
      );

    Array.from(candidates).forEach(
      function (element) {
        const label =
          normalizedTextV122(element)
            .toLowerCase();

        if (label !== "compact flow") {
          return;
        }

        /*
          The help modal contains Autonomous QA Flow,
          not Compact Flow. This guard prevents an
          unrelated dialog element from being hidden.
        */
        if (
          element.closest(
            "#qaDashboardFlowHelpV12"
          )
        ) {
          return;
        }

        hideCompactFlowControlV122(
          element
        );
      }
    );
  }

  function scheduleCompactFlowCleanupV122() {
    if (compactFlowCleanupScheduledV122) {
      return;
    }

    compactFlowCleanupScheduledV122 = true;

    window.setTimeout(
      function () {
        compactFlowCleanupScheduledV122 =
          false;

        removeCompactFlowV122(
          document
        );
      },
      0
    );
  }

  window.qaRemoveCompactFlowV122 =
    removeCompactFlowV122;

  window.addEventListener(
    "load",
    function () {
      removeCompactFlowV122(document);

      window.setTimeout(
        function () {
          removeCompactFlowV122(document);
        },
        250
      );

      window.setTimeout(
        function () {
          removeCompactFlowV122(document);
        },
        1000
      );
    }
  );

  window.addEventListener(
    "qa-project-changed",
    scheduleCompactFlowCleanupV122
  );

  if (
    document.readyState
    === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      function () {
        removeCompactFlowV122(document);
      }
    );
  } else {
    removeCompactFlowV122(document);
  }

  if (!compactFlowObserverV122) {
    compactFlowObserverV122 =
      new MutationObserver(
        function (mutations) {
          const hasAddedNodes =
            mutations.some(
              function (mutation) {
                return (
                  mutation.addedNodes
                  && mutation.addedNodes.length
                );
              }
            );

          if (hasAddedNodes) {
            scheduleCompactFlowCleanupV122();
          }
        }
      );

    compactFlowObserverV122.observe(
      document.body,
      {
        childList: true,
        subtree: true
      }
    );
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
        "[OK] Remove Compact Flow V1.2.2 CSS inserted"
    )
else:
    print(
        "[SKIP] Remove Compact Flow V1.2.2 CSS already exists"
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
        "[OK] Remove Compact Flow V1.2.2 JavaScript inserted"
    )
else:
    print(
        "[SKIP] Remove Compact Flow V1.2.2 JavaScript already exists"
    )


required_markers = [
    CSS_MARKER,
    JS_MARKER,
    "function removeCompactFlowV122(root)",
    "qaRemoveCompactFlowV122",
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
    "[SUCCESS] Remove Compact Flow V1.2.2 installed"
)
