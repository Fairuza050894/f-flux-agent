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

const statusFilterOptions = [
  {
    label: 'All statuses',
    value: 'all',
  },
  {
    label: 'Current',
    value: 'current',
  },
  {
    label: 'Outdated',
    value: 'outdated',
  },
  {
    label: 'Archived',
    value: 'archived',
  },
  {
    label: 'Missing',
    value: 'missing',
  },
  {
    label: 'No Snapshot',
    value: 'unsnapshotted',
  },
]

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

function normalizeSearchValue(
  value,
) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
}

function rowMatchesSearch(
  row,
  searchTerm,
) {
  if (!searchTerm) {
    return true
  }

  const searchableText = [
    row.assetId,
    row.name,
    row.module,
    row.feature,
    row.sourceLabel,
    row.sourcePlanId,
    row.statusLabel,
    row.reason,
  ]
    .map(normalizeSearchValue)
    .join(' ')

  return searchableText.includes(
    searchTerm,
  )
}

function SnapshotDefinition({
  row,
}) {
  if (!row.hasSnapshot) {
    return (
      <div className="cycle-assets-refined-empty-definition">
        <strong>
          Captured definition unavailable
        </strong>

        <p>
          This legacy or incomplete Test Cycle
          references an asset ID without an immutable
          Test Asset snapshot.
        </p>
      </div>
    )
  }

  return (
    <div className="cycle-assets-refined-definition">
      <dl className="cycle-assets-refined-definition-metadata">
        <div>
          <dt>Type</dt>
          <dd>{row.typeLabel}</dd>
        </div>

        <div>
          <dt>Priority</dt>
          <dd>{row.priority}</dd>
        </div>

        <div>
          <dt>Automation</dt>
          <dd>{row.automationStatus}</dd>
        </div>

        <div>
          <dt>Execution Ready</dt>
          <dd>
            {row.executionReady
              ? 'Yes'
              : 'No'}
          </dd>
        </div>

        <div>
          <dt>Version ID</dt>
          <dd>
            <code>
              {row.capturedVersionId ||
                'Not available'}
            </code>
          </dd>
        </div>

        <div>
          <dt>Change Summary</dt>
          <dd>
            {row.capturedChangeSummary ||
              'No change summary.'}
          </dd>
        </div>
      </dl>

      <div className="cycle-assets-refined-definition-grid">
        <section>
          <h4>Description</h4>
          <p>{row.description}</p>
        </section>

        <section>
          <h4>Preconditions</h4>
          <p>{row.preconditions}</p>
        </section>

        <section className="cycle-assets-refined-definition-wide">
          <h4>Test Steps</h4>

          {row.steps.length > 0 ? (
            <ol>
              {row.steps.map(
                (step, index) => (
                  <li
                    key={`${row.assetId}-step-${index + 1}`}
                  >
                    {step}
                  </li>
                ),
              )}
            </ol>
          ) : (
            <p>
              No captured test steps.
            </p>
          )}
        </section>

        <section className="cycle-assets-refined-definition-wide">
          <h4>Expected Result</h4>
          <p>{row.expectedResult}</p>
        </section>
      </div>
    </div>
  )
}

