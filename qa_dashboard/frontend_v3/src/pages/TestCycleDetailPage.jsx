import {
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
import CycleTestAssetsTab from '../components/test-cycle-detail/CycleTestAssetsTab'
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
  useExecutionSynchronization,
} from '../features/executions/useExecutionSynchronization'
import {
  useTestCycleExecutionOrchestrator,
} from '../features/executions/useTestCycleExecutionOrchestrator'
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
  buildCycleAssetVersionComparison,
} from '../features/test-cycle-detail/cycleAssetVersionComparison'
import {
  getExecutionArtifactUrl,
} from '../services/executionService'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestAssetStore } from '../stores/testAssetStore'
import { useTestCycleStore } from '../stores/testCycleStore'

const detailTabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'assets', label: 'Test Assets' },
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

  const assets = useTestAssetStore(
    (state) => state.assets,
  )

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

  const {
    dispatchableExecutions,
    dispatchExecutions:
      handleDispatchExecutions,
    failedScopeCount,
    isDispatching,
    isRerunning,
    isRetrying,
    isStarting,
    rerunSelectedScopes:
      handleRerunSelectedScopes,
    retryFailedScopes:
      handleRetryFailedScopes,
    scopesWithoutExecution,
    startCycle:
      handleStartCycle,
    startError,
  } = useTestCycleExecutionOrchestrator({
    cycle,
    environment,
    environmentTargetUrl,
    executions,

    onExecutionsCreated: () => {
      setActiveTab('executions')
    },

    registerCycleExecutions,
    selectedScopes,
    setCycleExecutionError,
    updateCycleExecution,
  })

  const executionListModel =
    buildExecutionListModel({
      dispatchableCount:
        dispatchableExecutions.length,
      executions,
      failedScopeCount,
      isDispatching,
      isRerunning,
      isRetrying,
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

  const cycleOverviewModel =
    buildCycleOverviewModel({
      cycle,
      executions,
      selectedScopes,
    })

  const cycleAssetComparison =
    buildCycleAssetVersionComparison({
      assets,
      cycle,
    })

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

  useExecutionSynchronization({
    cycleId: cycle?.id,
    executions,
    updateCycleExecution,
  })

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

      {activeTab === 'assets' && (
        <CycleTestAssetsTab
          comparison={
            cycleAssetComparison
          }
        />
      )}

      {activeTab === 'executions' && (
        <CycleExecutionsTab
          model={executionListModel}
          onDispatch={
            handleDispatchExecutions
          }
          onRerunSelected={
            handleRerunSelectedScopes
          }
          onRetryFailed={
            handleRetryFailedScopes
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
