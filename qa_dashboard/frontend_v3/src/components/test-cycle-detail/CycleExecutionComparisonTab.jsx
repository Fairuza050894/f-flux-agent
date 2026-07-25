import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../StatusBadge'
import {
  compareExecutionAttempts,
  formatExecutionDuration,
} from '../../features/executions/executionComparisonSelectors'

function DeltaValue({
  improvementDirection,
  value,
}) {
  const improved =
    value !== 0 &&
    (
      improvementDirection ===
        'increase'
        ? value > 0
        : value < 0
    )

  const regressed =
    value !== 0 &&
    !improved

  const className = [
    'cycle-execution-comparison-delta',
    improved
      ? 'cycle-execution-comparison-delta-improved'
      : '',
    regressed
      ? 'cycle-execution-comparison-delta-regressed'
      : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <span className={className}>
      {value > 0
        ? `+${value}`
        : value}
    </span>
  )
}

function FailureList({
  emptyLabel,
  items,
  title,
  tone,
}) {
  return (
    <section className="cycle-execution-comparison-failure-group">
      <div>
        <strong>{title}</strong>

        <StatusBadge tone={tone}>
          {items.length}
        </StatusBadge>
      </div>

      {items.length > 0 ? (
        <ul>
          {items.map(
            (item) => (
              <li key={item.key}>
                <code>{item.id}</code>
                <span>{item.scenario}</span>
              </li>
            ),
          )}
        </ul>
      ) : (
        <p>{emptyLabel}</p>
      )}
    </section>
  )
}

