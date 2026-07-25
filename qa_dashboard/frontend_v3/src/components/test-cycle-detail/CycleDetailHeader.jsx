import StatusBadge from '../StatusBadge'

function CycleDetailHeader({
  isDuplicating = false,
  model,
  onBack,
  onDuplicate,
  onStart,
}) {
  return (
    <>
      <div className="cycle-detail-header">
        <div>
          <div className="page-heading-meta">
            <span>
              TEST CYCLE DETAIL
            </span>

            <StatusBadge
              tone={model.statusTone}
            >
              {model.statusLabel}
            </StatusBadge>
          </div>

          <h2>{model.name}</h2>

          <p>{model.context}</p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-secondary"
            onClick={onBack}
            type="button"
          >
            Back to Cycles
          </button>

          <button
            className="button button-secondary"
            disabled={isDuplicating}
            onClick={onDuplicate}
            type="button"
          >
            {isDuplicating
              ? 'Duplicating...'
              : 'Duplicate Cycle'}
          </button>

          <button
            className="button button-primary"
            disabled={
              model.startAction.disabled
            }
            onClick={onStart}
            type="button"
          >
            {model.startAction.label}
          </button>
        </div>
      </div>

      {model.errorMessage && (
        <div
          className="cycle-start-error"
          role="alert"
        >
          <strong>
            Execution could not be created
          </strong>

          <p>{model.errorMessage}</p>
        </div>
      )}
    </>
  )
}

export default CycleDetailHeader
