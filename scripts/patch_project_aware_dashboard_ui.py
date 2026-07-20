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
    "dashboard.html.backup_before_project_aware_content_"
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
            candidates.append(
                position
            )

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
            "JavaScript function not found: "
            + function_name
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
    .qa-project-context-banner {
      margin: 0 0 16px;
      padding: 13px 15px;
      border: 1px solid #dbeafe;
      border-left: 4px solid #2563eb;
      border-radius: 10px;
      background: #eff6ff;
    }

    .qa-project-context-banner.adhoc {
      border-color: #e2e8f0;
      border-left-color: #64748b;
      background: #f8fafc;
    }

    .qa-project-context-title {
      margin-bottom: 4px;
      color: #0f172a;
      font-size: 13px;
      font-weight: 800;
    }

    .qa-project-context-description {
      color: #475569;
      font-size: 12px;
      line-height: 1.5;
    }

    .qa-project-context-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 9px;
    }

    .qa-project-context-pill {
      padding: 4px 8px;
      border: 1px solid #cbd5e1;
      border-radius: 999px;
      background: #ffffff;
      color: #475569;
      font-size: 10px;
      font-weight: 700;
    }

    .qa-regression-empty-state {
      margin: 14px 0;
      padding: 22px;
      border: 1px dashed #cbd5e1;
      border-radius: 10px;
      background: #f8fafc;
      color: #475569;
      text-align: center;
    }

    .qa-regression-empty-state strong {
      display: block;
      margin-bottom: 6px;
      color: #0f172a;
    }

    .qa-history-project-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      background: #e0e7ff;
      color: #3730a3;
      font-size: 10px;
      font-weight: 700;
      white-space: nowrap;
    }

    .qa-history-project-badge.legacy {
      background: #f1f5f9;
      color: #64748b;
    }
