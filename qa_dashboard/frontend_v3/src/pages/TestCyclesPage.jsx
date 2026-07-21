import {
  useMemo,
  useState,
} from 'react'

import { useNavigate } from 'react-router-dom'

import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

const previewCycles = [
  {
    id: 'TC-2026-0021',
    name: 'Uang Makan Driver',
    type: 'Feature Cycle',
    environment: 'Sandbox',
    scope: 'UI, API, E2E, Regression',
    progress: '68%',
    status: 'Running',
    tone: 'primary',
    created: 'Preview data',
    source: 'Preview',
  },
  {
    id: 'TC-2026-0020',
    name: 'Shipment Tracking',
    type: 'Change Cycle',
    environment: 'Staging',
    scope: 'API, UI, Regression',
    progress: '100%',
    status: 'Passed',
    tone: 'success',
    created: 'Preview data',
    source: 'Preview',
  },
  {
    id: 'TC-2026-0019',
    name: 'Mobospace Full Regression',
    type: 'Full Product Cycle',
    environment: 'Sandbox',
    scope: 'All Testing',
    progress: '100%',
    status: 'Failed',
    tone: 'danger',
    created: 'Preview data',
    source: 'Preview',
  },
]

const scopeLabels = {
  ui: 'UI',
  api: 'API',
  unit: 'Unit',
  e2e: 'E2E',
  regression: 'Regression',
}

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

function formatCycleScope(scope) {
  const enabledScopes = Object.entries(
    scope ?? {},
  )
    .filter(([, enabled]) => enabled)
    .map(
      ([key]) =>
        scopeLabels[key] ?? key,
    )

  return enabledScopes.length > 0
    ? enabledScopes.join(', ')
    : 'No scope'
}

function formatCreatedAt(value) {
  if (!value) {
    return 'Not available'
  }

  return new Date(value).toLocaleString()
}

