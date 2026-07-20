from pathlib import Path
from datetime import datetime
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_autonomous_app_shell_{timestamp}"
)

shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")


def find_function_block(source: str, function_name: str):
    markers = [
        f"    async function {function_name}(",
        f"    function {function_name}(",
    ]

    start = -1

    for marker in markers:
        start = source.find(marker)

        if start != -1:
            break

    if start == -1:
        return None

    candidates = []

    for marker in (
        "\n    async function ",
        "\n    function ",
        "\n    window.addEventListener",
        "\n    init();",
        "\n  </script>",
    ):
        position = source.find(marker, start + 10)

        if position != -1:
            candidates.append(position)

    end = min(candidates) if candidates else len(source)

    return start, end, source[start:end]


def replace_function_block(
    source: str,
    function_name: str,
    new_chunk: str,
):
    found = find_function_block(
        source,
        function_name,
    )

    if not found:
        raise RuntimeError(
            f"JavaScript function not found: {function_name}"
        )

    start, end, _ = found

    return source[:start] + new_chunk + source[end:]


# ============================================================
# Rename browser title and legacy visible title
# ============================================================

text, title_count = re.subn(
    r"<title>.*?</title>",
    "<title>QA Autonomous Dashboard</title>",
    text,
    count=1,
    flags=re.IGNORECASE | re.DOTALL,
)

if title_count:
    print("Renamed browser title")
else:
    print("Browser title tag was not found")


legacy_titles = [
    "Hermes Autonomous QA Command Center",
    "Hermes QA Agent Dashboard",
    "Hermes QA Dashboard",
    "Hermes QA",
]

for legacy_title in legacy_titles:
    text = text.replace(
        legacy_title,
        "QA Autonomous Dashboard",
    )


# ============================================================
# CSS
# ============================================================

