from pathlib import Path
from datetime import datetime
import shutil
import sys

ROOT = Path("/Users/user/.hermes/hermes-agent")
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"
CSS_MARKER = "/* QA SIDEBAR REFINEMENT V1 CSS */"
JS_MARKER = "/* QA SIDEBAR REFINEMENT V1 JS */"


def fail(message: str) -> None:
    print(f"[ERROR] {message}")
    raise SystemExit(1)


if not HTML_PATH.exists():
    fail(f"Dashboard file not found: {HTML_PATH}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_sidebar_refinement_v1_{timestamp}"
)
shutil.copy2(HTML_PATH, backup_path)
text = HTML_PATH.read_text(encoding="utf-8")

css = r'''
/* QA SIDEBAR REFINEMENT V1 CSS */
:root {
  --qa-sidebar-expanded-width: 264px;
  --qa-sidebar-collapsed-width: 76px;
  --qa-sidebar-mobile-width: 284px;
  --qa-sidebar-border: #e2e8f0;
  --qa-sidebar-text: #334155;
  --qa-sidebar-muted: #94a3b8;
  --qa-sidebar-active-bg: #eff6ff;
  --qa-sidebar-active-text: #1d4ed8;
}

.qa-app-shell {
  transition: grid-template-columns 180ms ease;
}

body.qa-sidebar-collapsed .qa-app-shell {
  grid-template-columns:
    var(--qa-sidebar-collapsed-width)
    minmax(0, 1fr) !important;
}

.qa-sidebar.qa-sidebar-v1 {
  width: var(--qa-sidebar-expanded-width);
  min-width: 0;
  overflow: visible;
  transition: width 180ms ease, transform 180ms ease;
}

body.qa-sidebar-collapsed .qa-sidebar.qa-sidebar-v1 {
  width: var(--qa-sidebar-collapsed-width);
}

.qa-sidebar-nav-v1 {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  gap: 18px;
  padding: 14px 12px 18px;
  overflow-y: auto;
  overflow-x: visible;
  scrollbar-width: thin;
}

.qa-sidebar-group-v1 {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.qa-sidebar-group-title-v1 {
  margin: 0;
  padding: 0 10px 5px;
  color: var(--qa-sidebar-muted);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.1em;
  line-height: 1;
  text-transform: uppercase;
  white-space: nowrap;
}

.qa-sidebar-group-items-v1 {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.qa-sidebar .qa-nav-item-v1 {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 42px;
  align-items: center;
  justify-content: flex-start;
  gap: 11px;
  margin: 0;
  padding: 9px 11px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: transparent;
  color: var(--qa-sidebar-text);
  box-shadow: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  text-align: left;
  white-space: nowrap;
  transition:
    background 140ms ease,
    border-color 140ms ease,
    color 140ms ease,
    transform 140ms ease;
}

.qa-sidebar .qa-nav-item-v1:hover {
  border-color: #e2e8f0;
  background: #f8fafc;
  color: #0f172a;
  transform: translateX(1px);
}

.qa-sidebar .qa-nav-item-v1:focus-visible,
.qa-sidebar-collapse-v1:focus-visible,
.qa-sidebar-mobile-toggle-v1:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.qa-sidebar .qa-nav-item-v1.active,
.qa-sidebar .qa-nav-item-v1[aria-current="page"] {
  border-color: #bfdbfe;
  background: var(--qa-sidebar-active-bg);
  color: var(--qa-sidebar-active-text);
}

.qa-sidebar .qa-nav-icon-v1 {
  display: inline-flex;
  width: 19px;
  min-width: 19px;
  height: 19px;
  align-items: center;
  justify-content: center;
}

.qa-sidebar .qa-nav-icon-v1 svg,
.qa-sidebar-collapse-icon-v1 svg,
.qa-sidebar-mobile-toggle-v1 svg {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.qa-sidebar .qa-nav-label-v1 {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.qa-sidebar-footer-v1 {
  margin-top: auto;
  padding: 12px;
  border-top: 1px solid var(--qa-sidebar-border);
}

.qa-sidebar-collapse-v1 {
  display: flex;
  width: 100%;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  color: #475569;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
}

.qa-sidebar-collapse-v1:hover {
  background: #f8fafc;
  color: #0f172a;
}

.qa-sidebar-collapse-icon-v1 {
  display: inline-flex;
  width: 17px;
  height: 17px;
  align-items: center;
  justify-content: center;
  transition: transform 180ms ease;
}

body.qa-sidebar-collapsed .qa-sidebar-collapse-icon-v1 {
  transform: rotate(180deg);
}

body.qa-sidebar-collapsed .qa-sidebar-group-title-v1,
body.qa-sidebar-collapsed .qa-nav-label-v1,
body.qa-sidebar-collapsed .qa-sidebar-collapse-label-v1 {
  display: none;
}

body.qa-sidebar-collapsed .qa-sidebar-nav-v1 {
  padding-right: 9px;
  padding-left: 9px;
}

body.qa-sidebar-collapsed .qa-sidebar-group-v1 {
  gap: 8px;
}

body.qa-sidebar-collapsed .qa-sidebar-group-items-v1 {
  gap: 7px;
}

body.qa-sidebar-collapsed .qa-sidebar .qa-nav-item-v1 {
  justify-content: center;
  min-height: 44px;
  padding: 9px;
}

body.qa-sidebar-collapsed .qa-sidebar .qa-nav-item-v1:hover::after {
  content: attr(data-qa-tooltip);
  position: absolute;
  z-index: 1200;
  top: 50%;
  left: calc(100% + 10px);
  padding: 7px 9px;
  border-radius: 7px;
  background: #0f172a;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  pointer-events: none;
  transform: translateY(-50%);
  white-space: nowrap;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.18);
}

.qa-sidebar-mobile-toggle-v1 {
  display: none;
  width: 38px;
  min-width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
}

.qa-sidebar-overlay-v1 {
  position: fixed;
  z-index: 998;
  inset: 0;
  display: none;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

@media (max-width: 900px) {
  .qa-app-shell,
  body.qa-sidebar-collapsed .qa-app-shell {
    grid-template-columns: minmax(0, 1fr) !important;
  }

  .qa-sidebar.qa-sidebar-v1,
  body.qa-sidebar-collapsed .qa-sidebar.qa-sidebar-v1 {
    position: fixed;
    z-index: 999;
    top: 0;
    bottom: 0;
    left: 0;
    width: var(--qa-sidebar-mobile-width);
    max-width: calc(100vw - 42px);
    transform: translateX(-105%);
    box-shadow: 18px 0 42px rgba(15, 23, 42, 0.2);
  }

  body.qa-sidebar-mobile-open .qa-sidebar.qa-sidebar-v1 {
    transform: translateX(0);
  }

  body.qa-sidebar-mobile-open .qa-sidebar-overlay-v1 {
    display: block;
  }

  body.qa-sidebar-collapsed .qa-sidebar-group-title-v1,
  body.qa-sidebar-collapsed .qa-nav-label-v1,
  body.qa-sidebar-collapsed .qa-sidebar-collapse-label-v1 {
    display: initial;
  }

  body.qa-sidebar-collapsed .qa-sidebar-nav-v1 {
    padding: 14px 12px 18px;
  }

  body.qa-sidebar-collapsed .qa-sidebar .qa-nav-item-v1 {
    justify-content: flex-start;
    padding: 9px 11px;
  }

  .qa-sidebar-mobile-toggle-v1 {
    display: inline-flex;
  }

  .qa-sidebar-collapse-v1 {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .qa-app-shell,
  .qa-sidebar.qa-sidebar-v1,
  .qa-sidebar .qa-nav-item-v1,
  .qa-sidebar-collapse-icon-v1 {
    transition: none;
  }
}
'''

