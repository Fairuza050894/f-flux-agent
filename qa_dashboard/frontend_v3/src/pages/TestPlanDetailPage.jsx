import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import StatusBadge from '../components/StatusBadge'
import TestPlanAssetCoverage from '../components/test-planning/TestPlanAssetCoverage'
import TestPlanAssetVersionComparison from '../components/test-planning/TestPlanAssetVersionComparison'
import TestPlanCycleHistory from '../components/test-planning/TestPlanCycleHistory'
import TestPlanDetailOverview from '../components/test-planning/TestPlanDetailOverview'
import TestPlanFormModal from '../components/test-planning/TestPlanFormModal'
import TestPlanReadinessPanel from '../components/test-planning/TestPlanReadinessPanel'
import {
  buildTestPlanDetailModel,
} from '../features/test-planning/testPlanDetailSelectors'
import {
  getTestPlanStatusTone,
} from '../features/test-planning/testPlanFormatters'
import {
  buildTestPlanAssetVersionComparison,
} from '../features/test-planning/testPlanAssetVersionComparison'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestAssetStore } from '../stores/testAssetStore'
import { useTestCycleStore } from '../stores/testCycleStore'
import { useTestPlanStore } from '../stores/testPlanStore'

function TestPlanDetailPage() {
  const navigate = useNavigate()
  const { planId } = useParams()

  const [
    isEditOpen,
    setIsEditOpen,
  ] = useState(false)

  const plans = useTestPlanStore(
    (state) => state.plans,
  )

  const updateTestPlan =
    useTestPlanStore(
      (state) =>
        state.updateTestPlan,
    )

  const backfillTestPlanAssetSnapshots =
    useTestPlanStore(
      (state) =>
        state
          .backfillTestPlanAssetSnapshots,
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

  useEffect(() => {
    backfillTestPlanAssetSnapshots(
      assets,
    )
  }, [
    assets,
    backfillTestPlanAssetSnapshots,
  ])

  const cycles = useTestCycleStore(
    (state) => state.cycles,
  )

  const hasCycleDraft =
    useTestCycleStore(
      (state) => state.hasDraft,
    )

  const startDraftFromPlan =
    useTestCycleStore(
      (state) =>
        state.startDraftFromPlan,
    )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const plan =
    plans.find(
      (candidate) =>
        candidate.id === planId,
    ) ?? null

  const model = useMemo(
    () =>
      buildTestPlanDetailModel({
        assets,
        cycles,
        environments,
        plan,
        projects,
      }),
    [
      assets,
      cycles,
      environments,
      plan,
      projects,
    ],
  )

  const assetVersionComparison =
    useMemo(
      () =>
        buildTestPlanAssetVersionComparison({
          assets,
          plan,
        }),
      [
        assets,
        plan,
      ],
    )

  function handleCreateCycle() {
    if (!model?.readiness.isReady) {
      window.alert(
        [
          'Test Cycle cannot be created from this plan.',
          '',
          ...(
            model?.readiness.issues ?? [
              'The Test Plan is not ready.',
            ]
          ),
        ].join('\n'),
      )

      return
    }

    if (hasCycleDraft) {
      const shouldReplace =
        window.confirm(
          'An existing Test Cycle draft is available. Replace it with this Test Plan configuration?',
        )

      if (!shouldReplace) {
        return
      }
    }

    startDraftFromPlan({
      plan: model.plan,

      selectedAssetIds:
        model.readiness
          .selectedAssetIds,
    })

    navigate(
      '/test-cycles/new',
    )
  }

  function handleArchive() {
    const shouldArchive =
      window.confirm(
        `Archive Test Plan "${plan.name}"?\n\nThe plan will remain stored and can be restored later.`,
      )

    if (!shouldArchive) {
      return
    }

    archiveTestPlan(plan.id)
  }

  function handleRestore() {
    restoreTestPlan(plan.id)
  }

  function handleDelete() {
    const shouldDelete =
      window.confirm(
        `Delete Test Plan "${plan.name}"?\n\nThis action cannot be undone.`,
      )

    if (!shouldDelete) {
      return
    }

    deleteTestPlan(plan.id)
    navigate('/test-planning')
  }

  function handleUpdate(input) {
    updateTestPlan(
      plan.id,
      input,
      assets,
    )

    setIsEditOpen(false)
  }

  if (!plan || !model) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-panel test-plan-detail-not-found">
          <StatusBadge tone="warning">
            Not Found
          </StatusBadge>

          <h2>
            Test Plan not found
          </h2>

          <p>
            The requested Test Plan may have
            been deleted or is no longer
            available.
          </p>

          <button
            className="button button-primary"
            onClick={() =>
              navigate(
                '/test-planning',
              )
            }
            type="button"
          >
            Back to Test Planning
          </button>
        </section>
      </div>
    )
  }

  const isArchived =
    plan.status === 'Archived'

  const createCycleTitle =
    model.readiness.isReady
      ? 'Create a Test Cycle from this plan.'
      : model.readiness.issues.join(' ')

  return (
    <div className="dashboard-page test-plan-detail-page">
      <div className="page-heading-row test-plan-detail-header">
        <div>
          <div className="page-heading-meta">
            <button
              className="test-plan-back-button"
              onClick={() =>
                navigate(
                  '/test-planning',
                )
              }
              type="button"
            >
              TEST PLANNING
            </button>

            <StatusBadge
              tone={getTestPlanStatusTone(
                plan.status,
              )}
            >
              {plan.status}
            </StatusBadge>
          </div>

          <h2>
            {plan.name ||
              'Untitled Test Plan'}
          </h2>

          <p>
            {plan.id}
          </p>
        </div>

        <div className="page-heading-actions test-plan-detail-actions">
          <button
            className="button button-primary"
            disabled={
              !model.readiness.isReady
            }
            onClick={
              handleCreateCycle
            }
            title={
              createCycleTitle
            }
            type="button"
          >
            Create Cycle
          </button>

          <button
            className="button button-secondary"
            disabled={isArchived}
            onClick={() =>
              setIsEditOpen(true)
            }
            title={
              isArchived
                ? 'Restore the plan before editing it.'
                : undefined
            }
            type="button"
          >
            Edit
          </button>

          {isArchived ? (
            <button
              className="button button-secondary"
              onClick={
                handleRestore
              }
              type="button"
            >
              Restore
            </button>
          ) : (
            <button
              className="button button-secondary"
              onClick={
                handleArchive
              }
              type="button"
            >
              Archive
            </button>
          )}

          <button
            className="button test-plan-delete-button"
            onClick={
              handleDelete
            }
            type="button"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="test-plan-detail-layout">
        <div className="test-plan-detail-main">
          <TestPlanDetailOverview
            model={model}
          />

          <TestPlanAssetCoverage
            assetHealth={
              model.assetHealth
            }
          />

          <TestPlanAssetVersionComparison
            comparison={
              assetVersionComparison
            }
          />

          <TestPlanCycleHistory
            cycles={
              model.linkedCycles
            }
          />
        </div>

        <aside className="test-plan-detail-sidebar">
          <TestPlanReadinessPanel
            assetHealth={
              model.assetHealth
            }
            readiness={
              model.readiness
            }
          />
        </aside>
      </div>

      {isEditOpen && (
        <TestPlanFormModal
          assets={assets}
          environments={
            environments
          }
          initialPlan={plan}
          onClose={() =>
            setIsEditOpen(false)
          }
          onSubmit={
            handleUpdate
          }
          projects={projects}
        />
      )}
    </div>
  )
}

export default TestPlanDetailPage