css = r'''
    body.qa-shell-ready {
      margin: 0 !important;
      background: #f1f5f9;
    }

    .qa-app-shell {
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
      min-height: 100vh;
    }

    .qa-sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      padding: 18px 14px;
      background: #0f172a;
      color: #e2e8f0;
      z-index: 80;
    }

    .qa-sidebar-brand {
      display: flex;
      align-items: center;
      gap: 11px;
      padding: 4px 6px 20px;
      border-bottom: 1px solid #334155;
      margin-bottom: 16px;
    }

    .qa-sidebar-logo {
      width: 38px;
      height: 38px;
      flex: 0 0 38px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 10px;
      background: #2563eb;
      color: white;
      font-size: 15px;
      font-weight: 800;
    }

    .qa-sidebar-brand-name {
      color: #f8fafc;
      font-size: 14px;
      font-weight: 800;
      line-height: 1.25;
    }

    .qa-sidebar-brand-subtitle {
      color: #94a3b8;
      font-size: 10px;
      margin-top: 3px;
    }

    .qa-sidebar-nav-host .tabs {
      display: flex !important;
      flex-direction: column !important;
      align-items: stretch !important;
      gap: 4px !important;
      margin: 0 !important;
      padding: 0 !important;
      border: none !important;
      background: transparent !important;
    }

    .qa-nav-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 16px;
    }

    .qa-nav-group-label {
      padding: 5px 10px;
      color: #64748b;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: .08em;
    }

    .qa-sidebar .tab-btn {
      width: 100% !important;
      min-height: 40px;
      display: flex !important;
      align-items: center;
      justify-content: flex-start;
      padding: 9px 11px !important;
      margin: 0 !important;
      border: 1px solid transparent !important;
      border-radius: 8px !important;
      background: transparent !important;
      color: #cbd5e1 !important;
      font-size: 13px !important;
      font-weight: 600 !important;
      text-align: left;
    }

    .qa-sidebar .tab-btn:hover {
      background: #1e293b !important;
      color: #ffffff !important;
    }

    .qa-sidebar .tab-btn.active {
      border-color: #3b82f6 !important;
      background: #1d4ed8 !important;
      color: #ffffff !important;
    }

    .qa-main {
      min-width: 0;
      width: 100%;
    }

    .qa-topbar {
      position: sticky;
      top: 0;
      z-index: 60;
      min-height: 70px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      padding: 12px 24px;
      border-bottom: 1px solid #e2e8f0;
      background: rgba(255, 255, 255, .96);
      backdrop-filter: blur(8px);
    }

    .qa-topbar-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .qa-sidebar-toggle {
      display: none;
      width: 38px;
      height: 38px;
      padding: 0;
      align-items: center;
      justify-content: center;
      font-size: 19px;
    }

    .qa-topbar-title {
      color: #0f172a;
      font-size: 18px;
      font-weight: 800;
      line-height: 1.2;
    }

    .qa-topbar-subtitle {
      color: #64748b;
      font-size: 11px;
      margin-top: 3px;
    }

    .qa-topbar-statuses {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .qa-global-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 9px;
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      background: #f8fafc;
      color: #475569;
      font-size: 11px;
      font-weight: 700;
      white-space: nowrap;
    }

    .qa-global-badge::before {
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 999px;
      background: #94a3b8;
    }

    .qa-global-badge.connected::before,
    .qa-global-badge.pass::before {
      background: #16a34a;
    }

    .qa-global-badge.running::before {
      background: #2563eb;
      animation: telemetryPulse 1.2s infinite;
    }

    .qa-global-badge.review::before {
      background: #f59e0b;
    }

    .qa-global-badge.failed::before,
    .qa-global-badge.disconnected::before {
      background: #dc2626;
    }

    .qa-main-content {
      width: 100% !important;
      max-width: none !important;
      min-width: 0;
      box-sizing: border-box;
      margin: 0 !important;
      padding: 22px 24px 40px !important;
    }

    .qa-main-content > h1:first-of-type,
    .qa-main-content > header > h1:first-of-type {
      display: none !important;
    }

    .qa-agent-flow-compact {
      padding: 16px !important;
    }

    .qa-agent-flow-heading {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }

    .qa-agent-flow-heading h2 {
      margin: 0;
    }

    .qa-agent-flow-toggle {
      flex: 0 0 auto;
      white-space: nowrap;
    }

    .qa-agent-flow-compact .agent-flow-grid {
      grid-template-columns:
        repeat(7, minmax(90px, 1fr)) !important;
      gap: 7px !important;
      overflow-x: auto;
      padding-bottom: 3px;
    }

    .qa-agent-flow-compact .agent-step {
      min-height: 70px !important;
      padding: 9px !important;
      border-radius: 9px !important;
    }

    .qa-agent-flow-compact .agent-step-number {
      width: 20px !important;
      height: 20px !important;
      margin-bottom: 5px !important;
      font-size: 10px !important;
    }

    .qa-agent-flow-compact .agent-step-title {
      margin-bottom: 2px !important;
      font-size: 11px !important;
    }

    .qa-agent-flow-compact .agent-step-desc {
      display: none;
    }

    .qa-agent-flow-compact .agent-step-status {
      margin-top: 5px !important;
      padding: 3px 6px !important;
      font-size: 9px !important;
    }

    .qa-agent-flow-compact .agent-flow-note {
      margin-top: 9px !important;
      padding: 8px 10px !important;
      font-size: 11px !important;
    }

    .qa-agent-flow-compact.expanded .agent-step {
      min-height: 110px !important;
    }

    .qa-agent-flow-compact.expanded .agent-step-desc {
      display: block;
      font-size: 10px !important;
    }

    .qa-mobile-overlay {
      display: none;
    }

    @media (max-width: 1100px) {
      .qa-topbar {
        align-items: flex-start;
      }

      .qa-topbar-statuses {
        max-width: 50%;
      }
    }

    @media (max-width: 900px) {
      .qa-app-shell {
        display: block;
      }

      .qa-sidebar {
        position: fixed;
        left: -280px;
        top: 0;
        width: 260px;
        box-sizing: border-box;
        transition: left .2s ease;
        box-shadow: 12px 0 30px rgba(15, 23, 42, .22);
      }

      .qa-app-shell.sidebar-open .qa-sidebar {
        left: 0;
      }

      .qa-sidebar-toggle {
        display: inline-flex;
      }

      .qa-mobile-overlay {
        display: block;
        position: fixed;
        inset: 0;
        z-index: 70;
        background: rgba(15, 23, 42, .45);
        opacity: 0;
        pointer-events: none;
        transition: opacity .2s ease;
      }

      .qa-app-shell.sidebar-open .qa-mobile-overlay {
        opacity: 1;
        pointer-events: auto;
      }

      .qa-topbar {
        padding: 11px 16px;
      }

      .qa-topbar-statuses {
        max-width: none;
      }

      .qa-main-content {
        padding: 16px !important;
      }
    }

    @media (max-width: 650px) {
      .qa-topbar {
        flex-direction: column;
      }

      .qa-topbar-statuses {
        justify-content: flex-start;
      }

      .qa-agent-flow-compact .agent-flow-grid {
        grid-template-columns:
          repeat(7, minmax(105px, 1fr)) !important;
      }
    }
'''

