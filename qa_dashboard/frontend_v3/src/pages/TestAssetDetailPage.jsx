import {
  useMemo,
  useState,
} from 'react'

import {
  useNavigate,
  useParams,
} from 'react-router-dom'

import StatusBadge from '../components/StatusBadge'
import TestAssetDefinition from '../components/test-assets/TestAssetDefinition'
import TestAssetDetailOverview from '../components/test-assets/TestAssetDetailOverview'
import TestAssetFormModal from '../components/test-assets/TestAssetFormModal'
import TestAssetLinkedCycles from '../components/test-assets/TestAssetLinkedCycles'
import TestAssetLinkedPlans from '../components/test-assets/TestAssetLinkedPlans'
import TestAssetVersionHistory from '../components/test-assets/TestAssetVersionHistory'
import TestAssetVersionSnapshot from '../components/test-assets/TestAssetVersionSnapshot'
import {
  buildTestAssetDetailModel,
  getTestAssetVersion,
} from '../features/test-assets/testAssetDetailSelectors'
import {
  getTestAssetReadyTone,
} from '../features/test-assets/testAssetFormatters'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestAssetStore } from '../stores/testAssetStore'
import { useTestCycleStore } from '../stores/testCycleStore'
import { useTestPlanStore } from '../stores/testPlanStore'

