import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../components/StatusBadge'
import TestPlanFilters from '../components/test-planning/TestPlanFilters'
import TestPlanMetrics from '../components/test-planning/TestPlanMetrics'
import TestPlanTable from '../components/test-planning/TestPlanTable'
import {
  TEST_PLAN_FILTER_DEFAULTS,
} from '../features/test-planning/testPlanConstants'
import {
  buildTestPlanMetrics,
  filterTestPlans,
} from '../features/test-planning/testPlanSelectors'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestPlanStore } from '../stores/testPlanStore'

function TestPlanningPage() {
  const [filters, setFilters] =
    useState(() => ({
      ...TEST_PLAN_FILTER_DEFAULTS,
    }))

  const plans = useTestPlanStore(
    (state) => state.plans,
  )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const metrics = useMemo(
    () =>
      buildTestPlanMetrics(
        plans,
      ),
    [plans],
  )

  const filteredPlans = useMemo(
    () =>
      filterTestPlans({
        filters,
        plans,
      }),
    [
      filters,
      plans,
    ],
  )

  const projectNames = useMemo(
    () =>
      Object.fromEntries(
        projects.map((project) => [
          project.id,
          project.name,
        ]),
      ),
    [projects],
  )

  const environmentNames = useMemo(
    () =>
      Object.fromEntries(
        environments.map(
          (environment) => [
            environment.id,
            environment.name,
          ],
        ),
      ),
    [environments],
  )

  const hasActiveFilters =
    Object.entries(
      TEST_PLAN_FILTER_DEFAULTS,
    ).some(
      ([key, defaultValue]) =>
        filters[key] !== defaultValue,
    )

  function handleFilterChange(
    field,
    value,
  ) {
    setFilters((currentFilters) => ({
      ...currentFilters,
      [field]: value,
    }))
  }

  function handleClearFilters() {
    setFilters({
      ...TEST_PLAN_FILTER_DEFAULTS,
    })
  }

  const emptyMessage =
    plans.length === 0
      ? 'Create a reusable Test Plan to prepare scope, assets, and execution settings before creating a Test Cycle.'
      : 'No Test Plans match the current search and filter criteria.'

  return (
    <div className="dashboard-page test-planning-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>TESTING</span>

            <StatusBadge
              tone={
                plans.length > 0
                  ? 'primary'
                  : 'neutral'
              }
            >
              {plans.length} Plans
            </StatusBadge>
          </div>

          <h2>Test Planning</h2>

          <p>
            Prepare reusable testing scope,
            Test Assets, environments, and
            execution settings.
          </p>
        </div>
      </div>

      <TestPlanMetrics
        metrics={metrics}
      />

      <section className="dashboard-panel test-planning-panel">
        <TestPlanFilters
          filters={filters}
          hasActiveFilters={
            hasActiveFilters
          }
          onChange={
            handleFilterChange
          }
          onClear={
            handleClearFilters
          }
          projects={projects}
          resultCount={
            filteredPlans.length
          }
          totalCount={plans.length}
        />

        <TestPlanTable
          environmentNames={
            environmentNames
          }
          emptyMessage={emptyMessage}
          plans={filteredPlans}
          projectNames={projectNames}
        />
      </section>
    </div>
  )
}

export default TestPlanningPage
