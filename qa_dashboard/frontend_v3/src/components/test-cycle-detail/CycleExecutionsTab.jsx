import StatusBadge from '../StatusBadge'

function ExecutionRow({
  row,
}) {
  return (
    <article
      className="cycle-execution-row"
    >
      <div className="cycle-execution-identity">
        <strong>
          {row.scopeLabel}
        </strong>

        <code title={row.runId}>
          {row.runId}
        </code>

        <span>
          {row.stageLabel}
        </span>
      </div>

      <div className="cycle-execution-progress-cell">
        <div
          aria-label={`${row.progress}% complete`}
          aria-valuemax="100"
          aria-valuemin="0"
          aria-valuenow={row.progress}
          className="cycle-execution-progress"
          role="progressbar"
        >
          <span
            style={{
              width:
                `${row.progress}%`,
            }}
          />
        </div>

        <strong className="cycle-execution-percent">
          {row.progress}%
        </strong>
      </div>

      <div className="cycle-execution-status">
        <StatusBadge
          tone={row.tone}
        >
          {row.statusLabel}
        </StatusBadge>
      </div>
    </article>
  )
}

function CycleExecutionsTab({
  model,
  onDispatch,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            RUNNER EXECUTIONS
          </span>

          <h3>Executions</h3>

          <p>
            Execution status and progress
            from the connected runners.
          </p>
        </div>

        <div className="cycle-execution-header-actions">
          <button
            className={
              model.dispatch
                .buttonClassName
            }
            disabled={
              model.dispatch.disabled
            }
            onClick={onDispatch}
            type="button"
          >
            {model.dispatch.label}
          </button>
        </div>
      </div>

      <div className="cycle-execution-table">
        <div
          aria-hidden="true"
          className="cycle-execution-table-header"
        >
          <span>Execution</span>
          <span>Progress</span>
          <span>Status</span>
        </div>

        <div className="cycle-execution-list">
          {model.rows.map((row) => (
            <ExecutionRow
              key={row.key}
              row={row}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

export default CycleExecutionsTab
