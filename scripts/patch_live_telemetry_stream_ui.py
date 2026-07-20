from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_live_telemetry_stream_{timestamp}"
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
# CSS
# ============================================================

css = r'''
    .live-telemetry-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      flex-wrap: wrap;
    }

    .live-telemetry-toolbar {
      display: flex;
      align-items: end;
      gap: 10px;
      flex-wrap: wrap;
      margin: 14px 0;
      padding: 12px;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      background: #f9fafb;
    }

    .live-telemetry-metric {
      min-width: 110px;
      padding: 8px 10px;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      background: white;
    }

    .live-telemetry-metric-label {
      color: #6b7280;
      font-size: 10px;
      text-transform: uppercase;
      margin-bottom: 4px;
    }

    .live-telemetry-metric-value {
      font-size: 13px;
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .live-telemetry-status {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: #e5e7eb;
      color: #374151;
    }

    .live-telemetry-status::before {
      content: "";
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: #9ca3af;
    }

    .live-telemetry-status.connecting {
      background: #fef3c7;
      color: #92400e;
    }

    .live-telemetry-status.connecting::before {
      background: #f59e0b;
    }

    .live-telemetry-status.running {
      background: #dbeafe;
      color: #1d4ed8;
    }

    .live-telemetry-status.running::before {
      background: #2563eb;
      animation: telemetryPulse 1.2s infinite;
    }

    .live-telemetry-status.completed {
      background: #dcfce7;
      color: #166534;
    }

    .live-telemetry-status.completed::before {
      background: #16a34a;
    }

    .live-telemetry-status.review {
      background: #fef3c7;
      color: #92400e;
    }

    .live-telemetry-status.review::before {
      background: #f59e0b;
    }

    .live-telemetry-status.error {
      background: #fee2e2;
      color: #991b1b;
    }

    .live-telemetry-status.error::before {
      background: #dc2626;
    }

    @keyframes telemetryPulse {
      0% {
        opacity: 1;
        transform: scale(1);
      }

      50% {
        opacity: .45;
        transform: scale(.75);
      }

      100% {
        opacity: 1;
        transform: scale(1);
      }
    }

    .live-telemetry-stream {
      height: 360px;
      overflow-y: auto;
      border: 1px solid #1f2937;
      border-radius: 10px;
      background: #111827;
      color: #e5e7eb;
      padding: 8px 12px;
      font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        Monaco,
        Consolas,
        monospace;
    }

    .live-telemetry-event {
      display: grid;
      grid-template-columns:
        86px
        72px
        110px
        minmax(130px, 190px)
        1fr;
      gap: 10px;
      align-items: start;
      padding: 9px 3px;
      border-bottom: 1px solid #374151;
      font-size: 12px;
      line-height: 1.45;
    }

    .live-telemetry-event:last-child {
      border-bottom: none;
    }

    .live-telemetry-time {
      color: #9ca3af;
    }

    .live-telemetry-level {
      display: inline-block;
      width: fit-content;
      padding: 2px 7px;
      border-radius: 999px;
      font-size: 10px;
      font-weight: 700;
    }

    .live-telemetry-level.info {
      background: #1e3a8a;
      color: #dbeafe;
    }

    .live-telemetry-level.warning {
      background: #78350f;
      color: #fef3c7;
    }

    .live-telemetry-level.error {
      background: #7f1d1d;
      color: #fee2e2;
    }

    .live-telemetry-stage {
      color: #93c5fd;
      font-weight: 700;
      text-transform: capitalize;
    }

    .live-telemetry-event-name {
      color: #c4b5fd;
      overflow-wrap: anywhere;
    }

    .live-telemetry-message {
      color: #e5e7eb;
      overflow-wrap: anywhere;
    }

    .live-telemetry-event-meta {
      color: #9ca3af;
      font-size: 10px;
      margin-top: 4px;
    }

    .live-telemetry-empty {
      color: #9ca3af;
      padding: 18px 4px;
      text-align: center;
      font-size: 13px;
    }

    .live-telemetry-paused {
      border-left: 4px solid #f59e0b;
    }

    @media (max-width: 900px) {
      .live-telemetry-event {
        grid-template-columns: 80px 70px 100px 1fr;
      }

      .live-telemetry-message {
        grid-column: 1 / -1;
        padding-bottom: 4px;
      }
    }
'''


