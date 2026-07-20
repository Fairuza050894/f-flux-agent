from pathlib import Path
from datetime import datetime
import shutil
import sys


ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

MARKER = "/* QA SIDEBAR VISUAL FIX V1.2 */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    sys.exit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_sidebar_visual_fix_v1_2_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")

css = r'''
/* QA SIDEBAR VISUAL FIX V1.2 */

#qaSidebarNavigation.qa-sidebar-nav-host {
  display: none !important;
}

#qaSidebar.qa-sidebar-v1 {
  display: flex !important;
  width: 264px !important;
  min-width: 264px !important;
  height: 100vh !important;
  min-height: 100vh !important;
  flex-direction: column !important;
  overflow: visible !important;
  border-right: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
  box-shadow: 8px 0 24px rgba(15, 23, 42, 0.035) !important;
}

#qaSidebarNavV1.qa-sidebar-nav-v1 {
  position: relative !important;
  top: auto !important;
  display: flex !important;
  width: 100% !important;
  min-height: 0 !important;
  flex: 1 1 auto !important;
  flex-direction: column !important;
  gap: 20px !important;
  margin: 0 !important;
  padding: 18px 12px !important;
  overflow-y: auto !important;
  overflow-x: visible !important;
}

#qaSidebarNavV1 .qa-sidebar-group-v1 {
  display: flex !important;
  flex-direction: column !important;
  gap: 6px !important;
  margin: 0 !important;
  padding: 0 !important;
}

#qaSidebarNavV1 .qa-sidebar-group-title-v1 {
  display: block !important;
  margin: 0 !important;
  padding: 0 11px 6px !important;
  color: #94a3b8 !important;
  font-size: 10px !important;
  font-weight: 800 !important;
  letter-spacing: 0.12em !important;
  line-height: 1 !important;
  text-transform: uppercase !important;
}

#qaSidebarNavV1 .qa-sidebar-group-items-v1 {
  display: flex !important;
  flex-direction: column !important;
  gap: 5px !important;
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
  color: #475569 !important;
  box-shadow: none !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  line-height: 1.2 !important;
  text-align: left !important;
}

#qaSidebarNavV1 .qa-nav-item-v1:hover {
  border-color: #e2e8f0 !important;
  background: #f8fafc !important;
  color: #0f172a !important;
}

#qaSidebarNavV1 .qa-nav-item-v1.active,
#qaSidebarNavV1 .qa-nav-item-v1[aria-current="page"] {
  border-color: #bfdbfe !important;
  background: #eff6ff !important;
  color: #1d4ed8 !important;
  box-shadow: inset 3px 0 0 #2563eb !important;
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
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

#qaSidebarFooterV1.qa-sidebar-footer-v1 {
  display: block !important;
  width: 100% !important;
  margin-top: auto !important;
  padding: 12px !important;
  border-top: 1px solid #e2e8f0 !important;
  background: #ffffff !important;
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
  border: 1px solid #e2e8f0 !important;
  border-radius: 9px !important;
  background: #ffffff !important;
  color: #475569 !important;
  box-shadow: none !important;
}

#qaSidebarCollapseV1.qa-sidebar-collapse-v1:hover {
  background: #f8fafc !important;
  color: #0f172a !important;
}

body.qa-sidebar-collapsed #qaSidebar.qa-sidebar-v1 {
  width: 76px !important;
  min-width: 76px !important;
}

body.qa-sidebar-collapsed #qaSidebarNavV1.qa-sidebar-nav-v1 {
  padding-right: 9px !important;
  padding-left: 9px !important;
}

body.qa-sidebar-collapsed
  #qaSidebarNavV1
  .qa-sidebar-group-title-v1,
body.qa-sidebar-collapsed
  #qaSidebarNavV1
  .qa-nav-label-v1,
body.qa-sidebar-collapsed
  #qaSidebarCollapseV1
  .qa-sidebar-collapse-label-v1 {
  display: none !important;
}

body.qa-sidebar-collapsed
  #qaSidebarNavV1
  .qa-nav-item-v1 {
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
    position: fixed !important;
    z-index: 999 !important;
    top: 0 !important;
    bottom: 0 !important;
    left: 0 !important;
    width: 284px !important;
    min-width: 284px !important;
    max-width: calc(100vw - 42px) !important;
    height: 100vh !important;
    transform: translateX(-105%) !important;
  }

  body.qa-sidebar-mobile-open #qaSidebar.qa-sidebar-v1 {
    transform: translateX(0) !important;
  }

  body.qa-sidebar-collapsed
    #qaSidebarNavV1
    .qa-sidebar-group-title-v1,
  body.qa-sidebar-collapsed
    #qaSidebarNavV1
    .qa-nav-label-v1 {
    display: block !important;
  }

  body.qa-sidebar-collapsed
    #qaSidebarNavV1
    .qa-nav-item-v1 {
    justify-content: flex-start !important;
    padding: 10px 11px !important;
  }

  #qaSidebarCollapseV1.qa-sidebar-collapse-v1 {
    display: none !important;
  }
}
'''

if MARKER in text:
    print("[SKIP] Sidebar Visual Fix V1.2 already exists")
else:
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

    print("[OK] Sidebar Visual Fix V1.2 CSS inserted")

required_markers = [
    MARKER,
    "#qaSidebarNavigation.qa-sidebar-nav-host",
    "#qaSidebarNavV1 .qa-nav-item-v1.active",
    "body.qa-sidebar-collapsed #qaSidebar.qa-sidebar-v1",
]

missing = [
    marker
    for marker in required_markers
    if marker not in text
]

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
print("[SUCCESS] Sidebar Visual Fix V1.2 installed")