if ".qa-app-shell" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print("Inserted App Shell CSS")
else:
    print("App Shell CSS already exists")


# ============================================================
# JavaScript
# ============================================================

js = r'''
    function qaCreateNavGroup(label) {
      const group = document.createElement("div");
      group.className = "qa-nav-group";

      const groupLabel = document.createElement("div");
      groupLabel.className = "qa-nav-group-label";
      groupLabel.textContent = label;

      group.appendChild(groupLabel);

      return group;
    }

    function qaRenameNavigationButton(button) {
      const action = String(
        button.getAttribute("onclick") || ""
      ).toLowerCase();

      if (action.includes("registered")) {
        button.textContent = "Registered QA";
        return "execute";
      }

      if (action.includes("custom")) {
        button.textContent = "Custom UI Smoke";
        return "execute";
      }

      if (action.includes("curl")) {
        button.textContent = "API cURL";
        return "execute";
      }

      if (action.includes("planning")) {
        button.textContent = "Test Planning";
        return "workspace";
      }

      if (action.includes("history")) {
        button.textContent = "History";
        return "workspace";
      }

      return "workspace";
    }

    function detectDashboardEnvironment() {
      const candidates = Array.from(
        document.querySelectorAll(
          "select, input"
        )
      );

      for (const element of candidates) {
        const id = String(
          element.id || ""
        ).toLowerCase();

        const name = String(
          element.name || ""
        ).toLowerCase();

        if (
          !id.includes("environment")
          && !name.includes("environment")
        ) {
          continue;
        }

        const value = String(
          element.value || ""
        ).trim();

        if (value) {
          return value;
        }
      }

      return "Sandbox";
    }

    function setQaBackendState(
      state,
      textValue
    ) {
      const badge = document.getElementById(
        "qaBackendBadge"
      );

      if (!badge) return;

      badge.className =
        "qa-global-badge "
        + String(state || "");

      badge.textContent =
        "Backend: "
        + String(textValue || "Unknown");
    }

    function setGlobalRunState(
      state,
      textValue
    ) {
      const badge = document.getElementById(
        "qaActiveRunBadge"
      );

      if (!badge) return;

      badge.className =
        "qa-global-badge "
        + String(state || "");

      badge.textContent =
        "Run: "
        + String(textValue || "Idle");
    }

    async function refreshQaBackendStatus() {
      setQaBackendState(
        "",
        "Checking"
      );

      try {
        const response = await fetch(
          "/health?_="
          + Date.now(),
          {
            cache: "no-store"
          }
        );

        if (!response.ok) {
          throw new Error(
            "HTTP " + response.status
          );
        }

        setQaBackendState(
          "connected",
          "Connected"
        );

      } catch (error) {
        console.error(
          "Backend health check failed:",
          error
        );

        setQaBackendState(
          "disconnected",
          "Disconnected"
        );
      }
    }

    function toggleQaSidebar() {
      const shell = document.getElementById(
        "qaAppShell"
      );

      if (!shell) return;

      shell.classList.toggle(
        "sidebar-open"
      );
    }

    function closeQaSidebar() {
      const shell = document.getElementById(
        "qaAppShell"
      );

      if (!shell) return;

      shell.classList.remove(
        "sidebar-open"
      );
    }

    function setupCompactAgentFlow() {
      const panel = document.getElementById(
        "agentFlowPanel"
      );

      if (!panel) return;

      panel.classList.add(
        "qa-agent-flow-compact"
      );

      const heading = panel.querySelector("h2");

      if (heading) {
        heading.textContent =
          "Autonomous QA Flow";
      }

      if (
        heading
        && !document.getElementById(
          "qaAgentFlowToggle"
        )
      ) {
        const wrapper =
          document.createElement("div");

        wrapper.className =
          "qa-agent-flow-heading";

        heading.parentNode.insertBefore(
          wrapper,
          heading
        );

        wrapper.appendChild(heading);

        const button =
          document.createElement("button");

        button.type = "button";
        button.id = "qaAgentFlowToggle";
        button.className =
          "secondary qa-agent-flow-toggle";
        button.textContent = "Detail Flow";

        button.addEventListener(
          "click",
          function () {
            const expanded =
              panel.classList.toggle(
                "expanded"
              );

            button.textContent =
              expanded
                ? "Compact Flow"
                : "Detail Flow";
          }
        );

        wrapper.appendChild(button);
      }
    }

    function setupAutonomousAppShell() {
      if (
        document.getElementById(
          "qaAppShell"
        )
      ) {
        return;
      }

      document.title =
        "QA Autonomous Dashboard";

      const contentRoot =
        document.querySelector(".container")
        || document.querySelector("main");

      if (!contentRoot) {
        console.error(
          "Dashboard content root not found."
        );
        return;
      }

      const tabs =
        contentRoot.querySelector(".tabs")
        || document.querySelector(".tabs");

      const shell =
        document.createElement("div");

      shell.id = "qaAppShell";
      shell.className = "qa-app-shell";

      const sidebar =
        document.createElement("aside");

      sidebar.className = "qa-sidebar";

      sidebar.innerHTML = `
        <div class="qa-sidebar-brand">
          <div class="qa-sidebar-logo">QA</div>

          <div>
            <div class="qa-sidebar-brand-name">
              QA Autonomous Dashboard
            </div>

            <div class="qa-sidebar-brand-subtitle">
              Autonomous testing command center
            </div>
          </div>
        </div>

        <div
          class="qa-sidebar-nav-host"
          id="qaSidebarNavigation"
        ></div>
      `;

      const main =
        document.createElement("div");

      main.className = "qa-main";

      const topbar =
        document.createElement("header");

      topbar.className = "qa-topbar";

      topbar.innerHTML = `
        <div class="qa-topbar-left">
          <button
            type="button"
            class="secondary qa-sidebar-toggle"
            onclick="toggleQaSidebar()"
            aria-label="Open navigation"
          >
            ☰
          </button>

          <div>
            <div class="qa-topbar-title">
              QA Autonomous Dashboard
            </div>

            <div class="qa-topbar-subtitle">
              Plan, execute, observe, analyze, and review QA runs
            </div>
          </div>
        </div>

        <div class="qa-topbar-statuses">
          <span
            class="qa-global-badge connected"
            id="qaEnvironmentBadge"
          >
            Environment:
            ${detectDashboardEnvironment()}
          </span>

          <span
            class="qa-global-badge"
            id="qaBackendBadge"
          >
            Backend: Checking
          </span>

          <span
            class="qa-global-badge"
            id="qaActiveRunBadge"
          >
            Run: Idle
          </span>
        </div>
      `;

      const overlay =
        document.createElement("div");

      overlay.className =
        "qa-mobile-overlay";

      overlay.addEventListener(
        "click",
        closeQaSidebar
      );

      contentRoot.parentNode.insertBefore(
        shell,
        contentRoot
      );

      shell.appendChild(sidebar);
      shell.appendChild(main);
      shell.appendChild(overlay);

      main.appendChild(topbar);

      contentRoot.classList.add(
        "qa-main-content"
      );

      main.appendChild(contentRoot);

      const navHost =
        document.getElementById(
          "qaSidebarNavigation"
        );

      if (tabs && navHost) {
        const buttons = Array.from(
          tabs.querySelectorAll(".tab-btn")
        );

        const executeGroup =
          qaCreateNavGroup("Execute");

        const workspaceGroup =
          qaCreateNavGroup("Workspace");

        buttons.forEach(button => {
          const group =
            qaRenameNavigationButton(button);

          button.addEventListener(
            "click",
            closeQaSidebar
          );

          if (group === "execute") {
            executeGroup.appendChild(button);
          } else {
            workspaceGroup.appendChild(button);
          }
        });

        tabs.innerHTML = "";
        tabs.appendChild(executeGroup);
        tabs.appendChild(workspaceGroup);

        navHost.appendChild(tabs);
      }

      document.body.classList.add(
        "qa-shell-ready"
      );

      setupCompactAgentFlow();
      refreshQaBackendStatus();

      setInterval(
        refreshQaBackendStatus,
        30000
      );
    }

    window.addEventListener(
      "load",
      function () {
        setTimeout(
          setupAutonomousAppShell,
          350
        );
      }
    );

'''