'''

if (
    ".qa-project-context-banner"
    not in text
):
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print(
        "Inserted project-aware CSS"
    )
else:
    print(
        "Project-aware CSS already exists"
    )


# ============================================================
# JavaScript
# ============================================================

js = r'''
    const qaProjectDetailCache = {};
    let qaOriginalRegisteredOptions = null;

    function qaFunctionalSidebarLabels() {
      const buttons = document.querySelectorAll(
        ".qa-sidebar .tab-btn, .tabs .tab-btn"
      );

      buttons.forEach(button => {
        const action = String(
          button.getAttribute("onclick")
          || ""
        ).toLowerCase();

        if (action.includes("registered")) {
          button.textContent =
            "Regression Testing";
        }

        if (action.includes("custom")) {
          button.textContent =
            "UI Testing";
        }

        if (action.includes("curl")) {
          button.textContent =
            "API Testing";
        }

        if (action.includes("planning")) {
          button.textContent =
            "Test Planning";
        }

        if (action.includes("history")) {
          button.textContent =
            "History";
        }
      });
    }

    function qaEnsureContextBanner(
      tabId
    ) {
      const tab = document.getElementById(
        tabId
      );

      if (!tab) {
        return null;
      }

      const bannerId =
        "qaProjectContextBanner-"
        + tabId;

      let banner = document.getElementById(
        bannerId
      );

      if (banner) {
        return banner;
      }

      banner = document.createElement(
        "div"
      );

      banner.id = bannerId;
      banner.className =
        "qa-project-context-banner";

      const heading =
        tab.querySelector("h2");

      if (heading) {
        heading.insertAdjacentElement(
          "afterend",
          banner
        );
      } else {
        tab.prepend(banner);
      }

      return banner;
    }

    function qaRenderContextBanner(
      tabId,
      title,
      description,
      pills,
      projectId
    ) {
      const banner =
        qaEnsureContextBanner(tabId);

      if (!banner) {
        return;
      }

      banner.className =
        "qa-project-context-banner"
        + (
          projectId === "adhoc"
            ? " adhoc"
            : ""
        );

      const pillHtml = (
        Array.isArray(pills)
          ? pills
          : []
      )
        .map(
          pill => `
            <span class="qa-project-context-pill">
              ${ltEscapeHtml(pill)}
            </span>
          `
        )
        .join("");

      banner.innerHTML = `
        <div class="qa-project-context-title">
          ${ltEscapeHtml(title)}
        </div>

        <div class="qa-project-context-description">
          ${ltEscapeHtml(description)}
        </div>

        ${
          pillHtml
            ? `
              <div class="qa-project-context-pills">
                ${pillHtml}
              </div>
            `
            : ""
        }
      `;
    }

    function qaStoreOriginalRegisteredOptions() {
      if (qaOriginalRegisteredOptions) {
        return;
      }

      const select = document.getElementById(
        "registeredFeature"
      );

      if (!select) {
        qaOriginalRegisteredOptions = [];
        return;
      }

      qaOriginalRegisteredOptions =
        Array.from(select.options)
          .map(option => ({
            value: option.value,
            text: option.textContent,
          }));
    }

    function qaSetRegressionAvailable(
      available
    ) {
      const tab = document.getElementById(
        "tab-registered"
      );

      const select = document.getElementById(
        "registeredFeature"
      );

      if (select) {
        select.disabled = !available;
      }

      if (!tab) {
        return;
      }

      tab.querySelectorAll("button")
        .forEach(button => {
          const action = String(
            button.getAttribute("onclick")
            || ""
          ).toLowerCase();

          if (
            action.includes(
              "runregisteredqa"
            )
          ) {
            button.disabled = !available;
          }
        });

      let emptyState =
        document.getElementById(
          "qaRegressionEmptyState"
        );

      if (!emptyState) {
        emptyState =
          document.createElement("div");

        emptyState.id =
          "qaRegressionEmptyState";

        emptyState.className =
          "qa-regression-empty-state hidden";

        const result =
          document.getElementById(
            "registeredResult"
          );

        if (result) {
          result.insertAdjacentElement(
            "beforebegin",
            emptyState
          );
        } else {
          tab.appendChild(emptyState);
        }
      }

      emptyState.classList.toggle(
        "hidden",
        available
      );

      if (!available) {
        emptyState.innerHTML = `
          <strong>
            No registered regression features
          </strong>

          Ad-hoc Testing is intended for direct
          UI and API execution. Save a reusable
          configuration as a project before
          creating regression suites.
        `;
      }
    }

    function qaPopulateMobospaceFeatures(
      detail
    ) {
      qaStoreOriginalRegisteredOptions();

      const select = document.getElementById(
        "registeredFeature"
      );

      if (!select) {
        return;
      }

      const features =
        Array.isArray(detail.features)
          ? detail.features
          : [];

      select.innerHTML = "";

      features.forEach(feature => {
        const option =
          document.createElement("option");

        option.value =
          feature.runner_feature_name
          || feature.name
          || feature.feature_id;

        option.textContent =
          feature.name
          || feature.runner_feature_name
          || feature.feature_id;

        select.appendChild(option);
      });

      const suites =
        Array.isArray(
          detail.regression_suites
        )
          ? detail.regression_suites
          : [];

      const allFeaturesSuite =
        suites.find(
          suite =>
            suite.suite_id
            === "all-features"
        );

      if (
        allFeaturesSuite
        && !Array.from(select.options)
          .some(
            option =>
              option.value
              === "All Features"
          )
      ) {
        const option =
          document.createElement("option");

        option.value = "All Features";
        option.textContent =
          "All Features";

        select.appendChild(option);
      }

      qaSetRegressionAvailable(true);
    }

    function qaRenderProjectAwareContent(
      detail
    ) {
      const project =
        detail && detail.project
          ? detail.project
          : {};

      const projectId =
        String(
          project.project_id || ""
        );

      const projectName =
        project.name || "Project";

      const environment =
        project.default_environment_name
        || project.default_environment
        || "Custom";

      const featureCount =
        Array.isArray(detail.features)
          ? detail.features.length
          : 0;

      const suiteCount =
        Array.isArray(
          detail.regression_suites
        )
          ? detail.regression_suites.length
          : 0;

      if (projectId === "mobospace") {
        qaRenderContextBanner(
          "tab-custom",
          "Mobospace UI Testing",
          (
            "Run route-level UI smoke tests "
            + "using the Mobospace project context."
          ),
          [
            "Environment: " + environment,
            featureCount
              + " registered features",
            "Project credential reference",
          ],
          projectId
        );

        qaRenderContextBanner(
          "tab-curl",
          "Mobospace API Testing",
          (
            "Paste a cURL request or use a "
            + "project-scoped template. No "
            + "Mobospace API collection is "
            + "registered yet."
          ),
          [
            "Positive case",
            "Negative case",
            "Masked report",
          ],
          projectId
        );

        qaRenderContextBanner(
          "tab-registered",
          "Mobospace Regression Testing",
          (
            "Select a registered Mobospace "
            + "feature or run all features."
          ),
          [
            featureCount + " features",
            suiteCount + " suites",
            "Environment: " + environment,
          ],
          projectId
        );

        qaRenderContextBanner(
          "tab-planning",
          "Mobospace Test Planning",
          (
            "Generate test scope and scenarios "
            + "within the Mobospace project context."
          ),
          [
            "Project: " + projectName,
            "Environment: " + environment,
          ],
          projectId
        );

        qaPopulateMobospaceFeatures(
          detail
        );

      } else {
        qaRenderContextBanner(
          "tab-custom",
          "Ad-hoc UI Testing",
          (
            "Enter a custom target URL, route, "
            + "expected text, and runtime "
            + "authentication configuration."
          ),
          [
            "Custom target",
            "Runtime credential",
            "Reusable template",
          ],
          projectId
        );

        qaRenderContextBanner(
          "tab-curl",
          "Ad-hoc API Testing",
          (
            "Paste a cURL request and configure "
            + "positive or negative expectations. "
            + "Credential values are not stored."
          ),
          [
            "Paste cURL",
            "Positive case",
            "Negative case",
          ],
          projectId
        );

        qaRenderContextBanner(
          "tab-registered",
          "Ad-hoc Regression Testing",
          (
            "No regression feature registry is "
            + "configured for Ad-hoc Testing."
          ),
          [
            "0 features",
            "0 suites",
          ],
          projectId
        );

        qaRenderContextBanner(
          "tab-planning",
          "Ad-hoc Test Planning",
          (
            "Create test scenarios from a custom "
            + "requirement, route, or cURL request."
          ),
          [
            "Environment: Custom",
            "Generic target",
          ],
          projectId
        );

        const select =
          document.getElementById(
            "registeredFeature"
          );

        if (select) {
          select.innerHTML = `
            <option value="">
              No registered feature
            </option>
          `;
        }

        qaSetRegressionAvailable(false);
      }

      qaFunctionalSidebarLabels();
    }

    async function loadQaProjectDetail(
      projectId
    ) {
      if (!projectId) {
        return null;
      }

      if (
        qaProjectDetailCache[
          projectId
        ]
      ) {
        const cached =
          qaProjectDetailCache[
            projectId
          ];

        qaRenderProjectAwareContent(
          cached
        );

        return cached;
      }

      try {
        const response = await fetch(
          "/projects/"
          + encodeURIComponent(projectId)
          + "?_="
          + Date.now(),
          {
            cache: "no-store"
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

        qaProjectDetailCache[
          projectId
        ] = payload;

        qaRenderProjectAwareContent(
          payload
        );

        return payload;

      } catch (error) {
        console.error(
          "Project detail error:",
          error
        );

        return null;
      }
    }

    function qaCollectResultArtifacts(
      result
    ) {
      const source =
        result
        && typeof result === "object"
          ? result
          : {};

      const nested =
        source.artifacts
        && typeof source.artifacts
          === "object"
          ? source.artifacts
          : {};

      return {
        standard_json:
          source.standard_json_path
          || nested.standard_json
          || null,

        report:
          source.report_path
          || source.documentation_path
          || nested.report
          || null,

        screenshot:
          source.screenshot_path
          || nested.screenshot
          || null,

        error_log:
          source.error_log_path
          || nested.error_log
          || null,

        spreadsheet:
          source.spreadsheet_path
          || nested.spreadsheet
          || null,

        raw_output:
          source.raw_output_path
          || nested.raw_output
          || null,

        analysis:
          source.analysis_path
          || nested.analysis
          || nested.analysis_path
          || null,

        telemetry:
          source.telemetry_path
          || nested.telemetry
          || null,
      };
    }

    async function attachActiveProjectContext(
      result
    ) {
      const project =
        qaSelectedProject
        || window.qaSelectedProject;

      if (
        !project
        || !project.project_id
      ) {
        return null;
      }

      const executionId =
        telemetryExecutionId(result);

      if (!executionId) {
        console.warn(
          "Project context was not attached: "
          + "execution_id unavailable."
        );

        return null;
      }

      try {
        const response = await fetch(
          "/project-context/attach",
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json"
            },
            body: JSON.stringify({
              project_id:
                project.project_id,

              execution_id:
                executionId,

              standard_json_path:
                telemetryStandardJsonPath(
                  result
                ),

              telemetry_id:
                activeTelemetrySessionId,

              artifact_paths:
                qaCollectResultArtifacts(
                  result
                ),
            }),
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

        if (
          result
          && typeof result === "object"
        ) {
          result.project_context =
            payload.project_context;

          result.project_id =
            payload.project_context
              .project_id;

          result.project_name =
            payload.project_context
              .project_name;

          result.project_metadata_path =
            payload.project_metadata_path;
        }

        return payload;

      } catch (error) {
        console.error(
          "Project context attachment error:",
          error
        );

        return null;
      }
    }

    function qaDecorateHistoryProjectColumn() {
      const table =
        document.querySelector(
          "#historyPaginationPanel "
          + "table"
        );

      const body =
        document.getElementById(
          "paginatedHistoryBody"
        );

      if (!table || !body) {
        return;
      }

      const headerRow =
        table.querySelector(
          "thead tr"
        );

      if (
        headerRow
        && !headerRow.querySelector(
          '[data-qa-project-column="true"]'
        )
      ) {
        const headers =
          headerRow.querySelectorAll(
            "th"
          );

        const header =
          document.createElement("th");

        header.dataset.qaProjectColumn =
          "true";

        header.textContent = "Project";

        if (headers.length >= 2) {
          headers[1].insertAdjacentElement(
            "afterend",
            header
          );
        } else {
          headerRow.appendChild(header);
        }
      }

      const emptyCell =
        body.querySelector(
          ".history-empty-row"
        );

      if (emptyCell) {
        emptyCell.colSpan = 10;
        return;
      }

      const startIndex =
        (
          paginatedHistoryPage - 1
        ) * paginatedHistoryPageSize;

      const pageItems =
        paginatedHistoryRuns.slice(
          startIndex,
          startIndex
            + paginatedHistoryPageSize
        );

      const rows =
        body.querySelectorAll("tr");

      rows.forEach(
        (row, index) => {
          if (
            row.querySelector(
              '[data-qa-project-column="true"]'
            )
          ) {
            return;
          }

          const item =
            pageItems[index] || {};

          const cells =
            row.querySelectorAll("td");

          if (cells.length < 2) {
            return;
          }

          const cell =
            document.createElement("td");

          cell.dataset.qaProjectColumn =
            "true";

          const projectName =
            item.project_name
            || (
              item.project_id
                ? item.project_id
                : "Legacy / Unassigned"
            );

          const badge =
            document.createElement("span");

          badge.className =
            "qa-history-project-badge"
            + (
              item.project_id
                ? ""
                : " legacy"
            );

          badge.textContent =
            projectName;

          cell.appendChild(badge);

          cells[1].insertAdjacentElement(
            "afterend",
            cell
          );
        }
      );
    }

    window.addEventListener(
      "qa-project-changed",
      function (event) {
        const project =
          event
          && event.detail
          && event.detail.project;

        if (
          project
          && project.project_id
        ) {
          loadQaProjectDetail(
            project.project_id
          );
        }
      }
    );

    window.addEventListener(
      "load",
      function () {
        setTimeout(
          function () {
            qaFunctionalSidebarLabels();

            if (qaSelectedProjectId) {
              loadQaProjectDetail(
                qaSelectedProjectId
              );
            }
          },
          1000
        );
      }
    );

'''

if (
    "async function attachActiveProjectContext"
    not in text
):
    marker = (
        "    async function "
        "runAnalysisAgent(result) {"
    )

    if marker not in text:
        raise RuntimeError(
            "runAnalysisAgent marker not found"
        )

    text = text.replace(
        marker,
        js + "\n" + marker,
        1,
    )

    print(
        "Inserted project-aware JavaScript"
    )
else:
    print(
        "Project-aware JavaScript already exists"
    )


# ============================================================
# Attach project context before Analysis Agent
# ============================================================

found = find_function_block(
    text,
    "runAnalysisAgent",
)

if not found:
    raise RuntimeError(
        "runAnalysisAgent function not found"
    )

_, _, chunk = found

if (
    "await attachActiveProjectContext(result);"
    not in chunk
):
    marker = (
        "    async function "
        "runAnalysisAgent(result) {"
    )

    replacement = marker + r'''

      await attachActiveProjectContext(
        result
      );
'''

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    text = replace_function_block(
        text,
        "runAnalysisAgent",
        chunk,
    )

    print(
        "Patched project context before analysis"
    )
else:
    print(
        "Project context hook already exists"
    )


# ============================================================
# Decorate paginated History after render
# ============================================================

found = find_function_block(
    text,
    "renderPaginatedHistory",
)

if not found:
    raise RuntimeError(
        "renderPaginatedHistory function not found"
    )

_, _, chunk = found

if (
    "qaDecorateHistoryProjectColumn();"
    not in chunk
):
    closing_position = chunk.rfind(
        "\n    }"
    )

    if closing_position == -1:
        raise RuntimeError(
            "renderPaginatedHistory closing "
            "marker not found"
        )

    chunk = (
        chunk[:closing_position]
        + r'''

      setTimeout(
        qaDecorateHistoryProjectColumn,
        0
      );
'''
        + chunk[closing_position:]
    )

    text = replace_function_block(
        text,
        "renderPaginatedHistory",
        chunk,
    )

    print(
        "Patched History project column"
    )
else:
    print(
        "History project column already patched"
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
