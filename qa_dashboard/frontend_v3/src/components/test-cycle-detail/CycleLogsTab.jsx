import StatusBadge from '../StatusBadge'

function LogsEmptyState() {
  return (
    <div className="cycle-empty-state">
      <strong>
        No execution logs available
      </strong>

      <p>
        Execution telemetry will appear
        after execution records are
        created.
      </p>
    </div>
  )
}

function ExecutionLogRow({
  formatDateTime,
  log,
}) {
  return (
    <article className="cycle-log-row">
      <div className="cycle-log-row-header">
        <div className="cycle-log-identity">
          <strong>
            {log.scopeLabel}
          </strong>

          <code>{log.runId}</code>
        </div>

        <StatusBadge tone={log.tone}>
          {log.statusLabel}
        </StatusBadge>
      </div>

      <dl className="cycle-log-metadata">
        <div>
          <dt>Stage</dt>

          <dd>{log.stageLabel}</dd>
        </div>

        <div>
          <dt>Current Step</dt>

          <dd>
            {log.currentStepLabel}
          </dd>
        </div>

        <div>
          <dt>Progress</dt>

          <dd>{log.progress}%</dd>
        </div>

        <div>
          <dt>Last Update</dt>

          <dd>
            {log.lastTimestamp
              ? formatDateTime(
                  log.lastTimestamp,
                )
              : 'Not available'}
          </dd>
        </div>
      </dl>

      {log.errorMessage && (
        <div className="cycle-log-message cycle-log-message-error">
          <strong>
            Execution error
          </strong>

          <pre>
            {log.errorMessage}
          </pre>
        </div>
      )}

      {!log.errorMessage &&
        log.runnerMessage && (
          <div className="cycle-log-message">
            <strong>
              Runner message
            </strong>

            <pre>
              {log.runnerMessage}
            </pre>
          </div>
        )}
    </article>
  )
}

function CycleLogsTab({
  formatDateTime,
  logs,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            EXECUTION TELEMETRY
          </span>

          <h3>Execution Logs</h3>

          <p>
            Current execution telemetry
            returned by the connected
            Execution Store.
          </p>
        </div>

        <StatusBadge
          tone={
            logs.length > 0
              ? 'primary'
              : 'neutral'
          }
        >
          {logs.length}
          {' '}
          Executions
        </StatusBadge>
      </div>

      {logs.length === 0 ? (
        <LogsEmptyState />
      ) : (
        <div className="cycle-log-list">
          {logs.map((log) => (
            <ExecutionLogRow
              formatDateTime={
                formatDateTime
              }
              key={log.key}
              log={log}
            />
          ))}
        </div>
      )}
    </section>
  )
}

export default CycleLogsTab
