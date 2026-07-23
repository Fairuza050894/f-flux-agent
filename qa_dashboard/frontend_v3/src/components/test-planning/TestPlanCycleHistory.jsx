import {
  Link,
} from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatTestPlanDate,
} from '../../features/test-planning/testPlanFormatters'

function getCycleStatusTone(
  status,
) {
  const normalizedStatus =
    String(status ?? '')
      .trim()
      .toLowerCase()

  if (
    normalizedStatus === 'passed' ||
    normalizedStatus === 'completed'
  ) {
    return 'success'
  }

  if (
    normalizedStatus === 'failed' ||
    normalizedStatus === 'error'
  ) {
    return 'danger'
  }

  if (
    normalizedStatus === 'running' ||
    normalizedStatus === 'in progress'
  ) {
    return 'primary'
  }

  if (
    normalizedStatus === 'ready'
  ) {
    return 'warning'
  }

  return 'neutral'
}

function TestPlanCycleHistory({
  cycles,
}) {
  return (
    <section className="dashboard-panel test-plan-detail-section">
      <div className="test-plan-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            HISTORY
          </span>

          <h3>Created Test Cycles</h3>

          <p>
            Test Cycles created from this
            reusable plan.
          </p>
        </div>

        <strong className="test-plan-detail-count">
          {cycles.length} Cycles
        </strong>
      </div>

      <div className="test-plan-detail-table-wrapper">
        <table className="test-plan-detail-table test-plan-cycle-history-table">
          <thead>
            <tr>
              <th>Test Cycle</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Environment</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {cycles.length > 0 ? (
              cycles.map((cycle) => (
                <tr key={cycle.id}>
                  <td>
                    <strong>
                      {cycle.name ||
                        'Untitled Test Cycle'}
                    </strong>

                    <span>
                      {cycle.id}
                    </span>
                  </td>

                  <td>
                    <StatusBadge
                      tone={getCycleStatusTone(
                        cycle.status,
                      )}
                    >
                      {cycle.status ??
                        'Unknown'}
                    </StatusBadge>
                  </td>

                  <td>
                    <strong className="test-plan-cycle-progress">
                      {Number(
                        cycle.progress ?? 0,
                      )}
                      %
                    </strong>
                  </td>

                  <td>
                    {cycle.environmentId ||
                      'Not configured'}
                  </td>

                  <td>
                    {formatTestPlanDate(
                      cycle.createdAt,
                    )}
                  </td>

                  <td>
                    <Link
                      className="button button-secondary test-plan-action-button"
                      to={`/test-cycles/${cycle.id}`}
                    >
                      View Cycle
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  className="test-plan-detail-empty-cell"
                  colSpan="6"
                >
                  <strong>
                    No Test Cycles created
                  </strong>

                  <span>
                    Create a Test Cycle from
                    this plan to start its
                    execution history.
                  </span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default TestPlanCycleHistory
