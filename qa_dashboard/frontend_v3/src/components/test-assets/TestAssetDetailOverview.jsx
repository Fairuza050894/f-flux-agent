import StatusBadge from '../StatusBadge'

import {
  formatTestAssetDate,
  getTestAssetAutomationTone,
  getTestAssetPriorityTone,
  getTestAssetReadyTone,
} from '../../features/test-assets/testAssetFormatters'

function TestAssetDetailOverview({
  model,
}) {
  const {
    asset,
    linkedCycleCount,
    linkedPlanCount,
    project,
  } = model

  return (
    <section className="dashboard-panel test-asset-detail-section">
      <div className="test-asset-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            OVERVIEW
          </span>

          <h3>Asset Information</h3>

          <p>
            Identity, classification, and
            current availability of this
            reusable Test Asset.
          </p>
        </div>

        <StatusBadge
          tone={
            asset.lifecycleStatus ===
            'Archived'
              ? 'neutral'
              : 'success'
          }
        >
          {asset.lifecycleStatus}
        </StatusBadge>
      </div>

      <div className="test-asset-detail-metrics">
        <div>
          <span>Current Version</span>

          <strong>
            v{asset.currentVersionNumber}
          </strong>
        </div>

        <div>
          <span>Version History</span>

          <strong>
            {asset.versions.length}
          </strong>
        </div>

        <div>
          <span>Linked Plans</span>

          <strong>
            {linkedPlanCount}
          </strong>
        </div>

        <div>
          <span>Linked Cycles</span>

          <strong>
            {linkedCycleCount}
          </strong>
        </div>
      </div>

      <div className="test-asset-detail-info-grid">
        <div>
          <span>Project</span>

          <strong>
            {project?.name ??
              'Project unavailable'}
          </strong>
        </div>

        <div>
          <span>Test Type</span>

          <strong>
            {asset.typeLabel}
          </strong>
        </div>

        <div>
          <span>Module</span>

          <strong>
            {asset.module ||
              'Not specified'}
          </strong>
        </div>

        <div>
          <span>Feature</span>

          <strong>
            {asset.feature ||
              'Not specified'}
          </strong>
        </div>

        <div>
          <span>Priority</span>

          <StatusBadge
            tone={getTestAssetPriorityTone(
              asset.priority,
            )}
          >
            {asset.priority}
          </StatusBadge>
        </div>

        <div>
          <span>Automation</span>

          <StatusBadge
            tone={getTestAssetAutomationTone(
              asset.automationStatus,
            )}
          >
            {asset.automationStatus}
          </StatusBadge>
        </div>

        <div>
          <span>Execution Readiness</span>

          <StatusBadge
            tone={getTestAssetReadyTone(
              asset.executionReady,
            )}
          >
            {asset.executionReady
              ? 'Ready'
              : 'Not Ready'}
          </StatusBadge>
        </div>

        <div>
          <span>Recommended</span>

          <StatusBadge
            tone={
              asset.recommended
                ? 'primary'
                : 'neutral'
            }
          >
            {asset.recommended
              ? 'Yes'
              : 'No'}
          </StatusBadge>
        </div>

        <div>
          <span>Created</span>

          <strong>
            {formatTestAssetDate(
              asset.createdAt,
            )}
          </strong>
        </div>

        <div>
          <span>Last Updated</span>

          <strong>
            {formatTestAssetDate(
              asset.updatedAt,
            )}
          </strong>
        </div>
      </div>
    </section>
  )
}

export default TestAssetDetailOverview
