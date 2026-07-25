import {
  Fragment,
  useMemo,
  useState,
} from 'react'
import {
  Link,
} from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatTestAssetDate,
} from '../../features/test-assets/testAssetFormatters'

const pageSizeOptions = [
  5,
  10,
  20,
]

function formatVersion(
  versionNumber,
) {
  return versionNumber
    ? `v${versionNumber}`
    : 'Not available'
}

function AssetDetailTable({
  group,
}) {
  return (
    <div className="report-traceability-details">
      <div className="report-traceability-details-heading">
        <div>
          <strong>
            Captured Test Asset versions
          </strong>

          <span>
            Historical asset definitions used by
            this Test Cycle.
          </span>
        </div>

        <Link
          className="button button-secondary report-traceability-action"
          to={`/test-cycles/${encodeURIComponent(
            group.cycleId,
          )}`}
        >
          View Cycle
        </Link>
      </div>

      <div className="report-traceability-asset-table-wrapper">
        <table className="report-traceability-asset-table">
          <thead>
            <tr>
              <th>Test Asset</th>
              <th>Captured Version</th>
              <th>Execution Coverage</th>
              <th>Traceability</th>
              <th>Captured At</th>
            </tr>
          </thead>

          <tbody>
            {group.rows.map(
              (row) => (
                <tr key={row.id}>
                  <td>
                    <strong>
                      {row.assetName}
                    </strong>

                    <span>
                      {row.module}
                      {' / '}
                      {row.feature}
                    </span>

                    <code>
                      {row.assetId}
                    </code>
                  </td>

                  <td>
                    <strong>
                      {formatVersion(
                        row
                          .capturedVersionNumber,
                      )}
                    </strong>

                    <span>
                      {row
                        .capturedVersionId ||
                        'No version ID'}
                    </span>
                  </td>

                  <td>
                    <strong>
                      {row.tracedExecutionCount}
                      {' / '}
                      {row.executionCount}
                    </strong>

                    <span>
                      Executions with this exact
                      captured version
                    </span>
                  </td>

                  <td>
                    <StatusBadge
                      tone={
                        row.traceabilityTone
                      }
                    >
                      {
                        row.traceabilityLabel
                      }
                    </StatusBadge>
                  </td>

                  <td>
                    {formatTestAssetDate(
                      row.capturedAt,
                    )}
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ReportAssetTraceability({
  model,
}) {
  const [
    pageSize,
    setPageSize,
  ] = useState(5)

  const [
    currentPage,
    setCurrentPage,
  ] = useState(1)

  const [
    expandedCycleIds,
    setExpandedCycleIds,
  ] = useState(
    () => new Set(),
  )

  const pageCount =
    Math.max(
      1,
      Math.ceil(
        model.groups.length /
        pageSize,
      ),
    )

  const safePage =
    Math.min(
      currentPage,
      pageCount,
    )

  const visibleGroups =
    useMemo(
      () => {
        const startIndex =
          (
            safePage -
            1
          ) *
          pageSize

        return model.groups.slice(
          startIndex,
          startIndex + pageSize,
        )
      },
      [
        model.groups,
        pageSize,
        safePage,
      ],
    )

  function toggleExpanded(
    cycleId,
  ) {
    setExpandedCycleIds(
      (current) => {
        const next =
          new Set(current)

        if (next.has(cycleId)) {
          next.delete(cycleId)
        } else {
          next.add(cycleId)
        }

        return next
      },
    )
  }

  function handlePageSizeChange(
    event,
  ) {
    setPageSize(
      Number(event.target.value),
    )
    setCurrentPage(1)
  }

  const firstVisibleRecord =
    model.groups.length === 0
      ? 0
      : (
          safePage -
          1
        ) *
          pageSize +
        1

  const lastVisibleRecord =
    Math.min(
      safePage * pageSize,
      model.groups.length,
    )

  return (
    <section className="dashboard-panel report-panel report-traceability-panel">
      <div className="panel-header report-panel-header">
        <div>
          <span className="panel-eyebrow">
            VERSION TRACEABILITY
          </span>

          <h3>
            Execution and Asset Versions
          </h3>

          <p>
            Test Cycles are grouped to avoid
            duplicate cycle information. Expand a
            cycle to review its captured assets.
          </p>
        </div>

        <strong className="report-traceability-count">
          {model.cycleCount} Test Cycles
        </strong>
      </div>

      <div className="report-traceability-summary">
        <div>
          <span>Captured Assets</span>
          <strong>
            {model.captured}
          </strong>
        </div>

        <div>
          <span>Traced Executions</span>
          <strong>
            {model.tracedExecutions}
            {' / '}
            {model.totalExecutions}
          </strong>
        </div>

        <div>
          <span>Complete Cycles</span>
          <strong>
            {model.completeCycles}
          </strong>
        </div>

        <div>
          <span>Needs Attention</span>
          <strong>
            {model.needsAttention}
          </strong>
        </div>

        <div>
          <span>Legacy Cycles</span>
          <strong>
            {model.legacyCycles}
          </strong>
        </div>
      </div>

      <div className="report-traceability-table-wrapper">
        <table className="report-traceability-table">
          <thead>
            <tr>
              <th>Test Cycle</th>
              <th>Assets</th>
              <th>Captured</th>
              <th>Executions</th>
              <th>Source</th>
              <th>Traceability</th>
              <th>Cycle Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {visibleGroups.length > 0 ? (
              visibleGroups.map(
                (group) => {
                  const isExpanded =
                    expandedCycleIds.has(
                      group.cycleId,
                    )

                  return (
                    <Fragment
                      key={group.cycleId}
                    >
                      <tr>
                        <td>
                          <strong>
                            {group.cycleName}
                          </strong>

                          <span>
                            {group.module}
                            {' / '}
                            {group.feature}
                          </span>

                          <code>
                            {group.cycleId}
                          </code>
                        </td>

                        <td>
                          <strong>
                            {group.assetCount}
                          </strong>

                          <span>
                            Selected Test Assets
                          </span>
                        </td>

                        <td>
                          <strong>
                            {group.capturedCount}
                            {' / '}
                            {group.assetCount}
                          </strong>

                          <span>
                            Immutable snapshots
                          </span>
                        </td>

                        <td>
                          <strong>
                            {
                              group
                                .tracedExecutionCount
                            }
                            {' / '}
                            {
                              group
                                .executionCount
                            }
                          </strong>

                          <span>
                            Snapshot coverage
                          </span>
                        </td>

                        <td>
                          <strong>
                            {
                              group
                                .triggerSource
                            }
                          </strong>

                          <span>
                            {group.sourcePlanId ||
                              'Direct cycle'}
                          </span>
                        </td>

                        <td>
                          <StatusBadge
                            tone={
                              group
                                .traceabilityTone
                            }
                          >
                            {
                              group
                                .traceabilityLabel
                            }
                          </StatusBadge>
                        </td>

                        <td>
                          <span>
                            {group.cycleStatus}
                          </span>
                        </td>

                        <td>
                          <div className="report-traceability-actions">
                            <button
                              aria-expanded={
                                isExpanded
                              }
                              className="button button-secondary report-traceability-action"
                              onClick={() =>
                                toggleExpanded(
                                  group.cycleId,
                                )
                              }
                              type="button"
                            >
                              {isExpanded
                                ? 'Collapse'
                                : 'Expand'}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {isExpanded && (
                        <tr className="report-traceability-expanded-row">
                          <td colSpan="8">
                            <AssetDetailTable
                              group={group}
                            />
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                },
              )
            ) : (
              <tr>
                <td
                  className="report-traceability-empty"
                  colSpan="8"
                >
                  <strong>
                    No version traceability records
                  </strong>

                  <span>
                    The matching Test Cycles do not
                    contain selected Test Assets.
                  </span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <footer className="report-traceability-pagination">
        <label>
          <span>Rows per page</span>

          <select
            onChange={
              handlePageSizeChange
            }
            value={pageSize}
          >
            {pageSizeOptions.map(
              (option) => (
                <option
                  key={option}
                  value={option}
                >
                  {option}
                </option>
              ),
            )}
          </select>
        </label>

        <span className="report-traceability-pagination-range">
          {firstVisibleRecord}
          {'–'}
          {lastVisibleRecord}
          {' of '}
          {model.groups.length}
          {' cycles'}
        </span>

        <div className="report-traceability-pagination-actions">
          <button
            className="button button-secondary"
            disabled={safePage <= 1}
            onClick={() =>
              setCurrentPage(
                Math.max(
                  1,
                  safePage - 1,
                ),
              )
            }
            type="button"
          >
            Previous
          </button>

          <span>
            Page {safePage} of {pageCount}
          </span>

          <button
            className="button button-secondary"
            disabled={
              safePage >= pageCount
            }
            onClick={() =>
              setCurrentPage(
                Math.min(
                  pageCount,
                  safePage + 1,
                ),
              )
            }
            type="button"
          >
            Next
          </button>
        </div>
      </footer>
    </section>
  )
}

export default ReportAssetTraceability
