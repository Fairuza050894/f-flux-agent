import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../components/StatusBadge'
import TestPlanFilters from '../components/test-planning/TestPlanFilters'
import TestPlanFormModal from '../components/test-planning/TestPlanFormModal'
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
import { useTestAssetStore } from '../stores/testAssetStore'
import { useTestPlanStore } from '../stores/testPlanStore'

function TestPlanningPage() {
  const [filters, setFilters] =
    useState(() => ({
      ...TEST_PLAN_FILTER_DEFAULTS,
    }))

  const [
    isFormOpen,
    setIsFormOpen,
  ] = useState(false)

  const [
    editingPlan,
    setEditingPlan,
  ] = useState(null)

  const plans = useTestPlanStore(
    (state) => state.plans,
  )

  const addTestPlan =
    useTestPlanStore(
      (state) =>
        state.addTestPlan,
    )

  const updateTestPlan =
    useTestPlanStore(
      (state) =>
        state.updateTestPlan,
    )

  const archiveTestPlan =
    useTestPlanStore(
      (state) =>
        state.archiveTestPlan,
    )

  const restoreTestPlan =
    useTestPlanStore(
      (state) =>
        state.restoreTestPlan,
    )

  const deleteTestPlan =
    useTestPlanStore(
      (state) =>
        state.deleteTestPlan,
    )

  const assets = useTestAssetStore(
    (state) => state.assets,
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

  function handleOpenCreate() {
    setEditingPlan(null)
    setIsFormOpen(true)
  }

  function handleOpenEdit(plan) {
    setEditingPlan(plan)
    setIsFormOpen(true)
  }

  function handleCloseForm() {
    setEditingPlan(null)
    setIsFormOpen(false)
  }

  function handleArchivePlan(plan) {
    const shouldArchive =
      window.confirm(
        `Archive Test Plan "${plan.name}"?\n\nThe plan will remain stored and can be restored later.`,
      )

    if (!shouldArchive) {
      return
    }

    archiveTestPlan(plan.id)

    if (editingPlan?.id === plan.id) {
      handleCloseForm()
    }
  }

  function handleRestorePlan(plan) {
    restoreTestPlan(plan.id)
  }

  function handleDeletePlan(plan) {
    const shouldDelete =
      window.confirm(
        `Delete Test Plan "${plan.name}"?\n\nThis action cannot be undone.`,
      )

    if (!shouldDelete) {
      return
    }

    deleteTestPlan(plan.id)

    if (editingPlan?.id === plan.id) {
      handleCloseForm()
    }
  }

  function handleSubmitPlan(input) {
    if (editingPlan?.id) {
      updateTestPlan(
        editingPlan.id,
        input,
      )
    } else {
      addTestPlan(input)

      setFilters({
        ...TEST_PLAN_FILTER_DEFAULTS,
      })
    }

    handleCloseForm()
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

        <div className="page-heading-actions">
          <button
            className="button button-primary"
            disabled={
              projects.length === 0
            }
            onClick={
              handleOpenCreate
            }
            title={
              projects.length === 0
                ? 'Create a Project before creating a Test Plan.'
                : undefined
            }
            type="button"
          >
            Create Test Plan
          </button>
        </div>
      </div>

      {projects.length === 0 && (
        <div
          className="test-plan-project-warning"
          role="status"
        >
          <strong>
            Project required
          </strong>

          <p>
            Create at least one Project before
            adding a Test Plan.
          </p>
        </div>
      )}

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
          onArchive={
            handleArchivePlan
          }
          onDelete={
            handleDeletePlan
          }
          onEdit={handleOpenEdit}
          onRestore={
            handleRestorePlan
          }
          plans={filteredPlans}
          projectNames={projectNames}
        />
      </section>

      {isFormOpen && (
        <TestPlanFormModal
          assets={assets}
          environments={
            environments
          }
          initialPlan={
            editingPlan
          }
          onClose={
            handleCloseForm
          }
          onSubmit={
            handleSubmitPlan
          }
          projects={projects}
        />
      )}
    </div>
  )
}

export default TestPlanningPage
