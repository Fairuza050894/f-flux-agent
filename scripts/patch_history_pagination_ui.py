from pathlib import Path
from datetime import datetime
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_history_pagination_{timestamp}"
)

shutil.copy2(HTML_PATH, backup_path)

text = HTML_PATH.read_text(encoding="utf-8")


# ============================================================
# Rename tab button: Run History -> History
# ============================================================

tab_pattern = re.compile(
    r'(<button[^>]*showTab\([\'"]history[\'"]\)[^>]*>)'
    r'.*?'
    r'(</button>)',
    flags=re.IGNORECASE | re.DOTALL,
)

text, tab_count = tab_pattern.subn(
    r'\1History\2',
    text,
    count=1,
)

print(
    "Renamed history tab button"
    if tab_count
    else "History tab button already renamed or not found"
)


# ============================================================
# Rename heading inside tab-history
# ============================================================

section_position = text.find('id="tab-history"')

if section_position == -1:
    raise RuntimeError("tab-history section not found")

heading_start = text.find("<h2", section_position)
heading_open_end = text.find(">", heading_start)
heading_end = text.find("</h2>", heading_open_end)

if (
    heading_start != -1
    and heading_open_end != -1
    and heading_end != -1
):
    current_heading = text[
        heading_open_end + 1:heading_end
    ].strip()

    if current_heading != "History":
        text = (
            text[:heading_open_end + 1]
            + "History"
            + text[heading_end:]
        )

        print("Renamed history heading")
    else:
        print("History heading already renamed")
else:
    raise RuntimeError("History heading not found")


text = text.replace(
    ">Refresh Runs</button>",
    ">Refresh History</button>",
)


# ============================================================
# CSS
# ============================================================

css = r'''
    .history-pagination-panel {
      margin: 14px 0 18px;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      background: #ffffff;
      overflow: hidden;
    }

    .history-pagination-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: end;
      flex-wrap: wrap;
      gap: 12px;
      padding: 14px;
      background: #f9fafb;
      border-bottom: 1px solid #e5e7eb;
    }

    .history-pagination-summary {
      color: #6b7280;
      font-size: 12px;
      margin-top: 4px;
    }

    .history-page-size {
      display: flex;
      align-items: end;
      gap: 8px;
    }

    .history-page-size select {
      min-width: 84px;
    }

    .history-table-wrapper {
      width: 100%;
      overflow-x: auto;
    }

    .history-pagination-table {
      width: 100%;
      min-width: 920px;
      border-collapse: collapse;
    }

    .history-pagination-table th,
    .history-pagination-table td {
      padding: 11px 12px;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      vertical-align: middle;
      font-size: 12px;
    }

    .history-pagination-table th {
      background: #f8fafc;
      color: #4b5563;
      font-size: 11px;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .history-pagination-table tbody tr:hover {
      background: #f9fafb;
    }

    .history-pagination-table tbody tr:last-child td {
      border-bottom: none;
    }

    .history-execution-id {
      font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        Monaco,
        Consolas,
        monospace;
      font-size: 11px;
      white-space: nowrap;
    }

    .history-status-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 700;
      white-space: nowrap;
      background: #e5e7eb;
      color: #374151;
    }

    .history-status-badge.pass {
      background: #dcfce7;
      color: #166534;
    }

    .history-status-badge.failed {
      background: #fee2e2;
      color: #991b1b;
    }

    .history-status-badge.need-review {
      background: #fef3c7;
      color: #92400e;
    }

    .history-pagination-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 14px;
      border-top: 1px solid #e5e7eb;
      background: #f9fafb;
    }

    .history-pagination-buttons {
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .history-pagination-buttons button:disabled {
      opacity: .45;
      cursor: not-allowed;
    }

    .history-page-indicator {
      min-width: 100px;
      text-align: center;
      color: #4b5563;
      font-size: 12px;
      font-weight: 700;
    }

    .history-empty-row {
      padding: 28px !important;
      text-align: center !important;
      color: #6b7280;
    }

    @media (max-width: 700px) {
      .history-pagination-toolbar,
      .history-pagination-footer {
        align-items: stretch;
        flex-direction: column;
      }

      .history-pagination-buttons {
        justify-content: space-between;
      }
    }
'''

