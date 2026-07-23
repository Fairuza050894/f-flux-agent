import StatusBadge from '../StatusBadge'

import {
  formatTestAssetDate,
} from '../../features/test-assets/testAssetFormatters'

function TestAssetVersionHistory({
  currentVersionId,
  onSelectVersion,
  selectedVersionId,
  versions,
}) {
  return (
    <section className="dashboard-panel test-asset-detail-section">
      <div className="test-asset-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            VERSIONING
          </span>

          <h3>Version History</h3>

          <p>
            Immutable snapshots created each
            time the Test Asset is edited.
          </p>
        </div>

        <strong className="test-asset-detail-count">
          {versions.length}{' '}
          {versions.length === 1
            ? 'Version'
            : 'Versions'}
        </strong>
      </div>

      <div className="test-asset-version-table-wrapper">
        <table className="test-asset-version-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Change Summary</th>
              <th>Created</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {versions.map(
              (version) => {
                const isCurrent =
                  version.versionId ===
                  currentVersionId

                const isSelected =
                  version.versionId ===
                  selectedVersionId

                return (
                  <tr
                    className={
                      isSelected
                        ? 'test-asset-version-selected'
                        : undefined
                    }
                    key={
                      version.versionId
                    }
                  >
                    <td>
                      <strong>
                        v
                        {
                          version.versionNumber
                        }
                      </strong>

                      <span>
                        {version.versionId}
                      </span>
                    </td>

                    <td>
                      <span className="test-asset-version-summary-text">
                        {
                          version.changeSummary
                        }
                      </span>
                    </td>

                    <td>
                      {formatTestAssetDate(
                        version.createdAt,
                      )}
                    </td>

                    <td>
                      <StatusBadge
                        tone={
                          isCurrent
                            ? 'success'
                            : 'neutral'
                        }
                      >
                        {isCurrent
                          ? 'Current'
                          : 'Historical'}
                      </StatusBadge>
                    </td>

                    <td>
                      <button
                        className="button button-secondary test-asset-action-button"
                        disabled={
                          isSelected
                        }
                        onClick={() =>
                          onSelectVersion(
                            version.versionId,
                          )
                        }
                        type="button"
                      >
                        {isSelected
                          ? 'Selected'
                          : 'View Snapshot'}
                      </button>
                    </td>
                  </tr>
                )
              },
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default TestAssetVersionHistory