if "function setupAutonomousAppShell()" not in text:
    marker = (
        "    function setAgentStep"
        "(step, status, label) {"
    )

    if marker not in text:
        marker = (
            "    async function "
            "runRegisteredQA() {"
        )

    if marker not in text:
        raise RuntimeError(
            "JavaScript insertion marker not found"
        )

    text = text.replace(
        marker,
        js + "\n" + marker,
        1,
    )

    print("Inserted App Shell JavaScript")
else:
    print("App Shell JavaScript already exists")


# ============================================================
# Update global run status from Agent Flow
# ============================================================

found = find_function_block(
    text,
    "startAgentFlow",
)

if not found:
    raise RuntimeError(
        "startAgentFlow function not found"
    )

_, _, chunk = found

if 'setGlobalRunState("running", "Running");' not in chunk:
    marker = (
        '      const typeLabel = '
        'runnerType || "QA Runner";'
    )

    replacement = marker + r'''

      setGlobalRunState(
        "running",
        "Running"
      );
'''

    if marker not in chunk:
        raise RuntimeError(
            "startAgentFlow marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    text = replace_function_block(
        text,
        "startAgentFlow",
        chunk,
    )

    print("Patched global running status")
else:
    print("Global running status already patched")


found = find_function_block(
    text,
    "completeAgentFlow",
)

