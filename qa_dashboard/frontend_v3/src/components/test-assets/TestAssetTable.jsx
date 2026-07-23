import {
  Link,
} from 'react-router-dom'

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
  linkedUsage = {},
  onArchive,
  onDelete,
  onEdit,
  onRestore,
  projectNames,
}) {
  return (
    <div className="test-asset-table-wrapper">
      <table className="test-asset-table">
        <thead>
          <tr>
            <th>Test Asset</th>
            <th>Project</th>
            <th>Lifecycle</th>
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
            assets.map((asset) => {
              const isArchived =
                asset.lifecycleStatus ===
                'Archived'

              const usage =
                linkedUsage[
                  asset.id
                ] ?? {
                  planCount: 0,
                  cycleCount: 0,
                }

              const hasLinkedUsage =
                usage.planCount > 0 ||
                usage.cycleCount > 0

              const deleteTitle =
                hasLinkedUsage
                  ? `Used by ${usage.planCount} Test Plan(s) and ${usage.cycleCount} Test Cycle(s). Unlink or archive the asset instead.`
                  : 'Permanently delete this Test Asset.'

              return (
                <tr
                  className={
                    isArchived
                      ? 'test-asset-row-archived'
                      : undefined
                  }
                  key={asset.id}
                >
                  <td>
                    <Link
                      className="test-asset-name-link"
                      to={`/test-assets/${asset.id}`}
                    >
                      {asset.name ||
                        'Unnamed Test Asset'}
                    </Link>

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
                    <StatusBadge
                      tone={
                        isArchived
                          ? 'neutral'
                          : 'success'
                      }
                    >
                      {asset.lifecycleStatus ??
                        'Active'}
                    </StatusBadge>
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
                        asset.executionReady &&
                        !isArchived,
                      )}
                    >
                      {asset.executionReady &&
                      !isArchived
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
                        disabled={isArchived}
                        onClick={() =>
                          onEdit(asset)
                        }
                        title={
                          isArchived
                            ? 'Restore the asset before editing it.'
                            : undefined
                        }
                        type="button"
                      >
                        Edit
                      </button>

                      {isArchived ? (
                        <button
                          className="button button-secondary test-asset-action-button"
                          onClick={() =>
                            onRestore(asset)
                          }
                          type="button"
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          className="button button-secondary test-asset-action-button"
                          onClick={() =>
                            onArchive(asset)
                          }
                          type="button"
                        >
                          Archive
                        </button>
                      )}

                      <button
                        className="button button-danger test-asset-action-button"
                        disabled={
                          hasLinkedUsage
                        }
                        onClick={() =>
                          onDelete(asset)
                        }
                        title={deleteTitle}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })
          ) : (
            <tr>
              <td
                className="test-asset-empty-cell"
                colSpan="10"
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
