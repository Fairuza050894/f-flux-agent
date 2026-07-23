import {
  TEST_ASSET_AUTOMATION_STATUSES,
  TEST_ASSET_PRIORITIES,
  TEST_ASSET_TYPES,
} from '../../features/test-assets/testAssetConstants'

function TestAssetFilters({
  filters,
  hasActiveFilters,
  onChange,
  onClear,
  projects,
  resultCount,
  totalCount,
}) {
  return (
    <div className="test-asset-filter-section">
      <div className="test-asset-filter-heading">
        <div>
          <h3>Asset Catalog</h3>

          <p>
            {resultCount} of {totalCount} Test Assets
            displayed
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

      <div className="test-asset-filter-grid">
        <label className="test-asset-filter-search">
          <span>Search</span>

          <input
            onChange={(event) =>
              onChange(
                'searchTerm',
                event.target.value,
              )
            }
            placeholder="Search ID, name, module, or feature"
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
          <span>Type</span>

          <select
            onChange={(event) =>
              onChange(
                'type',
                event.target.value,
              )
            }
            value={filters.type}
          >
            <option value="all">
              All Types
            </option>

            {TEST_ASSET_TYPES.map(
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

        <label>
          <span>Priority</span>

          <select
            onChange={(event) =>
              onChange(
                'priority',
                event.target.value,
              )
            }
            value={filters.priority}
          >
            <option value="all">
              All Priorities
            </option>

            {TEST_ASSET_PRIORITIES.map(
              (priority) => (
                <option
                  key={priority}
                  value={priority}
                >
                  {priority}
                </option>
              ),
            )}
          </select>
        </label>

        <label>
          <span>Automation</span>

          <select
            onChange={(event) =>
              onChange(
                'automationStatus',
                event.target.value,
              )
            }
            value={
              filters.automationStatus
            }
          >
            <option value="all">
              All Statuses
            </option>

            {TEST_ASSET_AUTOMATION_STATUSES.map(
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
          <span>Execution Ready</span>

          <select
            onChange={(event) =>
              onChange(
                'executionReady',
                event.target.value,
              )
            }
            value={
              filters.executionReady
            }
          >
            <option value="all">
              All
            </option>
            <option value="yes">
              Ready
            </option>
            <option value="no">
              Not Ready
            </option>
          </select>
        </label>

        <label>
          <span>Recommended</span>

          <select
            onChange={(event) =>
              onChange(
                'recommended',
                event.target.value,
              )
            }
            value={filters.recommended}
          >
            <option value="all">
              All
            </option>
            <option value="yes">
              Recommended
            </option>
            <option value="no">
              Not Recommended
            </option>
          </select>
        </label>
      </div>
    </div>
  )
}

export default TestAssetFilters
