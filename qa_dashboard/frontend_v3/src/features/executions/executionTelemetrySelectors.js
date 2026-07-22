import {
  formatResultStatus,
  getResultStatusTone,
  normalizeResultStatus,
} from '../results/resultFormatters'

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function formatExecutionValue(
  value,
) {
  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return ''
  }

  if (typeof value === 'string') {
    return value
  }

  if (
    typeof value?.message ===
    'string'
  ) {
    return value.message
  }

  try {
    return JSON.stringify(
      value,
      null,
      2,
    )
  } catch {
    return String(value)
  }
}

function clampExecutionProgress(
  value,
) {
  const numericValue =
    Number(value)

  if (!Number.isFinite(numericValue)) {
    return 0
  }

  return Math.round(
    Math.min(
      100,
      Math.max(
        0,
        numericValue,
      ),
    ),
  )
}

function getExecutionErrorMessage(
  execution,
) {
  return formatExecutionValue(
    execution?.error_message ??
      execution?.errorMessage ??
      execution?.failure_reason ??
      execution?.failureReason ??
      execution?.error ??
      null,
  )
}

function getExecutionRunnerMessage(
  execution,
) {
  return formatExecutionValue(
    execution?.runner_message ??
      execution?.runnerMessage ??
      execution?.message ??
      execution?.detail ??
      null,
  )
}

function getExecutionLastTimestamp(
  execution,
) {
  return (
    execution?.completed_at ??
    execution?.completedAt ??
    execution?.updated_at ??
    execution?.updatedAt ??
    execution?.started_at ??
    execution?.startedAt ??
    execution?.created_at ??
    execution?.createdAt ??
    null
  )
}

export function buildExecutionTelemetryRows(
  executions,
) {
  return toArray(executions).map(
    (execution, index) => {
      const runId =
        execution?.runId ??
        execution?.run_id ??
        ''

      const scopeLabel =
        execution?.scopeLabel ??
        execution?.scope_label ??
        execution?.scope ??
        execution?.source ??
        'Execution'

      const status =
        normalizeResultStatus(
          execution?.status,
        )

      const currentStage =
        execution?.current_stage ??
        execution?.currentStage ??
        ''

      const currentStep =
        execution?.current_step ??
        execution?.currentStep ??
        ''

      return {
        key:
          runId ||
          [
            scopeLabel,
            index,
          ].join('-'),

        runId:
          runId ||
          'Not available',

        scopeLabel,

        status,
        statusLabel:
          formatResultStatus(
            status,
          ),

        tone:
          getResultStatusTone(
            status,
          ),

        stageLabel:
          currentStage
            ? formatResultStatus(
                currentStage,
              )
            : 'Not reported',

        currentStepLabel:
          currentStep
            ? formatResultStatus(
                currentStep,
              )
            : 'Not reported',

        progress:
          clampExecutionProgress(
            execution?.progress,
          ),

        lastTimestamp:
          getExecutionLastTimestamp(
            execution,
          ),

        errorMessage:
          getExecutionErrorMessage(
            execution,
          ),

        runnerMessage:
          getExecutionRunnerMessage(
            execution,
          ),
      }
    },
  )
}
