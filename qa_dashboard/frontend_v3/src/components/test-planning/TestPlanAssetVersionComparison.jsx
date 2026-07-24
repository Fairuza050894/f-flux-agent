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

function TestPlanAssetVersionComparison({
  comparison,
}) {
  return (
    <section className="dashboard-panel test-plan-detail-section">
      <div className="test-plan-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            VERSION TRACEABILITY
          </span>

          <h3>
            Captured vs Live Versions
          </h3>

          <p>
            Compare the immutable asset
            versions captured by this Test
            Plan with the current Test Asset
            catalog.
          </p>
        </div>

        <strong className="test-plan-detail-count">
          {comparison.total} Assets
        </strong>
      </div>

      <div className="test-plan-version-comparison-summary">
        <div>
          <span>Current</span>
          <strong>
            {comparison.current}
          </strong>
        </div>

        <div>
          <span>Outdated</span>
          <strong>
            {comparison.outdated}
          </strong>
        </div>

        <div>
          <span>Archived</span>
          <strong>
            {comparison.archived}
          </strong>
        </div>

        <div>
          <span>Missing</span>
          <strong>
            {comparison.missing}
          </strong>
        </div>

        <div>
          <span>No Snapshot</span>
          <strong>
            {comparison.unsnapshotted}
          </strong>
        </div>
      </div>

      <div className="test-plan-detail-table-wrapper">
        <table className="test-plan-detail-table test-plan-version-comparison-table">
          <thead>
            <tr>
              <th>Test Asset</th>
              <th>Captured</th>
              <th>Live</th>
              <th>Snapshot Status</th>
              <th>Captured At</th>
              <th>Reason</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {comparison.rows.length > 0 ? (
              comparison.rows.map(
                (row) => (
                  <tr key={row.assetId}>
                    <td>
                      <strong>
                        {row.name}
                      </strong>

                      <span>
                        {row.module}
                        {' / '}
                        {row.feature}
                      </span>

                      <span>
                        {row.assetId}
                      </span>
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
                        {formatVersion(
                          row
                            .liveVersionNumber,
                        )}
                      </strong>

                      <span>
                        {row.liveVersionId ||
                          row.lifecycleStatus}
                      </span>
                    </td>

                    <td>
                      <StatusBadge
                        tone={
                          row.statusTone
                        }
                      >
                        {row.statusLabel}
                      </StatusBadge>
                    </td>

                    <td>
                      {formatTestAssetDate(
                        row.capturedAt,
                      )}
                    </td>

                    <td>
                      <span className="test-plan-version-reason">
                        {row.reason}
                      </span>
                    </td>

                    <td>
                      {row.hasLiveAsset ? (
                        <Link
                          className="button button-secondary test-plan-action-button"
                          to={`/test-assets/${row.assetId}`}
                        >
                          View Asset
                        </Link>
                      ) : (
                        <span className="test-plan-version-unavailable">
                          Unavailable
                        </span>
                      )}
                    </td>
                  </tr>
                ),
              )
            ) : (
              <tr>
                <td
                  className="test-plan-version-empty"
                  colSpan="7"
                >
                  <strong>
                    No captured Test Assets
                  </strong>

                  <span>
                    Select Test Assets and save
                    the Test Plan to create
                    version snapshots.
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

export default TestPlanAssetVersionComparison
