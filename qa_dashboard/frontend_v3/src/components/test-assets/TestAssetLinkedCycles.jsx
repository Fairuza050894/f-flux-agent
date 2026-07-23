import {
  Link,
} from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatTestAssetDate,
} from '../../features/test-assets/testAssetFormatters'

function getCycleStatusTone(
  status,
) {
  const normalizedStatus =
    String(status ?? '')
      .trim()
      .toLowerCase()

  if (
    normalizedStatus === 'passed' ||
    normalizedStatus === 'completed'
  ) {
    return 'success'
  }

  if (
    normalizedStatus === 'failed' ||
    normalizedStatus === 'error'
  ) {
    return 'danger'
  }

  if (
    normalizedStatus === 'running' ||
    normalizedStatus === 'in progress'
  ) {
    return 'primary'
  }

  if (
    normalizedStatus === 'ready'
  ) {
    return 'warning'
  }

  return 'neutral'
}

function TestAssetLinkedCycles({
  cycles,
  environmentNames,
}) {
  return (
    <section className="dashboard-panel test-asset-detail-section">
      <div className="test-asset-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            HISTORY
          </span>

          <h3>Linked Test Cycles</h3>

          <p>
            Test Cycles that currently
            reference this Test Asset ID.
          </p>
        </div>

        <strong className="test-asset-detail-count">
          {cycles.length} Cycles
        </strong>
      </div>

      <div className="test-asset-linked-table-wrapper">
        <table className="test-asset-linked-table test-asset-linked-cycle-table">
          <thead>
            <tr>
              <th>Test Cycle</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Environment</th>
              <th>Created</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {cycles.length > 0 ? (
              cycles.map((cycle) => {
                const parsedProgress =
                  Number(
                    cycle.progress ?? 0,
                  )

                const progress =
                  Number.isFinite(
                    parsedProgress,
                  )
                    ? parsedProgress
                    : 0

                return (
                  <tr key={cycle.id}>
                    <td>
                      <strong>
                        {cycle.name ||
                          'Untitled Test Cycle'}
                      </strong>

                      <span>
                        {cycle.id}
                      </span>
                    </td>

                    <td>
                      <StatusBadge
                        tone={getCycleStatusTone(
                          cycle.status,
                        )}
                      >
                        {cycle.status ??
                          'Unknown'}
                      </StatusBadge>
                    </td>

                    <td>
                      <strong className="test-asset-linked-progress">
                        {progress}%
                      </strong>
                    </td>

                    <td>
                      {environmentNames[
                        cycle.environmentId
                      ] ??
                        'Environment unavailable'}
                    </td>

                    <td>
                      {formatTestAssetDate(
                        cycle.createdAt,
                      )}
                    </td>

                    <td>
                      <Link
                        className="button button-secondary test-asset-action-button"
                        to={`/test-cycles/${cycle.id}`}
                      >
                        View Cycle
                      </Link>
                    </td>
                  </tr>
                )
              })
            ) : (
              <tr>
                <td
                  className="test-asset-linked-empty"
                  colSpan="6"
                >
                  <strong>
                    No linked Test Cycles
                  </strong>

                  <span>
                    No Test Cycle currently
                    references this asset.
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

export default TestAssetLinkedCycles
