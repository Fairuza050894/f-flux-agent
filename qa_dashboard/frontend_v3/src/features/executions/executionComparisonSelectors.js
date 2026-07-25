import {
  formatExecutionReason,
  getExecutionLineage,
  getExecutionRequestSnapshot,
  getExecutionRunId,
  getExecutionScopeKey,
  getExecutionTargetAssetIds,
  getExecutionTargetAssetSnapshots,
  selectExecutionAttemptsForScope,
} from './executionAttemptSelectors'
import {
  getExecutionMetrics,
  getExecutionResultSummary,
  hasExecutionResult,
} from '../results/resultSelectors'
import {
  formatResultStatus,
  getResultStatusTone,
  normalizeResultStatus,
} from '../results/resultFormatters'

function toArray(
  value,
) {
  return Array.isArray(value)
    ? value
    : []
}

function parseTimestamp(
  value,
) {
  if (!value) {
    return null
  }

  const parsed =
    new Date(value).getTime()

  return Number.isFinite(parsed)
    ? parsed
    : null
}

function getExecutionTimestamp(
  execution,
  field,
) {
  const aliases = {
    createdAt: [
      'createdAt',
      'created_at',
    ],
    startedAt: [
      'startedAt',
      'started_at',
    ],
    completedAt: [
      'completedAt',
      'completed_at',
      'updatedAt',
      'updated_at',
    ],
  }

  return (
    aliases[field] ?? []
  )
    .map(
      (alias) =>
        execution?.[alias],
    )
    .find(Boolean) ?? null
}

function getDurationMs(
  execution,
) {
  const startedAt =
    parseTimestamp(
      getExecutionTimestamp(
        execution,
        'startedAt',
      ) ??
      getExecutionTimestamp(
        execution,
        'createdAt',
      ),
    )

  const completedAt =
    parseTimestamp(
      getExecutionTimestamp(
        execution,
        'completedAt',
      ),
    )

  if (
    startedAt === null ||
    completedAt === null ||
    completedAt < startedAt
  ) {
    return null
  }

  return completedAt - startedAt
}

