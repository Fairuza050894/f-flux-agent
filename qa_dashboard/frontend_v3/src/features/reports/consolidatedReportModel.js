import {
  buildCycleArtifacts,
} from '../artifacts/artifactSelectors'
import {
  buildExecutionComparisonCatalog,
  compareExecutionAttempts,
} from '../executions/executionComparisonSelectors'
import {
  formatExecutionReason,
  getExecutionLineage,
  getExecutionRequestSnapshot,
  getExecutionRunId,
  getExecutionScopeKey,
  getExecutionTargetAssetIds,
  getExecutionTargetAssetSnapshots,
} from '../executions/executionAttemptSelectors'
import {
  buildExecutionTelemetryRows,
} from '../executions/executionTelemetrySelectors'
import {
  buildCycleResultModel,
  getExecutionMetrics,
  getExecutionResultSummary,
  hasExecutionResult,
} from '../results/resultSelectors'
import {
  formatPassRate,
  formatResultStatus,
  normalizeResultStatus,
} from '../results/resultFormatters'
import {
  buildCycleAssetVersionComparison,
} from '../test-cycle-detail/cycleAssetVersionComparison'

const scopeConfiguration = [
  {
    key: 'ui',
    label: 'UI Testing',
    runner: 'UI Runner',
    source: 'ui_testing',
    testType: 'ui',
  },
  {
    key: 'api',
    label: 'API Testing',
    runner: 'API Runner',
    source: 'api_testing',
    testType: 'api',
  },
  {
    key: 'unit',
    label: 'Unit Testing',
    runner: 'Unit Runner',
    source: 'unit_testing',
    testType: 'unit',
  },
  {
    key: 'e2e',
    label: 'E2E Testing',
    runner: 'E2E Runner',
    source: 'e2e_testing',
    testType: 'e2e',
  },
  {
    key: 'regression',
    label: 'Related Regression',
    runner: 'Regression Runner',
    source: 'regression_testing',
    testType: 'regression',
  },
]

function toArray(
  value,
) {
  return Array.isArray(value)
    ? value
    : []
}

function createLookup(
  items,
) {
  return new Map(
    toArray(items).map(
      (item) => [
        item?.id,
        item,
      ],
    ),
  )
}

function normalizeTimestamp(
  value,
) {
  if (!value) {
    return null
  }

  const date = new Date(value)

  return Number.isNaN(
    date.getTime(),
  )
    ? null
    : date.toISOString()
}

function sanitizeFilePart(
  value,
  fallback,
) {
  const normalized =
    String(value ?? '')
      .trim()
      .replace(
        /[^a-zA-Z0-9._-]+/g,
        '-',
      )
      .replace(
        /^[-._]+|[-._]+$/g,
        '',
      )

  return normalized || fallback
}

function normalizeTestCases(
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

  return toArray(values).map(
    (record, index) => ({
      id:
        String(
          record?.id ??
          record?.test_case_id ??
          record?.testCaseId ??
          `case-${index + 1}`,
        ),

      scenario:
        String(
          record?.scenario ??
          record?.name ??
          record?.title ??
          `Case ${index + 1}`,
        ),

      status:
        normalizeResultStatus(
          record?.status,
        ),

      message:
        String(
          record?.message ??
          record?.error ??
          record?.reason ??
          '',
        ),
    }),
  )
}

function getExecutionTimestamp(
  execution,
  aliases,
) {
  return aliases
    .map(
      (alias) =>
        execution?.[alias],
    )
    .find(Boolean) ?? null
}

