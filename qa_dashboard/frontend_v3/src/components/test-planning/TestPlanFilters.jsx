import {
  TEST_PLAN_SCOPE_OPTIONS,
  TEST_PLAN_STATUSES,
} from '../../features/test-planning/testPlanConstants'

function TestPlanFilters({
  filters,
  hasActiveFilters,
  onChange,
  onClear,
  projects,
  resultCount,
  totalCount,
}) {
  return (
    <div className="test-plan-filter-section">
      <div className="test-plan-filter-heading">
        <div>
          <h3>Plan Catalog</h3>

          <p>
            {resultCount} of {totalCount}{' '}
            Test Plans displayed
          </p>
        </div>

        <button
          className="button button-secondary"
          disabled={!hasActiveFilters}
          onClick={onClear}
          type="button"
        >
          Clear Filters
        </button>
      </div>

      <div className="test-plan-filter-grid">
        <label className="test-plan-filter-search">
          <span>Search</span>

          <input
            onChange={(event) =>
              onChange(
                'searchTerm',
                event.target.value,
              )
            }
            placeholder="Search ID, plan name, module, or objective"
            type="search"
            value={filters.searchTerm}
          />
        </label>

        <label>
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
            <option value="all">
              All Projects
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

        <label>
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
            <option value="all">
              All Statuses
            </option>

            {TEST_PLAN_STATUSES.map(
              (status) => (
                <option
                  key={status}
                  value={status}
                >
                  {status}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Testing Scope</span>

          <select
            onChange={(event) =>
              onChange(
                'scopeType',
                event.target.value,
              )
            }
            value={filters.scopeType}
          >
            <option value="all">
              All Scopes
            </option>

            {TEST_PLAN_SCOPE_OPTIONS.map(
              (option) => (
                <option
                  key={option.key}
                  value={option.key}
                >
                  {option.label}
                </option>
              ),
            )}
          </select>
        </label>
      </div>
    </div>
  )
}

export default TestPlanFilters
