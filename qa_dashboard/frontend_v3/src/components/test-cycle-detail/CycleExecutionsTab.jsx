import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../StatusBadge'

function ExecutionRow({
  checked,
  onToggle,
  row,
}) {
  return (
    <article
      className={[
        'cycle-execution-row',
        row.failed
          ? 'cycle-execution-row-failed'
          : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <label className="cycle-execution-selection">
        <input
          aria-label={`Select ${row.scopeLabel}`}
          checked={checked}
          disabled={!row.selectable}
          onChange={() =>
            onToggle(row.key)
          }
          type="checkbox"
        />
      </label>

      <div className="cycle-execution-identity">
        <strong>
          {row.scopeLabel}
        </strong>

        <code title={row.runId}>
          {row.runId}
        </code>

        <span>
          {row.executionReasonLabel}
          {row.attemptNumber > 0
            ? ` · Attempt ${row.attemptNumber}`
            : ''}
          {row.attemptCount > 1
            ? ` · ${row.attemptCount} runs`
            : ''}
        </span>

        {row.parentRunId && (
          <span
            className="cycle-execution-parent"
            title={row.parentRunId}
          >
            Parent: {row.parentRunId}
          </span>
        )}
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

        <span className="cycle-execution-stage">
          {row.stageLabel}
        </span>
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
  onRerunSelected,
  onRetryFailed,
}) {
  const [
    selectedScopeKeys,
    setSelectedScopeKeys,
  ] = useState(
    () => new Set(),
  )

  const eligibleScopeKeys =
    useMemo(
      () =>
        model.rows
          .filter(
            (row) =>
              row.selectable,
          )
          .map(
            (row) => row.key,
          ),
      [model.rows],
    )

  const eligibleScopeKeySet =
    useMemo(
      () =>
        new Set(
          eligibleScopeKeys,
        ),
      [eligibleScopeKeys],
    )

  const effectiveSelectedScopeKeys =
    useMemo(
      () =>
        new Set(
          Array.from(
            selectedScopeKeys,
          ).filter(
            (scopeKey) =>
              eligibleScopeKeySet.has(
                scopeKey,
              ),
          ),
        ),
      [
        eligibleScopeKeySet,
        selectedScopeKeys,
      ],
    )

  const allEligibleSelected =
    eligibleScopeKeys.length > 0 &&
    eligibleScopeKeys.every(
      (scopeKey) =>
        effectiveSelectedScopeKeys.has(
          scopeKey,
        ),
    )

  function toggleScope(
    scopeKey,
  ) {
    setSelectedScopeKeys(
      (current) => {
        const next =
          new Set(current)

        if (next.has(scopeKey)) {
          next.delete(scopeKey)
        } else {
          next.add(scopeKey)
        }

        return next
      },
    )
  }

  function toggleAllEligible() {
    setSelectedScopeKeys(
      allEligibleSelected
        ? new Set()
        : new Set(
            eligibleScopeKeys,
          ),
    )
  }

  async function handleRerun() {
    const selected =
      Array.from(
        effectiveSelectedScopeKeys,
      )

    if (
      selected.length === 0 ||
      typeof onRerunSelected !==
        'function'
    ) {
      return
    }

    await onRerunSelected(
      selected,
    )

    setSelectedScopeKeys(
      new Set(),
    )
  }

  const selectedCount =
    effectiveSelectedScopeKeys.size

  return (
    <section className="dashboard-panel cycle-detail-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            RUNNER EXECUTIONS
          </span>

          <h3>Executions</h3>

          <p>
            Retry failed scopes or select completed
            scopes to create traceable reruns.
          </p>
        </div>

        <div className="cycle-execution-header-actions">
          <button
            className="button button-secondary"
            disabled={
              model.retry.disabled
            }
            onClick={
              onRetryFailed
            }
            type="button"
          >
            {model.retry.label}
          </button>

          <button
            className="button button-secondary"
            disabled={
              model.rerun.busy ||
              selectedCount === 0
            }
            onClick={
              handleRerun
            }
            type="button"
          >
            {model.rerun.busy
              ? 'Rerunning...'
              : `Rerun Selected (${selectedCount})`}
          </button>

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

      <div className="cycle-execution-control-note">
        <strong>
          Latest attempt per scope
        </strong>

        <span>
          Previous executions, results, logs, and
          artifacts remain in the cycle history.
        </span>
      </div>

      <div className="cycle-execution-table">
        <div
          aria-hidden="true"
          className="cycle-execution-table-header"
        >
          <label className="cycle-execution-selection">
            <input
              checked={
                allEligibleSelected
              }
              disabled={
                eligibleScopeKeys.length ===
                0
              }
              onChange={
                toggleAllEligible
              }
              tabIndex="-1"
              type="checkbox"
            />
          </label>

          <span>Execution</span>
          <span>Progress</span>
          <span>Status</span>
        </div>

        <div className="cycle-execution-list">
          {model.rows.map((row) => (
            <ExecutionRow
              checked={
                effectiveSelectedScopeKeys.has(
                  row.key,
                )
              }
              key={row.key}
              onToggle={
                toggleScope
              }
              row={row}
            />
          ))}
        </div>
      </div>
    </section>
  )
}

export default CycleExecutionsTab
