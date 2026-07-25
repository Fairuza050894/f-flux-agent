import {
  useState,
} from 'react'

import {
  cancelExecution,
  createExecution,
  dispatchExecution,
} from '../../services/executionService'
import {
  findLatestExecutionForScope,
  getExecutionLineage,
  getExecutionRunId,
  isFailedExecution,
  isRerunnableExecution,
  selectExecutionAttemptsForScope,
} from './executionAttemptSelectors'

const dispatchableStatuses = new Set([
  'queued',
  'pending',
  'created',
  'ready',
  'not_started',
])

function normalizeStatus(status) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll(' ', '_')
}

function getCycleFeature(cycle) {
  return String(
    cycle?.feature ||
    cycle?.module ||
    cycle?.name ||
    '',
  ).slice(0, 240)
}

function getEnvironmentName(
  cycle,
  environment,
) {
  return String(
    environment?.name ||
    cycle?.environmentId ||
    '',
  ).slice(0, 120)
}

function buildRequestSnapshot({
  attemptNumber = 1,
  cycle,
  environmentTargetUrl,
  executionReason = 'initial',
  parentRunId = '',
  rootRunId = '',
  scopeKey,
  targetAssetIds = [],
  targetAssetSnapshots = [],
}) {
  return {
    cycle_id:
      cycle?.id,

    cycle_name:
      cycle?.name,

    environment_id:
      cycle?.environmentId,

    environment_url:
      environmentTargetUrl,

    cycle_type:
      cycle?.cycleType,

    scope_key:
      scopeKey,

    execution_reason:
      executionReason,

    attempt_number:
      attemptNumber,

    parent_run_id:
      parentRunId || null,

    root_run_id:
      rootRunId || null,

    requested_at:
      new Date().toISOString(),

    selected_asset_ids:
      cycle?.selectedAssetIds ?? [],

    selected_asset_snapshots:
      cycle?.selectedAssetSnapshots ?? [],

    target_asset_ids:
      targetAssetIds,

    target_asset_snapshots:
      targetAssetSnapshots,

    targeting_mode:
      targetAssetIds.length > 0
        ? 'selected_assets'
        : 'full_scope',

    source_plan_id:
      cycle?.sourcePlanId ?? '',

    snapshot_schema_version: 1,

    cycle_captured_at:
      cycle?.createdAt ?? null,

    execution_settings:
      cycle?.executionSettings,

    trigger_source:
      cycle?.triggerSource ??
      'Manual',
  }
}

function buildCreatePayload({
  attemptNumber = 1,
  cycle,
  environment,
  environmentTargetUrl,
  executionReason = 'initial',
  parentRunId = '',
  rootRunId = '',
  scope,
  targetAssetIds = [],
  targetAssetSnapshots = [],
}) {
  return {
    project_id:
      cycle?.projectId,

    source:
      scope.source,

    feature:
      getCycleFeature(cycle),

    test_type:
      scope.testType,

    environment:
      getEnvironmentName(
        cycle,
        environment,
      ),

    request_snapshot:
      buildRequestSnapshot({
        attemptNumber,
        cycle,
        environmentTargetUrl,
        executionReason,
        parentRunId,
        rootRunId,
        scopeKey: scope.key,
        targetAssetIds,
        targetAssetSnapshots,
      }),
  }
}

function enrichCreatedExecution(
  response,
  scope,
  requestSnapshot,
) {
  return {
    ...response,

    scopeKey:
      scope.key,

    scopeLabel:
      scope.label,

    runner:
      scope.runner,

    source:
      scope.source,

    testType:
      scope.testType,

    requestSnapshot:
      response.requestSnapshot ??
      response.request_snapshot ??
      requestSnapshot,

    executionReason:
      requestSnapshot
        ?.execution_reason ??
      'initial',

    attemptNumber:
      requestSnapshot
        ?.attempt_number ??
      1,

    parentRunId:
      requestSnapshot
        ?.parent_run_id ??
      '',

    rootRunId:
      requestSnapshot
        ?.root_run_id ??
      response.runId ??
      response.run_id ??
      '',

    createdAt:
      response.created_at ??
      response.createdAt ??
      new Date().toISOString(),
  }
}

