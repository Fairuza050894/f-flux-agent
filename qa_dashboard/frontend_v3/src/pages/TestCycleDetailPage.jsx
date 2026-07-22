import {
  useEffect,
  useState,
} from 'react'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import StatusBadge from '../components/StatusBadge'

import CycleArtifactsTab from '../components/test-cycle-detail/CycleArtifactsTab'
import CycleDetailHeader from '../components/test-cycle-detail/CycleDetailHeader'
import CycleDetailSummary from '../components/test-cycle-detail/CycleDetailSummary'
import CycleDetailTabs from '../components/test-cycle-detail/CycleDetailTabs'
import CycleActivityTab from '../components/test-cycle-detail/CycleActivityTab'
import CycleExecutionsTab from '../components/test-cycle-detail/CycleExecutionsTab'
import CycleLogsTab from '../components/test-cycle-detail/CycleLogsTab'
import CycleOverviewTab from '../components/test-cycle-detail/CycleOverviewTab'
import CycleResultsTab from '../components/test-cycle-detail/CycleResultsTab'
import {
  buildCycleArtifacts,
} from '../features/artifacts/artifactSelectors'
import {
  useArtifactPreview,
} from '../features/artifacts/useArtifactPreview'
import {
  buildExecutionActivityItems,
} from '../features/executions/executionActivitySelectors'
import {
  buildExecutionListModel,
} from '../features/executions/executionListSelectors'
import {
  buildExecutionTelemetryRows,
} from '../features/executions/executionTelemetrySelectors'
import {
  buildCycleResultModel,
} from '../features/results/resultSelectors'
import {
  buildCycleOverviewModel,
} from '../features/test-cycle-detail/cycleOverviewSelectors'
import {
  buildCycleDetailShellModel,
} from '../features/test-cycle-detail/cycleDetailShellSelectors'
import {
  createExecution,
  dispatchExecution,
  getExecution,
  getExecutionArtifactUrl,
} from '../services/executionService'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

const detailTabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'executions', label: 'Executions' },
  { id: 'results', label: 'Test Results' },
  { id: 'artifacts', label: 'Artifacts' },
  { id: 'logs', label: 'Logs' },
  { id: 'activity', label: 'Activity' },
]

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

const activePollingStatuses = new Set([
  'running',
  'in_progress',
  'processing',
])

function normalizeStatus(status) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll(' ', '_')
}

function formatDateTime(value) {
  if (!value) {
    return 'Not available'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Not available'
  }

  return date.toLocaleString()
}

function getEnvironmentTargetUrl(
  environment,
) {
  const candidates = [
    environment?.webUrl,
    environment?.baseUrl,
    environment?.applicationUrl,
    environment?.frontendUrl,
    environment?.uiUrl,
    environment?.url,
    environment?.web_url,
    environment?.base_url,
    environment?.urls?.web,
    environment?.urls?.base,
    environment?.urls?.application,
  ]

  const targetUrl = candidates.find(
    (value) =>
      typeof value === 'string' &&
      value.trim().length > 0,
  )

  return targetUrl?.trim() ?? ''
}

