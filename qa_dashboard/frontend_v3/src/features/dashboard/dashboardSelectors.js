import {
  DASHBOARD_ACTIVE_STATUSES,
  DASHBOARD_RECENT_CYCLE_LIMIT,
  DASHBOARD_TERMINAL_STATUSES,
} from './dashboardConstants'
import {
  isSameLocalDay,
  parseDashboardTimestamp,
} from './dashboardFormatters'
import {
  buildCycleResultModel,
} from '../results/resultSelectors'
import {
  calculatePassRate,
  normalizeResultStatus,
} from '../results/resultFormatters'

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

function getExecutionTimestamp(
  execution,
) {
  const timestampFields = [
    'completed_at',
    'completedAt',
    'updated_at',
    'updatedAt',
    'started_at',
    'startedAt',
    'created_at',
    'createdAt',
  ]

  for (
    const fieldName
    of timestampFields
  ) {
    const timestamp =
      parseDashboardTimestamp(
        execution?.[fieldName],
      )

    if (timestamp !== null) {
      return timestamp
    }
  }

  return null
}

function getLatestCycleTimestamp(
  cycle,
) {
  const executionTimestamps =
    toArray(cycle?.executions)
      .map(getExecutionTimestamp)
      .filter(
        (timestamp) =>
          timestamp !== null,
      )

  const cycleUpdatedTimestamp =
    parseDashboardTimestamp(
      cycle?.updatedAt,
    )

  const cycleCreatedTimestamp =
    parseDashboardTimestamp(
      cycle?.createdAt,
    )

  return [
    ...executionTimestamps,
    cycleUpdatedTimestamp,
    cycleCreatedTimestamp,
  ]
    .filter(
      (timestamp) =>
        timestamp !== null,
    )
    .reduce(
      (latest, timestamp) =>
        Math.max(
          latest,
          timestamp,
        ),
      0,
    )
}

function getCycleQualityStatus(
  totals,
) {
  if (
    totals.totalExecuted === 0 &&
    totals.totalObserved === 0
  ) {
    return 'no_results'
  }

  if (totals.failed > 0) {
    return 'failed'
  }

  if (totals.needReview > 0) {
    return 'need_review'
  }

  return 'passed'
}

function getConfiguredStatus(
  value,
) {
  return String(value ?? '').trim() &&
    String(value).trim() !==
      'Not configured'
    ? 'Configured'
    : 'Not configured'
}

export function buildDashboardCycleRows({
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
      const resultModel =
        buildCycleResultModel(
          cycle,
        )

      const project =
        projectLookup.get(
          cycle.projectId,
        )

      const environment =
        environmentLookup.get(
          cycle.environmentId,
        )

      const status =
        normalizeResultStatus(
          cycle.status,
        ) || 'ready'

      const qualityStatus =
        getCycleQualityStatus(
          resultModel.totals,
        )

      const lastActivityTimestamp =
        getLatestCycleTimestamp(
          cycle,
        )

      return {
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

        status,
        qualityStatus,

        progress:
          resultModel.progress,

        executions:
          resultModel.executions,

        executionCount:
          resultModel.executions.length,

        resultExecutionCount:
          resultModel
            .resultExecutions
            .length,

        unsupportedExecutionCount:
          resultModel
            .unsupportedExecutions
            .length,

        totals:
          resultModel.totals,

        executionError:
          String(
            cycle.executionError ??
            '',
          ).trim(),

        active:
          DASHBOARD_ACTIVE_STATUSES
            .includes(status),

        terminal:
          DASHBOARD_TERMINAL_STATUSES
            .includes(status),

        lastActivityTimestamp,

        lastActivityAt:
          lastActivityTimestamp
            ? new Date(
                lastActivityTimestamp,
              ).toISOString()
            : null,
      }
    })
    .sort(
      (first, second) =>
        second.lastActivityTimestamp -
        first.lastActivityTimestamp,
    )
}

