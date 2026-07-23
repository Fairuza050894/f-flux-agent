import StatusBadge from '../StatusBadge'

import {
  formatTestAssetDate,
  getTestAssetAutomationTone,
  getTestAssetPriorityTone,
  getTestAssetReadyTone,
} from '../../features/test-assets/testAssetFormatters'

function TestAssetTable({
  assets,
  emptyMessage,
  onDelete,
  onEdit,
  projectNames,
}) {
  return (
    <div className="test-asset-table-wrapper">
      <table className="test-asset-table">
        <thead>
          <tr>
            <th>Test Asset</th>
            <th>Project</th>
            <th>Type</th>
            <th>Module / Feature</th>
            <th>Priority</th>
            <th>Automation</th>
            <th>Readiness</th>
            <th>Updated</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {assets.length > 0 ? (
            assets.map((asset) => (
              <tr key={asset.id}>
                <td>
                  <strong>
                    {asset.name ||
                      'Unnamed Test Asset'}
                  </strong>

                  <span>{asset.id}</span>
                </td>

                <td>
                  <strong>
                    {projectNames[
                      asset.projectId
                    ] ?? 'Unknown Project'}
                  </strong>
                </td>

                <td>
                  <StatusBadge tone="neutral">
                    {asset.typeLabel}
                  </StatusBadge>
                </td>

                <td>
                  <strong>
                    {asset.module ||
                      'Not specified'}
                  </strong>

                  <span>
                    {asset.feature ||
                      'Not specified'}
                  </span>
                </td>

                <td>
                  <StatusBadge
                    tone={getTestAssetPriorityTone(
                      asset.priority,
                    )}
                  >
                    {asset.priority}
                  </StatusBadge>
                </td>

                <td>
                  <StatusBadge
                    tone={getTestAssetAutomationTone(
                      asset.automationStatus,
                    )}
                  >
                    {asset.automationStatus}
                  </StatusBadge>
                </td>

                <td>
                  <StatusBadge
                    tone={getTestAssetReadyTone(
                      asset.executionReady,
                    )}
                  >
                    {asset.executionReady
                      ? 'Ready'
                      : 'Not Ready'}
                  </StatusBadge>
                </td>

                <td>
                  <span className="test-asset-date">
                    {formatTestAssetDate(
                      asset.updatedAt,
                    )}
                  </span>
                </td>

                <td>
                  <div className="test-asset-row-actions">
                    <button
                      className="button button-secondary test-asset-action-button"
                      onClick={() =>
                        onEdit(asset)
                      }
                      type="button"
                    >
                      Edit
                    </button>

                    <button
                      className="button button-danger test-asset-action-button"
                      onClick={() =>
                        onDelete(asset)
                      }
                      type="button"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                className="test-asset-empty-cell"
                colSpan="9"
              >
                <strong>
                  No Test Assets available
                </strong>

                <span>{emptyMessage}</span>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default TestAssetTable