if ".live-telemetry-stream" not in text:
    text = text.replace(
        "</style>",
        css + "\n  </style>",
        1,
    )

    print("Inserted Live Telemetry CSS")
else:
    print("Live Telemetry CSS already exists")


# ============================================================
# HTML
# ============================================================

html = r'''
    <section class="section" id="liveTelemetryPanel">
      <div class="live-telemetry-header">
        <div>
          <h2>Live Telemetry Stream</h2>
          <p class="muted">
            Real execution events polled every second from the active
            telemetry session.
          </p>
        </div>

        <span
          class="live-telemetry-status"
          id="liveTelemetryConnectionStatus"
        >
          Ready
        </span>
      </div>

      <div class="live-telemetry-toolbar">
        <div class="live-telemetry-metric">
          <div class="live-telemetry-metric-label">
            Session
          </div>
          <div
            class="live-telemetry-metric-value"
            id="liveTelemetrySessionId"
          >
            -
          </div>
        </div>

        <div class="live-telemetry-metric">
          <div class="live-telemetry-metric-label">
            Event Count
          </div>
          <div
            class="live-telemetry-metric-value"
            id="liveTelemetryEventCount"
          >
            0
          </div>
        </div>

        <div class="live-telemetry-metric">
          <div class="live-telemetry-metric-label">
            Duration
          </div>
          <div
            class="live-telemetry-metric-value"
            id="liveTelemetryDuration"
          >
            0.0s
          </div>
        </div>

        <div>
          <label>Level Filter</label>
          <select
            id="liveTelemetryFilter"
            onchange="setLiveTelemetryFilter(this.value)"
          >
            <option value="all">All Events</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        <button
          type="button"
          class="secondary"
          id="liveTelemetryPauseBtn"
          onclick="toggleLiveTelemetryPause()"
        >
          Pause View
        </button>

        <button
          type="button"
          class="secondary"
          onclick="clearLiveTelemetryView()"
        >
          Clear View
        </button>
      </div>

      <div
        class="live-telemetry-stream"
        id="liveTelemetryStream"
      >
        <div class="live-telemetry-empty">
          Ready. Start a QA test to display live execution events.
        </div>
      </div>
    </section>

'''


if 'id="liveTelemetryPanel"' not in text:
    analysis_marker = (
        '    <section class="section hidden" '
        'id="analysisAgentPanel">'
    )

    tabs_marker = '    <div class="tabs">'

    if analysis_marker in text:
        text = text.replace(
            analysis_marker,
            html + analysis_marker,
            1,
        )

        print(
            "Inserted Live Telemetry panel before Analysis Agent"
        )

    elif tabs_marker in text:
        text = text.replace(
            tabs_marker,
            html + tabs_marker,
            1,
        )

        print(
            "Inserted Live Telemetry panel before tabs"
        )

    else:
        raise RuntimeError(
            "Could not find UI insertion marker"
        )
else:
    print("Live Telemetry panel already exists")


# ============================================================
# JavaScript
# ============================================================