function buildDispatchPayload({
  cycle,
  environmentTargetUrl,
  execution,
}) {
  return {
    url:
      environmentTargetUrl,

    module_name:
      cycle?.module ||
      cycle?.feature ||
      cycle?.name ||
      '',

    mode:
      execution.source ===
      'regression_testing'
        ? 'regression'
        : 'smoke',
  }
}

function buildRecreatePayload({
  cycle,
  environment,
  environmentTargetUrl,
  execution,
}) {
  return {
    project_id:
      cycle?.projectId,

    source:
      execution.source,

    feature:
      getCycleFeature(cycle),

    test_type:
      execution.testType,

    environment:
      getEnvironmentName(
        cycle,
        environment,
      ),

    request_snapshot:
      buildRequestSnapshot({
        cycle,
        environmentTargetUrl,
        scopeKey:
          execution.scopeKey,
      }),
  }
}

function getErrorMessage(
  error,
  fallback,
) {
  return error instanceof Error
    ? error.message
    : fallback
}

export function useTestCycleExecutionOrchestrator({
  cycle,
  environment,
  environmentTargetUrl = '',
  executions = [],
  onExecutionsCreated,
  registerCycleExecutions,
  selectedScopes = [],
  setCycleExecutionError,
  updateCycleExecution,
} = {}) {
  const [
    isStarting,
    setIsStarting,
  ] = useState(false)

  const [
    isDispatching,
    setIsDispatching,
  ] = useState(false)

  const [
    isRetrying,
    setIsRetrying,
  ] = useState(false)

  const [
    isRerunning,
    setIsRerunning,
  ] = useState(false)

  const [
    isTargetedRerunning,
    setIsTargetedRerunning,
  ] = useState(false)

  const [
    cancellingRunIds,
    setCancellingRunIds,
  ] = useState(
    () => new Set(),
  )

  const [
    startError,
    setStartError,
  ] = useState('')

  const executionByScope =
    Object.fromEntries(
      executions.map((execution) => [
        execution.scopeKey,
        execution,
      ]),
    )

  const scopesWithoutExecution =
    selectedScopes.filter(
      (scope) =>
        !executionByScope[scope.key],
    )

  const dispatchableExecutions =
    executions.filter(
      (execution) =>
        dispatchableStatuses.has(
          normalizeStatus(
            execution.status,
          ),
        ),
    )

  const latestScopePairs =
    selectedScopes.map(
      (scope) => ({
        execution:
          findLatestExecutionForScope(
            executions,
            scope,
          ),
        scope,
      }),
    )

  const failedScopePairs =
    latestScopePairs.filter(
      ({ execution }) =>
        execution &&
        isFailedExecution(
          execution,
        ),
    )

  function clearExecutionError() {
    setStartError('')

    if (
      cycle?.id &&
      typeof setCycleExecutionError ===
        'function'
    ) {
      setCycleExecutionError(
        cycle.id,
        '',
      )
    }
  }

  function storeExecutionError(
    message,
  ) {
    setStartError(message)

    if (
      cycle?.id &&
      typeof setCycleExecutionError ===
        'function'
    ) {
      setCycleExecutionError(
        cycle.id,
        message,
      )
    }
  }

  async function startCycle() {
    if (
      !cycle?.id ||
      scopesWithoutExecution.length ===
        0
    ) {
      return
    }

    setIsStarting(true)
    clearExecutionError()

    try {
      const outcomes =
        await Promise.allSettled(
          scopesWithoutExecution.map(
            async (scope) => {
              const createPayload =
                buildCreatePayload({
                  cycle,
                  environment,
                  environmentTargetUrl,
                  scope,
                })

              const response =
                await createExecution(
                  createPayload,
                )

              if (!response.runId) {
                throw new Error(
                  `${scope.label}: backend response does not contain a run ID.`,
                )
              }

              return enrichCreatedExecution(
                response,
                scope,
                createPayload
                  .request_snapshot,
              )
            },
          ),
        )

      const createdExecutions =
        outcomes
          .filter(
            (outcome) =>
              outcome.status ===
              'fulfilled',
          )
          .map(
            (outcome) =>
              outcome.value,
          )

      const failedOutcomes =
        outcomes.filter(
          (outcome) =>
            outcome.status ===
            'rejected',
        )

      if (
        createdExecutions.length > 0
      ) {
        if (
          typeof registerCycleExecutions ===
          'function'
        ) {
          registerCycleExecutions(
            cycle.id,
            createdExecutions,
          )
        }

        if (
          typeof onExecutionsCreated ===
          'function'
        ) {
          onExecutionsCreated(
            createdExecutions,
          )
        }
      }

      if (
        failedOutcomes.length > 0
      ) {
        const message =
          failedOutcomes
            .map(
              (outcome) =>
                outcome.reason
                  ?.message ??
                'Unknown execution error',
            )
            .join(' | ')

        storeExecutionError(
          message,
        )
      }
    } catch (error) {
      storeExecutionError(
        getErrorMessage(
          error,
          'Execution could not be created.',
        ),
      )
    } finally {
      setIsStarting(false)
    }
  }

  async function createAndDispatchAttempts({
    executionReason,
    targets,
  }) {
    if (
      !cycle?.id ||
      targets.length === 0
    ) {
      return []
    }

    clearExecutionError()

    const outcomes =
      await Promise.all(
        targets.map(
          async ({
            parentExecution,
            scope,
            targetAssetIds = [],
            targetAssetSnapshots = [],
          }) => {
            try {
              const attempts =
                selectExecutionAttemptsForScope(
                  executions,
                  scope,
                  {
                    includeTargeted:
                      true,
                  },
                )

              const parentRunId =
                getExecutionRunId(
                  parentExecution,
                )

              const parentLineage =
                getExecutionLineage(
                  parentExecution,
                )

              const attemptNumber =
                attempts.length + 1

              const createPayload =
                buildCreatePayload({
                  attemptNumber,
                  cycle,
                  environment,
                  environmentTargetUrl,
                  executionReason,
                  parentRunId,
                  rootRunId:
                    parentLineage
                      .rootRunId ||
                    parentRunId,
                  scope,
                  targetAssetIds,
                  targetAssetSnapshots,
                })

              const response =
                await createExecution(
                  createPayload,
                )

              if (!response.runId) {
                throw new Error(
                  `${scope.label}: backend response does not contain a run ID.`,
                )
              }

              const createdExecution =
                enrichCreatedExecution(
                  response,
                  scope,
                  createPayload
                    .request_snapshot,
                )

              try {
                const dispatched =
                  await dispatchExecution(
                    response.runId,
                    buildDispatchPayload({
                      cycle,
                      environmentTargetUrl,
                      execution:
                        createdExecution,
                    }),
                  )

                return {
                  error: '',
                  execution: {
                    ...createdExecution,
                    ...dispatched,
                    runId:
                      response.runId,
                    scopeKey:
                      scope.key,
                    scopeLabel:
                      scope.label,
                    runner:
                      scope.runner,
                    source:
                      scope.source,
                    testType:
                      scope.testType,
                    requestSnapshot:
                      dispatched
                        .requestSnapshot ??
                      createdExecution
                        .requestSnapshot,
                    executionReason,
                    attemptNumber,
                    parentRunId,
                    rootRunId:
                      parentLineage
                        .rootRunId ||
                      parentRunId,
                  },
                }
              } catch (error) {
                return {
                  error:
                    `${scope.label}: ${getErrorMessage(
                      error,
                      'Dispatch failed.',
                    )}`,
                  execution:
                    createdExecution,
                }
              }
            } catch (error) {
              return {
                error:
                  `${scope.label}: ${getErrorMessage(
                    error,
                    'Execution could not be created.',
                  )}`,
                execution: null,
              }
            }
          },
        ),
      )

    const createdExecutions =
      outcomes
        .map(
          (outcome) =>
            outcome.execution,
        )
        .filter(Boolean)

    if (
      createdExecutions.length > 0
    ) {
      if (
        typeof registerCycleExecutions ===
        'function'
      ) {
        registerCycleExecutions(
          cycle.id,
          createdExecutions,
        )
      }

      if (
        typeof onExecutionsCreated ===
        'function'
      ) {
        onExecutionsCreated(
          createdExecutions,
        )
      }
    }

    const errors =
      outcomes
        .map(
          (outcome) =>
            outcome.error,
        )
        .filter(Boolean)

    if (errors.length > 0) {
      storeExecutionError(
        errors.join(' | '),
      )
    }

    return createdExecutions
  }

  async function retryFailedScopes() {
    if (
      isRetrying ||
      failedScopePairs.length === 0
    ) {
      return []
    }

    setIsRetrying(true)

    try {
      return await createAndDispatchAttempts({
        executionReason:
          'retry_failed_scope',
        targets:
          failedScopePairs.map(
            ({
              execution,
              scope,
            }) => ({
              parentExecution:
                execution,
              scope,
            }),
          ),
      })
    } finally {
      setIsRetrying(false)
    }
  }

  async function rerunSelectedScopes(
    scopeKeys,
  ) {
    if (
      isRerunning ||
      !Array.isArray(scopeKeys)
    ) {
      return []
    }

    const requestedKeys =
      new Set(scopeKeys)

    const targets =
      latestScopePairs
        .filter(
          ({
            execution,
            scope,
          }) =>
            requestedKeys.has(
              scope.key,
            ) &&
            execution &&
            isRerunnableExecution(
              execution,
            ),
        )
        .map(
          ({
            execution,
            scope,
          }) => ({
            parentExecution:
              execution,
            scope,
          }),
        )

    if (targets.length === 0) {
      return []
    }

    setIsRerunning(true)

    try {
      return await createAndDispatchAttempts({
        executionReason:
          'rerun_selected_scope',
        targets,
      })
    } finally {
      setIsRerunning(false)
    }
  }

  async function rerunSelectedAssets({
    assetIds,
    scopeKey,
  } = {}) {
    if (
      isTargetedRerunning ||
      !Array.isArray(assetIds) ||
      assetIds.length === 0 ||
      !scopeKey
    ) {
      return []
    }

    const scope =
      selectedScopes.find(
        (candidate) =>
          candidate.key ===
          scopeKey,
      )

    const supported =
      [
        'ui_testing',
        'regression_testing',
      ].includes(
        scope?.source,
      )

    const parentExecution =
      scope
        ? findLatestExecutionForScope(
            executions,
            scope,
          )
        : null

    if (
      !scope ||
      !supported ||
      !parentExecution ||
      !isRerunnableExecution(
        parentExecution,
      )
    ) {
      storeExecutionError(
        'Selected scope is not eligible for a targeted asset rerun.',
      )
      return []
    }

    const normalizedAssetIds =
      Array.from(
        new Set(
          assetIds
            .map(
              (assetId) =>
                String(
                  assetId ?? '',
                ).trim(),
            )
            .filter(Boolean),
        ),
      )

    const requestedAssetIds =
      new Set(
        normalizedAssetIds,
      )

    const targetAssetSnapshots =
      (
        Array.isArray(
          cycle?.selectedAssetSnapshots,
        )
          ? cycle.selectedAssetSnapshots
          : []
      ).filter(
        (record) =>
          requestedAssetIds.has(
            String(
              record?.assetId ??
              record?.asset_id ??
              '',
            ).trim(),
          ),
      )

    if (
      targetAssetSnapshots.length !==
      normalizedAssetIds.length
    ) {
      storeExecutionError(
        'Targeted rerun requires a captured snapshot for every selected Test Asset.',
      )
      return []
    }

    setIsTargetedRerunning(true)

    try {
      return await createAndDispatchAttempts({
        executionReason:
          'rerun_selected_assets',

        targets: [
          {
            parentExecution,
            scope,
            targetAssetIds:
              normalizedAssetIds,
            targetAssetSnapshots,
          },
        ],
      })
    } finally {
      setIsTargetedRerunning(false)
    }
  }

  async function cancelCycleExecution(
    runId,
  ) {
    if (
      !cycle?.id ||
      !runId ||
      cancellingRunIds.has(runId)
    ) {
      return null
    }

    setCancellingRunIds(
      (current) => {
        const next =
          new Set(current)

        next.add(runId)

        return next
      },
    )

    clearExecutionError()

    try {
      const response =
        await cancelExecution(
          runId,
          {
            reason:
              'Cancelled from Test Cycle detail.',
          },
        )

      if (
        typeof updateCycleExecution ===
        'function'
      ) {
        updateCycleExecution(
          cycle.id,
          runId,
          response,
        )
      }

      return response
    } catch (error) {
      storeExecutionError(
        getErrorMessage(
          error,
          'Execution could not be cancelled.',
        ),
      )

      return null
    } finally {
      setCancellingRunIds(
        (current) => {
          const next =
            new Set(current)

          next.delete(runId)

          return next
        },
      )
    }
  }

  async function dispatchExecutions() {
    if (
      !cycle?.id ||
      dispatchableExecutions.length ===
        0
    ) {
      return
    }

    setIsDispatching(true)
    clearExecutionError()

    try {
      const outcomes =
        await Promise.allSettled(
          dispatchableExecutions.map(
            async (execution) => {
              let activeRunId =
                execution.runId

              let activeExecution =
                execution

              const dispatchPayload =
                () =>
                  buildDispatchPayload({
                    cycle,
                    environmentTargetUrl,
                    execution:
                      activeExecution,
                  })

              try {
                const response =
                  await dispatchExecution(
                    activeRunId,
                    dispatchPayload(),
                  )

                return {
                  response,
                  runId:
                    activeRunId,
                  execution:
                    activeExecution,
                }
              } catch (error) {
                const message =
                  error?.message ?? ''

                if (
                  !/run not found/i.test(
                    message,
                  )
                ) {
                  throw error
                }

                const recreated =
                  await createExecution(
                    buildRecreatePayload({
                      cycle,
                      environment,
                      environmentTargetUrl,
                      execution,
                    }),
                  )

                if (!recreated.runId) {
                  throw new Error(
                    `${execution.scopeLabel}: recreated execution does not contain a run ID.`,
                    {
                      cause: error,
                    },
                  )
                }

                activeRunId =
                  recreated.runId

                activeExecution = {
                  ...execution,
                  ...recreated,
                  runId:
                    activeRunId,
                }

                if (
                  typeof updateCycleExecution ===
                  'function'
                ) {
                  updateCycleExecution(
                    cycle.id,
                    execution.runId,
                    activeExecution,
                  )
                }

                const response =
                  await dispatchExecution(
                    activeRunId,
                    dispatchPayload(),
                  )

                return {
                  response,
                  runId:
                    activeRunId,
                  execution:
                    activeExecution,
                }
              }
            },
          ),
        )

      const errorMessages = []

      outcomes.forEach(
        (outcome, index) => {
          const originalExecution =
            dispatchableExecutions[
              index
            ]

          if (
            outcome.status ===
            'fulfilled'
          ) {
            const {
              response,
              runId,
              execution:
                activeExecution,
            } = outcome.value

            if (
              typeof updateCycleExecution ===
              'function'
            ) {
              updateCycleExecution(
                cycle.id,
                runId,
                {
                  ...activeExecution,
                  ...response,
                  runId,

                  scopeKey:
                    activeExecution
                      .scopeKey,

                  scopeLabel:
                    activeExecution
                      .scopeLabel,

                  runner:
                    activeExecution
                      .runner,

                  source:
                    activeExecution
                      .source,

                  testType:
                    activeExecution
                      .testType,
                },
              )
            }

            return
          }

          errorMessages.push(
            outcome.reason?.message ??
            `${originalExecution.scopeLabel}: dispatch failed.`,
          )
        },
      )

      if (
        errorMessages.length > 0
      ) {
        storeExecutionError(
          errorMessages.join(' | '),
        )
      }
    } catch (error) {
      storeExecutionError(
        getErrorMessage(
          error,
          'Executions could not be dispatched.',
        ),
      )
    } finally {
      setIsDispatching(false)
    }
  }

  return {
    cancelCycleExecution,
    cancellingRunIds,
    dispatchableExecutions,
    dispatchExecutions,
    failedScopeCount:
      failedScopePairs.length,
    isDispatching,
    isRerunning,
    isRetrying,
    isStarting,
    isTargetedRerunning,
    rerunSelectedAssets,
    rerunSelectedScopes,
    retryFailedScopes,
    scopesWithoutExecution,
    startCycle,
    startError,
  }
}
