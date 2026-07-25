import {
  Link,
} from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatTestAssetDate,
} from '../../features/test-assets/testAssetFormatters'

function formatVersion(
  versionNumber,
) {
  return versionNumber
    ? `v${versionNumber}`
    : 'Not available'
}

function ReportAssetTraceability({
  model,
}) {
  return (
    <section className="dashboard-panel report-panel report-traceability-panel">
      <div className="panel-header report-panel-header">
        <div>
          <span className="panel-eyebrow">
            VERSION TRACEABILITY
          </span>

          <h3>
            Execution and Asset Versions
          </h3>

          <p>
            Confirm that each execution and report
            retains the immutable Test Asset
            versions captured by its Test Cycle.
          </p>
        </div>

        <strong className="report-traceability-count">
          {model.total} Asset Records
        </strong>
      </div>

      <div className="report-traceability-summary">
        <div>
          <span>Captured Assets</span>
          <strong>
            {model.captured}
          </strong>
        </div>

        <div>
          <span>Traced Executions</span>
          <strong>
            {model.tracedExecutions}
            {' / '}
            {model.totalExecutions}
          </strong>
        </div>

        <div>
          <span>Complete Rows</span>
          <strong>
            {model.complete}
          </strong>
        </div>

        <div>
          <span>Partial Rows</span>
          <strong>
            {model.partial}
          </strong>
        </div>

        <div>
          <span>Missing Execution Snapshot</span>
          <strong>
            {model.missingExecutionSnapshots}
          </strong>
        </div>

        <div>
          <span>Legacy / No Snapshot</span>
          <strong>
            {model.noSnapshot}
          </strong>
        </div>
      </div>

      <div className="report-traceability-table-wrapper">
        <table className="report-traceability-table">
          <thead>
            <tr>
              <th>Test Cycle</th>
              <th>Test Asset</th>
              <th>Captured Version</th>
              <th>Source</th>
              <th>Execution Coverage</th>
              <th>Traceability</th>
              <th>Cycle Status</th>
              <th>Captured At</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {model.rows.length > 0 ? (
              model.rows.map(
                (row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>
                        {row.cycleName}
                      </strong>

                      <code>
                        {row.cycleId}
                      </code>
                    </td>

                    <td>
                      <strong>
                        {row.assetName}
                      </strong>

                      <span>
                        {row.module}
                        {' / '}
                        {row.feature}
                      </span>

                      <code>
                        {row.assetId}
                      </code>
                    </td>

                    <td>
                      <strong>
                        {formatVersion(
                          row
                            .capturedVersionNumber,
                        )}
                      </strong>

                      <span>
                        {row
                          .capturedVersionId ||
                          'No version ID'}
                      </span>
                    </td>

                    <td>
                      <strong>
                        {row.triggerSource}
                      </strong>

                      <span>
                        {row.sourcePlanId ||
                          'Direct cycle'}
                      </span>
                    </td>

                    <td>
                      <strong>
                        {row.tracedExecutionCount}
                        {' / '}
                        {row.executionCount}
                      </strong>

                      <span>
                        Executions carrying this
                        exact captured version
                      </span>
                    </td>

                    <td>
                      <StatusBadge
                        tone={
                          row.traceabilityTone
                        }
                      >
                        {
                          row.traceabilityLabel
                        }
                      </StatusBadge>
                    </td>

                    <td>
                      <span>
                        {row.cycleStatus}
                      </span>
                    </td>

                    <td>
                      {formatTestAssetDate(
                        row.capturedAt,
                      )}
                    </td>

                    <td>
                      <Link
                        className="button button-secondary report-traceability-action"
                        to={`/test-cycles/${row.cycleId}`}
                      >
                        View Cycle
                      </Link>
                    </td>
                  </tr>
                ),
              )
            ) : (
              <tr>
                <td
                  className="report-traceability-empty"
                  colSpan="9"
                >
                  <strong>
                    No version traceability records
                  </strong>

                  <span>
                    The matching Test Cycles do not
                    contain selected Test Assets.
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

export default ReportAssetTraceability
