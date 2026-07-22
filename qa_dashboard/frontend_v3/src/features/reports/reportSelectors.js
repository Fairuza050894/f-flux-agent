import {
  REPORT_DEFAULT_FILTERS,
  REPORT_FILTER_ALL,
} from './reportConstants'
import {
  parseReportTimestamp,
} from './reportFormatters'
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

function getLatestExecutionTimestamp(
  executions,
) {
  const timestamps =
    toArray(executions)
      .flatMap(
        (execution) => [
          parseReportTimestamp(
            execution.completedAt,
          ),
          parseReportTimestamp(
            execution.updatedAt,
          ),
          parseReportTimestamp(
            execution.startedAt,
          ),
          parseReportTimestamp(
            execution.createdAt,
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

function getQualityStatus(
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

function buildSearchText(row) {
  return [
    row.id,
    row.name,
    row.projectName,
    row.environmentName,
    row.cycleType,
    row.releaseVersion,
    row.module,
    row.feature,
    row.qualityStatus,
    ...row.runIds,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

export function buildReportRows({
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
      const model =
        buildCycleResultModel(
          cycle,
        )

      const project =
        projectLookup.get(
          model.projectId,
        )

      const environment =
        environmentLookup.get(
          model.environmentId,
        )

      const latestExecutionTimestamp =
        getLatestExecutionTimestamp(
          model.executions,
        )

      const fallbackTimestamp =
        parseReportTimestamp(
          model.updatedAt,
        ) ??
        parseReportTimestamp(
          model.createdAt,
        )

      const lastRunTimestamp =
        latestExecutionTimestamp ??
        fallbackTimestamp

      const row = {
        id: model.cycleId,
        name: model.cycleName,
        projectId:
          model.projectId,
        projectName:
          project?.name ??
          'Unknown project',
        environmentId:
          model.environmentId,
        environmentName:
          environment?.name ??
          'Unknown environment',
        cycleType:
          model.cycleType,
        releaseVersion:
          model.releaseVersion,
        module:
          model.module,
        feature:
          model.feature,
        cycleStatus:
          normalizeResultStatus(
            model.status,
          ),
        qualityStatus:
          getQualityStatus(
            model.totals,
          ),
        progress:
          model.progress,
        totals:
          model.totals,
        executions:
          model.executions,
        executionCount:
          model.executions.length,
        resultExecutionCount:
          model.resultExecutions.length,
        unsupportedExecutionCount:
          model.unsupportedExecutions.length,
        runIds:
          model.executions
            .map(
              (execution) =>
                execution.runId,
            )
            .filter(Boolean),
        lastRunAt:
          lastRunTimestamp === null
            ? null
            : new Date(
                lastRunTimestamp,
              ).toISOString(),
        sortTimestamp:
          lastRunTimestamp ?? 0,
      }

      return {
        ...row,
        searchText:
          buildSearchText(
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

function matchesReportPeriod(
  row,
  period,
  nowTimestamp,
) {
  if (
    !period ||
    period === REPORT_FILTER_ALL
  ) {
    return true
  }

  const periodDays =
    Number(period)

  if (
    !Number.isFinite(periodDays) ||
    periodDays <= 0
  ) {
    return true
  }

  if (!row.sortTimestamp) {
    return false
  }

  const rangeStart =
    nowTimestamp -
    periodDays *
      24 *
      60 *
      60 *
      1000

  return (
    row.sortTimestamp >= rangeStart
  )
}

export function filterReportRows(
  rows,
  filters = REPORT_DEFAULT_FILTERS,
  nowTimestamp = Date.now(),
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
          REPORT_FILTER_ALL &&
        row.projectId !==
          filters.projectId
      ) {
        return false
      }

      if (
        filters.environmentId &&
        filters.environmentId !==
          REPORT_FILTER_ALL &&
        row.environmentId !==
          filters.environmentId
      ) {
        return false
      }

      if (
        filters.cycleType &&
        filters.cycleType !==
          REPORT_FILTER_ALL &&
        row.cycleType !==
          filters.cycleType
      ) {
        return false
      }

      if (
        filters.qualityStatus &&
        filters.qualityStatus !==
          REPORT_FILTER_ALL &&
        row.qualityStatus !==
          filters.qualityStatus
      ) {
        return false
      }

      if (
        !matchesReportPeriod(
          row,
          filters.period,
          nowTimestamp,
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

export function summarizeReportRows(
  rows,
) {
  const summary =
    toArray(rows).reduce(
      (totals, row) => {
        totals.cycleCount += 1

        totals.executionCount +=
          row.executionCount

        totals.resultExecutionCount +=
          row.resultExecutionCount

        totals.unsupportedExecutionCount +=
          row.unsupportedExecutionCount

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

        return totals
      },
      {
        cycleCount: 0,
        executionCount: 0,
        resultExecutionCount: 0,
        unsupportedExecutionCount: 0,
        passed: 0,
        failed: 0,
        needReview: 0,
        skipped: 0,
        blocked: 0,
        bugsFound: 0,
        warnings: 0,
      },
    )

  const totalExecuted =
    summary.passed +
    summary.failed +
    summary.needReview

  return {
    ...summary,
    totalExecuted,
    passRate:
      calculatePassRate(
        summary,
      ),
  }
}

function createEmptyScopeRow(
  execution,
) {
  return {
    key:
      execution.scopeKey ??
      execution.scopeLabel,
    label:
      execution.scopeLabel,
    executionCount: 0,
    resultExecutionCount: 0,
    unsupportedExecutionCount: 0,
    passed: 0,
    failed: 0,
    needReview: 0,
    skipped: 0,
    blocked: 0,
    bugsFound: 0,
    warnings: 0,
  }
}

export function buildScopeBreakdown(
  rows,
) {
  const scopeLookup =
    new Map()

  toArray(rows).forEach(
    (row) => {
      row.executions.forEach(
        (execution) => {
          const key =
            execution.scopeKey ??
            execution.scopeLabel

          const current =
            scopeLookup.get(key) ??
            createEmptyScopeRow(
              execution,
            )

          current.executionCount += 1

          if (execution.hasResult) {
            current.resultExecutionCount += 1
          }

          if (execution.unsupported) {
            current.unsupportedExecutionCount += 1
          }

          current.passed +=
            execution.metrics.passed

          current.failed +=
            execution.metrics.failed

          current.needReview +=
            execution.metrics.needReview

          current.skipped +=
            execution.metrics.skipped

          current.blocked +=
            execution.metrics.blocked

          current.bugsFound +=
            execution.metrics.bugsFound

          current.warnings +=
            execution.metrics.warnings

          scopeLookup.set(
            key,
            current,
          )
        },
      )
    },
  )

  return Array.from(
    scopeLookup.values(),
  )
    .map((scope) => {
      const totalExecuted =
        scope.passed +
        scope.failed +
        scope.needReview

      const qualityStatus =
        getQualityStatus({
          ...scope,
          totalExecuted,
          totalObserved:
            totalExecuted +
            scope.skipped +
            scope.blocked,
        })

      return {
        ...scope,
        totalExecuted,
        qualityStatus,
        passRate:
          calculatePassRate(
            scope,
          ),
      }
    })
    .sort(
      (first, second) =>
        second.failed -
          first.failed ||
        second.needReview -
          first.needReview ||
        second.passed -
          first.passed ||
        first.label.localeCompare(
          second.label,
        ),
    )
}

export function selectReportEnvironments(
  environments,
  projectId,
) {
  const environmentList =
    toArray(environments)

  if (
    !projectId ||
    projectId === REPORT_FILTER_ALL
  ) {
    return environmentList
  }

  return environmentList.filter(
    (environment) =>
      environment.projectId ===
      projectId,
  )
}
