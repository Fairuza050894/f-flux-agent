from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_compact_execution_layout_{timestamp}"
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
    found = find_function_block(source, function_name)

    if not found:
        raise RuntimeError(
            f"JavaScript function not found: {function_name}"
        )

    start, end, _ = found

    return source[:start] + new_chunk + source[end:]


# ============================================================
# CSS
# ============================================================

css = r'''
    .analysis-compact-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
      margin: 14px 0;
      padding: 12px 14px;
      border: 1px solid #e5e7eb;
      border-left: 4px solid #2563eb;
      border-radius: 10px;
      background: #f8fafc;
    }

    .analysis-compact-content {
      min-width: 0;
      flex: 1;
    }

    .analysis-compact-title {
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .analysis-compact-summary {
      color: #4b5563;
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }

    .analysis-compact-bar.severity-low {
      border-left-color: #16a34a;
      background: #f0fdf4;
    }

    .analysis-compact-bar.severity-medium {
      border-left-color: #f59e0b;
      background: #fffbeb;
    }

    .analysis-compact-bar.severity-high {
      border-left-color: #dc2626;
      background: #fef2f2;
    }

    .analysis-detail-toggle {
      white-space: nowrap;
    }

    #analysisAgentPanel {
      margin-top: 12px;
      margin-bottom: 14px;
    }

    #liveTelemetryPanel {
      margin-top: 14px;
    }
'''

if ".analysis-compact-bar" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print("Inserted compact execution layout CSS")
else:
    print("Compact execution layout CSS already exists")


# ============================================================
# JavaScript helper
# ============================================================

