from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]

HTML_PATH = (
    ROOT
    / "qa_dashboard"
    / "frontend"
    / "dashboard.html"
)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_path = HTML_PATH.with_name(
    "dashboard.html.backup_before_project_selector_"
    + timestamp
)

shutil.copy2(
    HTML_PATH,
    backup_path,
)

text = HTML_PATH.read_text(
    encoding="utf-8"
)


def find_function_block(
    source: str,
    function_name: str,
):
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
        position = source.find(
            marker,
            start + 10,
        )

        if position != -1:
            candidates.append(position)

    end = (
        min(candidates)
        if candidates
        else len(source)
    )

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
            "JavaScript function "
            f"not found: {function_name}"
        )

    start, end, _ = found

    return (
        source[:start]
        + new_chunk
        + source[end:]
    )


# ============================================================
# CSS
# ============================================================

css = r'''
    .qa-project-control {
      display: flex;
      align-items: center;
      gap: 7px;
      padding: 4px 7px 4px 10px;
      border: 1px solid #e2e8f0;
      border-radius: 999px;
      background: #f8fafc;
    }

    .qa-project-control label {
      margin: 0;
      color: #64748b;
      font-size: 10px;
      font-weight: 800;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .qa-project-control select {
      width: auto;
      min-width: 138px;
      max-width: 220px;
      min-height: 30px;
      margin: 0;
      padding: 4px 28px 4px 8px;
      border: none;
      background-color: #ffffff;
      color: #0f172a;
      font-size: 11px;
      font-weight: 700;
    }

    .qa-project-control select:focus {
      outline: 2px solid #2563eb;
      outline-offset: 1px;
    }

    @media (max-width: 650px) {
      .qa-project-control {
        width: 100%;
        justify-content: space-between;
        border-radius: 9px;
      }

      .qa-project-control select {
        flex: 1;
        max-width: none;
      }
    }
'''

if ".qa-project-control" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print(
        "Inserted Project Selector CSS"
    )
else:
    print(
        "Project Selector CSS already exists"
    )


# ============================================================
# JavaScript helpers
# ============================================================

js = r'''
    let qaProjectRegistry = [];
    let qaSelectedProjectId = null;
    let qaSelectedProject = null;

    function qaSetEnvironmentBadge(
      environmentName
    ) {
      const badge = document.getElementById(
        "qaEnvironmentBadge"
      );

      if (!badge) return;

      badge.textContent =
        "Environment: "
        + String(
          environmentName || "Custom"
        );
    }

    function applyQaProjectSelection(
      projectId
    ) {
      const project =
        qaProjectRegistry.find(
          item =>
            String(item.project_id)
            === String(projectId)
        );

      if (!project) {
        return;
      }

      qaSelectedProjectId =
        project.project_id;

      qaSelectedProject = project;

      window.qaSelectedProject =
        project;

      document.body.dataset.projectId =
        project.project_id;

      localStorage.setItem(
        "qa_selected_project_id",
        project.project_id,
      );

      qaSetEnvironmentBadge(
        project.default_environment_name
        || project.default_environment
        || "Custom"
      );

      window.dispatchEvent(
        new CustomEvent(
          "qa-project-changed",
          {
            detail: {
              project,
            },
          }
        )
      );
    }

    function handleQaProjectChange(
      projectId
    ) {
      applyQaProjectSelection(
        projectId
      );
    }

    async function loadQaProjectRegistry() {
      const select = document.getElementById(
        "qaProjectSelect"
      );

      if (!select) {
        return;
      }

      select.disabled = true;

      try {
        const response = await fetch(
          "/projects?_="
          + Date.now(),
          {
            cache: "no-store",
          }
        );

        const payload =
          await response.json();

        if (
          !response.ok
          || !payload.ok
        ) {
          throw new Error(
            JSON.stringify(payload)
          );
        }

        qaProjectRegistry =
          Array.isArray(payload.projects)
            ? payload.projects
            : [];

        select.innerHTML = "";

        for (
          const project
          of qaProjectRegistry
        ) {
          const option =
            document.createElement(
              "option"
            );

          option.value =
            project.project_id;

          option.textContent =
            project.name;

          select.appendChild(
            option
          );
        }

        const storedProjectId =
          localStorage.getItem(
            "qa_selected_project_id"
          );

        const selectedProjectId =
          qaProjectRegistry.some(
            project =>
              project.project_id
              === storedProjectId
          )
            ? storedProjectId
            : qaProjectRegistry.some(
                project =>
                  project.project_id
                  === "mobospace"
              )
            ? "mobospace"
            : (
                qaProjectRegistry[0]
                && qaProjectRegistry[0]
                  .project_id
              );

        if (selectedProjectId) {
          select.value =
            selectedProjectId;

          applyQaProjectSelection(
            selectedProjectId
          );
        }

        select.disabled = false;

      } catch (error) {
        console.error(
          "Project registry error:",
          error
        );

        select.innerHTML = "";

        const option =
          document.createElement(
            "option"
          );

        option.value = "";
        option.textContent =
          "Project unavailable";

        select.appendChild(option);
      }
    }

'''


if "let qaProjectRegistry" not in text:
    marker = (
        "    function "
        "detectDashboardEnvironment() {"
    )

    if marker not in text:
        marker = (
            "    function "
            "setupAutonomousAppShell() {"
        )

    if marker not in text:
        raise RuntimeError(
            "App Shell JavaScript "
            "marker not found"
        )

    text = text.replace(
        marker,
        js + "\n" + marker,
        1,
    )

    print(
        "Inserted Project Selector JavaScript"
    )
else:
    print(
        "Project Selector JavaScript already exists"
    )


# ============================================================
# Add selector to App Shell topbar
# ============================================================

found = find_function_block(
    text,
    "setupAutonomousAppShell",
)

if not found:
    raise RuntimeError(
        "setupAutonomousAppShell "
        "function not found"
    )

_, _, chunk = found


if 'id="qaProjectSelect"' not in chunk:
    marker = '''        <div class="qa-topbar-statuses">
          <span
            class="qa-global-badge connected"
            id="qaEnvironmentBadge"
          >'''

    replacement = '''        <div class="qa-topbar-statuses">
          <div class="qa-project-control">
            <label for="qaProjectSelect">
              Project
            </label>

            <select
              id="qaProjectSelect"
              onchange="handleQaProjectChange(this.value)"
              disabled
            >
              <option value="">
                Loading...
              </option>
            </select>
          </div>

          <span
            class="qa-global-badge connected"
            id="qaEnvironmentBadge"
          >'''

    if marker not in chunk:
        raise RuntimeError(
            "Topbar status marker "
            "was not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Added Project Selector to header"
    )
else:
    print(
        "Project Selector already exists "
        "in header"
    )


if "loadQaProjectRegistry();" not in chunk:
    marker = '''      setupCompactAgentFlow();
      refreshQaBackendStatus();'''

    replacement = '''      setupCompactAgentFlow();
      refreshQaBackendStatus();
      loadQaProjectRegistry();'''

    if marker not in chunk:
        raise RuntimeError(
            "App Shell initialization "
            "marker was not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Added Project Registry initialization"
    )


text = replace_function_block(
    text,
    "setupAutonomousAppShell",
    chunk,
)


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
