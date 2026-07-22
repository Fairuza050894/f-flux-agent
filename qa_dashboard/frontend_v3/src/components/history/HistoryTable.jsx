import { Link } from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatHistoryDateTime,
  formatHistoryDuration,
  formatHistoryResultCount,
  formatHistoryStatus,
  getHistoryStatusTone,
} from '../../features/history/historyFormatters'

function HistoryResults({
  results,
}) {
  const totalResults =
    results.passed +
    results.failed +
    results.needReview +
    results.skipped

  if (totalResults === 0) {
    return (
      <span className="history-no-results">
        No metrics
      </span>
    )
  }

  return (
    <dl
      aria-label="Test result metrics"
      className="history-result-metrics"
    >
      <div>
        <dt>Passed</dt>
        <dd>
          {formatHistoryResultCount(
            results.passed,
          )}
        </dd>
      </div>

      <div>
        <dt>Failed</dt>
        <dd>
          {formatHistoryResultCount(
            results.failed,
          )}
        </dd>
      </div>

      <div>
        <dt>Review</dt>
        <dd>
          {formatHistoryResultCount(
            results.needReview,
          )}
        </dd>
      </div>
    </dl>
  )
}

function HistoryTable({
  rows,
}) {
  return (
    <div className="history-table-wrapper">
      <table className="history-table">
        <colgroup>
          <col className="history-column-cycle" />
          <col className="history-column-context" />
          <col className="history-column-type" />
          <col className="history-column-run" />
          <col className="history-column-results" />
          <col className="history-column-status" />
          <col className="history-column-action" />
        </colgroup>

        <thead>
          <tr>
            <th scope="col">
              Test Cycle
            </th>

            <th scope="col">
              Context
            </th>

            <th scope="col">
              Type
            </th>

            <th scope="col">
              Last Run
            </th>

            <th scope="col">
              Results
            </th>

            <th scope="col">
              Status
            </th>

            <th
              className="history-action-heading"
              scope="col"
            >
              Action
            </th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <div className="history-cycle-identity">
                  <strong title={row.name}>
                    {row.name}
                  </strong>

                  <code title={row.id}>
                    {row.id}
                  </code>

                  {(row.module ||
                    row.feature) && (
                    <span>
                      {[
                        row.module,
                        row.feature,
                      ]
                        .filter(Boolean)
                        .join(' · ')}
                    </span>
                  )}
                </div>
              </td>

              <td>
                <div className="history-context">
                  <strong>
                    {row.projectName}
                  </strong>

                  <span>
                    {row.environmentName}
                  </span>
                </div>
              </td>

              <td>
                <div className="history-type">
                  <strong>
                    {row.cycleType}
                  </strong>

                  <span>
                    {row.releaseVersion ||
                      'No release'}
                  </span>
                </div>
              </td>

              <td>
                <div className="history-run">
                  <strong>
                    {formatHistoryDateTime(
                      row.lastRunAt,
                    )}
                  </strong>

                  <span>
                    {row.executionCount}
                    {' '}
                    execution
                    {row.executionCount === 1
                      ? ''
                      : 's'}
                    {' · '}
                    {formatHistoryDuration(
                      row.durationMs,
                    )}
                  </span>
                </div>
              </td>

              <td>
                <HistoryResults
                  results={row.results}
                />
              </td>

              <td>
                <div className="history-status">
                  <StatusBadge
                    tone={getHistoryStatusTone(
                      row.status,
                    )}
                  >
                    {formatHistoryStatus(
                      row.status,
                    )}
                  </StatusBadge>

                  <span>
                    {row.progress}%
                  </span>
                </div>
              </td>

              <td className="history-action-cell">
                <Link
                  className="button button-secondary history-view-button"
                  to={`/test-cycles/${encodeURIComponent(
                    row.id,
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
  )
}

export default HistoryTable
