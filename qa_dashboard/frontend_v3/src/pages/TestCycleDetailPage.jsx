import {
  useEffect,
  useState,
} from 'react'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import StatusBadge from '../components/StatusBadge'
import {
  createExecution,
  dispatchExecution,
  getExecution,
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

const evidenceConfiguration = [
  { key: 'screenshot', label: 'Screenshots' },
  { key: 'video', label: 'Video Recording' },
  { key: 'consoleLogs', label: 'Console Logs' },
  { key: 'networkLogs', label: 'Network Logs' },
  { key: 'errorLogs', label: 'Error Logs' },
]

const notificationConfiguration = [
  {
    key: 'telegramTesting',
    label: 'Telegram Testing',
  },
  {
    key: 'telegramDocumentation',
    label: 'Telegram Documentation',
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

function formatStatus(status) {
  const normalized =
    normalizeStatus(status)

  if (!normalized) {
    return 'Not Started'
  }

  return normalized
    .split('_')
    .map(
      (part) =>
        part.charAt(0).toUpperCase()
        + part.slice(1),
    )
    .join(' ')
}

function getStatusTone(status) {
  const normalized =
    normalizeStatus(status)

  if (
    ['passed', 'completed'].includes(
      normalized,
    )
  ) {
    return 'success'
  }

  if (
    ['failed', 'error'].includes(
      normalized,
    )
  ) {
    return 'danger'
  }

  if (
    [
      'running',
      'ready',
      'queued',
      'pending',
      'created',
    ].includes(normalized)
  ) {
    return 'primary'
  }

  if (
    [
      'need_review',
      'cancelled',
    ].includes(normalized)
  ) {
    return 'warning'
  }

  return 'neutral'
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

function EmptyExecutionState({
  title,
  description,
}) {
  return (
    <div className="cycle-empty-state">
      <div className="cycle-empty-icon">
        —
      </div>

      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  )
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

  const selectedEvidence = cycle
    ? evidenceConfiguration.filter(
        (item) =>
          Boolean(
            cycle.executionSettings?.[
              item.key
            ],
          ),
      )
    : []

  const selectedNotifications = cycle
    ? notificationConfiguration.filter(
        (item) =>
          Boolean(
            cycle.executionSettings?.[
              item.key
            ],
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
      <div className="cycle-detail-header">
        <div>
          <div className="page-heading-meta">
            <span>TEST CYCLE DETAIL</span>

            <StatusBadge
              tone={getStatusTone(
                cycle.status,
              )}
            >
              {cycle.status}
            </StatusBadge>
          </div>

          <h2>{cycle.name}</h2>

          <p>
            {cycle.id}
            {' · '}
            {project?.name ??
              'Unknown Project'}
            {' · '}
            {environment?.name ??
              'Environment not configured'}
          </p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-secondary"
            onClick={() =>
              navigate('/test-cycles')
            }
            type="button"
          >
            Back to Cycles
          </button>

          <button
            className="button button-primary"
            disabled={
              isStarting ||
              scopesWithoutExecution.length ===
                0
            }
            onClick={handleStartCycle}
            type="button"
          >
            {isStarting
              ? 'Creating Executions...'
              : scopesWithoutExecution.length >
                  0
                ? executions.length > 0
                  ? 'Retry Missing Executions'
                  : 'Start Test Cycle'
                : 'Executions Created'}
          </button>
        </div>
      </div>

      {(startError ||
        cycle.executionError) && (
        <div
          className="cycle-start-error"
          role="alert"
        >
          <strong>
            Execution could not be created
          </strong>

          <p>
            {startError ||
              cycle.executionError}
          </p>
        </div>
      )}

      <section className="cycle-detail-summary">
        <div>
          <span>Project</span>
          <strong>
            {project?.name ??
              'Unknown Project'}
          </strong>
        </div>

        <div>
          <span>Environment</span>
          <strong>
            {environment?.name ??
              'Not configured'}
          </strong>
        </div>

        <div>
          <span>Cycle Type</span>
          <strong>
            {cycle.cycleType}
          </strong>
        </div>

        <div>
          <span>Trigger Source</span>
          <strong>
            {cycle.triggerSource ??
              'Manual'}
          </strong>
        </div>

        <div>
          <span>Progress</span>
          <strong>
            {cycle.progress ?? 0}%
          </strong>
        </div>

        <div>
          <span>Created</span>
          <strong>
            {formatDateTime(
              cycle.createdAt,
            )}
          </strong>
        </div>
      </section>

      <nav
        aria-label="Test Cycle detail tabs"
        className="cycle-detail-tabs"
      >
        {detailTabs.map((tab) => (
          <button
            className={[
              'cycle-detail-tab',
              activeTab === tab.id
                ? 'cycle-detail-tab-active'
                : '',
            ]
              .filter(Boolean)
              .join(' ')}
            key={tab.id}
            onClick={() =>
              setActiveTab(tab.id)
            }
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {activeTab === 'overview' && (
        <div className="cycle-detail-content">
          <section className="dashboard-panel cycle-detail-panel">
            <div className="panel-header">
              <div>
                <span className="panel-eyebrow">
                  CYCLE CONTEXT
                </span>

                <h3>Overview</h3>

                <p>
                  Configuration captured from the
                  Create Test Cycle wizard.
                </p>
              </div>

              <StatusBadge tone="primary">
                Saved Record
              </StatusBadge>
            </div>

            <div className="cycle-detail-context-grid">
              <div>
                <span>Release / Version</span>
                <strong>
                  {cycle.releaseVersion ||
                    'Not specified'}
                </strong>
              </div>

              <div>
                <span>Module</span>
                <strong>
                  {cycle.module ||
                    'Full Product'}
                </strong>
              </div>

              <div>
                <span>Feature</span>
                <strong>
                  {cycle.feature ||
                    'Not specified'}
                </strong>
              </div>

              <div>
                <span>Change Type</span>
                <strong>
                  {cycle.cycleType ===
                  'Change Cycle'
                    ? cycle.changeType
                    : 'Not applicable'}
                </strong>
              </div>

              <div>
                <span>Reference</span>
                <strong>
                  {cycle.reference ||
                    'Not specified'}
                </strong>
              </div>

              <div>
                <span>Last Updated</span>
                <strong>
                  {formatDateTime(
                    cycle.updatedAt,
                  )}
                </strong>
              </div>
            </div>

            <div className="cycle-detail-description">
              <span>Description</span>

              <p>
                {cycle.description ||
                  'No cycle description provided.'}
              </p>
            </div>
          </section>

          <section className="dashboard-panel cycle-detail-panel">
            <div className="panel-header">
              <div>
                <span className="panel-eyebrow">
                  TESTING SCOPE
                </span>

                <h3>Selected Runners</h3>
              </div>

              <strong className="cycle-detail-count">
                {selectedScopes.length}
              </strong>
            </div>

            <div className="cycle-runner-card-grid">
              {selectedScopes.map(
                (scope) => {
                  const execution =
                    executionByScope[
                      scope.key
                    ]

                  return (
                    <article
                      className="cycle-runner-card"
                      key={scope.key}
                    >
                      <div>
                        <strong>
                          {scope.label}
                        </strong>

                        <span>
                          {scope.runner}
                        </span>
                      </div>

                      <StatusBadge
                        tone={getStatusTone(
                          execution?.status,
                        )}
                      >
                        {execution
                          ? formatStatus(
                              execution.status,
                            )
                          : 'Not Started'}
                      </StatusBadge>
                    </article>
                  )
                },
              )}
            </div>
          </section>

          <section className="dashboard-panel cycle-detail-panel">
            <div className="panel-header">
              <div>
                <span className="panel-eyebrow">
                  TEST ASSETS
                </span>

                <h3>Selected Test Assets</h3>
              </div>

              <strong className="cycle-detail-count">
                {selectedAssetIds.length}
              </strong>
            </div>

            <div className="cycle-asset-id-grid">
              {selectedAssetIds.map(
                (assetId) => (
                  <div key={assetId}>
                    <span>Asset ID</span>
                    <strong>
                      {assetId}
                    </strong>
                  </div>
                ),
              )}
            </div>
          </section>

          <section className="dashboard-panel cycle-detail-panel">
            <div className="panel-header">
              <div>
                <span className="panel-eyebrow">
                  EXECUTION CONFIGURATION
                </span>

                <h3>Runner Settings</h3>
              </div>
            </div>

            <div className="cycle-detail-context-grid cycle-detail-context-grid-small">
              <div>
                <span>Execution Mode</span>
                <strong>
                  {cycle.executionSettings
                    ?.executionMode ??
                    'Sequential'}
                </strong>
              </div>

              <div>
                <span>Stop Policy</span>
                <strong>
                  {cycle.executionSettings
                    ?.stopPolicy ??
                    'Critical Failure'}
                </strong>
              </div>

              <div>
                <span>Evidence Types</span>
                <strong>
                  {selectedEvidence.length}
                </strong>
              </div>

              <div>
                <span>Notifications</span>
                <strong>
                  {selectedNotifications.length}
                </strong>
              </div>
            </div>

            <div className="cycle-detail-columns">
              <div>
                <h4>Evidence</h4>

                <ul>
                  {selectedEvidence.map(
                    (item) => (
                      <li key={item.key}>
                        {item.label}
                      </li>
                    ),
                  )}
                </ul>
              </div>

              <div>
                <h4>Notifications</h4>

                <ul>
                  {selectedNotifications.map(
                    (item) => (
                      <li key={item.key}>
                        {item.label}
                      </li>
                    ),
                  )}
                </ul>
              </div>
            </div>
          </section>
        </div>
      )}

      {activeTab === 'executions' && (
        <section className="dashboard-panel cycle-detail-panel">
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                RUNNER EXECUTIONS
              </span>

              <h3>Executions</h3>

              <p>
                Status and progress are retrieved
                from the FastAPI Execution Store.
              </p>
            </div>

            <div className="cycle-execution-header-actions">
              <button
                className="button button-primary"
                disabled={
                  isDispatching ||
                  dispatchableExecutions.length ===
                    0
                }
                onClick={handleDispatchExecutions}
                type="button"
              >
                {isDispatching
                  ? 'Dispatching...'
                  : dispatchableExecutions.length >
                      0
                    ? 'Run Queued Executions'
                    : 'No Queued Executions'}
              </button>
            </div>
          </div>

          <div className="cycle-execution-list">
            {selectedScopes.map(
              (scope) => {
                const execution =
                  executionByScope[
                    scope.key
                  ]

                const progress =
                  Number(
                    execution?.progress ??
                    0,
                  )

                return (
                  <article
                    className="cycle-execution-row"
                    key={scope.key}
                  >
                    <div>
                      <strong>
                        {scope.label}
                      </strong>

                      <span>
                        {execution?.runId ??
                          scope.runner}
                      </span>

                      {execution?.current_stage && (
                        <em>
                          {
                            execution.current_stage
                          }
                        </em>
                      )}
                    </div>

                    <div className="cycle-execution-progress">
                      <span
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              0,
                              progress,
                            ),
                          )}%`,
                        }}
                      />
                    </div>

                    <span>{progress}%</span>

                    <StatusBadge
                      tone={getStatusTone(
                        execution?.status,
                      )}
                    >
                      {execution
                        ? formatStatus(
                            execution.status,
                          )
                        : 'Not Started'}
                    </StatusBadge>
                  </article>
                )
              },
            )}
          </div>

          {executions.length > 0 && (
            <div className="cycle-execution-note">
              <strong>
                Execution records created
              </strong>

              <p>
                The Execution Store is now connected.
                Runner dispatch and real test progress
                will be connected in the next phase.
              </p>
            </div>
          )}
        </section>
      )}

      {activeTab === 'results' && (
        <section className="dashboard-panel cycle-detail-panel">
          <EmptyExecutionState
            description="Test results will appear after the runner completes an execution."
            title="No test results available"
          />
        </section>
      )}

      {activeTab === 'artifacts' && (
        <section className="dashboard-panel cycle-detail-panel">
          <EmptyExecutionState
            description="Screenshots, videos, reports, and generated files will appear after execution."
            title="No artifacts generated"
          />
        </section>
      )}

      {activeTab === 'logs' && (
        <section className="dashboard-panel cycle-detail-panel">
          <EmptyExecutionState
            description="Runner, console, network, error, and system logs will appear after execution."
            title="No execution logs available"
          />
        </section>
      )}

      {activeTab === 'activity' && (
        <section className="dashboard-panel cycle-detail-panel">
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                AUDIT ACTIVITY
              </span>

              <h3>Activity</h3>
            </div>
          </div>

          <div className="cycle-activity-list">
            {executions.map(
              (execution) => (
                <article
                  key={execution.runId}
                >
                  <span className="cycle-activity-dot" />

                  <div>
                    <strong>
                      {execution.scopeLabel}
                      {' '}
                      execution created
                    </strong>

                    <p>
                      Backend run ID:
                      {' '}
                      {execution.runId}
                    </p>

                    <span>
                      {formatDateTime(
                        execution.created_at ??
                        execution.createdAt,
                      )}
                    </span>
                  </div>
                </article>
              ),
            )}

            <article>
              <span className="cycle-activity-dot" />

              <div>
                <strong>
                  Test Cycle record created
                </strong>

                <p>
                  Created manually from the Test Cycle
                  wizard with status Ready.
                </p>

                <span>
                  {formatDateTime(
                    cycle.createdAt,
                  )}
                </span>
              </div>
            </article>
          </div>
        </section>
      )}
    </div>
  )
}

export default TestCycleDetailPage