if not found:
    raise RuntimeError(
        "completeAgentFlow function not found"
    )

_, _, chunk = found

if "setGlobalRunState(" not in chunk:
    marker = '''      const status = String(result && result.status ? result.status : "UNKNOWN").toUpperCase();'''

    replacement = marker + r'''

      if (status === "PASS") {
        setGlobalRunState(
          "pass",
          "PASS"
        );

      } else if (status === "FAILED") {
        setGlobalRunState(
          "failed",
          "FAILED"
        );

      } else if (status === "NEED REVIEW") {
        setGlobalRunState(
          "review",
          "NEED REVIEW"
        );

      } else {
        setGlobalRunState(
          "review",
          status
        );
      }
'''

    if marker not in chunk:
        raise RuntimeError(
            "completeAgentFlow status marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    text = replace_function_block(
        text,
        "completeAgentFlow",
        chunk,
    )

    print("Patched global completion status")
else:
    print("Global completion status already patched")


found = find_function_block(
    text,
    "failAgentFlow",
)

if not found:
    raise RuntimeError(
        "failAgentFlow function not found"
    )

_, _, chunk = found

if 'setGlobalRunState("failed", "FAILED");' not in chunk:
    marker = '''    function failAgentFlow(errorMessage) {'''

    replacement = marker + r'''

      setGlobalRunState(
        "failed",
        "FAILED"
      );
'''

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    text = replace_function_block(
        text,
        "failAgentFlow",
        chunk,
    )

    print("Patched global failed status")
else:
    print("Global failed status already patched")


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
