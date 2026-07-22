import {
  HISTORY_CYCLE_TYPE_OPTIONS,
  HISTORY_DEFAULT_FILTERS,
  HISTORY_FILTER_ALL,
  HISTORY_STATUS_OPTIONS,
} from '../../features/history/historyConstants'

function hasActiveHistoryFilters(
  filters,
) {
  return (
    filters.search.trim() !== '' ||
    filters.projectId !==
      HISTORY_DEFAULT_FILTERS.projectId ||
    filters.environmentId !==
      HISTORY_DEFAULT_FILTERS.environmentId ||
    filters.cycleType !==
      HISTORY_DEFAULT_FILTERS.cycleType ||
    filters.status !==
      HISTORY_DEFAULT_FILTERS.status
  )
}

function HistoryFilters({
  environments,
  filters,
  onChange,
  onReset,
  projects,
  resultCount,
  totalCount,
}) {
  const hasActiveFilters =
    hasActiveHistoryFilters(
      filters,
    )

  return (
    <div className="history-filter-section">
      <div className="history-filter-grid">
        <label className="history-filter-field history-filter-search">
          <span>Search</span>

          <input
            aria-label="Search test cycle history"
            onChange={(event) =>
              onChange(
                'search',
                event.target.value,
              )
            }
            placeholder="Cycle, module, release, or run ID"
            type="search"
            value={filters.search}
          />
        </label>

        <label className="history-filter-field">
          <span>Project</span>

          <select
            onChange={(event) =>
              onChange(
                'projectId',
                event.target.value,
              )
            }
            value={filters.projectId}
          >
            <option
              value={HISTORY_FILTER_ALL}
            >
              All projects
            </option>

            {projects.map((project) => (
              <option
                key={project.id}
                value={project.id}
              >
                {project.name}
              </option>
            ))}
          </select>
        </label>

        <label className="history-filter-field">
          <span>Environment</span>

          <select
            disabled={
              environments.length === 0
            }
            onChange={(event) =>
              onChange(
                'environmentId',
                event.target.value,
              )
            }
            value={filters.environmentId}
          >
            <option
              value={HISTORY_FILTER_ALL}
            >
              All environments
            </option>

            {environments.map(
              (environment) => (
                <option
                  key={environment.id}
                  value={environment.id}
                >
                  {environment.name}
                </option>
              ),
            )}
          </select>
        </label>

        <label className="history-filter-field">
          <span>Cycle Type</span>

          <select
            onChange={(event) =>
              onChange(
                'cycleType',
                event.target.value,
              )
            }
            value={filters.cycleType}
          >
            {HISTORY_CYCLE_TYPE_OPTIONS.map(
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
        </label>

        <label className="history-filter-field">
          <span>Status</span>

          <select
            onChange={(event) =>
              onChange(
                'status',
                event.target.value,
              )
            }
            value={filters.status}
          >
            {HISTORY_STATUS_OPTIONS.map(
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
        </label>

        <div className="history-filter-actions">
          <button
            className="button button-secondary"
            disabled={!hasActiveFilters}
            onClick={onReset}
            type="button"
          >
            Clear
          </button>
        </div>
      </div>

      <p className="history-filter-result">
        Showing
        {' '}
        <strong>{resultCount}</strong>
        {' '}
        of
        {' '}
        <strong>{totalCount}</strong>
        {' '}
        test cycles
      </p>
    </div>
  )
}

export default HistoryFilters
