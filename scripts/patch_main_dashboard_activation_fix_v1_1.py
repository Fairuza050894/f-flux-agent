from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

CSS_MARKER = "/* QA MAIN DASHBOARD ACTIVATION FIX V1.1 CSS */"
JS_MARKER = "/* QA MAIN DASHBOARD ACTIVATION FIX V1.1 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_main_dashboard_activation_fix_v1_1_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")


css = r'''
/* QA MAIN DASHBOARD ACTIVATION FIX V1.1 CSS */

#tab-dashboard.qa-main-dashboard-panel-v1 {
  display: none;
}

body.qa-main-dashboard-active-v11
  #tab-dashboard.qa-main-dashboard-panel-v1 {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

body.qa-main-dashboard-active-v11
  #qaMainDashboardRootV1 {
  display: flex !important;
  visibility: visible !important;
  opacity: 1 !important;
}
'''


js = r'''
/* QA MAIN DASHBOARD ACTIVATION FIX V1.1 JS */
(function () {
  "use strict";

  let installTimer = null;

  function getDashboardPanel() {
    return document.getElementById(
      "tab-dashboard"
    );
  }

  function getTabContainer() {
    const dashboard = getDashboardPanel();

    if (dashboard && dashboard.parentElement) {
      return dashboard.parentElement;
    }

    const registered =
      document.getElementById(
        "tab-registered"
      );

    return registered
      ? registered.parentElement
      : null;
  }

  function syncDashboardNavigation(active) {
    document
      .querySelectorAll(
        ".qa-nav-item-v1"
      )
      .forEach(function (button) {
        const isDashboard =
          button.getAttribute(
            "data-qa-panel-id"
          ) === "tab-dashboard";

        if (isDashboard && active) {
          button.classList.add("active");
          button.setAttribute(
            "aria-current",
            "page"
          );
        } else if (isDashboard) {
          button.classList.remove("active");
          button.removeAttribute(
            "aria-current"
          );
        } else if (active) {
          button.classList.remove("active");
          button.removeAttribute(
            "aria-current"
          );
        }
      });
  }

  function activateDashboard() {
    const panel =
      getDashboardPanel();

    if (!panel) {
      if (
        typeof window.qaMainDashboardRefreshV1
        === "function"
      ) {
        window.qaMainDashboardRefreshV1(
          true
        );
      }

      window.setTimeout(
        activateDashboard,
        120
      );

      return;
    }

    const container =
      getTabContainer();

    if (container) {
      Array.from(
        container.children
      ).forEach(function (child) {
        if (
          child.id
          && child.id.startsWith("tab-")
        ) {
          const isDashboard =
            child.id === "tab-dashboard";

          child.classList.toggle(
            "active",
            isDashboard
          );

          child.style.setProperty(
            "display",
            isDashboard
              ? "block"
              : "none",
            "important"
          );
        }
      });
    }

    panel.style.setProperty(
      "display",
      "block",
      "important"
    );

    panel.classList.add("active");

    document.body.classList.add(
      "qa-main-dashboard-active-v11"
    );

    syncDashboardNavigation(true);

    if (
      typeof window.qaMainDashboardRefreshV1
      === "function"
    ) {
      window.qaMainDashboardRefreshV1(
        true
      );
    }
  }

  function deactivateDashboard() {
    const panel =
      getDashboardPanel();

    document.body.classList.remove(
      "qa-main-dashboard-active-v11"
    );

    if (panel) {
      panel.classList.remove("active");

      panel.style.setProperty(
        "display",
        "none",
        "important"
      );
    }

    syncDashboardNavigation(false);
  }

  function installShowTabBridge() {
    const currentShowTab =
      window.showTab;

    if (
      typeof currentShowTab !== "function"
    ) {
      return false;
    }

    if (
      currentShowTab
        .qaMainDashboardActivationFixV11
    ) {
      return true;
    }

    function showTabWithDashboard(
      tabName
    ) {
      const normalized =
        String(tabName || "")
          .trim()
          .toLowerCase();

      let result;

      if (normalized !== "dashboard") {
        result =
          currentShowTab.apply(
            this,
            arguments
          );

        deactivateDashboard();

        return result;
      }

      try {
        result =
          currentShowTab.apply(
            this,
            arguments
          );
      } catch (error) {
        console.warn(
          "Legacy showTab did not handle dashboard; "
          + "using dashboard activation bridge.",
          error
        );
      }

      activateDashboard();

      return result;
    }

    showTabWithDashboard
      .qaMainDashboardActivationFixV11 =
        true;

    showTabWithDashboard
      .qaOriginalShowTabV11 =
        currentShowTab;

    window.showTab =
      showTabWithDashboard;

    return true;
  }

  function dashboardButtonIsActive() {
    const button =
      document.querySelector(
        '[data-qa-panel-id="tab-dashboard"]'
      );

    return Boolean(
      button
      && (
        button.classList.contains(
          "active"
        )
        || button.getAttribute(
          "aria-current"
        ) === "page"
      )
    );
  }

  function initialize() {
    window.clearTimeout(
      installTimer
    );

    const installed =
      installShowTabBridge();

    if (!installed) {
      installTimer =
        window.setTimeout(
          initialize,
          120
        );

      return;
    }

    if (
      dashboardButtonIsActive()
    ) {
      activateDashboard();
    }
  }

  window.qaActivateMainDashboardV11 =
    activateDashboard;

  window.qaDeactivateMainDashboardV11 =
    deactivateDashboard;

  window.addEventListener(
    "qa-project-changed",
    function () {
      if (
        document.body.classList.contains(
          "qa-main-dashboard-active-v11"
        )
      ) {
        window.setTimeout(
          activateDashboard,
          100
        );
      }
    }
  );

  window.addEventListener(
    "load",
    function () {
      initialize();

      window.setTimeout(
        initialize,
        350
      );
    }
  );

  if (
    document.readyState
    === "loading"
  ) {
    document.addEventListener(
      "DOMContentLoaded",
      initialize
    );
  } else {
    initialize();
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
        "[OK] Main Dashboard Activation Fix V1.1 CSS inserted"
    )
else:
    print(
        "[SKIP] Main Dashboard Activation Fix V1.1 CSS already exists"
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
        "[OK] Main Dashboard Activation Fix V1.1 JavaScript inserted"
    )
else:
    print(
        "[SKIP] Main Dashboard Activation Fix V1.1 JavaScript already exists"
    )


required_markers = [
    CSS_MARKER,
    JS_MARKER,
    "function activateDashboard()",
    "function installShowTabBridge()",
    "qaActivateMainDashboardV11",
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
print(f"[OK] Updated: {HTML_PATH}")
print()
print(
    "[SUCCESS] Main Dashboard Activation Fix V1.1 installed"
)