if ".history-pagination-panel" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print("Inserted History pagination CSS")
else:
    print("History pagination CSS already exists")


# ============================================================
# HTML panel
# ============================================================

panel_html = r'''
      <div
        class="history-pagination-panel"
        id="historyPaginationPanel"
      >
        <div class="history-pagination-toolbar">
          <div>
            <strong>Execution History</strong>

            <div
              class="history-pagination-summary"
              id="historyPaginationSummary"
            >
              Loading history...
            </div>
          </div>

          <div class="history-page-size">
            <div>
              <label>Rows per page</label>

              <select
                id="historyPageSize"
                onchange="changeHistoryPageSize(this.value)"
              >
                <option value="10" selected>10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
            </div>

            <button
              type="button"
              class="secondary"
              onclick="loadPaginatedHistory()"
            >
              Refresh History
            </button>
          </div>
        </div>

        <div class="history-table-wrapper">
          <table class="history-pagination-table">
            <thead>
              <tr>
                <th>Execution ID</th>
                <th>Feature</th>
                <th>Status</th>
                <th>Environment</th>
                <th>Mode</th>
                <th>Executed At</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody id="paginatedHistoryBody">
              <tr>
                <td colspan="9" class="history-empty-row">
                  Loading history...
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="history-pagination-footer">
          <div
            class="history-pagination-summary"
            id="historyPaginationRange"
          >
            -
          </div>

          <div class="history-pagination-buttons">
            <button
              type="button"
              class="secondary"
              id="historyPreviousBtn"
              onclick="changeHistoryPage(-1)"
            >
              Previous
            </button>

            <span
              class="history-page-indicator"
              id="historyPageIndicator"
            >
              Page 1 of 1
            </span>

            <button
              type="button"
              class="secondary"
              id="historyNextBtn"
              onclick="changeHistoryPage(1)"
            >
              Next
            </button>
          </div>
        </div>
      </div>

'''

if 'id="historyPaginationPanel"' not in text:
    run_detail_marker = (
        '      <div class="run-detail-toolbar" '
        'id="runDetailToolbar">'
    )

    if run_detail_marker in text:
        text = text.replace(
            run_detail_marker,
            panel_html + run_detail_marker,
            1,
        )

        print(
            "Inserted pagination panel before Run Detail"
        )
    else:
        section_position = text.find(
            'id="tab-history"'
        )

        heading_end = text.find(
            "</h2>",
            section_position,
        )

        if heading_end == -1:
            raise RuntimeError(
                "Unable to insert History panel"
            )

        heading_end += len("</h2>")

        text = (
            text[:heading_end]
            + "\n"
            + panel_html
            + text[heading_end:]
        )

        print(
            "Inserted pagination panel using fallback"
        )
else:
    print("History pagination panel already exists")


# ============================================================
# JavaScript
# ============================================================