function CycleTestAssetsTab({
  comparison,
}) {
  const [
    searchTerm,
    setSearchTerm,
  ] = useState('')

  const [
    statusFilter,
    setStatusFilter,
  ] = useState('all')

  const [
    pageSize,
    setPageSize,
  ] = useState(5)

  const [
    currentPage,
    setCurrentPage,
  ] = useState(1)

  const [
    expandedAssetIds,
    setExpandedAssetIds,
  ] = useState(
    () => new Set(),
  )

  const rows =
    Array.isArray(comparison?.rows)
      ? comparison.rows
      : []

  const normalizedSearch =
    normalizeSearchValue(
      searchTerm,
    )

  const filteredRows =
    useMemo(
      () =>
        rows.filter(
          (row) => {
            const matchesStatus =
              statusFilter === 'all' ||
              row.statusKey ===
                statusFilter

            return (
              matchesStatus &&
              rowMatchesSearch(
                row,
                normalizedSearch,
              )
            )
          },
        ),
      [
        normalizedSearch,
        rows,
        statusFilter,
      ],
    )

  const pageCount =
    Math.max(
      1,
      Math.ceil(
        filteredRows.length /
        pageSize,
      ),
    )

  const safePage =
    Math.min(
      currentPage,
      pageCount,
    )

  const visibleRows =
    useMemo(
      () => {
        const startIndex =
          (
            safePage -
            1
          ) *
          pageSize

        return filteredRows.slice(
          startIndex,
          startIndex + pageSize,
        )
      },
      [
        filteredRows,
        pageSize,
        safePage,
      ],
    )

  const firstVisibleRecord =
    filteredRows.length === 0
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
      filteredRows.length,
    )

  const hasActiveFilters =
    searchTerm.trim() !== '' ||
    statusFilter !== 'all'

  function handleSearchChange(
    event,
  ) {
    setSearchTerm(
      event.target.value,
    )
    setCurrentPage(1)
  }

  function handleStatusChange(
    event,
  ) {
    setStatusFilter(
      event.target.value,
    )
    setCurrentPage(1)
  }

  function handlePageSizeChange(
    event,
  ) {
    setPageSize(
      Number(event.target.value),
    )
    setCurrentPage(1)
  }

  function handleClearFilters() {
    setSearchTerm('')
    setStatusFilter('all')
    setCurrentPage(1)
  }

  function toggleDefinition(
    assetId,
  ) {
    setExpandedAssetIds(
      (current) => {
        const next =
          new Set(current)

        if (next.has(assetId)) {
          next.delete(assetId)
        } else {
          next.add(assetId)
        }

        return next
      },
    )
  }

  return (
    <div className="cycle-detail-content">
      <section className="dashboard-panel cycle-detail-panel cycle-assets-refined-panel">
        <div className="panel-header cycle-assets-refined-header">
          <div>
            <span className="panel-eyebrow">
              VERSION TRACEABILITY
            </span>

            <h3>
              Captured vs Live Test Assets
            </h3>

            <p>
              Review immutable Test Asset definitions
              used by this cycle and compare them with
              the current live catalog.
            </p>
          </div>

          <strong className="cycle-detail-count">
            {comparison?.total ?? 0} Assets
          </strong>
        </div>

        <div className="cycle-assets-refined-summary">
          <div>
            <span>Captured</span>
            <strong>
              {comparison?.captured ?? 0}
            </strong>
          </div>

          <div>
            <span>Current</span>
            <strong>
              {comparison?.current ?? 0}
            </strong>
          </div>

          <div>
            <span>Outdated</span>
            <strong>
              {comparison?.outdated ?? 0}
            </strong>
          </div>

          <div>
            <span>Archived</span>
            <strong>
              {comparison?.archived ?? 0}
            </strong>
          </div>

          <div>
            <span>Missing</span>
            <strong>
              {comparison?.missing ?? 0}
            </strong>
          </div>

          <div>
            <span>No Snapshot</span>
            <strong>
              {comparison?.unsnapshotted ?? 0}
            </strong>
          </div>
        </div>

        <div className="cycle-assets-refined-toolbar">
          <div className="cycle-assets-refined-search">
            <label htmlFor="cycle-asset-search">
              Search Test Assets
            </label>

            <input
              id="cycle-asset-search"
              onChange={
                handleSearchChange
              }
              placeholder="Search name, ID, module, feature, or source"
              type="search"
              value={searchTerm}
            />
          </div>

          <div className="cycle-assets-refined-filter">
            <label htmlFor="cycle-asset-status-filter">
              Comparison Status
            </label>

            <select
              id="cycle-asset-status-filter"
              onChange={
                handleStatusChange
              }
              value={statusFilter}
            >
              {statusFilterOptions.map(
                (option) => (
                  <option
                    key={option.value}
                    value={option.value}
                  >
                    {option.label}
                  </option>
                ),
              )}
            </select>
          </div>

          {hasActiveFilters && (
            <button
              className="button button-secondary cycle-assets-refined-clear"
              onClick={
                handleClearFilters
              }
              type="button"
            >
              Clear Filters
            </button>
          )}
        </div>

        <div className="cycle-assets-refined-result-bar">
          <span>
            Showing {filteredRows.length} of{' '}
            {rows.length} Test Assets
          </span>

          <span>
            Expand a row to review the captured
            definition.
          </span>
        </div>

        <div className="cycle-assets-refined-table-wrapper">
          <table className="cycle-assets-refined-table">
            <thead>
              <tr>
                <th>Test Asset</th>
                <th>Source</th>
                <th>Captured</th>
                <th>Live</th>
                <th>Comparison</th>
                <th>Captured At</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {visibleRows.length > 0 ? (
                visibleRows.map(
                  (row) => {
                    const isExpanded =
                      expandedAssetIds.has(
                        row.assetId,
                      )

                    return (
                      <Fragment
                        key={row.assetId}
                      >
                        <tr className="cycle-assets-refined-main-row">
                          <td>
                            <strong title={row.name}>
                              {row.name}
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
                              {row.sourceLabel}
                            </strong>

                            <span>
                              {row.sourcePlanId ||
                                'Direct cycle'}
                            </span>
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
                              {formatVersion(
                                row
                                  .liveVersionNumber,
                              )}
                            </strong>

                            <span>
                              {row.liveVersionId ||
                                row.lifecycleStatus}
                            </span>
                          </td>

                          <td>
                            <StatusBadge
                              tone={
                                row.statusTone
                              }
                            >
                              {row.statusLabel}
                            </StatusBadge>

                            <span className="cycle-assets-refined-reason">
                              {row.reason}
                            </span>
                          </td>

                          <td>
                            <span className="cycle-assets-refined-date">
                              {formatTestAssetDate(
                                row.capturedAt,
                              )}
                            </span>
                          </td>

                          <td>
                            <div className="cycle-assets-refined-actions">
                              <button
                                aria-expanded={
                                  isExpanded
                                }
                                className="button button-secondary cycle-assets-refined-action"
                                onClick={() =>
                                  toggleDefinition(
                                    row.assetId,
                                  )
                                }
                                type="button"
                              >
                                {isExpanded
                                  ? 'Hide Details'
                                  : 'View Details'}
                              </button>

                              {row.hasLiveAsset ? (
                                <Link
                                  className="button button-secondary cycle-assets-refined-action"
                                  to={`/test-assets/${encodeURIComponent(
                                    row.assetId,
                                  )}`}
                                >
                                  View Asset
                                </Link>
                              ) : (
                                <button
                                  className="button button-secondary cycle-assets-refined-action"
                                  disabled
                                  type="button"
                                >
                                  Unavailable
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>

                        {isExpanded && (
                          <tr className="cycle-assets-refined-expanded-row">
                            <td colSpan="7">
                              <div className="cycle-assets-refined-expanded-panel">
                                <div className="cycle-assets-refined-expanded-heading">
                                  <div>
                                    <strong>
                                      Captured Definition
                                    </strong>

                                    <span>
                                      Immutable Test Asset data stored
                                      with this Test Cycle.
                                    </span>
                                  </div>

                                  <StatusBadge
                                    tone={
                                      row.statusTone
                                    }
                                  >
                                    {row.statusLabel}
                                  </StatusBadge>
                                </div>

                                <SnapshotDefinition
                                  row={row}
                                />
                              </div>
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
                    className="cycle-assets-refined-empty"
                    colSpan="7"
                  >
                    <strong>
                      {hasActiveFilters
                        ? 'No matching Test Assets'
                        : 'No Test Assets selected'}
                    </strong>

                    <span>
                      {hasActiveFilters
                        ? 'Adjust the search term or comparison status filter.'
                        : 'This Test Cycle does not reference any Test Assets.'}
                    </span>

                    {hasActiveFilters && (
                      <button
                        className="button button-secondary"
                        onClick={
                          handleClearFilters
                        }
                        type="button"
                      >
                        Clear Filters
                      </button>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <footer className="cycle-assets-refined-pagination">
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

          <span className="cycle-assets-refined-pagination-range">
            {firstVisibleRecord}
            {'–'}
            {lastVisibleRecord}
            {' of '}
            {filteredRows.length}
          </span>

          <div className="cycle-assets-refined-pagination-actions">
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
    </div>
  )
}

export default CycleTestAssetsTab