function buildExecutionRecord(
  execution,
) {
  const lineage =
    getExecutionLineage(
      execution,
    )

  const requestSnapshot =
    getExecutionRequestSnapshot(
      execution,
    )

  const resultSummary =
    getExecutionResultSummary(
      execution,
    )

  return {
    runId:
      getExecutionRunId(
        execution,
      ),

    scopeKey:
      getExecutionScopeKey(
        execution,
      ),

    scopeLabel:
      String(
        execution?.scopeLabel ??
        execution?.scope_label ??
        execution?.source ??
        'Execution',
      ),

    runner:
      String(
        execution?.runner ??
        execution?.runner_name ??
        'Hermes QA Runner',
      ),

    source:
      String(
        execution?.source ??
        '',
      ),

    testType:
      String(
        execution?.testType ??
        execution?.test_type ??
        '',
      ),

    status:
      normalizeResultStatus(
        execution?.status,
      ),

    statusLabel:
      formatResultStatus(
        execution?.status,
      ),

    progress:
      Number(
        execution?.progress ?? 0,
      ),

    attemptNumber:
      lineage.attemptNumber,

    executionReason:
      lineage.executionReason,

    executionReasonLabel:
      formatExecutionReason(
        lineage.executionReason,
      ),

    parentRunId:
      lineage.parentRunId,

    rootRunId:
      lineage.rootRunId,

    targetingMode:
      String(
        requestSnapshot
          .targeting_mode ??
        'full_scope',
      ),

    targetAssetIds:
      getExecutionTargetAssetIds(
        execution,
      ),

    targetAssetSnapshots:
      getExecutionTargetAssetSnapshots(
        execution,
      ),

    targetingVerified:
      resultSummary
        .targeting_verified ??
      resultSummary
        .targetingVerified ??
      null,

    targetingMessage:
      String(
        resultSummary
          .targeting_message ??
        resultSummary
          .targetingMessage ??
        '',
      ),

    metrics:
      getExecutionMetrics(
        execution,
      ),

    hasResult:
      hasExecutionResult(
        execution,
      ),

    testingSummary:
      String(
        resultSummary
          .testing_summary ??
        resultSummary
          .testingSummary ??
        '',
      ),

    testCases:
      normalizeTestCases(
        execution,
      ),

    createdAt:
      normalizeTimestamp(
        getExecutionTimestamp(
          execution,
          [
            'createdAt',
            'created_at',
          ],
        ),
      ),

    startedAt:
      normalizeTimestamp(
        getExecutionTimestamp(
          execution,
          [
            'startedAt',
            'started_at',
          ],
        ),
      ),

    completedAt:
      normalizeTimestamp(
        getExecutionTimestamp(
          execution,
          [
            'completedAt',
            'completed_at',
            'updatedAt',
            'updated_at',
          ],
        ),
      ),

    currentStage:
      String(
        execution?.currentStage ??
        execution?.current_stage ??
        '',
      ),

    currentStep:
      String(
        execution?.currentStep ??
        execution?.current_step ??
        '',
      ),
  }
}

function buildSelectedScopes(
  cycle,
) {
  return scopeConfiguration.filter(
    (scope) =>
      Boolean(
        cycle?.scope?.[
          scope.key
        ],
      ),
  )
}

function buildLatestComparisons({
  executions,
  selectedScopes,
}) {
  const catalog =
    buildExecutionComparisonCatalog({
      executions,
      selectedScopes,
    })

  return catalog.groups
    .map(
      (group) => {
        const attempts =
          group.attempts

        const baselineOption =
          attempts[
            attempts.length - 2
          ]

        const candidateOption =
          attempts[
            attempts.length - 1
          ]

        const comparison =
          compareExecutionAttempts({
            baseline:
              baselineOption
                ?.execution,
            candidate:
              candidateOption
                ?.execution,
          })

        if (!comparison) {
          return null
        }

        return {
          scopeKey:
            group.key,

          scopeLabel:
            group.label,

          baselineRunId:
            comparison
              .baseline
              .runId,

          candidateRunId:
            comparison
              .candidate
              .runId,

          baseline:
            comparison.baseline,

          candidate:
            comparison.candidate,

          metrics:
            comparison.metrics,

          durationDeltaMs:
            comparison
              .durationDeltaMs,

          failureDelta:
            comparison
              .failureDelta,

          assetVersions:
            comparison
              .assetVersions,

          targeting:
            comparison.targeting,

          sameScope:
            comparison.sameScope,
        }
      },
    )
    .filter(Boolean)
}

