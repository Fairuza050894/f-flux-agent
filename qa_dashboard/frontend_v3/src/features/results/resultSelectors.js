import {
  EMPTY_RESULT_METRICS,
  RESULT_METRIC_ALIASES,
  RESULT_TERMINAL_STATUSES,
  RESULT_UNSUPPORTED_STATUSES,
} from './resultConstants'
import {
  calculatePassRate,
  clampResultPercentage,
  getResultStatusTone,
  normalizeResultCount,
  normalizeResultStatus,
} from './resultFormatters'
import {
  selectLatestExecutionsByScope,
} from '../executions/executionAttemptSelectors'

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function isObjectRecord(value) {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value)
  )
}

function firstNonEmptyValue(
  values,
  fallback = '',
) {
  const value = values.find(
    (candidate) =>
      candidate !== null &&
      candidate !== undefined &&
      String(candidate).trim() !== '',
  )

  return value ?? fallback
}

export function getExecutionResultSummary(
  execution,
) {
  const summary =
    execution?.result_summary ??
    execution?.resultSummary ??
    execution?.result ??
    null

  return isObjectRecord(summary)
    ? summary
    : {}
}

export function getExecutionResultSources(
  execution,
) {
  const summary =
    getExecutionResultSummary(
      execution,
    )

  return [
    summary.metrics,
    summary.summary,
    summary,
    execution,
  ].filter(isObjectRecord)
}

export function getExecutionMetric(
  execution,
  metricKey,
) {
  const aliases =
    RESULT_METRIC_ALIASES[
      metricKey
    ] ?? [metricKey]

  const sources =
    getExecutionResultSources(
      execution,
    )

  for (const source of sources) {
    for (const alias of aliases) {
      const value =
        Number(source[alias])

      if (Number.isFinite(value)) {
        return normalizeResultCount(
          value,
        )
      }
    }
  }

  return 0
}

export function getExecutionMetrics(
  execution,
) {
  return Object.keys(
    RESULT_METRIC_ALIASES,
  ).reduce(
    (metrics, metricKey) => ({
      ...metrics,
      [metricKey]:
        getExecutionMetric(
          execution,
          metricKey,
        ),
    }),
    {
      ...EMPTY_RESULT_METRICS,
    },
  )
}

export function hasExecutionResult(
  execution,
) {
  const status =
    normalizeResultStatus(
      execution?.status,
    )

  if (
    RESULT_UNSUPPORTED_STATUSES.includes(
      status,
    )
  ) {
    return false
  }

  if (
    RESULT_TERMINAL_STATUSES.includes(
      status,
    )
  ) {
    return true
  }

  const summary =
    getExecutionResultSummary(
      execution,
    )

  const testingSummary =
    String(
      summary.testing_summary ??
      summary.testingSummary ??
      '',
    ).trim()

  if (testingSummary) {
    return true
  }

  const metrics =
    getExecutionMetrics(
      execution,
    )

  return (
    metrics.passed +
    metrics.failed +
    metrics.needReview +
    metrics.skipped +
    metrics.blocked +
    metrics.bugsFound +
    metrics.warnings
  ) > 0
}

export function isUnsupportedExecution(
  execution,
) {
  return (
    RESULT_UNSUPPORTED_STATUSES.includes(
      normalizeResultStatus(
        execution?.status,
      ),
    )
  )
}