function TestCyclesPage() {
  const navigate = useNavigate()

  const [searchTerm, setSearchTerm] =
    useState('')

  const [statusFilter, setStatusFilter] =
    useState('all')

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const selectedProjectId =
    useProjectEnvironmentStore(
      (state) => state.selectedProjectId,
    )

  const selectedEnvironmentId =
    useProjectEnvironmentStore(
      (state) =>
        state.selectedEnvironmentId,
    )

  const savedCycles = useTestCycleStore(
    (state) => state.cycles,
  )

  const draft = useTestCycleStore(
    (state) => state.draft,
  )

  const currentStep = useTestCycleStore(
    (state) => state.currentStep,
  )

  const hasDraft = useTestCycleStore(
    (state) => state.hasDraft,
  )

  const startNewDraft =
    useTestCycleStore(
      (state) => state.startNewDraft,
    )

  const clearDraft = useTestCycleStore(
    (state) => state.clearDraft,
  )

  const projectMap = useMemo(
    () =>
      Object.fromEntries(
        projects.map((project) => [
          project.id,
          project,
        ]),
      ),
    [projects],
  )

  const environmentMap = useMemo(
    () =>
      Object.fromEntries(
        environments.map((environment) => [
          environment.id,
          environment,
        ]),
      ),
    [environments],
  )

  const registeredCycles = useMemo(
    () =>
      savedCycles.map((cycle) => ({
        id: cycle.id,
        name: cycle.name,
        type: cycle.cycleType,
        environment:
          environmentMap[
            cycle.environmentId
          ]?.name ?? 'Not configured',
        project:
          projectMap[cycle.projectId]
            ?.name ?? 'Unknown Project',
        scope: formatCycleScope(
          cycle.scope,
        ),
        progress: `${cycle.progress ?? 0}%`,
        status: cycle.status,
        tone: getStatusTone(
          cycle.status,
        ),
        created: formatCreatedAt(
          cycle.createdAt,
        ),
        source: 'Saved',
      })),
    [
      environmentMap,
      projectMap,
      savedCycles,
    ],
  )

  const allCycles = useMemo(
    () => [
      ...registeredCycles,
      ...previewCycles,
    ],
    [registeredCycles],
  )

  const filteredCycles = useMemo(() => {
    const normalizedSearch = searchTerm
      .trim()
      .toLowerCase()

    return allCycles.filter((cycle) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        cycle.name
          .toLowerCase()
          .includes(normalizedSearch) ||
        cycle.id
          .toLowerCase()
          .includes(normalizedSearch) ||
        cycle.type
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesStatus =
        statusFilter === 'all' ||
        cycle.status.toLowerCase() ===
          statusFilter

      return (
        matchesSearch &&
        matchesStatus
      )
    })
  }, [
    allCycles,
    searchTerm,
    statusFilter,
  ])

  const draftProject = projects.find(
    (project) =>
      project.id === draft.projectId,
  )

  const draftEnvironment =
    environments.find(
      (environment) =>
        environment.id ===
        draft.environmentId,
    )

  const runningCount = allCycles.filter(
    (cycle) =>
      cycle.status === 'Running',
  ).length

  const completedCount = allCycles.filter(
    (cycle) =>
      ['Passed', 'Failed'].includes(
        cycle.status,
      ),
  ).length

  function handleCreateCycle() {
    startNewDraft(
      selectedProjectId ?? '',
      selectedEnvironmentId ?? '',
    )

    navigate('/test-cycles/new')
  }

  function handleDiscardDraft() {
    const shouldDiscard =
      window.confirm(
        'Hapus draft Test Cycle yang sedang tersimpan?',
      )

    if (!shouldDiscard) {
      return
    }

    clearDraft()
  }

  return (
    <div className="dashboard-page test-cycles-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>TESTING</span>

            <StatusBadge tone="primary">
              MVP Workspace
            </StatusBadge>
          </div>

          <h2>Test Cycles</h2>

          <p>
            Plan and execute unified testing for
            products, features, releases, endpoint
            changes, and bug fixes.
          </p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-primary"
            onClick={handleCreateCycle}
            type="button"
          >
            + Create Test Cycle
          </button>
        </div>
      </div>

      <section
        aria-label="Test cycle summary"
        className="metric-grid"
      >
        <MetricCard
          detail="Saved and preview records"
          label="All Cycles"
          tone="primary"
          value={String(allCycles.length)}
        />

        <MetricCard
          detail="Currently executing"
          label="Running"
          tone="primary"
          value={String(runningCount)}
        />

        <MetricCard
          detail="Passed or failed"
          label="Completed"
          tone="success"
          value={String(completedCount)}
        />

        <MetricCard
          detail="Saved in current workspace"
          label="Draft"
          tone="neutral"
          value={hasDraft ? '1' : '0'}
        />
      </section>

      {hasDraft && (
        <section className="dashboard-panel cycle-draft-panel">
          <div className="cycle-draft-content">
            <div>
              <div className="cycle-draft-heading">
                <StatusBadge tone="warning">
                  Draft
                </StatusBadge>

                <span>
                  Step {currentStep} of 5
                </span>
              </div>

              <h3>
                {draft.cycleName ||
                  'Untitled Test Cycle'}
              </h3>

              <p>
                {draftProject?.name ??
                  'Project not selected'}
                {' · '}
                {draftEnvironment?.name ??
                  'Environment not selected'}
                {' · '}
                {draft.cycleType}
              </p>
            </div>

            <div className="cycle-draft-actions">
              <button
                className="button button-secondary"
                onClick={handleDiscardDraft}
                type="button"
              >
                Discard
              </button>

              <button
                className="button button-primary"
                onClick={() =>
                  navigate('/test-cycles/new')
                }
                type="button"
              >
                Resume Draft
              </button>
            </div>
          </div>
        </section>
      )}

      <section className="dashboard-panel cycle-list-panel">
        <div className="panel-header">
          <div>
            <span className="panel-eyebrow">
              CYCLE REGISTRY
            </span>

            <h3>Test Cycle Records</h3>

            <p>
              Saved cycles remain in the browser
              during the frontend MVP stage.
            </p>
          </div>

          <div className="cycle-list-filters">
            <input
              aria-label="Search test cycles"
              onChange={(event) =>
                setSearchTerm(
                  event.target.value,
                )
              }
              placeholder="Search cycle..."
              type="search"
              value={searchTerm}
            />

            <select
              aria-label="Filter cycle status"
              onChange={(event) =>
                setStatusFilter(
                  event.target.value,
                )
              }
              value={statusFilter}
            >
              <option value="all">
                All statuses
              </option>

              <option value="ready">
                Ready
              </option>

              <option value="running">
                Running
              </option>

              <option value="passed">
                Passed
              </option>

              <option value="failed">
                Failed
              </option>
            </select>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="dashboard-table cycle-table">
            <thead>
              <tr>
                <th>Cycle</th>
                <th>Type</th>
                <th>Scope</th>
                <th>Environment</th>
                <th>Progress</th>
                <th>Status</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {filteredCycles.map((cycle) => (
                <tr key={`${cycle.source}-${cycle.id}`}>
                  <td>
                    <strong>{cycle.name}</strong>

                    <span>
                      {cycle.id} · {cycle.source}
                    </span>
                  </td>

                  <td>{cycle.type}</td>
                  <td>{cycle.scope}</td>
                  <td>{cycle.environment}</td>
                  <td>{cycle.progress}</td>

                  <td>
                    <StatusBadge tone={cycle.tone}>
                      {cycle.status}
                    </StatusBadge>
                  </td>

                  <td>{cycle.created}</td>

                  <td>
                    {cycle.source === 'Saved' ? (
                      <button
                        className="button button-secondary cycle-open-button"
                        onClick={() =>
                          navigate(
                            `/test-cycles/${cycle.id}`,
                          )
                        }
                        type="button"
                      >
                        Open
                      </button>
                    ) : (
                      <span className="cycle-preview-label">
                        Preview only
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default TestCyclesPage