function countFailureDelta(
  comparisons,
  key,
) {
  return comparisons.reduce(
    (total, comparison) => {
      if (
        !comparison
          .failureDelta
          ?.available
      ) {
        return total
      }

      return (
        total +
        toArray(
          comparison
            .failureDelta[
              key
            ],
        ).length
      )
    },
    0,
  )
}

function buildChecklist({
  assetComparison,
  newFailureCount,
  resultModel,
}) {
  const totals =
    resultModel.totals

  const hasResults =
    resultModel
      .resultExecutions
      .length > 0

  return [
    {
      id: 'results-available',
      label:
        'Execution results available',
      status:
        hasResults
          ? 'pass'
          : 'fail',
      detail:
        hasResults
          ? (
              `${resultModel.resultExecutions.length} ` +
              'result-bearing execution scopes.'
            )
          : (
              'No result-bearing execution is available.'
            ),
    },
    {
      id: 'failed-tests',
      label:
        'No failed tests',
      status:
        totals.failed === 0
          ? 'pass'
          : 'fail',
      detail:
        `${totals.failed} failed tests.`,
    },
    {
      id: 'blocked-tests',
      label:
        'No blocked tests',
      status:
        totals.blocked === 0
          ? 'pass'
          : 'fail',
      detail:
        `${totals.blocked} blocked tests.`,
    },
    {
      id: 'new-failures',
      label:
        'No new failures',
      status:
        newFailureCount === 0
          ? 'pass'
          : 'fail',
      detail:
        `${newFailureCount} new failures from compatible comparisons.`,
    },
    {
      id: 'review-items',
      label:
        'Review items resolved',
      status:
        totals.needReview === 0
          ? 'pass'
          : 'review',
      detail:
        `${totals.needReview} items require review.`,
    },
    {
      id: 'asset-snapshots',
      label:
        'Test Asset snapshots complete',
      status:
        (
          assetComparison.total > 0 &&
          assetComparison
            .unsnapshotted === 0 &&
          assetComparison
            .missing === 0
        )
          ? 'pass'
          : 'review',
      detail:
        (
          `${assetComparison.unsnapshotted} without snapshot; ` +
          `${assetComparison.missing} missing from live catalog.`
        ),
    },
    {
      id: 'unsupported-scopes',
      label:
        'All scopes supported',
      status:
        resultModel
          .unsupportedExecutions
          .length === 0
          ? 'pass'
          : 'review',
      detail:
        (
          `${resultModel.unsupportedExecutions.length} ` +
          'latest scopes are unsupported.'
        ),
    },
  ]
}

function buildReleaseDecision({
  assetComparison,
  comparisons,
  resultModel,
}) {
  const totals =
    resultModel.totals

  const newFailureCount =
    countFailureDelta(
      comparisons,
      'newFailures',
    )

  const checklist =
    buildChecklist({
      assetComparison,
      newFailureCount,
      resultModel,
    })

  if (
    resultModel
      .resultExecutions
      .length === 0
  ) {
    return {
      status: 'not_ready',
      label: 'Not Ready',
      tone: 'danger',
      reason:
        'No result-bearing execution is available for release assessment.',
      checklist,
    }
  }

  if (
    totals.failed > 0 ||
    totals.blocked > 0 ||
    newFailureCount > 0
  ) {
    const reasons = []

    if (totals.failed > 0) {
      reasons.push(
        `${totals.failed} failed tests`,
      )
    }

    if (totals.blocked > 0) {
      reasons.push(
        `${totals.blocked} blocked tests`,
      )
    }

    if (newFailureCount > 0) {
      reasons.push(
        `${newFailureCount} new failures`,
      )
    }

    return {
      status: 'not_ready',
      label: 'Not Ready',
      tone: 'danger',
      reason:
        `Release blockers remain: ${reasons.join(', ')}.`,
      checklist,
    }
  }

  if (
    totals.needReview > 0 ||
    totals.warnings > 0 ||
    resultModel
      .unsupportedExecutions
      .length > 0 ||
    assetComparison.missing > 0 ||
    assetComparison
      .unsnapshotted > 0
  ) {
    return {
      status:
        'ready_with_review',
      label:
        'Ready with Review',
      tone: 'warning',
      reason:
        'No failed or blocked result remains, but review or traceability gaps require approval.',
      checklist,
    }
  }

  return {
    status: 'ready',
    label: 'Ready',
    tone: 'success',
    reason:
      'All available result and traceability checks passed without release blockers.',
    checklist,
  }
}