export function normalizeExecutionResult(
  execution,
  cycle = {},
) {
  const summary =
    getExecutionResultSummary(
      execution,
    )

  const status =
    normalizeResultStatus(
      execution?.status,
    )

  const metrics =
    getExecutionMetrics(
      execution,
    )

  const runId =
    execution?.runId ??
    execution?.run_id ??
    execution?.execution_id ??
    execution?.id ??
    null

  const testingSummary =
    String(
      summary.testing_summary ??
      summary.testingSummary ??
      '',
    ).trim()

  return {
    runId,

    scopeKey:
      execution?.scopeKey ??
      execution?.scope_key ??
      null,

    scopeLabel:
      firstNonEmptyValue(
        [
          execution?.scopeLabel,
          execution?.scope_label,
          execution?.source,
          execution?.scope,
        ],
        'Execution',
      ),

    runner:
      firstNonEmptyValue(
        [
          execution?.runner,
          execution?.runner_name,
          execution?.runnerName,
        ],
        'Hermes QA Runner',
      ),

    moduleName:
      firstNonEmptyValue(
        [
          summary.module_name,
          summary.moduleName,
          cycle.module,
        ],
        'Not specified',
      ),

    mode:
      firstNonEmptyValue(
        [
          summary.mode,
          execution?.testType,
          execution?.test_type,
        ],
        'Not specified',
      ),

    status,
    tone:
      getResultStatusTone(
        status,
      ),

    progress:
      clampResultPercentage(
        execution?.progress,
      ),

    currentStage:
      execution?.current_stage ??
      execution?.currentStage ??
      '',

    currentStep:
      execution?.current_step ??
      execution?.currentStep ??
      '',

    completedAt:
      execution?.completed_at ??
      execution?.completedAt ??
      execution?.updated_at ??
      execution?.updatedAt ??
      null,

    testingSummary,
    metrics,

    hasResult:
      hasExecutionResult(
        execution,
      ),

    unsupported:
      isUnsupportedExecution(
        execution,
      ),
  }
}

export function aggregateExecutionResults(
  executions,
) {
  const executionList =
    toArray(executions)

  const resultExecutions =
    executionList.filter(
      hasExecutionResult,
    )

  const unsupportedExecutions =
    executionList.filter(
      isUnsupportedExecution,
    )

  const metrics =
    resultExecutions.reduce(
      (totals, execution) => {
        const executionMetrics =
          getExecutionMetrics(
            execution,
          )

        return {
          passed:
            totals.passed +
            executionMetrics.passed,

          failed:
            totals.failed +
            executionMetrics.failed,

          needReview:
            totals.needReview +
            executionMetrics.needReview,

          skipped:
            totals.skipped +
            executionMetrics.skipped,

          blocked:
            totals.blocked +
            executionMetrics.blocked,

          bugsFound:
            totals.bugsFound +
            executionMetrics.bugsFound,

          warnings:
            totals.warnings +
            executionMetrics.warnings,
        }
      },
      {
        ...EMPTY_RESULT_METRICS,
      },
    )

  const totalExecuted =
    metrics.passed +
    metrics.failed +
    metrics.needReview

  const totalObserved =
    totalExecuted +
    metrics.skipped +
    metrics.blocked

  return {
    ...metrics,
    totalExecuted,
    totalObserved,

    passRate:
      calculatePassRate(
        metrics,
      ),

    resultExecutionCount:
      resultExecutions.length,

    unsupportedExecutionCount:
      unsupportedExecutions.length,
  }
}

export function buildCycleResultModel(
  cycle,
) {
  const allExecutions =
    toArray(
      cycle?.executions,
    )

  const executions =
    selectLatestExecutionsByScope(
      allExecutions,
    )

  const normalizedExecutions =
    executions.map(
      (execution) =>
        normalizeExecutionResult(
          execution,
          cycle,
        ),
    )

  return {
    cycleId:
      cycle?.id ?? null,

    cycleName:
      cycle?.name ??
      'Untitled Test Cycle',

    projectId:
      cycle?.projectId ?? '',

    environmentId:
      cycle?.environmentId ?? '',

    cycleType:
      cycle?.cycleType ??
      'Not specified',

    releaseVersion:
      cycle?.releaseVersion ?? '',

    module:
      cycle?.module ?? '',

    feature:
      cycle?.feature ?? '',

    status:
      normalizeResultStatus(
        cycle?.status,
      ),

    progress:
      clampResultPercentage(
        cycle?.progress,
      ),

    createdAt:
      cycle?.createdAt ?? null,

    updatedAt:
      cycle?.updatedAt ?? null,

    executions:
      normalizedExecutions,

    executionAttemptCount:
      allExecutions.length,

    resultExecutions:
      normalizedExecutions.filter(
        (execution) =>
          execution.hasResult,
      ),

    unsupportedExecutions:
      normalizedExecutions.filter(
        (execution) =>
          execution.unsupported,
      ),

    totals:
      aggregateExecutionResults(
        executions,
      ),
  }
}
