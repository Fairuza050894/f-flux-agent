import { Link } from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatResultStatus,
  getResultStatusTone,
} from '../../features/results/resultFormatters'

function DashboardCyclePanel({
  cycle,
}) {
  if (!cycle) {
    return (
      <section className="dashboard-panel main-dashboard-panel main-dashboard-cycle-panel">
        <div className="main-dashboard-empty">
          <strong>
            No Test Cycles available
          </strong>

          <p>
            Create a Test Cycle to begin
            collecting execution and quality data.
          </p>

          <Link
            className="button button-primary"
            to="/test-cycles/new"
          >
            Create Test Cycle
          </Link>
        </div>
      </section>
    )
  }

  return (
    <section className="dashboard-panel main-dashboard-panel main-dashboard-cycle-panel">
      <header className="main-dashboard-panel-header">
        <div>
          <span className="panel-eyebrow">
            {cycle.active
              ? 'ACTIVE TEST CYCLE'
              : 'LATEST TEST CYCLE'}
          </span>

          <h3>{cycle.name}</h3>

          <p>
            {[
              cycle.cycleType,
              cycle.projectName,
              cycle.environmentName,
            ].join(' · ')}
          </p>
        </div>

        <StatusBadge
          tone={getResultStatusTone(
            cycle.status,
          )}
        >
          {formatResultStatus(
            cycle.status,
          )}
        </StatusBadge>
      </header>

      <div className="main-dashboard-cycle-progress">
        <div>
          <span>Overall progress</span>

          <strong>
            {cycle.progress}%
          </strong>
        </div>

        <div
          aria-label="Overall test cycle progress"
          aria-valuemax="100"
          aria-valuemin="0"
          aria-valuenow={cycle.progress}
          className="main-dashboard-progress-track"
          role="progressbar"
        >
          <span
            style={{
              width:
                `${cycle.progress}%`,
            }}
          />
        </div>

        <p>
          {cycle.executionCount}
          {' '}
          execution
          {cycle.executionCount === 1
            ? ''
            : 's'}
          {' · '}
          {cycle.resultExecutionCount}
          {' '}
          with results
        </p>
      </div>

      {cycle.executions.length > 0 ? (
        <div className="main-dashboard-execution-table-wrapper">
          <table className="main-dashboard-execution-table">
            <thead>
              <tr>
                <th scope="col">
                  Scope
                </th>

                <th scope="col">
                  Runner
                </th>

                <th scope="col">
                  Progress
                </th>

                <th scope="col">
                  Status
                </th>
              </tr>
            </thead>

            <tbody>
              {cycle.executions.map(
                (execution) => (
                  <tr
                    key={
                      execution.runId ??
                      execution.scopeKey ??
                      execution.scopeLabel
                    }
                  >
                    <td>
                      <strong>
                        {execution.scopeLabel}
                      </strong>
                    </td>

                    <td>
                      {execution.runner}
                    </td>

                    <td>
                      <div className="main-dashboard-execution-progress">
                        <div>
                          <span
                            style={{
                              width:
                                `${execution.progress}%`,
                            }}
                          />
                        </div>

                        <strong>
                          {execution.progress}%
                        </strong>
                      </div>
                    </td>

                    <td>
                      <StatusBadge
                        tone={execution.tone}
                      >
                        {formatResultStatus(
                          execution.status,
                        )}
                      </StatusBadge>
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="main-dashboard-inline-empty">
          No execution records have been
          created for this Test Cycle.
        </p>
      )}

      <footer className="main-dashboard-panel-actions">
        <Link
          className="button button-secondary"
          to="/history"
        >
          View History
        </Link>

        <Link
          className="button button-primary"
          to={`/test-cycles/${encodeURIComponent(
            cycle.id,
          )}`}
        >
          View Cycle
        </Link>
      </footer>
    </section>
  )
}

export default DashboardCyclePanel
