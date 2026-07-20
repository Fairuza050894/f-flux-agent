from pathlib import Path
from datetime import datetime
import shutil


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "qa_dashboard" / "frontend" / "dashboard.html"

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = HTML_PATH.with_name(
    f"dashboard.html.backup_before_execution_telemetry_ui_{timestamp}"
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


telemetry_helpers = r'''
    let activeTelemetrySessionId = null;
    let activeTelemetryStartPromise = null;
    let activeTelemetryRunnerType = null;
    let activeTelemetryFeatureName = null;

    function telemetryFeatureName(runnerType) {
      const candidateIds = [];

      if (runnerType === "custom_smoke") {
        candidateIds.push("customFeatureName");
      }

      if (runnerType === "api_curl") {
        candidateIds.push("curlFeatureName");
      }

      if (runnerType === "template") {
        const curlTab = document.getElementById("tab-curl");
        const customTab = document.getElementById("tab-custom");

        if (curlTab && curlTab.classList.contains("active")) {
          candidateIds.push(
            "curlFeatureName",
            "customFeatureName"
          );
        } else if (
          customTab
          && customTab.classList.contains("active")
        ) {
          candidateIds.push(
            "customFeatureName",
            "curlFeatureName"
          );
        } else {
          candidateIds.push(
            "customFeatureName",
            "curlFeatureName"
          );
        }
      }

      candidateIds.push(
        "featureSelect",
        "registeredFeature",
        "registeredFeatureSelect",
        "qaFeature",
        "customFeatureName",
        "curlFeatureName"
      );

      for (const id of candidateIds) {
        const element = document.getElementById(id);

        if (!element) continue;

        const value = String(
          element.value || ""
        ).trim();

        if (!value) continue;

        if (
          element.tagName === "SELECT"
          && element.selectedOptions
          && element.selectedOptions.length
        ) {
          const optionText = String(
            element.selectedOptions[0].textContent || ""
          ).trim();

          if (optionText) {
            return optionText;
          }
        }

        return value;
      }

      return String(
        runnerType || "QA Execution"
      );
    }

    async function startExecutionTelemetry(runnerType) {
      const featureName = telemetryFeatureName(
        runnerType
      );

      const response = await fetch(
        "/telemetry/start",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            runner_type: runnerType,
            feature_name: featureName
          })
        }
      );

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(
          JSON.stringify(data)
        );
      }

      activeTelemetrySessionId =
        data.telemetry_id;

      activeTelemetryRunnerType =
        runnerType;

      activeTelemetryFeatureName =
        featureName;

      return data.telemetry_id;
    }

    function beginExecutionTelemetry(runnerType) {
      if (
        activeTelemetrySessionId
        || activeTelemetryStartPromise
      ) {
        return;
      }

      activeTelemetryStartPromise =
        startExecutionTelemetry(runnerType)
          .catch(error => {
            console.error(
              "Telemetry start error:",
              error
            );

            return null;
          })
          .finally(() => {
            activeTelemetryStartPromise = null;
          });
    }

    async function ensureTelemetrySession() {
      if (activeTelemetryStartPromise) {
        await activeTelemetryStartPromise;
      }

      return activeTelemetrySessionId;
    }

    async function recordExecutionTelemetry(
      stage,
      event,
      level,
      status,
      message,
      durationMs = null,
      metadata = {}
    ) {
      const sessionId =
        await ensureTelemetrySession();

      if (!sessionId) {
        return null;
      }

      try {
        const response = await fetch(
          "/telemetry/event",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              session_id: sessionId,
              stage,
              event,
              level,
              status,
              message,
              duration_ms: durationMs,
              metadata
            })
          }
        );

        const data = await response.json();

        if (!response.ok || !data.ok) {
          throw new Error(
            JSON.stringify(data)
          );
        }

        return data;

      } catch (error) {
        console.error(
          "Telemetry event error:",
          error
        );

        return null;
      }
    }

    function telemetryExecutionId(result) {
      if (!result || typeof result !== "object") {
        return null;
      }

      return (
        result.execution_id
        || result.run_id
        || (
          result.execution
          && result.execution.execution_id
        )
        || (
          result.result
          && result.result.execution_id
        )
        || null
      );
    }

    function telemetryStandardJsonPath(result) {
      if (!result || typeof result !== "object") {
        return null;
      }

      return (
        result.standard_json_path
        || (
          result.artifacts
          && result.artifacts.standard_json
        )
        || (
          result.result
          && result.result.standard_json_path
        )
        || null
      );
    }

    function telemetrySummary(result) {
      const source =
        result && typeof result === "object"
          ? result
          : {};

      const summary =
        source.summary
        && typeof source.summary === "object"
          ? source.summary
          : source;

      return {
        passed: Number(summary.passed || 0),
        failed: Number(summary.failed || 0),
        need_review: Number(
          summary.need_review || 0
        ),
        skipped: Number(summary.skipped || 0),
        warnings: Number(summary.warnings || 0),
        bugs_found: Number(
          summary.bugs_found || 0
        )
      };
    }

    function telemetryArtifactCount(result) {
      if (!result || typeof result !== "object") {
        return 0;
      }

      const candidates = [
        result.report_path,
        result.documentation_path,
        result.screenshot_path,
        result.error_log_path,
        result.spreadsheet_path,
        result.standard_json_path,
        result.analysis_path
      ];

      return candidates.filter(Boolean).length;
    }

    async function completeExecutionTelemetry(result) {
      const sessionId =
        await ensureTelemetrySession();

      if (!sessionId) {
        return null;
      }

      const status = String(
        result && result.status
          ? result.status
          : "UNKNOWN"
      ).toUpperCase();

      try {
        const response = await fetch(
          "/telemetry/complete",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              session_id: sessionId,
              execution_id:
                telemetryExecutionId(result),
              standard_json_path:
                telemetryStandardJsonPath(result),
              result_status: status,
              summary: telemetrySummary(result)
            })
          }
        );

        const data = await response.json();

        if (!response.ok || !data.ok) {
          throw new Error(
            JSON.stringify(data)
          );
        }

        return data;

      } catch (error) {
        console.error(
          "Telemetry completion error:",
          error
        );

        return null;

      } finally {
        activeTelemetrySessionId = null;
        activeTelemetryStartPromise = null;
        activeTelemetryRunnerType = null;
        activeTelemetryFeatureName = null;
      }
    }

'''

if "let activeTelemetrySessionId" not in text:
    marker = (
        "    function setAgentStep"
        "(step, status, label) {"
    )

    if marker not in text:
        raise RuntimeError(
            "setAgentStep function was not found"
        )

    text = text.replace(
        marker,
        telemetry_helpers + "\n" + marker,
        1,
    )

    print("Inserted telemetry UI helpers")
else:
    print("Telemetry UI helpers already exist")


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

if "beginExecutionTelemetry(typeLabel);" not in chunk:
    marker = (
        '      const typeLabel = '
        'runnerType || "QA Runner";'
    )

    replacement = marker + r'''

      beginExecutionTelemetry(typeLabel);

      recordExecutionTelemetry(
        "execution",
        "runner_requested",
        "info",
        "running",
        "QA runner execution was requested.",
        null,
        {
          runner_type: typeLabel,
          feature_name:
            telemetryFeatureName(typeLabel)
        }
      );
'''

    if marker not in chunk:
        raise RuntimeError(
            "startAgentFlow insertion marker not found"
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

    print("Patched startAgentFlow telemetry")
else:
    print("startAgentFlow already patched")


# ============================================================
# Patch completeAgentFlow
# ============================================================

found = find_function_block(
    text,
    "completeAgentFlow",
)

if not found:
    raise RuntimeError(
        "completeAgentFlow function not found"
    )

_, _, chunk = found

if '"runner_completed"' not in chunk:
    marker = (
        '      setAgentStep('
        '"report", "completed", "Generated");'
    )

    replacement = marker + r'''

      const telemetryLevel =
        status === "FAILED"
          ? "error"
          : status === "NEED REVIEW"
          ? "warning"
          : "info";

      recordExecutionTelemetry(
        "execution",
        "runner_completed",
        telemetryLevel,
        "completed",
        "QA runner returned status "
          + status
          + ".",
        null,
        telemetrySummary(result)
      );

      const artifactCount =
        telemetryArtifactCount(result);

      recordExecutionTelemetry(
        "evidence",
        "artifacts_detected",
        artifactCount > 0
          ? "info"
          : "warning",
        artifactCount > 0
          ? "completed"
          : "partial",
        artifactCount > 0
          ? artifactCount
            + " execution artifact(s) were detected."
          : "No execution artifact path was returned.",
        null,
        {
          artifact_count: artifactCount
        }
      );

      const hasReport = Boolean(
        result
        && (
          result.report_path
          || result.documentation_path
          || result.standard_json_path
        )
      );

      recordExecutionTelemetry(
        "report",
        "report_ready",
        hasReport ? "info" : "warning",
        hasReport ? "completed" : "partial",
        hasReport
          ? "Stored report or Standard JSON is available."
          : "No stored report path was returned."
      );
'''

    if marker not in chunk:
        raise RuntimeError(
            "completeAgentFlow insertion marker not found"
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

    print("Patched completeAgentFlow telemetry")
else:
    print("completeAgentFlow already patched")


# ============================================================
# Patch runAnalysisAgent
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

if '"analysis_started"' not in chunk:
    marker = (
        '      setAgentStep('
        '"analysis", "running", "Analyzing");'
    )

    replacement = marker + r'''

      await recordExecutionTelemetry(
        "analysis",
        "analysis_started",
        "info",
        "running",
        "Analysis Agent started processing "
          + "the execution result."
      );
'''

    if marker not in chunk:
        raise RuntimeError(
            "Analysis start marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print("Patched analysis_started event")


if '"analysis_completed"' not in chunk:
    marker = '''        return data;

      } catch (error) {'''

    replacement = '''        await recordExecutionTelemetry(
          "analysis",
          "analysis_completed",
          "info",
          "completed",
          "Analysis Agent completed with category "
            + (
              data.analysis
              && data.analysis.category
                ? data.analysis.category
                : "-"
            )
            + "."
        );

        await completeExecutionTelemetry(
          result
        );

        return data;

      } catch (error) {'''

    if marker not in chunk:
        raise RuntimeError(
            "Analysis success marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print("Patched analysis_completed event")


if '"analysis_failed"' not in chunk:
    marker = '''        console.error("Analysis Agent error:", error);
        return null;'''

    replacement = '''        console.error(
          "Analysis Agent error:",
          error
        );

        await recordExecutionTelemetry(
          "analysis",
          "analysis_failed",
          "error",
          "failed",
          "Analysis Agent failed: "
            + error.message
        );

        await completeExecutionTelemetry(
          result
        );

        return null;'''

    if marker not in chunk:
        raise RuntimeError(
            "Analysis failure marker not found"
        )

    chunk = chunk.replace(
        marker,
        replacement,
        1,
    )

    print("Patched analysis_failed event")


text = replace_function_block(
    text,
    "runAnalysisAgent",
    chunk,
)


# ============================================================
# Patch failAgentFlow
# ============================================================

found = find_function_block(
    text,
    "failAgentFlow",
)

if not found:
    raise RuntimeError(
        "failAgentFlow function not found"
    )

_, _, chunk = found

if '"dashboard_request_failed"' not in chunk:
    marker = (
        '      setAgentStep('
        '"execution", "failed", "Failed");'
    )

    replacement = marker + r'''

      recordExecutionTelemetry(
        "execution",
        "dashboard_request_failed",
        "error",
        "failed",
        "Dashboard runner request failed: "
          + errorMessage
      ).finally(() => {
        completeExecutionTelemetry({
          status: "FAILED"
        });
      });
'''

    if marker not in chunk:
        raise RuntimeError(
            "failAgentFlow insertion marker not found"
        )

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

    print("Patched failAgentFlow telemetry")
else:
    print("failAgentFlow already patched")


HTML_PATH.write_text(
    text,
    encoding="utf-8",
)

print(f"Backup created: {backup_path}")
