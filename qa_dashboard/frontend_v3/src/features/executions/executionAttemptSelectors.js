const failedStatuses = new Set([
  'failed',
  'error',
])

const rerunnableStatuses = new Set([
  'completed',
  'passed',
  'failed',
  'error',
  'need_review',
  'cancelled',
])

export function normalizeExecutionStatus(
  status,
) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll('-', '_')
    .replaceAll(' ', '_')
}

export function getExecutionRunId(
  execution,
) {
  return (
    execution?.runId ??
    execution?.run_id ??
    execution?.execution_id ??
    execution?.id ??
    ''
  )
}

export function getExecutionRequestSnapshot(
  execution,
) {
  const snapshot =
    execution?.requestSnapshot ??
    execution?.request_snapshot ??
    {}

  return (
    snapshot !== null &&
    typeof snapshot === 'object' &&
    !Array.isArray(snapshot)
  )
    ? snapshot
    : {}
}

export function getExecutionScopeKey(
  execution,
) {
  const snapshot =
    getExecutionRequestSnapshot(
      execution,
    )

  return String(
    execution?.scopeKey ??
    execution?.scope_key ??
    snapshot.scope_key ??
    execution?.testType ??
    execution?.test_type ??
    execution?.source ??
    '',
  ).trim()
}

export function executionMatchesScope(
  execution,
  scope,
) {
  const executionAliases = [
    getExecutionScopeKey(execution),
    execution?.scopeKey,
    execution?.scope_key,
    execution?.testType,
    execution?.test_type,
    execution?.source,
  ]
    .filter(Boolean)
    .map(String)

  const scopeAliases = [
    scope?.key,
    scope?.testType,
    scope?.source,
  ]
    .filter(Boolean)
    .map(String)

  return scopeAliases.some(
    (alias) =>
      executionAliases.includes(alias),
  )
}

export function selectExecutionAttemptsForScope(
  executions,
  scope,
) {
  return (
    Array.isArray(executions)
      ? executions
      : []
  ).filter(
    (execution) =>
      executionMatchesScope(
        execution,
        scope,
      ),
  )
}

export function findLatestExecutionForScope(
  executions,
  scope,
) {
  const attempts =
    selectExecutionAttemptsForScope(
      executions,
      scope,
    )

  return attempts.length > 0
    ? attempts[
        attempts.length - 1
      ]
    : null
}

export function selectLatestExecutionsByScope(
  executions,
) {
  const latestByScope =
    new Map()

  ;(
    Array.isArray(executions)
      ? executions
      : []
  ).forEach(
    (execution, index) => {
      const scopeKey =
        getExecutionScopeKey(
          execution,
        ) ||
        `execution-${index}`

      latestByScope.set(
        scopeKey,
        execution,
      )
    },
  )

  return Array.from(
    latestByScope.values(),
  )
}

export function getExecutionLineage(
  execution,
) {
  const snapshot =
    getExecutionRequestSnapshot(
      execution,
    )

  const attemptNumber =
    Number(
      execution?.attemptNumber ??
      execution?.attempt_number ??
      snapshot.attempt_number ??
      1,
    )

  return {
    attemptNumber:
      Number.isFinite(attemptNumber) &&
      attemptNumber > 0
        ? Math.round(attemptNumber)
        : 1,

    executionReason:
      String(
        execution?.executionReason ??
        execution?.execution_reason ??
        snapshot.execution_reason ??
        'initial',
      ),

    parentRunId:
      String(
        execution?.parentRunId ??
        execution?.parent_run_id ??
        snapshot.parent_run_id ??
        '',
      ),

    rootRunId:
      String(
        execution?.rootRunId ??
        execution?.root_run_id ??
        snapshot.root_run_id ??
        getExecutionRunId(
          execution,
        ),
      ),
  }
}

export function isFailedExecution(
  execution,
) {
  return failedStatuses.has(
    normalizeExecutionStatus(
      execution?.status,
    ),
  )
}

export function isRerunnableExecution(
  execution,
) {
  return rerunnableStatuses.has(
    normalizeExecutionStatus(
      execution?.status,
    ),
  )
}

export function formatExecutionReason(
  reason,
) {
  switch (
    String(reason ?? '')
  ) {
    case 'retry_failed_scope':
      return 'Retry'
    case 'rerun_selected_scope':
      return 'Selected rerun'
    case 'recreate_missing_run':
      return 'Recreated run'
    default:
      return 'Initial run'
  }
}
