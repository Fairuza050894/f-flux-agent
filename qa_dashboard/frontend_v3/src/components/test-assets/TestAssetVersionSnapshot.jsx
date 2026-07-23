import StatusBadge from '../StatusBadge'

import {
  formatTestAssetDate,
  getTestAssetAutomationTone,
  getTestAssetPriorityTone,
  getTestAssetReadyTone,
} from '../../features/test-assets/testAssetFormatters'

function TestAssetVersionSnapshot({
  version,
}) {
  if (!version) {
    return null
  }

  const snapshot =
    version.snapshot

  return (
    <section className="dashboard-panel test-asset-detail-section">
      <div className="test-asset-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            SNAPSHOT
          </span>

          <h3>
            Version {version.versionNumber}
          </h3>

          <p>
            {version.changeSummary}
          </p>
        </div>

        <strong className="test-asset-detail-count">
          {formatTestAssetDate(
            version.createdAt,
          )}
        </strong>
      </div>

      <div className="test-asset-snapshot-classification">
        <div>
          <span>Type</span>

          <strong>
            {snapshot.typeLabel}
          </strong>
        </div>

        <div>
          <span>Priority</span>

          <StatusBadge
            tone={getTestAssetPriorityTone(
              snapshot.priority,
            )}
          >
            {snapshot.priority}
          </StatusBadge>
        </div>

        <div>
          <span>Automation</span>

          <StatusBadge
            tone={getTestAssetAutomationTone(
              snapshot.automationStatus,
            )}
          >
            {snapshot.automationStatus}
          </StatusBadge>
        </div>

        <div>
          <span>Readiness</span>

          <StatusBadge
            tone={getTestAssetReadyTone(
              snapshot.executionReady,
            )}
          >
            {snapshot.executionReady
              ? 'Ready'
              : 'Not Ready'}
          </StatusBadge>
        </div>
      </div>

      <div className="test-asset-definition-block">
        <span>Name</span>

        <p>
          {snapshot.name ||
            'Unnamed Test Asset'}
        </p>
      </div>

      <div className="test-asset-definition-block">
        <span>Module / Feature</span>

        <p>
          {snapshot.module ||
            'Not specified'}
          {' / '}
          {snapshot.feature ||
            'Not specified'}
        </p>
      </div>

      <div className="test-asset-definition-block">
        <span>Description</span>

        <p>
          {snapshot.description ||
            'No description provided.'}
        </p>
      </div>

      <div className="test-asset-definition-block">
        <span>Preconditions</span>

        <p>
          {snapshot.preconditions ||
            'No preconditions provided.'}
        </p>
      </div>

      <div className="test-asset-definition-block">
        <span>Test Steps</span>

        {snapshot.steps.length > 0 ? (
          <ol className="test-asset-step-list">
            {snapshot.steps.map(
              (
                step,
                index,
              ) => (
                <li
                  key={`${index}-${step}`}
                >
                  <span>
                    {index + 1}
                  </span>

                  <p>{step}</p>
                </li>
              ),
            )}
          </ol>
        ) : (
          <p>
            No test steps provided.
          </p>
        )}
      </div>

      <div className="test-asset-definition-block">
        <span>Expected Result</span>

        <p>
          {snapshot.expectedResult ||
            'No expected result provided.'}
        </p>
      </div>
    </section>
  )
}

export default TestAssetVersionSnapshot
