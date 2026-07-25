import {
  findLatestExecutionForScope,
  formatExecutionReason,
  getExecutionLineage,
  getExecutionRunId,
  getExecutionTargetAssetIds,
  isRerunnableExecution,
  isTargetedExecution,
  normalizeExecutionStatus,
} from './executionAttemptSelectors'

const supportedSources =
  new Set([
    'ui_testing',
    'regression_testing',
  ])

export function buildTargetedRerunModel({
  assetRows = [],
  executions = [],
  isSubmitting = false,
  selectedScopes = [],
} = {}) {
  const assets =
    (
      Array.isArray(assetRows)
        ? assetRows
        : []
    )
      .filter(
        (row) =>
          row?.hasSnapshot,
      )
      .map(
        (row) => ({
          assetId:
            row.assetId,

          name:
            row.name ??
            row.assetId,

          module:
            row.module ??
            'Not specified',

          feature:
            row.feature ??
            'Not specified',

          statusLabel:
            row.statusLabel ??
            'Captured',

          typeLabel:
            row.typeLabel ??
            'Test Asset',
        }),
      )

  const scopes =
    (
      Array.isArray(selectedScopes)
        ? selectedScopes
        : []
    ).map(
      (scope) => {
        const execution =
          findLatestExecutionForScope(
            executions,
            scope,
          )

        const supported =
          supportedSources.has(
            scope.source,
          )

        const rerunnable =
          Boolean(
            execution &&
            isRerunnableExecution(
              execution,
            ),
          )

        let unavailableReason = ''

        if (!supported) {
          unavailableReason =
            'Built-in runner does not support this scope.'
        } else if (!execution) {
          unavailableReason =
            'Create an execution for this scope first.'
        } else if (!rerunnable) {
          unavailableReason =
            'The latest scope execution is not ready for rerun.'
        }

        return {
          eligible:
            supported &&
            rerunnable,

          key:
            scope.key,

          label:
            scope.label,

          parentRunId:
            getExecutionRunId(
              execution,
            ),

          runner:
            scope.runner,

          source:
            scope.source,

          unavailableReason,
        }
      },
    )


  const targetedRuns =
    (
      Array.isArray(executions)
        ? executions
        : []
    )
      .filter(
        isTargetedExecution,
      )
      .map(
        (execution) => {
          const lineage =
            getExecutionLineage(
              execution,
            )

          return {
            attemptNumber:
              lineage.attemptNumber,

            progress:
              Number(
                execution?.progress ??
                0,
              ),

            reasonLabel:
              formatExecutionReason(
                lineage.executionReason,
              ),

            runId:
              getExecutionRunId(
                execution,
              ),

            status:
              normalizeExecutionStatus(
                execution?.status,
              ),

            targetAssetIds:
              getExecutionTargetAssetIds(
                execution,
              ),
          }
        },
      )
      .reverse()

  return {
    assets,

    eligibleScopeCount:
      scopes.filter(
        (scope) =>
          scope.eligible,
      ).length,

    isSubmitting:
      Boolean(isSubmitting),

    scopes,

    targetedRuns,
  }
}
