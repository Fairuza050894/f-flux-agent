import {
  HISTORY_COMPLETED_STATUSES,
  HISTORY_DEFAULT_FILTERS,
  HISTORY_FAILED_STATUSES,
  HISTORY_FILTER_ALL,
} from './historyConstants'
import {
  normalizeHistoryStatus,
  parseHistoryTimestamp,
} from './historyFormatters'
import {
  aggregateExecutionResults,
} from '../results/resultSelectors'

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function createLookup(items) {
  return new Map(
    toArray(items).map(
      (item) => [
        item.id,
        item,
      ],
    ),
  )
}

function clampPercentage(value) {
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

function getExecutionTimestamp(
  execution,
  fieldNames,
) {
  for (const fieldName of fieldNames) {
    const timestamp =
      parseHistoryTimestamp(
        execution?.[fieldName],
      )

    if (timestamp !== null) {
      return timestamp
    }
  }

  return null
}

function getExecutionStartTimestamp(
  execution,
) {
  return getExecutionTimestamp(
    execution,
    [
      'started_at',
      'startedAt',
      'created_at',
      'createdAt',
    ],
  )
}

function getExecutionEndTimestamp(
  execution,
) {
  return getExecutionTimestamp(
    execution,
    [
      'completed_at',
      'completedAt',
      'updated_at',
      'updatedAt',
    ],
  )
}

function getLatestExecutionTimestamp(
  executions,
) {
  const timestamps =
    toArray(executions)
      .flatMap(
        (execution) => [
          getExecutionEndTimestamp(
            execution,
          ),
          getExecutionStartTimestamp(
            execution,
          ),
        ],
      )
      .filter(
        (timestamp) =>
          timestamp !== null,
      )

  return timestamps.length > 0
    ? Math.max(...timestamps)
    : null
}

function getExecutionDuration(
  executions,
) {
  const executionList =
    toArray(executions)

  const startTimestamps =
    executionList
      .map(
        getExecutionStartTimestamp,
      )
      .filter(
        (timestamp) =>
          timestamp !== null,
      )

  const endTimestamps =
    executionList
      .map(
        getExecutionEndTimestamp,
      )
      .filter(
        (timestamp) =>
          timestamp !== null,
      )

  if (
    startTimestamps.length === 0 ||
    endTimestamps.length === 0
  ) {
    return null
  }

  const startedAt =
    Math.min(...startTimestamps)

  const endedAt =
    Math.max(...endTimestamps)

  return endedAt >= startedAt
    ? endedAt - startedAt
    : null
}

function getAverageProgress(
  executions,
) {
  const executionList =
    toArray(executions)

  if (executionList.length === 0) {
    return 0
  }

  const totalProgress =
    executionList.reduce(
      (total, execution) =>
        total +
        clampPercentage(
          execution?.progress,
        ),
      0,
    )

  return Math.round(
    totalProgress /
      executionList.length,
  )
}

function getCycleStatus(
  cycle,
  executions,
) {
  const cycleStatus =
    normalizeHistoryStatus(
      cycle?.status,
    )

  if (cycleStatus) {
    return cycleStatus
  }

  const statuses =
    toArray(executions).map(
      (execution) =>
        normalizeHistoryStatus(
          execution?.status,
        ),
    )

  if (
    statuses.some(
      (status) =>
        [
          'running',
          'in_progress',
          'processing',
        ].includes(status),
    )
  ) {
    return 'running'
  }

  if (
    statuses.some(
      (status) =>
        [
          'queued',
          'pending',
          'created',
          'not_started',
        ].includes(status),
    )
  ) {
    return 'queued'
  }

  if (
    statuses.some(
      (status) =>
        HISTORY_FAILED_STATUSES.includes(
          status,
        ),
    )
  ) {
    return 'failed'
  }

  if (
    statuses.includes(
      'need_review',
    )
  ) {
    return 'need_review'
  }

  if (
    statuses.length > 0 &&
    statuses.every(
      (status) =>
        status === 'passed',
    )
  ) {
    return 'passed'
  }

  return statuses.length > 0
    ? 'completed'
    : 'ready'
}

function buildHistorySearchText(
  row,
) {
  return [
    row.id,
    row.name,
    row.projectName,
    row.environmentName,
    row.cycleType,
    row.releaseVersion,
    row.module,
    row.feature,
    row.reference,
    ...row.runIds,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

export function buildHistoryRows({
  cycles = [],
  projects = [],
  environments = [],
} = {}) {
  const projectLookup =
    createLookup(projects)

  const environmentLookup =
    createLookup(environments)

  return toArray(cycles)
    .map((cycle) => {
      const executions =
        toArray(cycle.executions)

      const project =
        projectLookup.get(
          cycle.projectId,
        )

      const environment =
        environmentLookup.get(
          cycle.environmentId,
        )

      const latestExecutionTimestamp =
        getLatestExecutionTimestamp(
          executions,
        )

      const cycleUpdatedTimestamp =
        parseHistoryTimestamp(
          cycle.updatedAt,
        )

      const cycleCreatedTimestamp =
        parseHistoryTimestamp(
          cycle.createdAt,
        )

      const lastRunTimestamp =
        latestExecutionTimestamp ??
        cycleUpdatedTimestamp ??
        cycleCreatedTimestamp

      const results =
        aggregateExecutionResults(
          executions,
        )

      const row = {
        id: cycle.id,
        name:
          cycle.name ||
          'Untitled Test Cycle',
        projectId:
          cycle.projectId ?? '',
        projectName:
          project?.name ??
          'Unknown project',
        environmentId:
          cycle.environmentId ?? '',
        environmentName:
          environment?.name ??
          'Unknown environment',
        cycleType:
          cycle.cycleType ??
          'Not specified',
        releaseVersion:
          cycle.releaseVersion ?? '',
        module:
          cycle.module ?? '',
        feature:
          cycle.feature ?? '',
        reference:
          cycle.reference ?? '',
        status:
          getCycleStatus(
            cycle,
            executions,
          ),
        progress:
          cycle.progress ===
          undefined
            ? getAverageProgress(
                executions,
              )
            : clampPercentage(
                cycle.progress,
              ),
        executionCount:
          executions.length,
        runIds:
          executions
            .map(
              (execution) =>
                execution.runId ??
                execution.run_id,
            )
            .filter(Boolean),
        lastRunAt:
          lastRunTimestamp === null
            ? null
            : new Date(
                lastRunTimestamp,
              ).toISOString(),
        durationMs:
          getExecutionDuration(
            executions,
          ),
        results,
        createdAt:
          cycle.createdAt ?? null,
        updatedAt:
          cycle.updatedAt ?? null,
        sortTimestamp:
          lastRunTimestamp ?? 0,
      }

      return {
        ...row,
        searchText:
          buildHistorySearchText(
            row,
          ),
      }
    })
    .sort(
      (first, second) =>
        second.sortTimestamp -
        first.sortTimestamp,
    )
}

export function filterHistoryRows(
  rows,
  filters = HISTORY_DEFAULT_FILTERS,
) {
  const normalizedSearch =
    String(
      filters.search ?? '',
    )
      .trim()
      .toLowerCase()

  return toArray(rows).filter(
    (row) => {
      if (
        filters.projectId &&
        filters.projectId !==
          HISTORY_FILTER_ALL &&
        row.projectId !==
          filters.projectId
      ) {
        return false
      }

      if (
        filters.environmentId &&
        filters.environmentId !==
          HISTORY_FILTER_ALL &&
        row.environmentId !==
          filters.environmentId
      ) {
        return false
      }

      if (
        filters.cycleType &&
        filters.cycleType !==
          HISTORY_FILTER_ALL &&
        row.cycleType !==
          filters.cycleType
      ) {
        return false
      }

      if (
        filters.status &&
        filters.status !==
          HISTORY_FILTER_ALL &&
        row.status !==
          normalizeHistoryStatus(
            filters.status,
          )
      ) {
        return false
      }

      if (
        normalizedSearch &&
        !row.searchText.includes(
          normalizedSearch,
        )
      ) {
        return false
      }

      return true
    },
  )
}

export function summarizeHistoryRows(
  rows,
) {
  return toArray(rows).reduce(
    (summary, row) => {
      summary.total += 1

      if (
        HISTORY_COMPLETED_STATUSES.includes(
          row.status,
        )
      ) {
        summary.completed += 1
      }

      if (
        HISTORY_FAILED_STATUSES.includes(
          row.status,
        )
      ) {
        summary.failed += 1
      }

      if (
        row.status === 'need_review'
      ) {
        summary.needReview += 1
      }

      if (
        [
          'running',
          'in_progress',
          'processing',
        ].includes(row.status)
      ) {
        summary.running += 1
      }

      summary.passedTests +=
        row.results.passed

      summary.failedTests +=
        row.results.failed

      summary.reviewTests +=
        row.results.needReview

      return summary
    },
    {
      total: 0,
      completed: 0,
      failed: 0,
      needReview: 0,
      running: 0,
      passedTests: 0,
      failedTests: 0,
      reviewTests: 0,
    },
  )
}

export function selectHistoryEnvironments(
  environments,
  projectId,
) {
  const environmentList =
    toArray(environments)

  if (
    !projectId ||
    projectId === HISTORY_FILTER_ALL
  ) {
    return environmentList
  }

  return environmentList.filter(
    (environment) =>
      environment.projectId ===
      projectId,
  )
}