export function summarizeDashboardRows(
  rows,
  nowTimestamp = Date.now(),
) {
  const summary =
    toArray(rows).reduce(
      (totals, row) => {
        totals.cycleCount += 1

        totals.executionCount +=
          row.executionCount

        if (row.active) {
          totals.activeCycles += 1
        }

        if (
          row.terminal &&
          isSameLocalDay(
            row.lastActivityTimestamp,
            nowTimestamp,
          )
        ) {
          totals.completedToday += 1
        }

        totals.passed +=
          row.totals.passed

        totals.failed +=
          row.totals.failed

        totals.needReview +=
          row.totals.needReview

        totals.skipped +=
          row.totals.skipped

        totals.blocked +=
          row.totals.blocked

        totals.bugsFound +=
          row.totals.bugsFound

        totals.warnings +=
          row.totals.warnings

        totals.unsupportedExecutions +=
          row.unsupportedExecutionCount

        if (row.executionError) {
          totals.executionErrors += 1
        }

        return totals
      },
      {
        cycleCount: 0,
        executionCount: 0,
        activeCycles: 0,
        completedToday: 0,
        passed: 0,
        failed: 0,
        needReview: 0,
        skipped: 0,
        blocked: 0,
        bugsFound: 0,
        warnings: 0,
        unsupportedExecutions: 0,
        executionErrors: 0,
      },
    )

  const totalExecuted =
    summary.passed +
    summary.failed +
    summary.needReview

  const needAttention =
    summary.failed +
    summary.needReview +
    summary.bugsFound +
    summary.unsupportedExecutions +
    summary.executionErrors

  return {
    ...summary,

    totalExecuted,
    needAttention,

    passRate:
      calculatePassRate(
        summary,
      ),
  }
}

export function selectPrimaryDashboardCycle(
  rows,
) {
  const rowList =
    toArray(rows)

  return (
    rowList.find(
      (row) => row.active,
    ) ??
    rowList[0] ??
    null
  )
}

export function selectRecentDashboardCycles(
  rows,
  limit =
    DASHBOARD_RECENT_CYCLE_LIMIT,
) {
  return toArray(rows).slice(
    0,
    Math.max(
      0,
      Number(limit) || 0,
    ),
  )
}

export function selectDashboardEnvironment({
  projects = [],
  environments = [],
  selectedProjectId,
  selectedEnvironmentId,
} = {}) {
  const projectList =
    toArray(projects)

  const environmentList =
    toArray(environments)

  const project =
    projectList.find(
      (item) =>
        item.id ===
        selectedProjectId,
    ) ??
    projectList[0] ??
    null

  const environment =
    environmentList.find(
      (item) =>
        item.id ===
        selectedEnvironmentId,
    ) ??
    environmentList.find(
      (item) =>
        item.projectId ===
        project?.id,
    ) ??
    null

  if (!project && !environment) {
    return null
  }

  return {
    project,
    environment,

    webConfigurationStatus:
      getConfiguredStatus(
        environment?.webBaseUrl,
      ),

    apiConfigurationStatus:
      getConfiguredStatus(
        environment?.apiBaseUrl,
      ),

    credentialStatus:
      getConfiguredStatus(
        environment
          ?.credentialReference,
      ),
  }
}

export function buildDashboardQualityRows(
  summary,
) {
  const totalObserved =
    summary.passed +
    summary.failed +
    summary.needReview +
    summary.skipped +
    summary.blocked

  function createRow(
    key,
    label,
    value,
    tone,
  ) {
    return {
      key,
      label,
      value,
      tone,

      percentage:
        totalObserved > 0
          ? Math.round(
              (
                value /
                totalObserved
              ) * 100,
            )
          : 0,
    }
  }

  return [
    createRow(
      'passed',
      'Passed',
      summary.passed,
      'success',
    ),

    createRow(
      'failed',
      'Failed',
      summary.failed,
      'danger',
    ),

    createRow(
      'need-review',
      'Need Review',
      summary.needReview,
      'warning',
    ),

    createRow(
      'skipped',
      'Skipped',
      summary.skipped,
      'neutral',
    ),

    createRow(
      'blocked',
      'Blocked',
      summary.blocked,
      'neutral',
    ),
  ]
}

export function buildDashboardAttentionRows(
  summary,
) {
  return [
    {
      key: 'failed',
      label: 'Failed tests',
      description:
        'Automated checks that did not pass.',
      value: summary.failed,
      tone: 'danger',
    },

    {
      key: 'review',
      label: 'Need review',
      description:
        'Results waiting for manual verification.',
      value:
        summary.needReview,
      tone: 'warning',
    },

    {
      key: 'bugs',
      label: 'Bugs found',
      description:
        'Bugs reported by supported runners.',
      value:
        summary.bugsFound,
      tone: 'danger',
    },

    {
      key: 'unsupported',
      label: 'Unsupported runners',
      description:
        'Execution scopes not implemented in the current runner.',
      value:
        summary.unsupportedExecutions,
      tone: 'neutral',
    },

    {
      key: 'execution-errors',
      label: 'Execution errors',
      description:
        'Test Cycles with recorded execution errors.',
      value:
        summary.executionErrors,
      tone: 'danger',
    },
  ]
}