function buildExecutiveSummary({
  assetComparison,
  comparisons,
  releaseDecision,
  resultModel,
}) {
  const totals =
    resultModel.totals

  const newFailureCount =
    countFailureDelta(
      comparisons,
      'newFailures',
    )

  const resolvedFailureCount =
    countFailureDelta(
      comparisons,
      'resolvedFailures',
    )

  return [
    (
      `Release recommendation: ${releaseDecision.label}. ` +
      releaseDecision.reason
    ),
    (
      `${totals.passed} passed, ${totals.failed} failed, ` +
      `${totals.needReview} need review, and ` +
      `${totals.blocked} blocked.`
    ),
    (
      `${newFailureCount} new failures and ` +
      `${resolvedFailureCount} resolved failures were identified from compatible execution comparisons.`
    ),
    (
      `${assetComparison.captured} of ${assetComparison.total} Test Assets have immutable captured definitions; ` +
      `${assetComparison.unsnapshotted} have no snapshot.`
    ),
  ]
}

function mapAssetRows(
  comparison,
) {
  return comparison.rows.map(
    (row) => ({
      assetId:
        row.assetId,
      name:
        row.name,
      module:
        row.module,
      feature:
        row.feature,
      typeLabel:
        row.typeLabel,
      priority:
        row.priority,
      automationStatus:
        row.automationStatus,
      executionReady:
        row.executionReady,
      statusKey:
        row.statusKey,
      statusLabel:
        row.statusLabel,
      reason:
        row.reason,
      capturedVersionId:
        row.capturedVersionId,
      capturedVersionNumber:
        row.capturedVersionNumber,
      capturedChangeSummary:
        row.capturedChangeSummary,
      liveVersionId:
        row.liveVersionId,
      liveVersionNumber:
        row.liveVersionNumber,
      lifecycleStatus:
        row.lifecycleStatus,
      capturedAt:
        normalizeTimestamp(
          row.capturedAt,
        ),
      hasSnapshot:
        row.hasSnapshot,
      hasLiveAsset:
        row.hasLiveAsset,
    }),
  )
}

function mapArtifacts(
  executions,
) {
  return buildCycleArtifacts(
    executions,
  ).map(
    (artifact) => ({
      runId:
        artifact.runId,
      scopeLabel:
        artifact.scopeLabel,
      name:
        artifact.name,
      filename:
        artifact.filename,
      type:
        artifact.type,
      mimeType:
        artifact.mimeType,
      available:
        artifact.available,
      size:
        artifact.size,
      createdAt:
        normalizeTimestamp(
          artifact.createdAt,
        ),
    }),
  )
}

