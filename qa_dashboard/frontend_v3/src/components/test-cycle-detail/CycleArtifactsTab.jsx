import StatusBadge from '../StatusBadge'
import ArtifactPreviewModal from './ArtifactPreviewModal'
import {
  formatResultStatus,
} from '../../features/results/resultFormatters'

function ArtifactsEmptyState() {
  return (
    <div className="cycle-empty-state">
      <strong>
        No artifacts generated
      </strong>

      <p>
        Screenshots, reports, logs, JSON
        files, and spreadsheets will appear
        after execution.
      </p>
    </div>
  )
}

function ArtifactRow({
  artifact,
  onPreview,
}) {
  return (
    <article
      className="cycle-artifact-list-row"
      role="listitem"
    >
      <div className="cycle-artifact-list-type">
        <span>
          {artifact.typeLabel}
        </span>
      </div>

      <div className="cycle-artifact-list-file">
        <strong>
          {artifact.name}
        </strong>

        <span>
          {artifact.previewLabel}
        </span>
      </div>

      <div className="cycle-artifact-list-execution">
        <strong>
          {artifact.scopeLabel}
        </strong>

        <span>
          {formatResultStatus(
            artifact.executionStatus,
          )}
        </span>
      </div>

      <div className="cycle-artifact-list-status">
        <StatusBadge
          tone={
            artifact.available
              ? 'success'
              : 'danger'
          }
        >
          {artifact.available
            ? 'Available'
            : 'Unavailable'}
        </StatusBadge>
      </div>

      <div className="cycle-artifact-list-actions">
        <button
          className="button button-secondary"
          disabled={
            !artifact.canPreview
          }
          onClick={() =>
            onPreview(artifact)
          }
          type="button"
        >
          View
        </button>

        {artifact.available ? (
          <a
            className="button button-primary"
            href={artifact.downloadUrl}
          >
            Download
          </a>
        ) : (
          <button
            className="button button-primary"
            disabled
            type="button"
          >
            Download
          </button>
        )}
      </div>
    </article>
  )
}

function CycleArtifactsTab({
  artifacts,
  onClosePreview,
  onPreview,
  preview,
  previewContent,
  previewError,
  previewLoading,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            EXECUTION EVIDENCE
          </span>

          <h3>Artifacts</h3>

          <p>
            Evidence and reports generated
            by test executions.
          </p>
        </div>

        <StatusBadge
          tone={
            artifacts.length > 0
              ? 'success'
              : 'neutral'
          }
        >
          {artifacts.length}
          {' '}
          Files
        </StatusBadge>
      </div>

      {artifacts.length === 0 ? (
        <ArtifactsEmptyState />
      ) : (
        <div className="cycle-artifact-list">
          <div className="cycle-artifact-list-header">
            <span>Type</span>
            <span>File</span>
            <span>Execution</span>
            <span>Status</span>
            <span>Actions</span>
          </div>

          <div
            className="cycle-artifact-list-body"
            role="list"
          >
            {artifacts.map(
              (artifact) => (
                <ArtifactRow
                  artifact={artifact}
                  key={artifact.key}
                  onPreview={onPreview}
                />
              ),
            )}
          </div>
        </div>
      )}

      <ArtifactPreviewModal
        artifact={preview}
        content={previewContent}
        error={previewError}
        loading={previewLoading}
        onClose={onClosePreview}
      />
    </section>
  )
}

export default CycleArtifactsTab
