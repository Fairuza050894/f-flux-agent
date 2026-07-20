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
    created: 'Today',
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
    created: 'Yesterday',
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
    created: '18 Jul 2026',
  },
]

function TestCyclesPage() {
  const navigate = useNavigate()

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
              Static Preview
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
          detail="Preview execution records"
          label="All Cycles"
          tone="primary"
          value="3"
        />

        <MetricCard
          detail="Currently executing"
          label="Running"
          tone="primary"
          value="1"
        />

        <MetricCard
          detail="Finished executions"
          label="Completed"
          tone="success"
          value="2"
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

            <h3>Recent Test Cycles</h3>

            <p>
              Current records are preview data until
              the backend cycle registry is connected.
            </p>
          </div>

          <div className="cycle-list-filters">
            <input
              aria-label="Search test cycles"
              placeholder="Search cycle..."
              type="search"
            />

            <select
              aria-label="Filter cycle status"
              defaultValue="all"
            >
              <option value="all">
                All statuses
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
              </tr>
            </thead>

            <tbody>
              {previewCycles.map((cycle) => (
                <tr key={cycle.id}>
                  <td>
                    <strong>
                      {cycle.name}
                    </strong>

                    <span>{cycle.id}</span>
                  </td>

                  <td>{cycle.type}</td>
                  <td>{cycle.scope}</td>
                  <td>{cycle.environment}</td>
                  <td>{cycle.progress}</td>

                  <td>
                    <StatusBadge
                      tone={cycle.tone}
                    >
                      {cycle.status}
                    </StatusBadge>
                  </td>

                  <td>{cycle.created}</td>
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