js = r'''
    let lastExecutionPanelRunnerType = "registered";

    function resolveExecutionRunnerTab(runnerType) {
      const normalized = String(
        runnerType || ""
      ).toLowerCase();

      if (normalized === "registered") {
        return document.getElementById(
          "tab-registered"
        );
      }

      if (normalized === "custom_smoke") {
        return document.getElementById(
          "tab-custom"
        );
      }

      if (normalized === "api_curl") {
        return document.getElementById(
          "tab-curl"
        );
      }

      const activeRunnerPanel =
        document.querySelector(
          "#tab-registered.active, "
          + "#tab-custom.active, "
          + "#tab-curl.active"
        );

      if (activeRunnerPanel) {
        return activeRunnerPanel;
      }

      return (
        document.getElementById("tab-registered")
        || document.getElementById("tab-custom")
        || document.getElementById("tab-curl")
      );
    }

    function findExecutionResultAnchor(runnerType) {
      const panel = resolveExecutionRunnerTab(
        runnerType
      );

      if (!panel) {
        return null;
      }

      const normalized = String(
        runnerType || ""
      ).toLowerCase();

      const candidateIds = [];

      if (normalized === "custom_smoke") {
        candidateIds.push(
          "customResult"
        );
      }

      if (normalized === "api_curl") {
        candidateIds.push(
          "curlResult"
        );
      }

      if (normalized === "registered") {
        candidateIds.push(
          "registeredResult",
          "registeredQaResult",
          "qaResult",
          "result"
        );
      }

      candidateIds.push(
        "registeredResult",
        "registeredQaResult",
        "qaResult",
        "customResult",
        "curlResult"
      );

      for (const id of candidateIds) {
        const element = document.getElementById(id);

        if (element && panel.contains(element)) {
          return element;
        }
      }

      const resultBoxes = Array.from(
        panel.querySelectorAll(".result-box")
      );

      if (resultBoxes.length) {
        return resultBoxes[
          resultBoxes.length - 1
        ];
      }

      const runButton = panel.querySelector(
        "button[id*='run'], "
        + "button[onclick*='runRegisteredQA'], "
        + "button[onclick*='runCustomSmoke'], "
        + "button[onclick*='runCurlTest']"
      );

      return runButton || panel;
    }

    function ensureAnalysisCompactBar() {
      let bar = document.getElementById(
        "analysisCompactBar"
      );

      if (bar) {
        return bar;
      }

      bar = document.createElement("div");
      bar.id = "analysisCompactBar";
      bar.className =
        "analysis-compact-bar hidden";

      bar.innerHTML = `
        <div class="analysis-compact-content">
          <div class="analysis-compact-title">
            Analysis Agent
          </div>

          <div
            class="analysis-compact-summary"
            id="analysisCompactSummary"
          >
            Analysis has not been generated.
          </div>
        </div>

        <button
          type="button"
          class="secondary analysis-detail-toggle"
          id="analysisDetailToggleBtn"
          onclick="toggleAnalysisDetail()"
        >
          Detail Analysis
        </button>
      `;

      return bar;
    }

    function placeExecutionPanels(runnerType) {
      const normalized = String(
        runnerType || "registered"
      ).toLowerCase();

      lastExecutionPanelRunnerType =
        normalized;

      const panel = resolveExecutionRunnerTab(
        normalized
      );

      const anchor = findExecutionResultAnchor(
        normalized
      );

      const analysisBar =
        ensureAnalysisCompactBar();

      const analysisPanel =
        document.getElementById(
          "analysisAgentPanel"
        );

      const telemetryPanel =
        document.getElementById(
          "liveTelemetryPanel"
        );

      if (!panel) {
        return;
      }

      if (
        anchor
        && anchor !== panel
        && typeof anchor.insertAdjacentElement
          === "function"
      ) {
        anchor.insertAdjacentElement(
          "afterend",
          analysisBar
        );
      } else {
        panel.appendChild(analysisBar);
      }

      if (analysisPanel) {
        analysisBar.insertAdjacentElement(
          "afterend",
          analysisPanel
        );
      }

      if (telemetryPanel) {
        if (analysisPanel) {
          analysisPanel.insertAdjacentElement(
            "afterend",
            telemetryPanel
          );
        } else {
          analysisBar.insertAdjacentElement(
            "afterend",
            telemetryPanel
          );
        }
      }
    }

    function resetAnalysisCompactBar() {
      const bar = ensureAnalysisCompactBar();

      bar.className =
        "analysis-compact-bar hidden";

      const summary = document.getElementById(
        "analysisCompactSummary"
      );

      if (summary) {
        summary.textContent =
          "Analysis is being prepared.";
      }

      const analysisPanel =
        document.getElementById(
          "analysisAgentPanel"
        );

      if (analysisPanel) {
        analysisPanel.classList.add(
          "hidden"
        );
      }

      const button = document.getElementById(
        "analysisDetailToggleBtn"
      );

      if (button) {
        button.textContent =
          "Detail Analysis";
      }
    }

    function showAnalysisCompactSummary(
      responseData
    ) {
      const analysis =
        responseData
        && responseData.analysis
          ? responseData.analysis
          : {};

      placeExecutionPanels(
        lastExecutionPanelRunnerType
      );

      const bar = ensureAnalysisCompactBar();

      bar.classList.remove(
        "hidden",
        "severity-low",
        "severity-medium",
        "severity-high"
      );

      const severity = String(
        analysis.severity || "medium"
      ).toLowerCase();

      if (
        ["low", "medium", "high"]
          .includes(severity)
      ) {
        bar.classList.add(
          "severity-" + severity
        );
      }

      const summary = document.getElementById(
        "analysisCompactSummary"
      );

      if (summary) {
        summary.textContent = [
          "Category: "
            + (analysis.category || "-"),
          "Severity: "
            + (analysis.severity || "-"),
          "Confidence: "
            + (analysis.confidence || "-"),
          "Release: "
            + (
              analysis.release_recommendation
              || "-"
            )
        ].join(" | ");
      }

      const analysisPanel =
        document.getElementById(
          "analysisAgentPanel"
        );

      if (analysisPanel) {
        analysisPanel.classList.add(
          "hidden"
        );
      }
    }

    function showAnalysisCompactFailure(
      errorMessage
    ) {
      placeExecutionPanels(
        lastExecutionPanelRunnerType
      );

      const bar = ensureAnalysisCompactBar();

      bar.classList.remove(
        "hidden",
        "severity-low",
        "severity-medium"
      );

      bar.classList.add(
        "severity-high"
      );

      const summary = document.getElementById(
        "analysisCompactSummary"
      );

      if (summary) {
        summary.textContent =
          "Analysis Agent failed: "
          + String(errorMessage || "-");
      }
    }

    function toggleAnalysisDetail() {
      const panel = document.getElementById(
        "analysisAgentPanel"
      );

      const button = document.getElementById(
        "analysisDetailToggleBtn"
      );

      if (!panel) {
        return;
      }

      const willOpen =
        panel.classList.contains("hidden");

      panel.classList.toggle(
        "hidden",
        !willOpen
      );

      if (button) {
        button.textContent =
          willOpen
            ? "Tutup Detail"
            : "Detail Analysis";
      }

      if (willOpen) {
        panel.scrollIntoView({
          behavior: "smooth",
          block: "nearest"
        });
      }
    }

    window.addEventListener(
      "load",
      function () {
        setTimeout(function () {
          placeExecutionPanels(
            "registered"
          );
        }, 700);
      }
    );

'''

