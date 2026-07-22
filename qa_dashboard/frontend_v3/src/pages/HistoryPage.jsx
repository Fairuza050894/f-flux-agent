import {
  useMemo,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import HistoryEmptyState from '../components/history/HistoryEmptyState'
import HistoryFilters from '../components/history/HistoryFilters'
import HistorySummary from '../components/history/HistorySummary'
import HistoryTable from '../components/history/HistoryTable'
import {
  HISTORY_DEFAULT_FILTERS,
  HISTORY_FILTER_ALL,
} from '../features/history/historyConstants'
import {
  buildHistoryRows,
  filterHistoryRows,
  selectHistoryEnvironments,
  summarizeHistoryRows,
} from '../features/history/historySelectors'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

import '../styles/history.css'

function hasActiveFilters(
  filters,
) {
  return (
    filters.search.trim() !== '' ||
    filters.projectId !==
      HISTORY_FILTER_ALL ||
    filters.environmentId !==
      HISTORY_FILTER_ALL ||
    filters.cycleType !==
      HISTORY_FILTER_ALL ||
    filters.status !==
      HISTORY_FILTER_ALL
  )
}

function HistoryPage() {
  const cycles =
    useTestCycleStore(
      (state) => state.cycles,
    )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const [
    filters,
    setFilters,
  ] = useState(() => ({
    ...HISTORY_DEFAULT_FILTERS,
  }))

  const historyRows =
    useMemo(
      () =>
        buildHistoryRows({
          cycles,
          projects,
          environments,
        }),
      [
        cycles,
        projects,
        environments,
      ],
    )

  const visibleEnvironments =
    useMemo(
      () =>
        selectHistoryEnvironments(
          environments,
          filters.projectId,
        ),
      [
        environments,
        filters.projectId,
      ],
    )

  const filteredRows =
    useMemo(
      () =>
        filterHistoryRows(
          historyRows,
          filters,
        ),
      [
        historyRows,
        filters,
      ],
    )

  const summary =
    useMemo(
      () =>
        summarizeHistoryRows(
          filteredRows,
        ),
      [filteredRows],
    )

  function handleFilterChange(
    field,
    value,
  ) {
    setFilters((current) => {
      if (field === 'projectId') {
        return {
          ...current,
          projectId: value,
          environmentId:
            HISTORY_FILTER_ALL,
        }
      }

      return {
        ...current,
        [field]: value,
      }
    })
  }

  function handleResetFilters() {
    setFilters({
      ...HISTORY_DEFAULT_FILTERS,
    })
  }

  const activeFilters =
    hasActiveFilters(filters)

  return (
    <section className="dashboard-page history-page">
      <header className="history-page-heading">
        <div>
          <h2>History</h2>

          <p>
            Review previous test cycles,
            execution outcomes, and recorded
            result metrics.
          </p>
        </div>

        <Link
          className="button button-secondary"
          to="/test-cycles"
        >
          View Test Cycles
        </Link>
      </header>

      <HistorySummary
        summary={summary}
      />

      <section className="dashboard-panel history-panel">
        <div className="panel-header history-panel-header">
          <div>
            <h3>Test Cycle History</h3>

            <p>
              Search and filter stored test
              cycle records.
            </p>
          </div>
        </div>

        <HistoryFilters
          environments={visibleEnvironments}
          filters={filters}
          onChange={handleFilterChange}
          onReset={handleResetFilters}
          projects={projects}
          resultCount={filteredRows.length}
          totalCount={historyRows.length}
        />

        {filteredRows.length > 0 ? (
          <HistoryTable
            rows={filteredRows}
          />
        ) : (
          <HistoryEmptyState
            hasFilters={activeFilters}
            onReset={handleResetFilters}
          />
        )}
      </section>
    </section>
  )
}

export default HistoryPage
