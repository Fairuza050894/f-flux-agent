from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"
CSS_MARKER = "/* QA SIDEBAR CLEANUP V1.4 CSS */"
JS_MARKER = "/* QA SIDEBAR CLEANUP V1.4 JS */"

def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)

if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_sidebar_cleanup_v1_4_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)
text = HTML_PATH.read_text(encoding="utf-8")

css = r"""
/* QA SIDEBAR CLEANUP V1.4 CSS */

#qaSidebarNavigation.qa-sidebar-nav-host {
  display: flex !important;
  min-height: 0 !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow-y: auto !important;
  overflow-x: visible !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavigation.qa-sidebar-nav-host > :not(#qaSidebarNavV1) {
  display: none !important;
}

#qaSidebar.qa-sidebar-v1 {
  display: flex !important;
  width: 264px !important;
  min-width: 264px !important;
  min-height: 100vh !important;
  flex-direction: column !important;
  overflow: visible !important;
  border-right: 1px solid #1e293b !important;
  background: #0f172a !important;
  color: #e2e8f0 !important;
  box-shadow: 8px 0 26px rgba(15, 23, 42, 0.18) !important;
  opacity: 1 !important;
}

#qaSidebar.qa-sidebar-v1 h1,
#qaSidebar.qa-sidebar-v1 h2,
#qaSidebar.qa-sidebar-v1 h3,
#qaSidebar.qa-sidebar-v1 strong {
  color: #f8fafc;
}

#qaSidebar.qa-sidebar-v1 p,
#qaSidebar.qa-sidebar-v1 small {
  color: #94a3b8;
}

#qaSidebarNavigation > #qaSidebarNavV1.qa-sidebar-nav-v1 {
  position: relative !important;
  inset: auto !important;
  display: flex !important;
  width: 100% !important;
  min-height: 0 !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  gap: 20px !important;
  margin: 0 !important;
  padding: 18px 14px !important;
  overflow: visible !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavV1 .qa-sidebar-group-v1,
#qaSidebarNavV1 .qa-sidebar-group-items-v1 {
  display: flex !important;
  flex-direction: column !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavV1 .qa-sidebar-group-v1 {
  gap: 6px !important;
}

#qaSidebarNavV1 .qa-sidebar-group-items-v1 {
  gap: 5px !important;
}

#qaSidebarNavV1 .qa-sidebar-group-title-v1 {
  display: block !important;
  margin: 0 !important;
  padding: 0 11px 6px !important;
  color: #7f8ea3 !important;
  font-size: 10px !important;
  font-weight: 800 !important;
  letter-spacing: 0.12em !important;
  line-height: 1 !important;
  text-transform: uppercase !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavV1 .qa-nav-item-v1 {
  position: relative !important;
  display: flex !important;
  width: 100% !important;
  min-height: 44px !important;
  align-items: center !important;
  justify-content: flex-start !important;
  gap: 11px !important;
  margin: 0 !important;
  padding: 10px 11px !important;
  border: 1px solid transparent !important;
  border-radius: 10px !important;
  background: transparent !important;
  color: #cbd5e1 !important;
  box-shadow: none !important;
  cursor: pointer !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  line-height: 1.2 !important;
  text-align: left !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarNavV1 .qa-nav-item-v1:hover {
  border-color: rgba(148, 163, 184, 0.25) !important;
  background: rgba(255, 255, 255, 0.07) !important;
  color: #ffffff !important;
}

#qaSidebarNavV1 .qa-nav-item-v1.active,
#qaSidebarNavV1 .qa-nav-item-v1[aria-current="page"] {
  border-color: rgba(96, 165, 250, 0.42) !important;
  background: rgba(37, 99, 235, 0.24) !important;
  color: #ffffff !important;
  box-shadow: inset 3px 0 0 #60a5fa !important;
}

#qaSidebarNavV1 .qa-nav-icon-v1 {
  display: inline-flex !important;
  width: 20px !important;
  min-width: 20px !important;
  height: 20px !important;
  align-items: center !important;
  justify-content: center !important;
  color: inherit !important;
}

#qaSidebarNavV1 .qa-nav-icon-v1 svg {
  display: block !important;
  width: 19px !important;
  height: 19px !important;
  fill: none !important;
  stroke: currentColor !important;
}

#qaSidebarNavV1 .qa-nav-label-v1 {
  display: inline-block !important;
  min-width: 0 !important;
  overflow: hidden !important;
  color: inherit !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  visibility: visible !important;
  opacity: 1 !important;
}

#qaSidebarFooterV1.qa-sidebar-footer-v1 {
  display: block !important;
  flex: 0 0 auto !important;
  width: 100% !important;
  margin-top: auto !important;
  padding: 12px !important;
  border-top: 1px solid #1e293b !important;
  background: #0f172a !important;
  opacity: 1 !important;
}

#qaSidebarCollapseV1.qa-sidebar-collapse-v1 {
  display: flex !important;
  width: 100% !important;
  min-height: 40px !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 9px !important;
  margin: 0 !important;
  padding: 9px 10px !important;
  border: 1px solid rgba(148, 163, 184, 0.25) !important;
  border-radius: 9px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  color: #cbd5e1 !important;
  box-shadow: none !important;
}

#qaSidebarCollapseV1.qa-sidebar-collapse-v1:hover {
  background: rgba(255, 255, 255, 0.09) !important;
  color: #ffffff !important;
}

body.qa-sidebar-collapsed #qaSidebar.qa-sidebar-v1 {
  width: 76px !important;
  min-width: 76px !important;
}

body.qa-sidebar-collapsed #qaSidebarNavigation > #qaSidebarNavV1.qa-sidebar-nav-v1 {
  padding-right: 9px !important;
  padding-left: 9px !important;
}

body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-sidebar-group-title-v1,
body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-label-v1,
body.qa-sidebar-collapsed #qaSidebarCollapseV1 .qa-sidebar-collapse-label-v1 {
  display: none !important;
}

body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-item-v1 {
  justify-content: center !important;
  padding: 10px !important;
}

@media (min-width: 901px) {
  body:not(.qa-sidebar-collapsed) .qa-app-shell {
    grid-template-columns: 264px minmax(0, 1fr) !important;
  }

  body.qa-sidebar-collapsed .qa-app-shell {
    grid-template-columns: 76px minmax(0, 1fr) !important;
  }
}

@media (max-width: 900px) {
  #qaSidebar.qa-sidebar-v1,
  body.qa-sidebar-collapsed #qaSidebar.qa-sidebar-v1 {
    width: 284px !important;
    min-width: 284px !important;
  }

  body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-sidebar-group-title-v1,
  body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-label-v1 {
    display: block !important;
  }

  body.qa-sidebar-collapsed #qaSidebarNavV1 .qa-nav-item-v1 {
    justify-content: flex-start !important;
    padding: 10px 11px !important;
  }
}
"""

