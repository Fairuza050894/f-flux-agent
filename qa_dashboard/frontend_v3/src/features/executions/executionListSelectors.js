import {
  formatResultStatus,
  getResultStatusTone,
} from '../results/resultFormatters'

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

function getExecutionAliases(
  execution,
) {
  return [
    execution?.scopeKey,
    execution?.scope_key,
    execution?.testType,
    execution?.test_type,
    execution?.source,
  ]
    .filter(Boolean)
    .map(String)
}

function createExecutionLookup(
  executions,
) {
  const lookup = new Map()

  toArray(executions).forEach(
    (execution) => {
      getExecutionAliases(
        execution,
      ).forEach((alias) => {
        lookup.set(
          alias,
          execution,
        )
      })
    },
  )

  return lookup
}

function findScopeExecution(
  lookup,
  scope,
) {
  const aliases = [
    scope?.key,
    scope?.testType,
    scope?.source,
  ]
    .filter(Boolean)
    .map(String)

  for (const alias of aliases) {
    const execution =
      lookup.get(alias)

    if (execution) {
      return execution
    }
  }

  return null
}

function getExecutionRunId(
  execution,
) {
  return (
    execution?.runId ??
    execution?.run_id ??
    ''
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
  executions,
  selectedScopes,
}) {
  const executionLookup =
    createExecutionLookup(
      executions,
    )

  return toArray(
    selectedScopes,
  ).map((scope) => {
    const execution =
      findScopeExecution(
        executionLookup,
        scope,
      )

    const status =
      execution?.status ?? ''

    const currentStage =
      getExecutionStage(
        execution,
      )

    return {
      key: scope.key,

      scopeLabel:
        scope.label ??
        scope.key ??
        'Execution',

      runId:
        getExecutionRunId(
          execution,
        ) ||
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

export function buildExecutionListModel({
  dispatchableCount = 0,
  executions,
  isDispatching = false,
  selectedScopes,
} = {}) {
  return {
    dispatch:
      buildDispatchControl({
        dispatchableCount,
        isDispatching,
      }),

    rows:
      buildExecutionRows({
        executions,
        selectedScopes,
      }),
  }
}