js = r'''
    let liveTelemetryPollingTimer = null;
    let liveTelemetryElapsedTimer = null;
    let liveTelemetryCurrentSessionId = null;
    let liveTelemetryEvents = [];
    let liveTelemetryFilterValue = "all";
    let liveTelemetryPaused = false;
    let liveTelemetryPollInFlight = false;
    let liveTelemetryStartedEpochMs = null;
    let liveTelemetryTotalDurationMs = null;
    let liveTelemetryHiddenBeforeSequence = 0;

    function ltEscapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function ltFormatTime(timestamp) {
      if (!timestamp) return "-";

      const date = new Date(timestamp);

      if (Number.isNaN(date.getTime())) {
        return String(timestamp);
      }

      return date.toLocaleTimeString(
        "id-ID",
        {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit"
        }
      );
    }

    function ltFormatDuration(durationMs) {
      const value = Number(durationMs);

      if (!Number.isFinite(value) || value < 0) {
        return "0.0s";
      }

      if (value < 60000) {
        return (value / 1000).toFixed(1) + "s";
      }

      const minutes = Math.floor(
        value / 60000
      );

      const seconds = (
        (value % 60000) / 1000
      ).toFixed(1);

      return minutes + "m " + seconds + "s";
    }

    function ltFormatMetadata(metadata) {
      if (!metadata || typeof metadata !== "object") {
        return "";
      }

      const entries = Object.entries(metadata)
        .filter(([, value]) =>
          value !== null
          && value !== undefined
          && value !== ""
        );

      if (!entries.length) {
        return "";
      }

      return entries
        .map(([key, value]) =>
          key + "=" + value
        )
        .join(" | ");
    }

    function setLiveTelemetryConnectionState(
      state,
      label
    ) {
      const element = document.getElementById(
        "liveTelemetryConnectionStatus"
      );

      if (!element) return;

      element.className =
        "live-telemetry-status "
        + String(state || "");

      element.textContent = label || "Ready";
    }

    function updateLiveTelemetryMetrics() {
      const sessionElement = document.getElementById(
        "liveTelemetrySessionId"
      );

      const countElement = document.getElementById(
        "liveTelemetryEventCount"
      );

      const durationElement = document.getElementById(
        "liveTelemetryDuration"
      );

      if (sessionElement) {
        sessionElement.textContent =
          liveTelemetryCurrentSessionId || "-";
      }

      if (countElement) {
        countElement.textContent =
          String(liveTelemetryEvents.length);
      }

      let durationMs =
        liveTelemetryTotalDurationMs;

      if (
        durationMs === null
        && liveTelemetryStartedEpochMs
      ) {
        durationMs = Math.max(
          0,
          Date.now()
          - liveTelemetryStartedEpochMs
        );
      }

      if (durationElement) {
        durationElement.textContent =
          ltFormatDuration(
            durationMs || 0
          );
      }
    }

    function renderLiveTelemetryStream() {
      const stream = document.getElementById(
        "liveTelemetryStream"
      );

      if (!stream) return;

      const events = liveTelemetryEvents.filter(
        item => {
          const sequence = Number(
            item.sequence || 0
          );

          if (
            sequence
            <= liveTelemetryHiddenBeforeSequence
          ) {
            return false;
          }

          if (
            liveTelemetryFilterValue === "all"
          ) {
            return true;
          }

          return String(
            item.level || "info"
          ).toLowerCase()
            === liveTelemetryFilterValue;
        }
      );

      if (!events.length) {
        stream.innerHTML = `
          <div class="live-telemetry-empty">
            No telemetry event matches the current view.
          </div>
        `;

        return;
      }

      stream.innerHTML = events
        .map(item => {
          const level = String(
            item.level || "info"
          ).toLowerCase();

          const metadata = ltFormatMetadata(
            item.metadata
          );

          const duration = item.duration_ms !== null
            && item.duration_ms !== undefined
            ? (
              "duration="
              + ltFormatDuration(
                item.duration_ms
              )
            )
            : "";

          const extra = [
            metadata,
            duration
          ].filter(Boolean).join(" | ");

          return `
            <div class="live-telemetry-event">
              <div class="live-telemetry-time">
                ${ltEscapeHtml(
                  ltFormatTime(item.timestamp)
                )}
              </div>

              <div>
                <span
                  class="live-telemetry-level ${ltEscapeHtml(level)}"
                >
                  ${ltEscapeHtml(level.toUpperCase())}
                </span>
              </div>

              <div class="live-telemetry-stage">
                ${ltEscapeHtml(item.stage || "-")}
              </div>

              <div class="live-telemetry-event-name">
                ${ltEscapeHtml(item.event || "-")}
              </div>

              <div class="live-telemetry-message">
                ${ltEscapeHtml(item.message || "-")}

                ${
                  extra
                    ? `
                      <div class="live-telemetry-event-meta">
                        ${ltEscapeHtml(extra)}
                      </div>
                    `
                    : ""
                }
              </div>
            </div>
          `;
        })
        .join("");

      if (!liveTelemetryPaused) {
        stream.scrollTop =
          stream.scrollHeight;
      }
    }

    function stopLiveTelemetryPolling() {
      if (liveTelemetryPollingTimer) {
        clearInterval(
          liveTelemetryPollingTimer
        );

        liveTelemetryPollingTimer = null;
      }

      if (liveTelemetryElapsedTimer) {
        clearInterval(
          liveTelemetryElapsedTimer
        );

        liveTelemetryElapsedTimer = null;
      }
    }

    function prepareLiveTelemetryStream(
      runnerType
    ) {
      stopLiveTelemetryPolling();

      liveTelemetryCurrentSessionId = null;
      liveTelemetryEvents = [];
      liveTelemetryFilterValue = "all";
      liveTelemetryPaused = false;
      liveTelemetryPollInFlight = false;
      liveTelemetryStartedEpochMs =
        Date.now();
      liveTelemetryTotalDurationMs = null;
      liveTelemetryHiddenBeforeSequence = 0;

      const filter = document.getElementById(
        "liveTelemetryFilter"
      );

      if (filter) {
        filter.value = "all";
      }

      const pauseButton = document.getElementById(
        "liveTelemetryPauseBtn"
      );

      if (pauseButton) {
        pauseButton.textContent =
          "Pause View";
      }

      const stream = document.getElementById(
        "liveTelemetryStream"
      );

      if (stream) {
        stream.classList.remove(
          "live-telemetry-paused"
        );

        stream.innerHTML = `
          <div class="live-telemetry-empty">
            Connecting telemetry for
            ${ltEscapeHtml(runnerType || "QA Runner")}...
          </div>
        `;
      }

      setLiveTelemetryConnectionState(
        "connecting",
        "Connecting"
      );

      updateLiveTelemetryMetrics();
    }

    function startLiveTelemetryStream(
      sessionId
    ) {
      stopLiveTelemetryPolling();

      liveTelemetryCurrentSessionId =
        sessionId;

      setLiveTelemetryConnectionState(
        "running",
        "Live"
      );

      updateLiveTelemetryMetrics();

      pollLiveTelemetryStream(
        sessionId,
        true
      );

      liveTelemetryPollingTimer =
        setInterval(() => {
          pollLiveTelemetryStream();
        }, 1000);

      liveTelemetryElapsedTimer =
        setInterval(() => {
          updateLiveTelemetryMetrics();
        }, 250);
    }

    async function pollLiveTelemetryStream(
      sessionIdOverride = null,
      forceRender = false
    ) {
      const sessionId =
        sessionIdOverride
        || liveTelemetryCurrentSessionId;

      if (!sessionId) {
        return null;
      }

      if (
        liveTelemetryPollInFlight
        && !forceRender
      ) {
        return null;
      }

      liveTelemetryPollInFlight = true;

      try {
        const response = await fetch(
          "/telemetry/"
          + encodeURIComponent(sessionId)
          + "?_="
          + Date.now(),
          {
            cache: "no-store"
          }
        );

        const payload = await response.json();

        if (!response.ok || !payload.ok) {
          throw new Error(
            JSON.stringify(payload)
          );
        }

        const telemetry =
          payload.telemetry || {};

        liveTelemetryCurrentSessionId =
          telemetry.telemetry_id
          || sessionId;

        liveTelemetryStartedEpochMs =
          Number(
            telemetry.created_at_epoch_ms
            || liveTelemetryStartedEpochMs
            || Date.now()
          );

        liveTelemetryTotalDurationMs =
          telemetry.total_duration_ms !== null
          && telemetry.total_duration_ms !== undefined
            ? Number(
              telemetry.total_duration_ms
            )
            : null;

        liveTelemetryEvents =
          Array.isArray(telemetry.events)
            ? [...telemetry.events].sort(
              (a, b) =>
                Number(a.sequence || 0)
                - Number(b.sequence || 0)
            )
            : [];

        updateLiveTelemetryMetrics();

        if (
          !liveTelemetryPaused
          || forceRender
        ) {
          renderLiveTelemetryStream();
        }

        const completedEvent =
          liveTelemetryEvents.some(
            item =>
              item.event
              === "session_completed"
          );

        const resultStatus = String(
          telemetry.result_status || ""
        ).toUpperCase();

        if (
          completedEvent
          || (
            resultStatus
            && resultStatus !== "RUNNING"
          )
        ) {
          stopLiveTelemetryPolling();

          if (resultStatus === "FAILED") {
            setLiveTelemetryConnectionState(
              "error",
              "Failed"
            );

          } else if (
            resultStatus === "NEED REVIEW"
          ) {
            setLiveTelemetryConnectionState(
              "review",
              "Need Review"
            );

          } else {
            setLiveTelemetryConnectionState(
              "completed",
              "Completed"
            );
          }

          updateLiveTelemetryMetrics();
        }

        return payload;

      } catch (error) {
        console.error(
          "Live telemetry polling error:",
          error
        );

        setLiveTelemetryConnectionState(
          "error",
          "Stream Error"
        );

        return null;

      } finally {
        liveTelemetryPollInFlight = false;
      }
    }

    function completeLiveTelemetryStream(
      resultStatus,
      totalDurationMs = null
    ) {
      if (
        totalDurationMs !== null
        && totalDurationMs !== undefined
      ) {
        liveTelemetryTotalDurationMs =
          Number(totalDurationMs);
      }

      const status = String(
        resultStatus || "UNKNOWN"
      ).toUpperCase();

      if (status === "FAILED") {
        setLiveTelemetryConnectionState(
          "error",
          "Failed"
        );

      } else if (status === "NEED REVIEW") {
        setLiveTelemetryConnectionState(
          "review",
          "Need Review"
        );

      } else {
        setLiveTelemetryConnectionState(
          "completed",
          "Completed"
        );
      }

      stopLiveTelemetryPolling();
      updateLiveTelemetryMetrics();
      renderLiveTelemetryStream();
    }

    function setLiveTelemetryFilter(value) {
      liveTelemetryFilterValue =
        String(value || "all").toLowerCase();

      renderLiveTelemetryStream();
    }

    function toggleLiveTelemetryPause() {
      liveTelemetryPaused =
        !liveTelemetryPaused;

      const button = document.getElementById(
        "liveTelemetryPauseBtn"
      );

      const stream = document.getElementById(
        "liveTelemetryStream"
      );

      if (button) {
        button.textContent =
          liveTelemetryPaused
            ? "Resume View"
            : "Pause View";
      }

      if (stream) {
        stream.classList.toggle(
          "live-telemetry-paused",
          liveTelemetryPaused
        );
      }

      if (!liveTelemetryPaused) {
        renderLiveTelemetryStream();
      }
    }

    function clearLiveTelemetryView() {
      const sequences = liveTelemetryEvents
        .map(item =>
          Number(item.sequence || 0)
        );

      liveTelemetryHiddenBeforeSequence =
        sequences.length
          ? Math.max(...sequences)
          : 0;

      renderLiveTelemetryStream();
    }

'''