function TestCycleDetailPage() {
  const navigate = useNavigate()
  const { cycleId } = useParams()

  const [activeTab, setActiveTab] =
    useState('overview')

  const [isStarting, setIsStarting] =
    useState(false)

  const [
    isDispatching,
    setIsDispatching,
  ] = useState(false)

  const [startError, setStartError] =
    useState('')

  const {
    closePreview:
      closeArtifactPreview,
    openPreview:
      handleArtifactPreview,
    preview:
      artifactPreview,
    previewContent:
      artifactPreviewContent,
    previewError:
      artifactPreviewError,
    previewLoading:
      artifactPreviewLoading,
  } = useArtifactPreview()

  const cycles = useTestCycleStore(
    (state) => state.cycles,
  )

  const registerCycleExecutions =
    useTestCycleStore(
      (state) =>
        state.registerCycleExecutions,
    )

  const updateCycleExecution =
    useTestCycleStore(
      (state) =>
        state.updateCycleExecution,
    )

  const setCycleExecutionError =
    useTestCycleStore(
      (state) =>
        state.setCycleExecutionError,
    )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const cycle = cycles.find(
    (record) => record.id === cycleId,
  )

  const project = cycle
    ? projects.find(
        (record) =>
          record.id === cycle.projectId,
      )
    : null

  const environment = cycle
    ? environments.find(
        (record) =>
          record.id ===
          cycle.environmentId,
      )
    : null

  const selectedScopes = cycle
    ? scopeConfiguration.filter(
        (scope) =>
          Boolean(
            cycle.scope?.[scope.key],
          ),
      )
    : []

  const executions =
    cycle?.executions ?? []

  const environmentTargetUrl =
    getEnvironmentTargetUrl(
      environment,
    )

  const dispatchableExecutions =
    executions.filter((execution) =>
      [
        'queued',
        'pending',
        'created',
        'ready',
        'not_started',
      ].includes(
        normalizeStatus(
          execution.status,
        ),
      ),
    )

  const executionListModel =
    buildExecutionListModel({
      dispatchableCount:
        dispatchableExecutions.length,
      executions,
      isDispatching,
      selectedScopes,
    })

  const cycleResultModel =
    buildCycleResultModel({
      ...(cycle ?? {}),
      executions,
    })

  const {
    resultExecutions,
    unsupportedExecutions,
    totals: resultTotals,
  } = cycleResultModel

  const executionLogRows =
    buildExecutionTelemetryRows(
      executions,
    )

  const executionActivityItems =
    buildExecutionActivityItems({
      cycle,
      executions,
    })

  const cycleArtifacts =
    buildCycleArtifacts(
      executions,
    ).map((artifact) => ({
      ...artifact,

      previewUrl:
        artifact.available
          ? getExecutionArtifactUrl(
              artifact.runId,
              artifact.artifactIndex,
            )
          : '',

      downloadUrl:
        artifact.available
          ? getExecutionArtifactUrl(
              artifact.runId,
              artifact.artifactIndex,
              {
                download: true,
              },
            )
          : '',
    }))

  const executionByScope =
    Object.fromEntries(
      executions.map((execution) => [
        execution.scopeKey,
        execution,
      ]),
    )

  const cycleOverviewModel =
    buildCycleOverviewModel({
      cycle,
      executions,
      selectedScopes,
    })

  const scopesWithoutExecution =
    selectedScopes.filter(
      (scope) =>
        !executionByScope[scope.key],
    )

  const cycleDetailShellModel =
    buildCycleDetailShellModel({
      cycle,
      environment,
      executionCount:
        executions.length,
      isStarting,
      missingExecutionCount:
        scopesWithoutExecution.length,
      project,
      startError,
    })

  const executionRunIds = executions
    .filter(
      (execution) =>
        Boolean(execution.runId),
    )
    .map(
      (execution) =>
        execution.runId,
    )
    .sort()
    .join('|')

  const activeRunIds = executions
    .filter(
      (execution) =>
        execution.runId &&
        activePollingStatuses.has(
          normalizeStatus(
            execution.status,
          ),
        ),
    )
    .map(
      (execution) =>
        execution.runId,
    )
    .sort()
    .join('|')

  useEffect(() => {
    if (
      !cycle?.id ||
      !executionRunIds
    ) {
      return undefined
    }

    let cancelled = false

    async function synchronizeExecutions() {
      const runIds =
        executionRunIds.split('|')

      const results =
        await Promise.allSettled(
          runIds.map((runId) =>
            getExecution(runId),
          ),
        )

      if (cancelled) {
        return
      }

      results.forEach(
        (result, index) => {
          if (
            result.status !==
            'fulfilled'
          ) {
            return
          }

          updateCycleExecution(
            cycle.id,
            runIds[index],
            result.value,
          )
        },
      )
    }

    synchronizeExecutions()

    return () => {
      cancelled = true
    }
  }, [
    cycle?.id,
    executionRunIds,
    updateCycleExecution,
  ])

  useEffect(() => {
    if (
      !cycle?.id ||
      !activeRunIds
    ) {
      return undefined
    }

    let cancelled = false

    async function pollActiveExecutions() {
      const runIds =
        activeRunIds.split('|')

      const results =
        await Promise.allSettled(
          runIds.map((runId) =>
            getExecution(runId),
          ),
        )

      if (cancelled) {
        return
      }

      results.forEach(
        (result, index) => {
          if (
            result.status !==
            'fulfilled'
          ) {
            return
          }

          updateCycleExecution(
            cycle.id,
            runIds[index],
            result.value,
          )
        },
      )
    }

    const timer = window.setInterval(
      pollActiveExecutions,
      2500,
    )

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [
    activeRunIds,
    cycle?.id,
    updateCycleExecution,
  ])

  if (!cycle) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-panel cycle-not-found">
          <StatusBadge tone="danger">
            Not Found
          </StatusBadge>

          <h2>Test Cycle not found</h2>

          <p>
            The requested Test Cycle does not exist
            in the current workspace.
          </p>

          <button
            className="button button-primary"
            onClick={() =>
              navigate('/test-cycles')
            }
            type="button"
          >
            Back to Test Cycles
          </button>
        </section>
      </div>
    )
  }

  const selectedAssetIds =
    cycle.selectedAssetIds ?? []

  async function handleStartCycle() {
    if (
      scopesWithoutExecution.length ===
      0
    ) {
      return
    }

    setIsStarting(true)
    setStartError('')
    setCycleExecutionError(
      cycle.id,
      '',
    )

    const outcomes =
      await Promise.allSettled(
        scopesWithoutExecution.map(
          async (scope) => {
            const response =
              await createExecution({
                project_id:
                  cycle.projectId,
                source: scope.source,
                feature: (
                  cycle.feature ||
                  cycle.module ||
                  cycle.name
                ).slice(0, 240),
                test_type:
                  scope.testType,
                environment: (
                  environment?.name ||
                  cycle.environmentId ||
                  ''
                ).slice(0, 120),
                request_snapshot: {
                  cycle_id: cycle.id,
                  cycle_name:
                    cycle.name,
                  environment_id:
                    cycle.environmentId,
                  environment_url:
                    environmentTargetUrl,
                  cycle_type:
                    cycle.cycleType,
                  scope_key:
                    scope.key,
                  selected_asset_ids:
                    selectedAssetIds,
                  execution_settings:
                    cycle.executionSettings,
                  trigger_source:
                    cycle.triggerSource ??
                    'Manual',
                },
              })

            if (!response.runId) {
              throw new Error(
                `${scope.label}: backend response does not contain a run ID.`,
              )
            }

            return {
              ...response,
              scopeKey: scope.key,
              scopeLabel:
                scope.label,
              runner: scope.runner,
              source: scope.source,
              testType:
                scope.testType,
              createdAt:
                response.created_at ??
                response.createdAt ??
                new Date().toISOString(),
            }
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
      registerCycleExecutions(
        cycle.id,
        createdExecutions,
      )

      setActiveTab('executions')
    }

    if (failedOutcomes.length > 0) {
      const message =
        failedOutcomes
          .map(
            (outcome) =>
              outcome.reason?.message ??
              'Unknown execution error',
          )
          .join(' | ')

      setStartError(message)

      setCycleExecutionError(
        cycle.id,
        message,
      )
    }

    setIsStarting(false)
  }

  function handleDetailTabChange(
    nextTab,
  ) {
    if (
      nextTab !== 'artifacts' &&
      artifactPreview
    ) {
      closeArtifactPreview()
    }

    setActiveTab(nextTab)
  }

  async function handleDispatchExecutions() {
    if (
      dispatchableExecutions.length ===
      0
    ) {
      return
    }

    setIsDispatching(true)
    setStartError('')
    setCycleExecutionError(
      cycle.id,
      '',
    )

    const dispatchPayload = (
      execution
    ) => ({
      url: environmentTargetUrl,
      module_name:
        cycle.module ||
        cycle.feature ||
        cycle.name,
      mode:
        execution.source ===
        'regression_testing'
          ? 'regression'
          : 'smoke',
    })

    const recreatePayload = (
      execution
    ) => ({
      project_id: cycle.projectId,
      source: execution.source,
      feature: (
        cycle.feature ||
        cycle.module ||
        cycle.name
      ).slice(0, 240),
      test_type:
        execution.testType,
      environment: (
        environment?.name ||
        cycle.environmentId ||
        ''
      ).slice(0, 120),
      request_snapshot: {
        cycle_id: cycle.id,
        cycle_name: cycle.name,
        environment_id:
          cycle.environmentId,
        environment_url:
          environmentTargetUrl,
        cycle_type:
          cycle.cycleType,
        scope_key:
          execution.scopeKey,
        selected_asset_ids:
          selectedAssetIds,
        execution_settings:
          cycle.executionSettings,
        trigger_source:
          cycle.triggerSource ??
          'Manual',
      },
    })

    const outcomes =
      await Promise.allSettled(
        dispatchableExecutions.map(
          async (execution) => {
            let activeRunId =
              execution.runId

            let activeExecution =
              execution

            try {
              const response =
                await dispatchExecution(
                  activeRunId,
                  dispatchPayload(
                    execution,
                  ),
                )

              return {
                response,
                runId: activeRunId,
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
                  recreatePayload(
                    execution,
                  ),
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
                runId: activeRunId,
              }

              updateCycleExecution(
                cycle.id,
                execution.runId,
                activeExecution,
              )

              const response =
                await dispatchExecution(
                  activeRunId,
                  dispatchPayload(
                    activeExecution,
                  ),
                )

              return {
                response,
                runId: activeRunId,
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
          dispatchableExecutions[index]

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

          updateCycleExecution(
            cycle.id,
            runId,
            {
              ...activeExecution,
              ...response,
              runId,
              scopeKey:
                activeExecution.scopeKey,
              scopeLabel:
                activeExecution.scopeLabel,
              runner:
                activeExecution.runner,
              source:
                activeExecution.source,
              testType:
                activeExecution.testType,
            },
          )

          return
        }

        errorMessages.push(
          outcome.reason?.message ??
          `${originalExecution.scopeLabel}: dispatch failed.`,
        )
      },
    )

    if (errorMessages.length > 0) {
      const message =
        errorMessages.join(' | ')

      setStartError(message)

      setCycleExecutionError(
        cycle.id,
        message,
      )
    }

    setIsDispatching(false)
  }

  return (
    <div className="dashboard-page cycle-detail-page">
      <CycleDetailHeader
        model={
          cycleDetailShellModel.header
        }
        onBack={() =>
          navigate('/test-cycles')
        }
        onStart={handleStartCycle}
      />

      <CycleDetailSummary
        formatDateTime={
          formatDateTime
        }
        items={
          cycleDetailShellModel.summary
        }
      />

      <CycleDetailTabs
        activeTab={activeTab}
        onChange={
          handleDetailTabChange
        }
        tabs={detailTabs}
      />

      {activeTab === 'overview' && (
        <CycleOverviewTab
          formatDateTime={
            formatDateTime
          }
          model={cycleOverviewModel}
        />
      )}

      {activeTab === 'executions' && (
        <CycleExecutionsTab
          model={executionListModel}
          onDispatch={
            handleDispatchExecutions
          }
        />
      )}

      {activeTab === 'results' && (
        <CycleResultsTab
          cycleStatus={cycle.status}
          formatDateTime={formatDateTime}
          resultExecutions={
            resultExecutions
          }
          totals={resultTotals}
          unsupportedExecutions={
            unsupportedExecutions
          }
        />
      )}

      {activeTab === 'artifacts' && (
        <CycleArtifactsTab
          artifacts={cycleArtifacts}
          onClosePreview={
            closeArtifactPreview
          }
          onPreview={
            handleArtifactPreview
          }
          preview={artifactPreview}
          previewContent={
            artifactPreviewContent
          }
          previewError={
            artifactPreviewError
          }
          previewLoading={
            artifactPreviewLoading
          }
        />
      )}

      {activeTab === 'logs' && (
        <CycleLogsTab
          formatDateTime={
            formatDateTime
          }
          logs={executionLogRows}
        />
      )}

      {activeTab === 'activity' && (
        <CycleActivityTab
          formatDateTime={
            formatDateTime
          }
          items={
            executionActivityItems
          }
        />
      )}

    </div>
  )
}

export default TestCycleDetailPage
