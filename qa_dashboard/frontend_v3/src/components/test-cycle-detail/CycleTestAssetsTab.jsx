import {
  Fragment,
} from 'react'
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

function SnapshotDefinition({
  row,
}) {
  if (!row.hasSnapshot) {
    return (
      <div className="cycle-asset-definition-empty">
        <strong>
          Captured definition unavailable
        </strong>

        <p>
          This is a legacy or incomplete Test
          Cycle record that contains an asset ID
          without an immutable snapshot.
        </p>
      </div>
    )
  }

  return (
    <div className="cycle-asset-definition">
      <dl className="cycle-asset-definition-metadata">
        <div>
          <dt>Type</dt>
          <dd>{row.typeLabel}</dd>
        </div>

        <div>
          <dt>Priority</dt>
          <dd>{row.priority}</dd>
        </div>

        <div>
          <dt>Automation</dt>
          <dd>
            {row.automationStatus}
          </dd>
        </div>

        <div>
          <dt>Execution Ready</dt>
          <dd>
            {row.executionReady
              ? 'Yes'
              : 'No'}
          </dd>
        </div>

        <div>
          <dt>Version ID</dt>
          <dd>
            <code>
              {row.capturedVersionId ||
                'Not available'}
            </code>
          </dd>
        </div>

        <div>
          <dt>Change Summary</dt>
          <dd>
            {row.capturedChangeSummary ||
              'No change summary.'}
          </dd>
        </div>
      </dl>

      <div className="cycle-asset-definition-grid">
        <section>
          <h4>Description</h4>
          <p>{row.description}</p>
        </section>

        <section>
          <h4>Preconditions</h4>
          <p>{row.preconditions}</p>
        </section>

        <section className="cycle-asset-definition-wide">
          <h4>Test Steps</h4>

          {row.steps.length > 0 ? (
            <ol>
              {row.steps.map(
                (step, index) => (
                  <li
                    key={`${row.assetId}-step-${index + 1}`}
                  >
                    {step}
                  </li>
                ),
              )}
            </ol>
          ) : (
            <p>
              No captured test steps.
            </p>
          )}
        </section>

        <section className="cycle-asset-definition-wide">
          <h4>Expected Result</h4>
          <p>{row.expectedResult}</p>
        </section>
      </div>
    </div>
  )
}

function CycleTestAssetsTab({
  comparison,
}) {
  return (
    <div className="cycle-detail-content">
      <section className="dashboard-panel cycle-detail-panel cycle-assets-panel">
        <div className="panel-header">
          <div>
            <span className="panel-eyebrow">
              VERSION TRACEABILITY
            </span>

            <h3>
              Captured vs Live Test Assets
            </h3>

            <p>
              Review the immutable Test Asset
              definitions used by this cycle and
              compare them with the current live
              catalog.
            </p>
          </div>

          <strong className="cycle-detail-count">
            {comparison.total} Assets
          </strong>
        </div>

        <div className="cycle-asset-comparison-summary">
          <div>
            <span>Captured</span>
            <strong>
              {comparison.captured}
            </strong>
          </div>

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

        <div className="cycle-asset-table-wrapper">
          <table className="cycle-asset-table">
            <thead>
              <tr>
                <th>Test Asset</th>
                <th>Source</th>
                <th>Captured</th>
                <th>Live</th>
                <th>Comparison</th>
                <th>Captured At</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {comparison.rows.length > 0 ? (
                comparison.rows.map(
                  (row) => (
                    <Fragment key={row.assetId}>
                      <tr>
                        <td>
                          <strong>
                            {row.name}
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
                            {row.sourceLabel}
                          </strong>

                          <span>
                            {row.sourcePlanId ||
                              'Direct cycle'}
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

                          <span className="cycle-asset-comparison-reason">
                            {row.reason}
                          </span>
                        </td>

                        <td>
                          {formatTestAssetDate(
                            row.capturedAt,
                          )}
                        </td>

                        <td>
                          {row.hasLiveAsset ? (
                            <Link
                              className="button button-secondary cycle-asset-action"
                              to={`/test-assets/${row.assetId}`}
                            >
                              View Asset
                            </Link>
                          ) : (
                            <span className="cycle-asset-unavailable">
                              Unavailable
                            </span>
                          )}
                        </td>
                      </tr>

                      <tr className="cycle-asset-definition-row">
                        <td colSpan="7">
                          <details>
                            <summary>
                              View captured definition
                            </summary>

                            <SnapshotDefinition
                              row={row}
                            />
                          </details>
                        </td>
                      </tr>
                    </Fragment>
                  ),
                )
              ) : (
                <tr>
                  <td
                    className="cycle-asset-empty"
                    colSpan="7"
                  >
                    <strong>
                      No Test Assets selected
                    </strong>

                    <span>
                      This Test Cycle does not
                      reference any Test Assets.
                    </span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default CycleTestAssetsTab