export function formatExecutionDuration(
  durationMs,
) {
  if (
    durationMs === null ||
    durationMs === undefined
  ) {
    return 'Not available'
  }

  const seconds =
    Math.max(
      0,
      Math.round(
        durationMs / 1000,
      ),
    )

  if (seconds < 60) {
    return `${seconds}s`
  }

  const minutes =
    Math.floor(seconds / 60)

  const remainingSeconds =
    seconds % 60

  if (minutes < 60) {
    return (
      remainingSeconds > 0
        ? `${minutes}m ${remainingSeconds}s`
        : `${minutes}m`
    )
  }

  const hours =
    Math.floor(minutes / 60)

  const remainingMinutes =
    minutes % 60

  return (
    remainingMinutes > 0
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h`
  )
}

function normalizeCaseStatus(
  status,
) {
  const normalized =
    normalizeResultStatus(
      status,
    )

  if (
    [
      'fail',
      'failed',
      'error',
    ].includes(normalized)
  ) {
    return 'failed'
  }

  if (
    [
      'need_review',
      'review',
      'needs_review',
    ].includes(normalized)
  ) {
    return 'need_review'
  }

  if (
    [
      'pass',
      'passed',
      'success',
    ].includes(normalized)
  ) {
    return 'passed'
  }

  return normalized || 'unknown'
}

function getStructuredCases(
  execution,
) {
  const summary =
    getExecutionResultSummary(
      execution,
    )

  const values =
    summary.test_cases ??
    summary.testCases ??
    summary.targeted_test_cases ??
    summary.targetedTestCases ??
    []

  return toArray(values)
    .filter(
      (record) =>
        record &&
        typeof record ===
          'object',
    )
    .map(
      (record, index) => {
        const id =
          String(
            record.id ??
            record.test_case_id ??
            record.testCaseId ??
            `case-${index + 1}`,
          ).trim()

        const scenario =
          String(
            record.scenario ??
            record.name ??
            record.title ??
            id,
          ).trim()

        return {
          id,
          key:
            id || scenario,

          scenario,

          status:
            normalizeCaseStatus(
              record.status,
            ),
        }
      },
    )
}

function buildFailureMap(
  execution,
) {
  return new Map(
    getStructuredCases(
      execution,
    )
      .filter(
        (record) =>
          record.status ===
          'failed',
      )
      .map(
        (record) => [
          record.key,
          record,
        ],
      ),
  )
}

function haveSameTargetSet(
  baseline,
  candidate,
) {
  const baselineIds =
    getExecutionTargetAssetIds(
      baseline,
    ).sort()

  const candidateIds =
    getExecutionTargetAssetIds(
      candidate,
    ).sort()

  return (
    baselineIds.length ===
      candidateIds.length &&
    baselineIds.every(
      (assetId, index) =>
        assetId ===
        candidateIds[index],
    )
  )
}

function buildFailureDelta(
  baseline,
  candidate,
) {
  const sameTargetSet =
    haveSameTargetSet(
      baseline,
      candidate,
    )

  const baselineCases =
    getStructuredCases(
      baseline,
    )

  const candidateCases =
    getStructuredCases(
      candidate,
    )

  const baselineFailures =
    buildFailureMap(
      baseline,
    )

  const candidateFailures =
    buildFailureMap(
      candidate,
    )

  const newFailures = []
  const resolvedFailures = []
  const unchangedFailures = []

  candidateFailures.forEach(
    (record, key) => {
      if (
        baselineFailures.has(
          key,
        )
      ) {
        unchangedFailures.push(
          record,
        )
      } else {
        newFailures.push(
          record,
        )
      }
    },
  )

  baselineFailures.forEach(
    (record, key) => {
      if (
        !candidateFailures.has(
          key,
        )
      ) {
        resolvedFailures.push(
          record,
        )
      }
    },
  )

  return {
    available:
      sameTargetSet &&
      baselineCases.length > 0 &&
      candidateCases.length > 0,

    reason:
      !sameTargetSet
        ? 'Target asset sets differ between the selected executions.'
        : (
            baselineCases.length === 0 ||
            candidateCases.length === 0
              ? 'Structured test-case results are not available for both executions.'
              : ''
          ),

    newFailures,
    resolvedFailures,
    unchangedFailures,
  }
}

function normalizeVersionMap(
  execution,
) {
  return new Map(
    getExecutionTargetAssetSnapshots(
      execution,
    ).map(
      (record) => [
        record.assetId,
        record.versionId ??
        record.versionNumber ??
        '',
      ],
    ),
  )
}

function buildAssetVersionDelta(
  baseline,
  candidate,
) {
  const baselineVersions =
    normalizeVersionMap(
      baseline,
    )

  const candidateVersions =
    normalizeVersionMap(
      candidate,
    )

  const changedAssetIds = []

  candidateVersions.forEach(
    (version, assetId) => {
      if (
        baselineVersions.has(
          assetId,
        ) &&
        baselineVersions.get(
          assetId,
        ) !== version
      ) {
        changedAssetIds.push(
          assetId,
        )
      }
    },
  )

  return {
    changedAssetIds,

    candidateTargetCount:
      getExecutionTargetAssetIds(
        candidate,
      ).length,

    baselineTargetCount:
      getExecutionTargetAssetIds(
        baseline,
      ).length,
  }
}

function buildAttemptOption(
  execution,
) {
  const lineage =
    getExecutionLineage(
      execution,
    )

  const runId =
    getExecutionRunId(
      execution,
    )

  const targetCount =
    getExecutionTargetAssetIds(
      execution,
    ).length

  return {
    attemptNumber:
      lineage.attemptNumber,

    completedAt:
      getExecutionTimestamp(
        execution,
        'completedAt',
      ),

    execution,

    label: [
      `Attempt ${lineage.attemptNumber}`,
      formatExecutionReason(
        lineage.executionReason,
      ),
      targetCount > 0
        ? `${targetCount} targeted assets`
        : 'Full scope',
    ].join(' · '),

    reason:
      lineage.executionReason,

    runId,

    status:
      execution?.status ??
      'unknown',

    targetCount,
  }
}

export function buildExecutionComparisonCatalog({
  executions = [],
  selectedScopes = [],
} = {}) {
  const groups =
    toArray(
      selectedScopes,
    )
      .map(
        (scope) => {
          const attempts =
            selectExecutionAttemptsForScope(
              executions,
              scope,
              {
                includeTargeted:
                  true,
              },
            )
              .filter(
                (execution) =>
                  hasExecutionResult(
                    execution,
                  ),
              )
              .map(
                buildAttemptOption,
              )

          return {
            attempts,

            key:
              scope.key,

            label:
              scope.label,
          }
        },
      )
      .filter(
        (group) =>
          group.attempts.length >= 2,
      )

  return {
    groups,

    hasComparableExecutions:
      groups.length > 0,
  }
}

export function compareExecutionAttempts({
  baseline,
  candidate,
} = {}) {
  if (
    !baseline ||
    !candidate
  ) {
    return null
  }

  const baselineMetrics =
    getExecutionMetrics(
      baseline,
    )

  const candidateMetrics =
    getExecutionMetrics(
      candidate,
    )

  const metricKeys = [
    {
      key: 'passed',
      label: 'Passed',
    },
    {
      key: 'failed',
      label: 'Failed',
    },
    {
      key: 'needReview',
      label: 'Need Review',
    },
    {
      key: 'skipped',
      label: 'Skipped',
    },
    {
      key: 'blocked',
      label: 'Blocked',
    },
  ]

  const metrics =
    metricKeys.map(
      ({ key, label }) => ({
        baseline:
          baselineMetrics[key] ??
          0,

        candidate:
          candidateMetrics[key] ??
          0,

        delta:
          (
            candidateMetrics[key] ??
            0
          ) -
          (
            baselineMetrics[key] ??
            0
          ),

        improvementDirection:
          key === 'passed'
            ? 'increase'
            : 'decrease',

        key,
        label,
      }),
    )

  const baselineDuration =
    getDurationMs(
      baseline,
    )

  const candidateDuration =
    getDurationMs(
      candidate,
    )

  return {
    assetVersions:
      buildAssetVersionDelta(
        baseline,
        candidate,
      ),

    baseline: {
      duration:
        formatExecutionDuration(
          baselineDuration,
        ),

      reason:
        formatExecutionReason(
          getExecutionLineage(
            baseline,
          ).executionReason,
        ),

      runId:
        getExecutionRunId(
          baseline,
        ),

      status:
        formatResultStatus(
          baseline.status,
        ),

      tone:
        getResultStatusTone(
          baseline.status,
        ),
    },

    candidate: {
      duration:
        formatExecutionDuration(
          candidateDuration,
        ),

      reason:
        formatExecutionReason(
          getExecutionLineage(
            candidate,
          ).executionReason,
        ),

      runId:
        getExecutionRunId(
          candidate,
        ),

      status:
        formatResultStatus(
          candidate.status,
        ),

      tone:
        getResultStatusTone(
          candidate.status,
        ),
    },

    durationDeltaMs:
      baselineDuration !== null &&
      candidateDuration !== null
        ? (
            candidateDuration -
            baselineDuration
          )
        : null,

    failureDelta:
      buildFailureDelta(
        baseline,
        candidate,
      ),

    metrics,

    sameScope:
      getExecutionScopeKey(
        baseline,
      ) ===
      getExecutionScopeKey(
        candidate,
      ),

    targeting: {
      baselineTargetIds:
        getExecutionTargetAssetIds(
          baseline,
        ),

      candidateTargetIds:
        getExecutionTargetAssetIds(
          candidate,
        ),

      baselineMode:
        getExecutionRequestSnapshot(
          baseline,
        ).targeting_mode ??
        'full_scope',

      candidateMode:
        getExecutionRequestSnapshot(
          candidate,
        ).targeting_mode ??
        'full_scope',
    },
  }
}
