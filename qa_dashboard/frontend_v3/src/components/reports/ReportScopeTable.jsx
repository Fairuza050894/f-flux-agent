import StatusBadge from '../StatusBadge'
import {
  formatReportNumber,
  formatReportPercentage,
} from '../../features/reports/reportFormatters'
import {
  formatResultStatus,
  getResultStatusTone,
} from '../../features/results/resultFormatters'

function ReportScopeTable({
  rows,
}) {
  return (
    <div className="report-table-wrapper">
      <table className="report-table report-scope-table">
        <thead>
          <tr>
            <th scope="col">Scope</th>
            <th scope="col">Executions</th>
            <th scope="col">Passed</th>
            <th scope="col">Failed</th>
            <th scope="col">Need Review</th>
            <th scope="col">Skipped</th>
            <th scope="col">Pass Rate</th>
            <th scope="col">Quality</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td>
                <strong>
                  {row.label}
                </strong>

                {row.unsupportedExecutionCount >
                  0 && (
                  <span>
                    {row.unsupportedExecutionCount}
                    {' '}
                    unsupported
                  </span>
                )}
              </td>

              <td>
                {formatReportNumber(
                  row.executionCount,
                )}
              </td>

              <td>
                {formatReportNumber(
                  row.passed,
                )}
              </td>

              <td>
                {formatReportNumber(
                  row.failed,
                )}
              </td>

              <td>
                {formatReportNumber(
                  row.needReview,
                )}
              </td>

              <td>
                {formatReportNumber(
                  row.skipped,
                )}
              </td>

              <td>
                {formatReportPercentage(
                  row.passRate,
                )}
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ReportScopeTable
