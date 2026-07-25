import {
  useMemo,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import ReportAssetTraceability from '../components/reports/ReportAssetTraceability'
import ReportDeliveryPanel from '../components/reports/ReportDeliveryPanel'
import ReportCycleTable from '../components/reports/ReportCycleTable'
import ReportEmptyState from '../components/reports/ReportEmptyState'
import ReportFilters from '../components/reports/ReportFilters'
import ReportScopeTable from '../components/reports/ReportScopeTable'
import ReportSummary from '../components/reports/ReportSummary'
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
import { useTestAssetStore } from '../stores/testAssetStore'
import { useTestCycleStore } from '../stores/testCycleStore'

import '../styles/reports.css'
import '../styles/report-traceability.css'

const reportTabs = [
  {
    id: 'overview',
    label: 'Overview',
  },
  {
    id: 'traceability',
    label: 'Traceability',
  },
  {
    id: 'results',
    label: 'Cycle Results',
  },
  {
    id: 'delivery',
    label: 'Export & Delivery',
  },
]

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

  const assets =
    useTestAssetStore(
      (state) => state.assets,
    )

  const [
    activeTab,
    setActiveTab,
  ] = useState('overview')

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

  const filteredCycles =
    useMemo(
      () => {
        const visibleCycleIds =
          new Set(
            filteredRows.map(
              (row) => row.id,
            ),
          )

        return cycles.filter(
          (cycle) =>
            visibleCycleIds.has(
              cycle.id,
            ),
        )
      },
      [cycles, filteredRows],
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
            Consolidated quality results,
            execution traceability, and historical
            Test Cycle outcomes.
          </p>
        </div>

        <Link
          className="button button-secondary"
          to="/history"
        >
          View History
        </Link>
      </header>

      <section className="dashboard-panel report-panel">
        <div className="panel-header report-panel-header">
          <div>
            <h3>Report Scope</h3>

            <p>
              Filters are shared across Overview,
              Traceability, and Cycle Results.
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

      <nav
        aria-label="Report sections"
        className="report-section-tabs"
      >
        {reportTabs.map((tab) => {
          const isActive =
            activeTab === tab.id

          return (
            <button
              aria-current={
                isActive
                  ? 'page'
                  : undefined
              }
              className={[
                'report-section-tab',
                isActive
                  ? 'report-section-tab-active'
                  : '',
              ]
                .filter(Boolean)
                .join(' ')}
              key={tab.id}
              onClick={() =>
                setActiveTab(tab.id)
              }
              type="button"
            >
              {tab.label}
            </button>
          )
        })}
      </nav>

      {filteredRows.length === 0 ? (
        <section className="dashboard-panel report-panel">
          <ReportEmptyState
            hasFilters={activeFilters}
            onReset={handleResetFilters}
          />
        </section>
      ) : (
        <>
          {activeTab === 'overview' && (
            <div className="report-tab-content">
              <ReportSummary
                summary={summary}
              />

              <section className="dashboard-panel report-panel">
                <div className="panel-header report-panel-header">
                  <div>
                    <span className="panel-eyebrow">
                      SCOPE BREAKDOWN
                    </span>

                    <h3>
                      Quality by Test Scope
                    </h3>

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
                    onReset={
                      handleResetFilters
                    }
                  />
                )}
              </section>
            </div>
          )}

          {activeTab === 'traceability' && (
            <ReportAssetTraceability
              model={
                assetTraceability
              }
            />
          )}

          {activeTab === 'delivery' && (
            <ReportDeliveryPanel
              assets={assets}
              cycles={filteredCycles}
              environments={environments}
              projects={projects}
            />
          )}

          {activeTab === 'results' && (
            <section className="dashboard-panel report-panel">
              <div className="panel-header report-panel-header">
                <div>
                  <span className="panel-eyebrow">
                    CYCLE REPORTS
                  </span>

                  <h3>
                    Test Cycle Results
                  </h3>

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
          )}
        </>
      )}
    </section>
  )
}

export default ReportsPage