js = r'''
    let paginatedHistoryRuns = [];
    let paginatedHistoryPage = 1;
    let paginatedHistoryPageSize = 10;

    function hpEscapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function hpExtractHistoryItems(payload) {
      if (Array.isArray(payload)) {
        return payload.filter(
          item =>
            item
            && typeof item === "object"
        );
      }

      if (
        !payload
        || typeof payload !== "object"
      ) {
        return [];
      }

      for (const key of [
        "runs",
        "history",
        "items",
        "records",
        "entries",
        "data"
      ]) {
        if (Array.isArray(payload[key])) {
          return payload[key].filter(
            item =>
              item
              && typeof item === "object"
          );
        }
      }

      return [];
    }

    function hpStatusClass(status) {
      const value = String(
        status || ""
      ).toUpperCase();

      if (value === "PASS") {
        return "pass";
      }

      if (value === "FAILED") {
        return "failed";
      }

      if (value === "NEED REVIEW") {
        return "need-review";
      }

      return "";
    }

    function hideLegacyHistoryView() {
      const candidateIds = [
        "historyResult",
        "historyList",
        "historyTable",
        "historyTableBody",
        "historyBody",
        "historyOutput",
        "historyContainer"
      ];

      candidateIds.forEach(id => {
        const element = document.getElementById(id);

        if (
          !element
          || element.closest(
            "#historyPaginationPanel"
          )
          || element.closest(
            "#runDetailPanel"
          )
        ) {
          return;
        }

        const table = element.closest("table");

        if (table) {
          const wrapper =
            table.closest(".table-wrap")
            || table.closest(".table-wrapper")
            || table;

          wrapper.classList.add("hidden");
        } else {
          element.classList.add("hidden");
        }
      });

      const tab = document.getElementById(
        "tab-history"
      );

      if (!tab) return;

      tab.querySelectorAll(
        ":scope > .result-box"
      ).forEach(element => {
        if (
          !element.closest(
            "#runDetailPanel"
          )
          && !element.closest(
            "#historyPaginationPanel"
          )
        ) {
          element.classList.add("hidden");
        }
      });
    }

    function renderPaginatedHistory() {
      const body = document.getElementById(
        "paginatedHistoryBody"
      );

      const summary = document.getElementById(
        "historyPaginationSummary"
      );

      const range = document.getElementById(
        "historyPaginationRange"
      );

      const pageIndicator = document.getElementById(
        "historyPageIndicator"
      );

      const previousButton = document.getElementById(
        "historyPreviousBtn"
      );

      const nextButton = document.getElementById(
        "historyNextBtn"
      );

      if (!body) return;

      const totalItems =
        paginatedHistoryRuns.length;

      const totalPages = Math.max(
        1,
        Math.ceil(
          totalItems
          / paginatedHistoryPageSize
        )
      );

      if (
        paginatedHistoryPage > totalPages
      ) {
        paginatedHistoryPage =
          totalPages;
      }

      const startIndex =
        (
          paginatedHistoryPage - 1
        ) * paginatedHistoryPageSize;

      const endIndex = Math.min(
        startIndex + paginatedHistoryPageSize,
        totalItems,
      );

      const pageItems =
        paginatedHistoryRuns.slice(
          startIndex,
          endIndex,
        );

      if (!pageItems.length) {
        body.innerHTML = `
          <tr>
            <td
              colspan="9"
              class="history-empty-row"
            >
              No execution history is available.
            </td>
          </tr>
        `;
      } else {
        body.innerHTML = pageItems.map(run => {
          const executionId =
            run.execution_id || "";

          const status =
            run.status || "-";

          return `
            <tr>
              <td class="history-execution-id">
                ${hpEscapeHtml(
                  executionId || "-"
                )}
              </td>

              <td>
                ${hpEscapeHtml(
                  run.feature || "-"
                )}
              </td>

              <td>
                <span
                  class="history-status-badge ${hpStatusClass(status)}"
                >
                  ${hpEscapeHtml(status)}
                </span>
              </td>

              <td>
                ${hpEscapeHtml(
                  run.environment || "-"
                )}
              </td>

              <td>
                ${hpEscapeHtml(
                  run.mode || "-"
                )}
              </td>

              <td>
                ${hpEscapeHtml(
                  run.executed_at
                  || run.created_at
                  || "-"
                )}
              </td>

              <td>
                ${hpEscapeHtml(
                  run.passed ?? 0
                )}
              </td>

              <td>
                ${hpEscapeHtml(
                  run.failed ?? 0
                )}
              </td>

              <td>
                ${
                  executionId
                    ? `
                      <button
                        type="button"
                        class="secondary"
                        onclick="openPaginatedHistoryDetail('${hpEscapeHtml(executionId)}')"
                      >
                        Detail
                      </button>
                    `
                    : '<span class="muted">Unavailable</span>'
                }
              </td>
            </tr>
          `;
        }).join("");
      }

      if (summary) {
        summary.textContent =
          totalItems
          + " execution run(s) stored.";
      }

      if (range) {
        range.textContent =
          totalItems
            ? (
              "Showing "
              + (startIndex + 1)
              + "–"
              + endIndex
              + " of "
              + totalItems
            )
            : "Showing 0 of 0";
      }

      if (pageIndicator) {
        pageIndicator.textContent =
          "Page "
          + paginatedHistoryPage
          + " of "
          + totalPages;
      }

      if (previousButton) {
        previousButton.disabled =
          paginatedHistoryPage <= 1;
      }

      if (nextButton) {
        nextButton.disabled =
          paginatedHistoryPage
          >= totalPages;
      }
    }

    async function loadPaginatedHistory() {
      const body = document.getElementById(
        "paginatedHistoryBody"
      );

      if (body) {
        body.innerHTML = `
          <tr>
            <td
              colspan="9"
              class="history-empty-row"
            >
              Loading history...
            </td>
          </tr>
        `;
      }

      try {
        const response = await fetch(
          "/history?_="
          + Date.now(),
          {
            cache: "no-store"
          }
        );

        const payload = await response.json();

        if (!response.ok) {
          throw new Error(
            JSON.stringify(payload)
          );
        }

        paginatedHistoryRuns =
          hpExtractHistoryItems(payload);

        paginatedHistoryPage = 1;

        renderPaginatedHistory();
        hideLegacyHistoryView();

      } catch (error) {
        console.error(
          "History pagination error:",
          error
        );

        if (body) {
          body.innerHTML = `
            <tr>
              <td
                colspan="9"
                class="history-empty-row"
              >
                Failed to load history:
                ${hpEscapeHtml(error.message)}
              </td>
            </tr>
          `;
        }
      }
    }

    function changeHistoryPage(direction) {
      const totalPages = Math.max(
        1,
        Math.ceil(
          paginatedHistoryRuns.length
          / paginatedHistoryPageSize
        )
      );

      const nextPage =
        paginatedHistoryPage
        + Number(direction || 0);

      if (
        nextPage < 1
        || nextPage > totalPages
      ) {
        return;
      }

      paginatedHistoryPage =
        nextPage;

      renderPaginatedHistory();

      const panel = document.getElementById(
        "historyPaginationPanel"
      );

      if (panel) {
        panel.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });
      }
    }

    function changeHistoryPageSize(value) {
      const parsed = Number(value);

      paginatedHistoryPageSize =
        [10, 20, 50].includes(parsed)
          ? parsed
          : 10;

      paginatedHistoryPage = 1;

      renderPaginatedHistory();
    }

    async function openPaginatedHistoryDetail(
      executionId
    ) {
      const select = document.getElementById(
        "runDetailExecutionSelect"
      );

      if (select) {
        const existingOption = Array.from(
          select.options || []
        ).find(
          option =>
            option.value === executionId
        );

        if (!existingOption) {
          const option =
            document.createElement("option");

          option.value = executionId;
          option.textContent = executionId;

          select.appendChild(option);
        }

        select.value = executionId;
      }

      if (
        typeof openSelectedRunDetail
        === "function"
      ) {
        await openSelectedRunDetail();
      }
    }

    window.addEventListener(
      "load",
      function () {
        setTimeout(function () {
          loadPaginatedHistory();
        }, 800);
      }
    );

'''

if "let paginatedHistoryRuns" not in text:
    marker = (
        "    async function "
        "loadRunDetailOptions() {"
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

    print(
        "Inserted History pagination JavaScript"
    )
else:
    print(
        "History pagination JavaScript already exists"
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
