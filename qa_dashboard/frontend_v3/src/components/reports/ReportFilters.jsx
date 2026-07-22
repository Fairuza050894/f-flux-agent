import {
  REPORT_CYCLE_TYPE_OPTIONS,
  REPORT_DEFAULT_FILTERS,
  REPORT_FILTER_ALL,
  REPORT_PERIOD_OPTIONS,
  REPORT_QUALITY_STATUS_OPTIONS,
} from '../../features/reports/reportConstants'

function hasActiveFilters(
  filters,
) {
  return (
    filters.search.trim() !== '' ||
    filters.projectId !==
      REPORT_DEFAULT_FILTERS.projectId ||
    filters.environmentId !==
      REPORT_DEFAULT_FILTERS.environmentId ||
    filters.cycleType !==
      REPORT_DEFAULT_FILTERS.cycleType ||
    filters.qualityStatus !==
      REPORT_DEFAULT_FILTERS.qualityStatus ||
    filters.period !==
      REPORT_DEFAULT_FILTERS.period
  )
}

function ReportFilters({
  environments,
  filters,
  onChange,
  onReset,
  projects,
  resultCount,
  totalCount,
}) {
  const activeFilters =
    hasActiveFilters(filters)

  return (
    <div className="report-filter-section">
      <div className="report-filter-grid">
        <label className="report-filter-field report-filter-search">
          <span>Search</span>

          <input
            aria-label="Search consolidated reports"
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

        <label className="report-filter-field">
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
              value={REPORT_FILTER_ALL}
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

        <label className="report-filter-field">
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
              value={REPORT_FILTER_ALL}
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

        <label className="report-filter-field">
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
            {REPORT_CYCLE_TYPE_OPTIONS.map(
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

        <label className="report-filter-field">
          <span>Quality Status</span>

          <select
            onChange={(event) =>
              onChange(
                'qualityStatus',
                event.target.value,
              )
            }
            value={filters.qualityStatus}
          >
            {REPORT_QUALITY_STATUS_OPTIONS.map(
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

        <label className="report-filter-field">
          <span>Period</span>

          <select
            onChange={(event) =>
              onChange(
                'period',
                event.target.value,
              )
            }
            value={filters.period}
          >
            {REPORT_PERIOD_OPTIONS.map(
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

        <div className="report-filter-actions">
          <button
            className="button button-secondary"
            disabled={!activeFilters}
            onClick={onReset}
            type="button"
          >
            Clear
          </button>
        </div>
      </div>

      <p className="report-filter-result">
        Showing
        {' '}
        <strong>{resultCount}</strong>
        {' '}
        of
        {' '}
        <strong>{totalCount}</strong>
        {' '}
        test cycle reports
      </p>
    </div>
  )
}

export default ReportFilters
