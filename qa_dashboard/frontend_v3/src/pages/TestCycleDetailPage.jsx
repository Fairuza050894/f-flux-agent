import { useState } from 'react'
import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import StatusBadge from '../components/StatusBadge'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

const detailTabs = [
  {
    id: 'overview',
    label: 'Overview',
  },
  {
    id: 'executions',
    label: 'Executions',
  },
  {
    id: 'results',
    label: 'Test Results',
  },
  {
    id: 'artifacts',
    label: 'Artifacts',
  },
  {
    id: 'logs',
    label: 'Logs',
  },
  {
    id: 'activity',
    label: 'Activity',
  },
]

const scopeConfiguration = [
  {
    key: 'ui',
    label: 'UI Testing',
    runner: 'UI Runner',
  },
  {
    key: 'api',
    label: 'API Testing',
    runner: 'API Runner',
  },
  {
    key: 'unit',
    label: 'Unit Testing',
    runner: 'Unit Runner',
  },
  {
    key: 'e2e',
    label: 'E2E Testing',
    runner: 'E2E Runner',
  },
  {
    key: 'regression',
    label: 'Related Regression',
    runner: 'Regression Runner',
  },
]

const evidenceConfiguration = [
  {
    key: 'screenshot',
    label: 'Screenshots',
  },
  {
    key: 'video',
    label: 'Video Recording',
  },
  {
    key: 'consoleLogs',
    label: 'Console Logs',
  },
  {
    key: 'networkLogs',
    label: 'Network Logs',
  },
  {
    key: 'errorLogs',
    label: 'Error Logs',
  },
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

function getStatusTone(status) {
  switch (status) {
    case 'Passed':
      return 'success'
    case 'Failed':
      return 'danger'
    case 'Running':
    case 'Ready':
      return 'primary'
    case 'Need Review':
      return 'warning'
    default:
      return 'neutral'
  }
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

  const cycles = useTestCycleStore(
    (state) => state.cycles,
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

  const project = projects.find(
    (record) =>
      record.id === cycle.projectId,
  )

  const environment = environments.find(
    (record) =>
      record.id === cycle.environmentId,
  )

  const selectedScopes =
    scopeConfiguration.filter(
      (scope) =>
        Boolean(cycle.scope?.[scope.key]),
    )

  const selectedEvidence =
    evidenceConfiguration.filter(
      (item) =>
        Boolean(
          cycle.executionSettings?.[
            item.key
          ],
        ),
    )

  const selectedNotifications =
    notificationConfiguration.filter(
      (item) =>
        Boolean(
          cycle.executionSettings?.[
            item.key
          ],
        ),
    )

  const selectedAssetIds =
    cycle.selectedAssetIds ?? []

  return (
    <div className="dashboard-page cycle-detail-page">
      <div className="cycle-detail-header">
        <div>
          <div className="page-heading-meta">
            <span>TEST CYCLE DETAIL</span>

            <StatusBadge
              tone={getStatusTone(cycle.status)}
            >
              {cycle.status}
            </StatusBadge>
          </div>

          <h2>{cycle.name}</h2>

          <p>
            {cycle.id}
            {' · '}
            {project?.name ?? 'Unknown Project'}
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
            disabled
            title="Backend execution integration is not connected yet."
            type="button"
          >
            Start Test Cycle
          </button>
        </div>
      </div>

      <section className="cycle-detail-summary">
        <div>
          <span>Project</span>
          <strong>
            {project?.name ?? 'Unknown Project'}
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
          <strong>{cycle.cycleType}</strong>
        </div>

        <div>
          <span>Trigger Source</span>
          <strong>
            {cycle.triggerSource ?? 'Manual'}
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
            {formatDateTime(cycle.createdAt)}
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

                <p>
                  Only selected testing types will
                  participate in this cycle.
                </p>
              </div>

              <strong className="cycle-detail-count">
                {selectedScopes.length}
              </strong>
            </div>

            <div className="cycle-runner-card-grid">
              {selectedScopes.map((scope) => (
                <article
                  className="cycle-runner-card"
                  key={scope.key}
                >
                  <div>
                    <strong>{scope.label}</strong>
                    <span>{scope.runner}</span>
                  </div>

                  <StatusBadge tone="neutral">
                    Not Started
                  </StatusBadge>
                </article>
              ))}
            </div>
          </section>

          <section className="dashboard-panel cycle-detail-panel">
            <div className="panel-header">
              <div>
                <span className="panel-eyebrow">
                  TEST ASSETS
                </span>

                <h3>Selected Test Assets</h3>

                <p>
                  Asset IDs captured when the cycle
                  was created.
                </p>
              </div>

              <strong className="cycle-detail-count">
                {selectedAssetIds.length}
              </strong>
            </div>

            {selectedAssetIds.length > 0 ? (
              <div className="cycle-asset-id-grid">
                {selectedAssetIds.map(
                  (assetId) => (
                    <div key={assetId}>
                      <span>Asset ID</span>
                      <strong>{assetId}</strong>
                    </div>
                  ),
                )}
              </div>
            ) : (
              <EmptyExecutionState
                description="No Test Assets were selected for this cycle."
                title="No Test Assets"
              />
            )}
          </section>

          <section className="dashboard-panel cycle-detail-panel">
            <div className="panel-header">
              <div>
                <span className="panel-eyebrow">
                  EXECUTION CONFIGURATION
                </span>

                <h3>Runner Settings</h3>

                <p>
                  Execution behaviour, evidence,
                  and notification configuration.
                </p>
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

                {selectedEvidence.length > 0 ? (
                  <ul>
                    {selectedEvidence.map(
                      (item) => (
                        <li key={item.key}>
                          {item.label}
                        </li>
                      ),
                    )}
                  </ul>
                ) : (
                  <p>No evidence selected.</p>
                )}
              </div>

              <div>
                <h4>Notifications</h4>

                {selectedNotifications.length >
                0 ? (
                  <ul>
                    {selectedNotifications.map(
                      (item) => (
                        <li key={item.key}>
                          {item.label}
                        </li>
                      ),
                    )}
                  </ul>
                ) : (
                  <p>
                    No notification channels selected.
                  </p>
                )}
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
                Runner execution will become available
                after FastAPI integration.
              </p>
            </div>
          </div>

          <div className="cycle-execution-list">
            {selectedScopes.map((scope) => (
              <article
                className="cycle-execution-row"
                key={scope.key}
              >
                <div>
                  <strong>{scope.label}</strong>
                  <span>{scope.runner}</span>
                </div>

                <div className="cycle-execution-progress">
                  <span />
                </div>

                <span>0%</span>

                <StatusBadge tone="neutral">
                  Not Started
                </StatusBadge>
              </article>
            ))}
          </div>
        </section>
      )}

      {activeTab === 'results' && (
        <section className="dashboard-panel cycle-detail-panel">
          <EmptyExecutionState
            description="Test results will appear after the cycle has been executed."
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
