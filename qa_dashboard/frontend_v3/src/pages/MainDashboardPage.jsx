import {
  useMemo,
} from 'react'
import { Link } from 'react-router-dom'

import DashboardAttention from '../components/dashboard/DashboardAttention'
import DashboardCyclePanel from '../components/dashboard/DashboardCyclePanel'
import DashboardEnvironmentPanel from '../components/dashboard/DashboardEnvironmentPanel'
import DashboardQualityOverview from '../components/dashboard/DashboardQualityOverview'
import DashboardRecentCycles from '../components/dashboard/DashboardRecentCycles'
import DashboardSummary from '../components/dashboard/DashboardSummary'
import {
  buildDashboardAttentionRows,
  buildDashboardCycleRows,
  buildDashboardQualityRows,
  selectDashboardEnvironment,
  selectPrimaryDashboardCycle,
  selectRecentDashboardCycles,
  summarizeDashboardRows,
} from '../features/dashboard/dashboardSelectors'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

import '../styles/main-dashboard.css'

function MainDashboardPage() {
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

  const selectedProjectId =
    useProjectEnvironmentStore(
      (state) =>
        state.selectedProjectId,
    )

  const selectedEnvironmentId =
    useProjectEnvironmentStore(
      (state) =>
        state.selectedEnvironmentId,
    )

  const dashboardRows =
    useMemo(
      () =>
        buildDashboardCycleRows({
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

  const summary =
    useMemo(
      () =>
        summarizeDashboardRows(
          dashboardRows,
        ),
      [dashboardRows],
    )

  const primaryCycle =
    useMemo(
      () =>
        selectPrimaryDashboardCycle(
          dashboardRows,
        ),
      [dashboardRows],
    )

  const recentCycles =
    useMemo(
      () =>
        selectRecentDashboardCycles(
          dashboardRows,
        ),
      [dashboardRows],
    )

  const environmentContext =
    useMemo(
      () =>
        selectDashboardEnvironment({
          projects,
          environments,
          selectedProjectId,
          selectedEnvironmentId,
        }),
      [
        projects,
        environments,
        selectedProjectId,
        selectedEnvironmentId,
      ],
    )

  const qualityRows =
    useMemo(
      () =>
        buildDashboardQualityRows(
          summary,
        ),
      [summary],
    )

  const attentionRows =
    useMemo(
      () =>
        buildDashboardAttentionRows(
          summary,
        ),
      [summary],
    )

  return (
    <section className="dashboard-page main-dashboard-page">
      <header className="main-dashboard-heading">
        <div>
          <h2>
            Quality Operations Dashboard
          </h2>

          <p>
            Monitor actual Test Cycle activity,
            execution results, environment
            configuration, and quality signals.
          </p>
        </div>

        <div className="main-dashboard-heading-actions">
          <Link
            className="button button-secondary"
            to="/history"
          >
            View History
          </Link>

          <Link
            className="button button-primary"
            to="/test-cycles/new"
          >
            Create Test Cycle
          </Link>
        </div>
      </header>

      <DashboardSummary
        summary={summary}
      />

      <div className="main-dashboard-primary-grid">
        <DashboardCyclePanel
          cycle={primaryCycle}
        />

        <DashboardEnvironmentPanel
          context={environmentContext}
        />
      </div>

      <div className="main-dashboard-secondary-grid">
        <DashboardRecentCycles
          cycles={recentCycles}
        />

        <DashboardQualityOverview
          rows={qualityRows}
          summary={summary}
        />
      </div>

      <DashboardAttention
        rows={attentionRows}
      />
    </section>
  )
}

export default MainDashboardPage
