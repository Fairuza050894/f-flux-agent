import {
  useState,
} from 'react'

import {
  createExecution,
  dispatchExecution,
} from '../../services/executionService'

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
  cycle,
  environmentTargetUrl,
  scopeKey,
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

    selected_asset_ids:
      cycle?.selectedAssetIds ?? [],

    selected_asset_snapshots:
      cycle?.selectedAssetSnapshots ?? [],

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
  cycle,
  environment,
  environmentTargetUrl,
  scope,
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
        cycle,
        environmentTargetUrl,
        scopeKey: scope.key,
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
    dispatchableExecutions,
    dispatchExecutions,
    isDispatching,
    isStarting,
    scopesWithoutExecution,
    startCycle,
    startError,
  }
}