function CycleExecutionComparisonTab({
  catalog,
}) {
  const [
    selectedScopeKey,
    setSelectedScopeKey,
  ] = useState('')

  const effectiveGroup =
    catalog.groups.find(
      (group) =>
        group.key ===
        selectedScopeKey,
    ) ??
    catalog.groups[0] ??
    null

  const [
    baselineRunId,
    setBaselineRunId,
  ] = useState('')

  const [
    candidateRunId,
    setCandidateRunId,
  ] = useState('')

  const effectiveCandidate =
    effectiveGroup
      ?.attempts.find(
        (attempt) =>
          attempt.runId ===
          candidateRunId,
      ) ??
    effectiveGroup
      ?.attempts.at(-1) ??
    null

  const effectiveBaseline =
    effectiveGroup
      ?.attempts.find(
        (attempt) =>
          attempt.runId ===
          baselineRunId,
      ) ??
    effectiveGroup
      ?.attempts.at(-2) ??
    null

  const comparison =
    useMemo(
      () =>
        compareExecutionAttempts({
          baseline:
            effectiveBaseline
              ?.execution,

          candidate:
            effectiveCandidate
              ?.execution,
        }),
      [
        effectiveBaseline,
        effectiveCandidate,
      ],
    )

  if (
    !catalog.hasComparableExecutions
  ) {
    return (
      <section className="dashboard-panel cycle-detail-panel cycle-execution-comparison-empty">
        <StatusBadge tone="neutral">
          Comparison Unavailable
        </StatusBadge>

        <h3>
          Two completed attempts are required
        </h3>

        <p>
          Retry, rerun a scope, or rerun selected
          Test Assets to create a comparable
          execution pair.
        </p>
      </section>
    )
  }

  return (
    <section className="dashboard-panel cycle-detail-panel cycle-execution-comparison-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            EXECUTION LINEAGE
          </span>

          <h3>
            Execution Comparison
          </h3>

          <p>
            Compare two result-bearing attempts in
            the same scope without modifying their
            historical records.
          </p>
        </div>
      </div>

      <div className="cycle-execution-comparison-controls">
        <label>
          <span>Scope</span>

          <select
            onChange={(event) => {
              setSelectedScopeKey(
                event.target.value,
              )
              setBaselineRunId('')
              setCandidateRunId('')
            }}
            value={
              effectiveGroup?.key ?? ''
            }
          >
            {catalog.groups.map(
              (group) => (
                <option
                  key={group.key}
                  value={group.key}
                >
                  {group.label}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Baseline Run</span>

          <select
            onChange={(event) =>
              setBaselineRunId(
                event.target.value,
              )
            }
            value={
              effectiveBaseline?.runId ??
              ''
            }
          >
            {effectiveGroup.attempts.map(
              (attempt) => (
                <option
                  disabled={
                    attempt.runId ===
                    effectiveCandidate?.runId
                  }
                  key={attempt.runId}
                  value={attempt.runId}
                >
                  {attempt.label}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Candidate Run</span>

          <select
            onChange={(event) =>
              setCandidateRunId(
                event.target.value,
              )
            }
            value={
              effectiveCandidate?.runId ??
              ''
            }
          >
            {effectiveGroup.attempts.map(
              (attempt) => (
                <option
                  disabled={
                    attempt.runId ===
                    effectiveBaseline?.runId
                  }
                  key={attempt.runId}
                  value={attempt.runId}
                >
                  {attempt.label}
                </option>
              ),
            )}
          </select>
        </label>
      </div>

      {comparison && (
        <>
          <div className="cycle-execution-comparison-runs">
            <article>
              <span>Baseline</span>

              <div>
                <StatusBadge
                  tone={
                    comparison
                      .baseline
                      .tone
                  }
                >
                  {
                    comparison
                      .baseline
                      .status
                  }
                </StatusBadge>

                <strong>
                  {
                    comparison
                      .baseline
                      .reason
                  }
                </strong>
              </div>

              <code>
                {
                  comparison
                    .baseline
                    .runId
                }
              </code>

              <p>
                Duration:{' '}
                {
                  comparison
                    .baseline
                    .duration
                }
              </p>
            </article>

            <article>
              <span>Candidate</span>

              <div>
                <StatusBadge
                  tone={
                    comparison
                      .candidate
                      .tone
                  }
                >
                  {
                    comparison
                      .candidate
                      .status
                  }
                </StatusBadge>

                <strong>
                  {
                    comparison
                      .candidate
                      .reason
                  }
                </strong>
              </div>

              <code>
                {
                  comparison
                    .candidate
                    .runId
                }
              </code>

              <p>
                Duration:{' '}
                {
                  comparison
                    .candidate
                    .duration
                }
              </p>
            </article>

            <article className="cycle-execution-comparison-duration">
              <span>Duration Delta</span>

              <strong>
                {comparison.durationDeltaMs ===
                null
                  ? 'Not available'
                  : formatExecutionDuration(
                      Math.abs(
                        comparison
                          .durationDeltaMs,
                      ),
                    )}
              </strong>

              <p>
                {comparison.durationDeltaMs ===
                null
                  ? 'Both executions need valid timestamps.'
                  : comparison.durationDeltaMs >
                      0
                    ? 'Candidate was slower.'
                    : comparison.durationDeltaMs <
                        0
                      ? 'Candidate was faster.'
                      : 'No duration change.'}
              </p>
            </article>
          </div>

          <div className="cycle-execution-comparison-metrics">
            {comparison.metrics.map(
              (metric) => (
                <article key={metric.key}>
                  <span>
                    {metric.label}
                  </span>

                  <div>
                    <strong>
                      {
                        metric
                          .baseline
                      }
                    </strong>

                    <span>→</span>

                    <strong>
                      {
                        metric
                          .candidate
                      }
                    </strong>
                  </div>

                  <DeltaValue
                    improvementDirection={
                      metric
                        .improvementDirection
                    }
                    value={
                      metric.delta
                    }
                  />
                </article>
              ),
            )}
          </div>

          <div className="cycle-execution-comparison-targets">
            <article>
              <span>
                Baseline Target
              </span>

              <strong>
                {
                  comparison
                    .assetVersions
                    .baselineTargetCount
                } assets
              </strong>

              <p>
                {
                  comparison
                    .targeting
                    .baselineMode
                }
              </p>
            </article>

            <article>
              <span>
                Candidate Target
              </span>

              <strong>
                {
                  comparison
                    .assetVersions
                    .candidateTargetCount
                } assets
              </strong>

              <p>
                {
                  comparison
                    .targeting
                    .candidateMode
                }
              </p>
            </article>

            <article>
              <span>
                Version Changes
              </span>

              <strong>
                {
                  comparison
                    .assetVersions
                    .changedAssetIds
                    .length
                }
              </strong>

              <p>
                {comparison
                  .assetVersions
                  .changedAssetIds
                  .length > 0
                  ? comparison
                      .assetVersions
                      .changedAssetIds
                      .join(', ')
                  : 'No target version changes detected.'}
              </p>
            </article>
          </div>

          {comparison.failureDelta.available ? (
            <div className="cycle-execution-comparison-failures">
              <FailureList
                emptyLabel="No new failures."
                items={
                  comparison
                    .failureDelta
                    .newFailures
                }
                title="New Failures"
                tone="danger"
              />

              <FailureList
                emptyLabel="No resolved failures."
                items={
                  comparison
                    .failureDelta
                    .resolvedFailures
                }
                title="Resolved Failures"
                tone="success"
              />

              <FailureList
                emptyLabel="No unchanged failures."
                items={
                  comparison
                    .failureDelta
                    .unchangedFailures
                }
                title="Unchanged Failures"
                tone="warning"
              />
            </div>
          ) : (
            <div className="cycle-execution-comparison-notice">
              {comparison.failureDelta.reason ||
                'Detailed failure comparison is unavailable.'}{' '}
              The aggregate metrics above remain
              visible, but new and resolved failures
              are not inferred across incompatible
              target sets.
            </div>
          )}
        </>
      )}
    </section>
  )
}

export default CycleExecutionComparisonTab
