import { Link } from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatReportDateTime,
  formatReportNumber,
  formatReportPercentage,
} from '../../features/reports/reportFormatters'
import {
  formatResultStatus,
  getResultStatusTone,
} from '../../features/results/resultFormatters'

function ReportCycleTable({
  rows,
}) {
  return (
    <div className="report-table-wrapper">
      <table className="report-table report-cycle-table">
        <colgroup>
          <col className="report-cycle-column-name" />
          <col className="report-cycle-column-context" />
          <col className="report-cycle-column-results" />
          <col className="report-cycle-column-issues" />
          <col className="report-cycle-column-rate" />
          <col className="report-cycle-column-quality" />
          <col className="report-cycle-column-updated" />
          <col className="report-cycle-column-action" />
        </colgroup>

        <thead>
          <tr>
            <th scope="col">Test Cycle</th>
            <th scope="col">Context</th>
            <th scope="col">Results</th>
            <th scope="col">Issues</th>
            <th scope="col">Pass Rate</th>
            <th scope="col">Quality</th>
            <th scope="col">Last Run</th>
            <th
              className="report-action-heading"
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
                <div className="report-cycle-identity">
                  <strong title={row.name}>
                    {row.name}
                  </strong>

                  <code title={row.id}>
                    {row.id}
                  </code>

                  <span>
                    {[
                      row.cycleType,
                      row.releaseVersion ||
                        'No release',
                    ].join(' · ')}
                  </span>
                </div>
              </td>

              <td>
                <div className="report-cycle-context">
                  <strong>
                    {row.projectName}
                  </strong>

                  <span>
                    {row.environmentName}
                  </span>
                </div>
              </td>

              <td>
                <div className="report-result-pair">
                  <span>
                    Passed
                    {' '}
                    <strong>
                      {formatReportNumber(
                        row.totals.passed,
                      )}
                    </strong>
                  </span>

                  <span>
                    Executed
                    {' '}
                    <strong>
                      {formatReportNumber(
                        row.totals.totalExecuted,
                      )}
                    </strong>
                  </span>
                </div>
              </td>

              <td>
                <div className="report-result-pair">
                  <span>
                    Failed
                    {' '}
                    <strong>
                      {formatReportNumber(
                        row.totals.failed,
                      )}
                    </strong>
                  </span>

                  <span>
                    Review
                    {' '}
                    <strong>
                      {formatReportNumber(
                        row.totals.needReview,
                      )}
                    </strong>
                  </span>
                </div>
              </td>

              <td>
                <strong className="report-pass-rate">
                  {formatReportPercentage(
                    row.totals.passRate,
                  )}
                </strong>
              </td>

              <td>
                <StatusBadge
                  tone={getResultStatusTone(
                    row.qualityStatus,
                  )}
                >
                  {formatResultStatus(
                    row.qualityStatus,
                  )}
                </StatusBadge>
              </td>

              <td>
                <div className="report-cycle-updated">
                  <strong>
                    {formatReportDateTime(
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
                  </span>
                </div>
              </td>

              <td className="report-action-cell">
                <Link
                  className="button button-secondary report-view-button"
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

export default ReportCycleTable
