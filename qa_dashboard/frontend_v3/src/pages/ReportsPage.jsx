import {
  useMemo,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import ReportCycleTable from '../components/reports/ReportCycleTable'
import ReportEmptyState from '../components/reports/ReportEmptyState'
import ReportFilters from '../components/reports/ReportFilters'
import ReportScopeTable from '../components/reports/ReportScopeTable'
import ReportSummary from '../components/reports/ReportSummary'
import ReportAssetTraceability from '../components/reports/ReportAssetTraceability'
import {
  REPORT_DEFAULT_FILTERS,
  REPORT_FILTER_ALL,
} from '../features/reports/reportConstants'
import {
  buildReportRows,
  buildScopeBreakdown,
  filterReportRows,
  selectReportEnvironments,
  summarizeReportRows,
} from '../features/reports/reportSelectors'
import {
  buildReportAssetTraceability,
} from '../features/reports/reportTraceabilitySelectors'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

import '../styles/reports.css'
import '../styles/report-traceability.css'

function hasActiveFilters(
  filters,
) {
  return (
    filters.search.trim() !== '' ||
    filters.projectId !==
      REPORT_FILTER_ALL ||
    filters.environmentId !==
      REPORT_FILTER_ALL ||
    filters.cycleType !==
      REPORT_FILTER_ALL ||
    filters.qualityStatus !==
      REPORT_FILTER_ALL ||
    filters.period !==
      REPORT_FILTER_ALL
  )
}

function ReportsPage() {
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
    ...REPORT_DEFAULT_FILTERS,
  }))

  const reportRows =
    useMemo(
      () =>
        buildReportRows({
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
        selectReportEnvironments(
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
        filterReportRows(
          reportRows,
          filters,
        ),
      [
        reportRows,
        filters,
      ],
    )

  const summary =
    useMemo(
      () =>
        summarizeReportRows(
          filteredRows,
        ),
      [filteredRows],
    )

  const scopeBreakdown =
    useMemo(
      () =>
        buildScopeBreakdown(
          filteredRows,
        ),
      [filteredRows],
    )

  const assetTraceability =
    useMemo(
      () =>
        buildReportAssetTraceability({
          cycles,
          reportRows:
            filteredRows,
        }),
      [
        cycles,
        filteredRows,
      ],
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
            REPORT_FILTER_ALL,
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
      ...REPORT_DEFAULT_FILTERS,
    })
  }

  const activeFilters =
    hasActiveFilters(filters)

  return (
    <section className="dashboard-page reports-page">
      <header className="reports-page-heading">
        <div>
          <h2>Reports</h2>

          <p>
            Consolidated quality results from
            stored test cycles and supported
            execution runners.
          </p>
        </div>

        <Link
          className="button button-secondary"
          to="/history"
        >
          View History
        </Link>
      </header>

      <ReportSummary
        summary={summary}
      />

      <section className="dashboard-panel report-panel">
        <div className="panel-header report-panel-header">
          <div>
            <h3>Report Scope</h3>

            <p>
              Filter the report dataset without
              changing the stored test results.
            </p>
          </div>
        </div>

        <ReportFilters
          environments={visibleEnvironments}
          filters={filters}
          onChange={handleFilterChange}
          onReset={handleResetFilters}
          projects={projects}
          resultCount={filteredRows.length}
          totalCount={reportRows.length}
        />
      </section>

      {filteredRows.length === 0 ? (
        <section className="dashboard-panel report-panel">
          <ReportEmptyState
            hasFilters={activeFilters}
            onReset={handleResetFilters}
          />
        </section>
      ) : (
        <>
          <section className="dashboard-panel report-panel">
            <div className="panel-header report-panel-header">
              <div>
                <span className="panel-eyebrow">
                  SCOPE BREAKDOWN
                </span>

                <h3>Quality by Test Scope</h3>

                <p>
                  Aggregated results grouped by
                  execution scope.
                </p>
              </div>
            </div>

            {scopeBreakdown.length > 0 ? (
              <ReportScopeTable
                rows={scopeBreakdown}
              />
            ) : (
              <ReportEmptyState
                hasFilters={false}
                onReset={handleResetFilters}
              />
            )}
          </section>

          <ReportAssetTraceability
            model={
              assetTraceability
            }
          />

          <section className="dashboard-panel report-panel">
            <div className="panel-header report-panel-header">
              <div>
                <span className="panel-eyebrow">
                  CYCLE REPORTS
                </span>

                <h3>Test Cycle Results</h3>

                <p>
                  Consolidated quality outcome for
                  each matching Test Cycle.
                </p>
              </div>
            </div>

            <ReportCycleTable
              rows={filteredRows}
            />
          </section>
        </>
      )}
    </section>
  )
}

export default ReportsPage