if "function placeExecutionPanels(" not in text:
    marker = (
        "    function renderAnalysisAgent"
        "(responseData) {"
    )

    if marker not in text:
        raise RuntimeError(
            "renderAnalysisAgent function not found"
        )

    text = text.replace(
        marker,
        js + "\n" + marker,
        1,
    )

    print(
        "Inserted compact execution layout JavaScript"
    )
else:
    print(
        "Compact execution layout JavaScript already exists"
    )


# ============================================================
# Patch startAgentFlow
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

if "placeExecutionPanels(typeLabel);" not in chunk:
    marker = (
        '      const typeLabel = '
        'runnerType || "QA Runner";'
    )

    replacement = marker + r'''

      placeExecutionPanels(
        typeLabel
      );

      resetAnalysisCompactBar();
'''

    if marker not in chunk:
        raise RuntimeError(
            "startAgentFlow typeLabel marker not found"
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

    print(
        "Patched runner-specific panel placement"
    )
else:
    print(
        "Runner panel placement already patched"
    )


# ============================================================
# Patch renderAnalysisAgent
# ============================================================

found = find_function_block(
    text,
    "renderAnalysisAgent",
)

if not found:
    raise RuntimeError(
        "renderAnalysisAgent function not found"
    )

_, _, chunk = found

chunk = chunk.replace(
    '      panel.classList.remove("hidden");',
    '      panel.classList.add("hidden");',
    1,
)

if "showAnalysisCompactSummary(responseData);" not in chunk:
    closing_position = chunk.rfind(
        "\n    }"
    )

    if closing_position == -1:
        raise RuntimeError(
            "renderAnalysisAgent closing marker not found"
        )

    chunk = (
        chunk[:closing_position]
        + r'''

      showAnalysisCompactSummary(
        responseData
      );
'''
        + chunk[closing_position:]
    )

    print(
        "Patched Analysis Agent compact summary"
    )

text = replace_function_block(
    text,
    "renderAnalysisAgent",
    chunk,
)


# ============================================================
# Patch Analysis Agent error state
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

if "showAnalysisCompactFailure(" not in chunk:
    marker = '''        console.error(
          "Analysis Agent error:",
          error
        );'''

    replacement = marker + r'''

        showAnalysisCompactFailure(
          error.message
        );
'''

    if marker not in chunk:
        fallback = (
            '        console.error('
            '"Analysis Agent error:", error);'
        )

        fallback_replacement = fallback + r'''

        showAnalysisCompactFailure(
          error.message
        );
'''

        if fallback not in chunk:
            raise RuntimeError(
                "Analysis Agent error marker not found"
            )

        chunk = chunk.replace(
            fallback,
            fallback_replacement,
            1,
        )
    else:
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
        "Patched compact Analysis Agent error state"
    )
else:
    print(
        "Compact Analysis Agent error already patched"
    )


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