js = r'''
/* QA SIDEBAR REFINEMENT V1 JS */
(function () {
  "use strict";

  const STORAGE_KEY = "qa_sidebar_collapsed";
  const MOBILE_BREAKPOINT = 900;

  const NAV_ITEMS = [
    {
      key: "ui-testing",
      panelId: "tab-custom",
      label: "UI Testing",
      group: "execute",
      match: ["custom", "custom_smoke", "tab-custom"],
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="15" rx="2"></rect><path d="M3 8h18"></path><path d="m8 13 2 2 4-4"></path></svg>`
    },
    {
      key: "api-testing",
      panelId: "tab-curl",
      label: "API Testing",
      group: "execute",
      match: ["curl", "api_curl", "tab-curl"],
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 9-3 3 3 3"></path><path d="m16 9 3 3-3 3"></path><path d="m14 5-4 14"></path></svg>`
    },
    {
      key: "regression-testing",
      panelId: "tab-registered",
      label: "Regression Testing",
      group: "execute",
      match: ["registered", "regression", "tab-registered"],
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7h-7"></path><path d="M20 17h-7"></path><path d="m4 7 2 2 4-4"></path><path d="m4 17 2 2 4-4"></path></svg>`
    },
    {
      key: "test-planning",
      panelId: "tab-planning",
      label: "Test Planning",
      group: "workspace",
      match: ["planning", "tab-planning"],
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5h6"></path><path d="M9 9h6"></path><path d="M9 13h4"></path><path d="M5 5h.01"></path><path d="M5 9h.01"></path><path d="M5 13h.01"></path><path d="M4 19h16"></path></svg>`
    },
    {
      key: "history",
      panelId: "tab-history",
      label: "History",
      group: "workspace",
      match: ["history", "tab-history"],
      icon: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"></path><path d="M3 4v5h5"></path><path d="M12 7v5l3 2"></path></svg>`
    }
  ];

  const GROUP_LABELS = {
    execute: "Execute",
    workspace: "Workspace"
  };

  let observer = null;
  let repairScheduled = false;
  let repairing = false;

  function isMobile() {
    return window.innerWidth <= MOBILE_BREAKPOINT;
  }

  function findButton(item, sidebar) {
    const existing = sidebar.querySelector(
      `[data-qa-nav-key="${item.key}"]`
    );

    if (existing) return existing;

    return Array.from(
      document.querySelectorAll(
        ".tab-btn, [data-tab], [aria-controls], button"
      )
    ).find((button) => {
      if (!(button instanceof HTMLElement)) return false;

      const values = [
        button.getAttribute("onclick"),
        button.getAttribute("aria-controls"),
        button.getAttribute("data-tab"),
        button.getAttribute("data-target"),
        button.textContent
      ]
        .map((value) => String(value || "").trim().toLowerCase());

      if (
        values.includes(item.panelId.toLowerCase())
        || values.includes(item.label.toLowerCase())
      ) {
        return true;
      }

      return item.match.some((token) =>
        values.some((value) =>
          value.includes(token.toLowerCase())
        )
      );
    });
  }

  function renderButton(button, item) {
    if (!button || !item) return;

    button.classList.add("qa-nav-item-v1");
    button.dataset.qaNavKey = item.key;
    button.dataset.qaPanelId = item.panelId;
    button.dataset.qaTooltip = item.label;
    button.setAttribute("aria-label", item.label);
    button.setAttribute("title", item.label);

    const label = button.querySelector(".qa-nav-label-v1");
    const icon = button.querySelector(".qa-nav-icon-v1");

    if (
      label
      && icon
      && label.textContent.trim() === item.label
    ) {
      return;
    }

    button.innerHTML = `
      <span class="qa-nav-icon-v1">${item.icon}</span>
      <span class="qa-nav-label-v1">${item.label}</span>
    `;
  }

  function buildGroup(key) {
    const section = document.createElement("section");
    section.className = "qa-sidebar-group-v1";
    section.dataset.qaSidebarGroup = key;

    const title = document.createElement("h2");
    title.className = "qa-sidebar-group-title-v1";
    title.textContent = GROUP_LABELS[key];

    const items = document.createElement("div");
    items.className = "qa-sidebar-group-items-v1";

    section.append(title, items);
    return {section, items};
  }

  function syncActive() {
    const activePanel = document.querySelector(
      ".tab-panel.active, .tab-panel:not(.hidden)[aria-hidden='false']"
    );

    const activePanelId = activePanel ? activePanel.id : null;

    document
      .querySelectorAll(".qa-nav-item-v1")
      .forEach((button) => {
        const active =
          activePanelId
          && button.dataset.qaPanelId === activePanelId;

        button.classList.toggle("active", Boolean(active));

        if (active) {
          button.setAttribute("aria-current", "page");
        } else {
          button.removeAttribute("aria-current");
        }
      });
  }

  function setCollapsed(collapsed, persist = true) {
    const value = Boolean(collapsed) && !isMobile();

    document.body.classList.toggle(
      "qa-sidebar-collapsed",
      value
    );

    const button = document.getElementById(
      "qaSidebarCollapseV1"
    );

    if (button) {
      const label = value
        ? "Expand sidebar"
        : "Collapse sidebar";

      button.setAttribute(
        "aria-expanded",
        String(!value)
      );
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
    }

    if (persist) {
      localStorage.setItem(
        STORAGE_KEY,
        value ? "true" : "false"
      );
    }
  }

  function closeMobile() {
    document.body.classList.remove(
      "qa-sidebar-mobile-open"
    );

    const button = document.getElementById(
      "qaSidebarMobileToggleV1"
    );

    if (button) {
      button.setAttribute("aria-expanded", "false");
    }
  }

  function createFooter(sidebar) {
    let footer = document.getElementById(
      "qaSidebarFooterV1"
    );

    if (footer) return;

    footer = document.createElement("div");
    footer.id = "qaSidebarFooterV1";
    footer.className = "qa-sidebar-footer-v1";
    footer.innerHTML = `
      <button
        type="button"
        class="qa-sidebar-collapse-v1"
        id="qaSidebarCollapseV1"
        aria-expanded="true"
        aria-label="Collapse sidebar"
        title="Collapse sidebar"
      >
        <span class="qa-sidebar-collapse-icon-v1">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="m15 18-6-6 6-6"></path>
          </svg>
        </span>
        <span class="qa-sidebar-collapse-label-v1">
          Collapse sidebar
        </span>
      </button>
    `;

    sidebar.appendChild(footer);

    footer
      .querySelector("#qaSidebarCollapseV1")
      .addEventListener("click", function () {
        if (isMobile()) {
          closeMobile();
          return;
        }

        setCollapsed(
          !document.body.classList.contains(
            "qa-sidebar-collapsed"
          )
        );
      });
  }

  function createMobileControls(sidebar) {
    if (!document.getElementById("qaSidebarOverlayV1")) {
      const overlay = document.createElement("div");
      overlay.id = "qaSidebarOverlayV1";
      overlay.className = "qa-sidebar-overlay-v1";
      overlay.setAttribute("aria-hidden", "true");
      overlay.addEventListener("click", closeMobile);
      document.body.appendChild(overlay);
    }

    if (document.getElementById("qaSidebarMobileToggleV1")) {
      return;
    }

    const topbar = document.querySelector(
      ".qa-topbar, .qa-global-header, .qa-app-header, header"
    );

    if (!topbar) return;

    const button = document.createElement("button");
    button.type = "button";
    button.id = "qaSidebarMobileToggleV1";
    button.className = "qa-sidebar-mobile-toggle-v1";
    button.setAttribute("aria-controls", sidebar.id);
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-label", "Open navigation");
    button.setAttribute("title", "Open navigation");
    button.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M4 7h16"></path>
        <path d="M4 12h16"></path>
        <path d="M4 17h16"></path>
      </svg>
    `;

    button.addEventListener("click", function () {
      document.body.classList.toggle(
        "qa-sidebar-mobile-open"
      );

      button.setAttribute(
        "aria-expanded",
        String(
          document.body.classList.contains(
            "qa-sidebar-mobile-open"
          )
        )
      );
    });

    topbar.prepend(button);
  }

  function repairNavigation() {
    if (repairing) return;
    repairing = true;

    try {
      const sidebar = document.querySelector(
        ".qa-sidebar, aside.qa-sidebar, [data-qa-sidebar]"
      );
      const nav = document.getElementById(
        "qaSidebarNavV1"
      );

      if (!sidebar || !nav) return;

      NAV_ITEMS.forEach((item) => {
        const button = findButton(item, sidebar);

        if (!button) return;

        renderButton(button, item);

        const target = nav.querySelector(
          `[data-qa-sidebar-group="${item.group}"] `
          + ".qa-sidebar-group-items-v1"
        );

        if (target && button.parentElement !== target) {
          target.appendChild(button);
        }
      });

      syncActive();
    } finally {
      repairing = false;
    }
  }

  function scheduleRepair() {
    if (repairScheduled) return;
    repairScheduled = true;

    window.setTimeout(function () {
      repairScheduled = false;
      repairNavigation();
    }, 0);
  }

  function enhance() {
    const sidebar = document.querySelector(
      ".qa-sidebar, aside.qa-sidebar, [data-qa-sidebar]"
    );

    if (!sidebar) {
      console.warn(
        "Sidebar refinement skipped: sidebar element not found."
      );
      return;
    }

    if (!sidebar.id) sidebar.id = "qaSidebar";
    sidebar.classList.add("qa-sidebar-v1");

    let nav = document.getElementById(
      "qaSidebarNavV1"
    );

    if (!nav) {
      nav = document.createElement("nav");
      nav.id = "qaSidebarNavV1";
      nav.className = "qa-sidebar-nav-v1";
      nav.setAttribute(
        "aria-label",
        "QA dashboard navigation"
      );

      const execute = buildGroup("execute");
      const workspace = buildGroup("workspace");

      nav.append(execute.section, workspace.section);
      sidebar.appendChild(nav);
    }

    createFooter(sidebar);
    createMobileControls(sidebar);
    repairNavigation();

    setCollapsed(
      localStorage.getItem(STORAGE_KEY) === "true",
      false
    );

    if (!observer) {
      observer = new MutationObserver(scheduleRepair);
      observer.observe(sidebar, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: ["class", "aria-hidden"]
      });
    }

    sidebar.addEventListener("click", function (event) {
      const button = event.target.closest(
        ".qa-nav-item-v1"
      );

      if (!button) return;

      window.setTimeout(syncActive, 0);

      if (isMobile()) {
        closeMobile();
      }
    });
  }

  window.qaEnhanceSidebarV1 = enhance;
  window.qaSidebarSyncActiveState = syncActive;

  window.addEventListener(
    "qa-project-changed",
    scheduleRepair
  );

  window.addEventListener("resize", function () {
    if (!isMobile()) {
      closeMobile();
      setCollapsed(
        localStorage.getItem(STORAGE_KEY) === "true",
        false
      );
    }
  });

  document.addEventListener("keydown", function (event) {
    if (
      event.key === "Escape"
      && document.body.classList.contains(
        "qa-sidebar-mobile-open"
      )
    ) {
      closeMobile();
    }
  });

  if (document.readyState === "loading") {
    document.addEventListener(
      "DOMContentLoaded",
      function () {
        window.setTimeout(enhance, 0);
      }
    );
  } else {
    window.setTimeout(enhance, 0);
  }

  window.addEventListener("load", function () {
    window.setTimeout(enhance, 250);
  });
})();
'''

if CSS_MARKER not in text:
    index = text.rfind("</style>")
    if index == -1:
        fail("Closing </style> tag was not found.")
    text = text[:index] + "\n" + css + "\n" + text[index:]
    print("[OK] Sidebar refinement CSS inserted")
else:
    print("[SKIP] Sidebar refinement CSS already exists")

if JS_MARKER not in text:
    index = text.rfind("</script>")
    if index == -1:
        fail("Closing </script> tag was not found.")
    text = text[:index] + "\n" + js + "\n" + text[index:]
    print("[OK] Sidebar refinement JavaScript inserted")
else:
    print("[SKIP] Sidebar refinement JavaScript already exists")

required = [
    "qaSidebarNavV1",
    "qaSidebarCollapseV1",
    "qaSidebarMobileToggleV1",
    "qa-sidebar-collapsed",
    "UI Testing",
    "API Testing",
    "Regression Testing",
    "Test Planning",
    "History",
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
print("[SUCCESS] Sidebar Refinement V1 installed")