js = r"""
/* QA SIDEBAR CLEANUP V1.4 JS */
(function () {
  "use strict";

  let cleanupScheduled = false;
  let cleanupObserver = null;

  function qaSidebarCleanupV14() {
    const sidebar =
      document.getElementById("qaSidebar")
      || document.querySelector(
        ".qa-sidebar, aside.qa-sidebar, [data-qa-sidebar]"
      );

    if (!sidebar) {
      return;
    }

    const host = document.getElementById("qaSidebarNavigation");
    const nav = document.getElementById("qaSidebarNavV1");

    if (!host || !nav) {
      if (typeof window.qaEnhanceSidebarV1 === "function") {
        window.qaEnhanceSidebarV1();
      }
      return;
    }

    sidebar.classList.add("qa-sidebar-v1");
    host.hidden = false;
    host.removeAttribute("aria-hidden");

    if (nav.parentElement !== host) {
      host.appendChild(nav);
    }

    Array.from(host.children).forEach(function (child) {
      const keep = child.id === "qaSidebarNavV1";
      child.hidden = !keep;

      if (keep) {
        child.removeAttribute("aria-hidden");
      } else {
        child.setAttribute("aria-hidden", "true");
      }
    });

    if (typeof window.qaSidebarSyncActiveState === "function") {
      window.qaSidebarSyncActiveState();
    }

    document.body.classList.add("qa-sidebar-clean-v14-ready");
  }

  function scheduleCleanup() {
    if (cleanupScheduled) {
      return;
    }

    cleanupScheduled = true;

    window.setTimeout(function () {
      cleanupScheduled = false;
      qaSidebarCleanupV14();
    }, 0);
  }

  window.qaSidebarCleanupV14 = qaSidebarCleanupV14;

  window.addEventListener("qa-project-changed", scheduleCleanup);

  window.addEventListener("load", function () {
    qaSidebarCleanupV14();
    window.setTimeout(qaSidebarCleanupV14, 250);
    window.setTimeout(qaSidebarCleanupV14, 1000);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", qaSidebarCleanupV14);
  } else {
    qaSidebarCleanupV14();
  }

  if (!cleanupObserver) {
    cleanupObserver = new MutationObserver(scheduleCleanup);

    cleanupObserver.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
})();
"""

if CSS_MARKER not in text:
    style_close = text.rfind("</style>")
    if style_close == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Closing </style> tag was not found")

    text = text[:style_close] + "\n" + css + "\n" + text[style_close:]
    print("[OK] Sidebar Cleanup V1.4 CSS inserted")
else:
    print("[SKIP] Sidebar Cleanup V1.4 CSS already exists")

if JS_MARKER not in text:
    script_close = text.rfind("</script>")
    if script_close == -1:
        shutil.copy2(backup_path, HTML_PATH)
        fail("Closing </script> tag was not found")

    text = text[:script_close] + "\n" + js + "\n" + text[script_close:]
    print("[OK] Sidebar Cleanup V1.4 JavaScript inserted")
else:
    print("[SKIP] Sidebar Cleanup V1.4 JavaScript already exists")

required = [
    CSS_MARKER,
    JS_MARKER,
    "function qaSidebarCleanupV14()",
    "#qaSidebarNavigation.qa-sidebar-nav-host",
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
print("[SUCCESS] Sidebar Cleanup V1.4 installed")