function TestAssetDetailPage() {
  const navigate = useNavigate()
  const { assetId } = useParams()

  const [
    isEditOpen,
    setIsEditOpen,
  ] = useState(false)

  const [
    selectedVersionId,
    setSelectedVersionId,
  ] = useState('')

  const assets = useTestAssetStore(
    (state) => state.assets,
  )

  const updateTestAsset =
    useTestAssetStore(
      (state) =>
        state.updateTestAsset,
    )

  const archiveTestAsset =
    useTestAssetStore(
      (state) =>
        state.archiveTestAsset,
    )

  const restoreTestAsset =
    useTestAssetStore(
      (state) =>
        state.restoreTestAsset,
    )

  const deleteTestAsset =
    useTestAssetStore(
      (state) =>
        state.deleteTestAsset,
    )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const plans = useTestPlanStore(
    (state) => state.plans,
  )

  const cycles = useTestCycleStore(
    (state) => state.cycles,
  )

  const asset =
    assets.find(
      (candidate) =>
        candidate.id === assetId,
    ) ?? null

  const environmentNames =
    useMemo(
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

  const model = useMemo(
    () =>
      buildTestAssetDetailModel({
        asset,
        cycles,
        plans,
        projects,
      }),
    [
      asset,
      cycles,
      plans,
      projects,
    ],
  )

  const effectiveVersionId =
    selectedVersionId ||
    model?.asset.currentVersionId ||
    ''

  const selectedVersion =
    useMemo(
      () =>
        getTestAssetVersion(
          model?.asset,
          effectiveVersionId,
        ),
      [
        effectiveVersionId,
        model?.asset,
      ],
    )

  function handleUpdate(input) {
    if (!asset) {
      return
    }

    const {
      changeSummary,
      ...changes
    } = input

    const updatedAsset =
      updateTestAsset(
        asset.id,
        changes,
        {
          changeSummary,
        },
      )

    if (
      updatedAsset
        ?.currentVersionId
    ) {
      setSelectedVersionId(
        updatedAsset
          .currentVersionId,
      )
    }

    setIsEditOpen(false)
  }

  function handleArchive() {
    if (!asset) {
      return
    }

    const shouldArchive =
      window.confirm(
        `Archive Test Asset "${asset.name}"?\n\nThe asset will remain available in history but cannot be selected for a new Test Plan or Test Cycle.`,
      )

    if (!shouldArchive) {
      return
    }

    archiveTestAsset(asset.id)
    setIsEditOpen(false)
  }

  function handleRestore() {
    if (!asset) {
      return
    }

    restoreTestAsset(asset.id)
  }

  function handleDelete() {
    if (!asset || !model) {
      return
    }

    const hasLinkedUsage =
      model.linkedPlanCount > 0 ||
      model.linkedCycleCount > 0

    if (hasLinkedUsage) {
      window.alert(
        `This Test Asset cannot be deleted because it is used by ${model.linkedPlanCount} Test Plan(s) and ${model.linkedCycleCount} Test Cycle(s). Archive the asset instead.`,
      )

      return
    }

    const shouldDelete =
      window.confirm(
        `Delete Test Asset "${asset.name}"?\n\nThis action cannot be undone.`,
      )

    if (!shouldDelete) {
      return
    }

    deleteTestAsset(asset.id)

    navigate('/test-assets')
  }

  if (!asset || !model) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-panel test-asset-detail-not-found">
          <StatusBadge tone="warning">
            Not Found
          </StatusBadge>

          <h2>
            Test Asset not found
          </h2>

          <p>
            The requested Test Asset may have
            been deleted or is no longer
            available.
          </p>

          <button
            className="button button-primary"
            onClick={() =>
              navigate('/test-assets')
            }
            type="button"
          >
            Back to Test Assets
          </button>
        </section>
      </div>
    )
  }

  const isArchived =
    asset.lifecycleStatus ===
    'Archived'

  const hasLinkedUsage =
    model.linkedPlanCount > 0 ||
    model.linkedCycleCount > 0

  return (
    <div className="dashboard-page test-asset-detail-page">
      <div className="page-heading-row test-asset-detail-header">
        <div>
          <div className="page-heading-meta">
            <button
              className="test-asset-back-button"
              onClick={() =>
                navigate('/test-assets')
              }
              type="button"
            >
              TEST ASSETS
            </button>

            <StatusBadge
              tone={
                isArchived
                  ? 'neutral'
                  : getTestAssetReadyTone(
                      asset.executionReady,
                    )
              }
            >
              {isArchived
                ? 'Archived'
                : asset.executionReady
                  ? 'Execution Ready'
                  : 'Not Ready'}
            </StatusBadge>
          </div>

          <h2>
            {asset.name ||
              'Unnamed Test Asset'}
          </h2>

          <p>
            {asset.id}
            {' · '}
            Current version v
            {asset.currentVersionNumber}
          </p>
        </div>

        <div className="page-heading-actions test-asset-detail-actions">
          <button
            className="button button-secondary"
            onClick={() =>
              setSelectedVersionId(
                asset.currentVersionId,
              )
            }
            type="button"
          >
            View Current
          </button>

          <button
            className="button button-primary"
            disabled={isArchived}
            onClick={() =>
              setIsEditOpen(true)
            }
            title={
              isArchived
                ? 'Restore the asset before editing it.'
                : undefined
            }
            type="button"
          >
            Edit Asset
          </button>

          {isArchived ? (
            <button
              className="button button-secondary"
              onClick={handleRestore}
              type="button"
            >
              Restore
            </button>
          ) : (
            <button
              className="button button-secondary"
              onClick={handleArchive}
              type="button"
            >
              Archive
            </button>
          )}

          <button
            className="button button-danger"
            disabled={hasLinkedUsage}
            onClick={handleDelete}
            title={
              hasLinkedUsage
                ? 'Unlink this asset from all Test Plans and Test Cycles before deleting it.'
                : 'Permanently delete this Test Asset.'
            }
            type="button"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="test-asset-detail-layout">
        <div className="test-asset-detail-main">
          <TestAssetDetailOverview
            model={model}
          />

          <TestAssetDefinition
            asset={model.asset}
          />

          <TestAssetVersionHistory
            currentVersionId={
              model.asset
                .currentVersionId
            }
            onSelectVersion={
              setSelectedVersionId
            }
            selectedVersionId={
              effectiveVersionId
            }
            versions={model.versions}
          />

          <TestAssetLinkedPlans
            plans={model.linkedPlans}
          />

          <TestAssetLinkedCycles
            cycles={model.linkedCycles}
            environmentNames={
              environmentNames
            }
          />
        </div>

        <aside className="test-asset-detail-sidebar">
          <TestAssetVersionSnapshot
            version={selectedVersion}
          />
        </aside>
      </div>

      {isEditOpen && (
        <TestAssetFormModal
          initialAsset={asset}
          onClose={() =>
            setIsEditOpen(false)
          }
          onSubmit={handleUpdate}
          projects={projects}
        />
      )}
    </div>
  )
}

export default TestAssetDetailPage