if "let liveTelemetryPollingTimer" not in text:
    marker = (
        "    let activeTelemetrySessionId = null;"
    )

    if marker not in text:
        raise RuntimeError(
            "activeTelemetrySessionId marker not found"
        )

    text = text.replace(
        marker,
        js + "\n" + marker,
        1,
    )

    print(
        "Inserted Live Telemetry JavaScript"
    )
else:
    print(
        "Live Telemetry JavaScript already exists"
    )


# ============================================================
# Patch startExecutionTelemetry
# ============================================================

found = find_function_block(
    text,
    "startExecutionTelemetry",
)

if not found:
    raise RuntimeError(
        "startExecutionTelemetry function not found"
    )

_, _, chunk = found


if "prepareLiveTelemetryStream(runnerType);" not in chunk:
    marker = '''    async function startExecutionTelemetry(runnerType) {
      const featureName = telemetryFeatureName(
        runnerType
      );
'''

    replacement = '''    async function startExecutionTelemetry(runnerType) {
      const featureName = telemetryFeatureName(
        runnerType
      );

      prepareLiveTelemetryStream(
        runnerType
      );
'''

    if marker not in chunk:
        raise RuntimeError(
            "startExecutionTelemetry start marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Patched Live Stream preparation"
    )


if "startLiveTelemetryStream(data.telemetry_id);" not in chunk:
    marker = '''      activeTelemetryFeatureName =
        featureName;

      return data.telemetry_id;'''

    replacement = '''      activeTelemetryFeatureName =
        featureName;

      startLiveTelemetryStream(
        data.telemetry_id
      );

      return data.telemetry_id;'''

    if marker not in chunk:
        raise RuntimeError(
            "Telemetry session success marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Patched Live Stream session start"
    )


