import {
  formatResultStatus,
  getResultStatusTone,
} from '../results/resultFormatters'
import {
  findLatestExecutionForScope,
  formatExecutionReason,
  getExecutionLineage,
  getExecutionRunId,
  isCancellableExecution,
  isFailedExecution,
  isRerunnableExecution,
  selectExecutionAttemptsForScope,
} from './executionAttemptSelectors'

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function clampProgress(value) {
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

function getExecutionStage(
  execution,
) {
  return (
    execution?.current_stage ??
    execution?.currentStage ??
    ''
  )
}

function buildExecutionRows({
  cancellingRunIds,
  executions,
  selectedScopes,
}) {
  return toArray(
    selectedScopes,
  ).map((scope) => {
    const attempts =
      selectExecutionAttemptsForScope(
        executions,
        scope,
      )

    const execution =
      findLatestExecutionForScope(
        executions,
        scope,
      )

    const status =
      execution?.status ?? ''

    const currentStage =
      getExecutionStage(
        execution,
      )

    const lineage =
      getExecutionLineage(
        execution,
      )

    const runId =
      getExecutionRunId(
        execution,
      )

    return {
      key: scope.key,

      scopeLabel:
        scope.label ??
        scope.key ??
        'Execution',

      runId:
        runId ||
        'Execution not created',

      stageLabel:
        currentStage
          ? formatResultStatus(
              currentStage,
            )
          : execution
            ? 'Waiting for runner'
            : (
                scope.runner ??
                'Runner not configured'
              ),

      progress:
        clampProgress(
          execution?.progress,
        ),

      statusLabel:
        execution
          ? formatResultStatus(
              status ||
              'not_started',
            )
          : 'Not Started',

      tone:
        execution
          ? getResultStatusTone(
              status ||
              'not_started',
            )
          : 'neutral',

      attemptCount:
        attempts.length,

      attemptNumber:
        execution
          ? lineage.attemptNumber
          : 0,

      executionReason:
        lineage.executionReason,

      executionReasonLabel:
        execution
          ? formatExecutionReason(
              lineage.executionReason,
            )
          : 'Not started',

      parentRunId:
        lineage.parentRunId,

      failed:
        Boolean(
          execution &&
          isFailedExecution(
            execution,
          ),
        ),

      selectable:
        Boolean(
          execution &&
          isRerunnableExecution(
            execution,
          ),
        ),

      cancelable:
        Boolean(
          execution &&
          isCancellableExecution(
            execution,
          ),
        ),

      isCancelling:
        Boolean(
          runId &&
          cancellingRunIds?.has?.(
            runId,
          ),
        ),
    }
  })
}

function buildDispatchControl({
  dispatchableCount,
  isDispatching,
}) {
  const hasDispatchableExecutions =
    Number(dispatchableCount) > 0

  return {
    buttonClassName: [
      'button',
      hasDispatchableExecutions
        ? 'button-primary'
        : 'button-secondary',
    ].join(' '),

    disabled:
      Boolean(isDispatching) ||
      !hasDispatchableExecutions,

    label:
      isDispatching
        ? 'Dispatching...'
        : hasDispatchableExecutions
          ? 'Run Queued Executions'
          : 'No Queued Executions',
  }
}

function buildRetryControl({
  failedScopeCount,
  isRetrying,
}) {
  const hasFailedScopes =
    Number(failedScopeCount) > 0

  return {
    disabled:
      Boolean(isRetrying) ||
      !hasFailedScopes,

    label:
      isRetrying
        ? 'Retrying...'
        : hasFailedScopes
          ? `Retry Failed (${failedScopeCount})`
          : 'No Failed Scopes',
  }
}

export function buildExecutionListModel({
  cancellingRunIds = new Set(),
  dispatchableCount = 0,
  executions,
  failedScopeCount = 0,
  isDispatching = false,
  isRerunning = false,
  isRetrying = false,
  selectedScopes,
} = {}) {
  const rows =
    buildExecutionRows({
      cancellingRunIds,
      executions,
      selectedScopes,
    })

  return {
    dispatch:
      buildDispatchControl({
        dispatchableCount,
        isDispatching,
      }),

    retry:
      buildRetryControl({
        failedScopeCount,
        isRetrying,
      }),

    rerun: {
      busy:
        Boolean(isRerunning),

      eligibleCount:
        rows.filter(
          (row) => row.selectable,
        ).length,
    },

    rows,
  }
}
