import StatusBadge from '../StatusBadge'
import {
  formatResultStatus,
  getResultStatusTone,
} from '../../features/results/resultFormatters'

function ResultMetric({
  emphasis = '',
  label,
  value,
}) {
  const className = [
    'cycle-result-metric',
    emphasis
      ? `cycle-result-metric-${emphasis}`
      : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <article className={className}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function ResultsEmptyState() {
  return (
    <div className="cycle-empty-state">
      <strong>
        No test results available
      </strong>

      <p>
        Test results will appear after a
        supported runner completes an
        execution.
      </p>
    </div>
  )
}

function ResultExecutionCard({
  execution,
  formatDateTime,
}) {
  const executionKey =
    execution.runId ??
    execution.scopeKey ??
    execution.scopeLabel

  return (
    <article
      className="cycle-result-execution-card"
      key={executionKey}
    >
      <div className="cycle-result-execution-header">
        <div>
          <span>
            {execution.runner}
          </span>

          <h4>
            {execution.scopeLabel}
          </h4>

          <p>
            {execution.moduleName}
            {' · '}
            {formatResultStatus(
              execution.mode,
            )}
          </p>
        </div>

        <StatusBadge
          tone={getResultStatusTone(
            execution.status,
          )}
        >
          {formatResultStatus(
            execution.status,
          )}
        </StatusBadge>
      </div>

      <div className="cycle-result-execution-metrics">
        <div>
          <span>Passed</span>

          <strong>
            {execution.metrics.passed}
          </strong>
        </div>

        <div>
          <span>Failed</span>

          <strong>
            {execution.metrics.failed}
          </strong>
        </div>

        <div>
          <span>Need Review</span>

          <strong>
            {execution.metrics.needReview}
          </strong>
        </div>

        <div>
          <span>Skipped</span>

          <strong>
            {execution.metrics.skipped}
          </strong>
        </div>

        <div>
          <span>Bugs</span>

          <strong>
            {execution.metrics.bugsFound}
          </strong>
        </div>

        <div>
          <span>Completed</span>

          <strong>
            {formatDateTime(
              execution.completedAt,
            )}
          </strong>
        </div>
      </div>

      <div className="cycle-result-run-id">
        <span>Backend run ID</span>

        <code>
          {execution.runId ??
            'Not available'}
        </code>
      </div>

      {execution.testingSummary && (
        <details className="cycle-result-summary-details">
          <summary>
            View runner summary
          </summary>

          <pre>
            {execution.testingSummary}
          </pre>
        </details>
      )}
    </article>
  )
}

function UnsupportedExecutions({
  executions,
}) {
  if (executions.length === 0) {
    return null
  }

  return (
    <div className="cycle-unsupported-results">
      <div className="cycle-unsupported-results-heading">
        <div>
          <span className="panel-eyebrow">
            RUNNER AVAILABILITY
          </span>

          <h4>
            Unsupported MVP Runners
          </h4>
        </div>

        <StatusBadge tone="warning">
          {executions.length}
        </StatusBadge>
      </div>

      <div className="cycle-unsupported-result-list">
        {executions.map(
          (execution) => (
            <article
              key={
                execution.runId ??
                execution.scopeKey ??
                execution.scopeLabel
              }
            >
              <div>
                <strong>
                  {execution.scopeLabel}
                </strong>

                <span>
                  {execution.currentStep ||
                    'Runner is not implemented in the MVP.'}
                </span>
              </div>

              <StatusBadge tone="warning">
                {formatResultStatus(
                  execution.status,
                )}
              </StatusBadge>
            </article>
          ),
        )}
      </div>
    </div>
  )
}

function CycleResultsTab({
  cycleStatus,
  formatDateTime,
  resultExecutions,
  totals,
  unsupportedExecutions,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            CONSOLIDATED RESULTS
          </span>

          <h3>Test Results</h3>

          <p>
            Consolidated results from
            completed executions.
          </p>
        </div>

        <StatusBadge
          tone={getResultStatusTone(
            cycleStatus,
          )}
        >
          {formatResultStatus(
            cycleStatus,
          )}
        </StatusBadge>
      </div>

      {resultExecutions.length === 0 ? (
        <ResultsEmptyState />
      ) : (
        <>
          <div className="cycle-result-metric-grid">
            <ResultMetric
              label="Total Executed"
              value={totals.totalExecuted}
            />

            <ResultMetric
              emphasis="success"
              label="Passed"
              value={totals.passed}
            />

            <ResultMetric
              emphasis="danger"
              label="Failed"
              value={totals.failed}
            />

            <ResultMetric
              emphasis="warning"
              label="Need Review"
              value={totals.needReview}
            />

            <ResultMetric
              label="Skipped"
              value={totals.skipped}
            />

            <ResultMetric
              emphasis="danger"
              label="Bugs Found"
              value={totals.bugsFound}
            />

            <ResultMetric
              emphasis="warning"
              label="Warnings"
              value={totals.warnings}
            />
          </div>

          <div className="cycle-result-execution-list">
            {resultExecutions.map(
              (execution) => (
                <ResultExecutionCard
                  execution={execution}
                  formatDateTime={
                    formatDateTime
                  }
                  key={
                    execution.runId ??
                    execution.scopeKey ??
                    execution.scopeLabel
                  }
                />
              ),
            )}
          </div>
        </>
      )}

      <UnsupportedExecutions
        executions={
          unsupportedExecutions
        }
      />
    </section>
  )
}

export default CycleResultsTab