text = replace_function_block(
    text,
    "startExecutionTelemetry",
    chunk,
)


# ============================================================
# Patch beginExecutionTelemetry error state
# ============================================================

found = find_function_block(
    text,
    "beginExecutionTelemetry",
)

if not found:
    raise RuntimeError(
        "beginExecutionTelemetry function not found"
    )

_, _, chunk = found


if '"Telemetry Start Failed"' not in chunk:
    marker = '''            console.error(
              "Telemetry start error:",
              error
            );

            return null;'''

    replacement = '''            console.error(
              "Telemetry start error:",
              error
            );

            setLiveTelemetryConnectionState(
              "error",
              "Telemetry Start Failed"
            );

            return null;'''

    if marker not in chunk:
        raise RuntimeError(
            "Telemetry start error marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Patched telemetry connection error state"
    )


text = replace_function_block(
    text,
    "beginExecutionTelemetry",
    chunk,
)


# ============================================================
# Patch completeExecutionTelemetry
# ============================================================

found = find_function_block(
    text,
    "completeExecutionTelemetry",
)

if not found:
    raise RuntimeError(
        "completeExecutionTelemetry function not found"
    )

_, _, chunk = found


if "await pollLiveTelemetryStream(sessionId, true);" not in chunk:
    marker = '''        return data;

      } catch (error) {'''

    replacement = '''        await pollLiveTelemetryStream(
          sessionId,
          true
        );

        completeLiveTelemetryStream(
          status,
          data.total_duration_ms
        );

        return data;

      } catch (error) {'''

    if marker not in chunk:
        raise RuntimeError(
            "Telemetry complete success marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Patched final Live Stream refresh"
    )


if '"Telemetry Completion Failed"' not in chunk:
    marker = '''        console.error(
          "Telemetry completion error:",
          error
        );

        return null;'''

    replacement = '''        console.error(
          "Telemetry completion error:",
          error
        );

        setLiveTelemetryConnectionState(
          "error",
          "Telemetry Completion Failed"
        );

        return null;'''

    if marker not in chunk:
        raise RuntimeError(
            "Telemetry completion error marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print(
        "Patched completion error state"
    )


text = replace_function_block(
    text,
    "completeExecutionTelemetry",
    chunk,
)


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
