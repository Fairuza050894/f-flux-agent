import { Link } from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatDashboardDateTime,
  formatDashboardNumber,
  formatDashboardPercentage,
} from '../../features/dashboard/dashboardFormatters'
import {
  formatResultStatus,
  getResultStatusTone,
} from '../../features/results/resultFormatters'

function DashboardRecentCycles({
  cycles,
}) {
  return (
    <section className="dashboard-panel main-dashboard-panel main-dashboard-recent-panel">
      <header className="main-dashboard-panel-header">
        <div>
          <span className="panel-eyebrow">
            RECENT ACTIVITY
          </span>

          <h3>Recent Test Cycles</h3>
        </div>

        <Link
          className="text-link"
          to="/history"
        >
          View all
        </Link>
      </header>

      {cycles.length > 0 ? (
        <div className="main-dashboard-table-wrapper">
          <table className="main-dashboard-recent-table">
            <thead>
              <tr>
                <th scope="col">
                  Test Cycle
                </th>

                <th scope="col">
                  Context
                </th>

                <th scope="col">
                  Results
                </th>

                <th scope="col">
                  Quality
                </th>

                <th scope="col">
                  Last Activity
                </th>

                <th
                  className="main-dashboard-action-heading"
                  scope="col"
                >
                  Action
                </th>
              </tr>
            </thead>

            <tbody>
              {cycles.map((cycle) => (
                <tr key={cycle.id}>
                  <td>
                    <div className="main-dashboard-cycle-identity">
                      <strong>
                        {cycle.name}
                      </strong>

                      <code>
                        {cycle.id}
                      </code>
                    </div>
                  </td>

                  <td>
                    <strong>
                      {cycle.projectName}
                    </strong>

                    <span>
                      {cycle.environmentName}
                    </span>
                  </td>

                  <td>
                    <strong>
                      {formatDashboardNumber(
                        cycle.totals
                          .passed,
                      )}
                      {' / '}
                      {formatDashboardNumber(
                        cycle.totals
                          .totalExecuted,
                      )}
                    </strong>

                    <span>
                      {formatDashboardPercentage(
                        cycle.totals
                          .passRate,
                      )}
                    </span>
                  </td>

                  <td>
                    <StatusBadge
                      tone={getResultStatusTone(
                        cycle
                          .qualityStatus,
                      )}
                    >
                      {formatResultStatus(
                        cycle
                          .qualityStatus,
                      )}
                    </StatusBadge>
                  </td>

                  <td>
                    {formatDashboardDateTime(
                      cycle.lastActivityAt,
                    )}
                  </td>

                  <td className="main-dashboard-action-cell">
                    <Link
                      className="button button-secondary main-dashboard-view-button"
                      to={`/test-cycles/${encodeURIComponent(
                        cycle.id,
                      )}`}
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="main-dashboard-empty main-dashboard-empty-compact">
          <strong>
            No recent Test Cycles
          </strong>

          <p>
            Recently created and executed Test
            Cycles will appear here.
          </p>
        </div>
      )}
    </section>
  )
}

export default DashboardRecentCycles