export function buildConsolidatedReport({
  assets = [],
  cycle,
  environments = [],
  projects = [],
} = {}) {
  if (!cycle?.id) {
    return null
  }

  const projectLookup =
    createLookup(
      projects,
    )

  const environmentLookup =
    createLookup(
      environments,
    )

  const project =
    projectLookup.get(
      cycle.projectId,
    ) ?? null

  const environment =
    environmentLookup.get(
      cycle.environmentId,
    ) ?? null

  const selectedScopes =
    buildSelectedScopes(
      cycle,
    )

  const executions =
    toArray(
      cycle.executions,
    )

  const resultModel =
    buildCycleResultModel(
      cycle,
    )

  const assetComparison =
    buildCycleAssetVersionComparison({
      assets,
      cycle,
    })

  const comparisons =
    buildLatestComparisons({
      executions,
      selectedScopes,
    })

  const releaseDecision =
    buildReleaseDecision({
      assetComparison,
      comparisons,
      resultModel,
    })

  const executionRecords =
    executions.map(
      buildExecutionRecord,
    )

  const artifacts =
    mapArtifacts(
      executions,
    )

  const logs =
    buildExecutionTelemetryRows(
      executions,
    )

  const newFailureCount =
    countFailureDelta(
      comparisons,
      'newFailures',
    )

  const resolvedFailureCount =
    countFailureDelta(
      comparisons,
      'resolvedFailures',
    )

  const generatedAt =
    new Date().toISOString()

  const fileBaseName =
    sanitizeFilePart(
      `qa-report-${cycle.id}-${generatedAt.slice(0, 10)}`,
      'qa-report',
    )

  const summary = {
    ...resultModel.totals,

    passRateLabel:
      formatPassRate(
        resultModel
          .totals
          .passRate,
      ),

    executionAttemptCount:
      executions.length,

    latestExecutionCount:
      resultModel
        .executions
        .length,

    resultExecutionCount:
      resultModel
        .resultExecutions
        .length,

    unsupportedExecutionCount:
      resultModel
        .unsupportedExecutions
        .length,

    comparisonCount:
      comparisons.length,

    newFailureCount,
    resolvedFailureCount,

    artifactCount:
      artifacts.length,

    logCount:
      logs.length,
  }

  return {
    schemaVersion: 1,

    reportId:
      `report-${cycle.id}-${Date.now()}`,

    generatedAt,

    fileBaseName,

    title:
      `${cycle.name ?? 'Untitled Test Cycle'} QA Report`,

    cycle: {
      id:
        cycle.id,
      name:
        cycle.name,
      cycleType:
        cycle.cycleType,
      releaseVersion:
        cycle.releaseVersion,
      module:
        cycle.module,
      feature:
        cycle.feature,
      status:
        cycle.status,
      progress:
        cycle.progress,
      triggerSource:
        cycle.triggerSource,
      sourcePlanId:
        cycle.sourcePlanId,
      createdAt:
        normalizeTimestamp(
          cycle.createdAt,
        ),
      updatedAt:
        normalizeTimestamp(
          cycle.updatedAt,
        ),
    },

    project: {
      id:
        project?.id ??
        cycle.projectId ??
        '',
      name:
        project?.name ??
        'Unknown project',
    },

    environment: {
      id:
        environment?.id ??
        cycle.environmentId ??
        '',
      name:
        environment?.name ??
        'Unknown environment',
      url:
        environment?.webUrl ??
        environment?.baseUrl ??
        environment?.url ??
        '',
    },

    selectedScopes:
      selectedScopes.map(
        (scope) => ({
          key:
            scope.key,
          label:
            scope.label,
          runner:
            scope.runner,
          testType:
            scope.testType,
        }),
      ),

    releaseDecision,

    executiveSummary:
      buildExecutiveSummary({
        assetComparison,
        comparisons,
        releaseDecision,
        resultModel,
      }),

    summary,

    executions:
      executionRecords,

    comparisons,

    assetTraceability: {
      total:
        assetComparison.total,
      captured:
        assetComparison.captured,
      current:
        assetComparison.current,
      outdated:
        assetComparison.outdated,
      archived:
        assetComparison.archived,
      missing:
        assetComparison.missing,
      unsnapshotted:
        assetComparison
          .unsnapshotted,
      rows:
        mapAssetRows(
          assetComparison,
        ),
    },

    artifacts,

    logs,
  }
}
