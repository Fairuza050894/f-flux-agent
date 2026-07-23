import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../components/StatusBadge'
import TestAssetFilters from '../components/test-assets/TestAssetFilters'
import TestAssetFormModal from '../components/test-assets/TestAssetFormModal'
import TestAssetMetrics from '../components/test-assets/TestAssetMetrics'
import TestAssetTable from '../components/test-assets/TestAssetTable'
import {
  TEST_ASSET_FILTER_DEFAULTS,
} from '../features/test-assets/testAssetConstants'
import {
  buildTestAssetMetrics,
  filterTestAssets,
} from '../features/test-assets/testAssetSelectors'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestAssetStore } from '../stores/testAssetStore'

function TestAssetsPage() {
  const [filters, setFilters] =
    useState(() => ({
      ...TEST_ASSET_FILTER_DEFAULTS,
    }))

  const [
    isCreateModalOpen,
    setIsCreateModalOpen,
  ] = useState(false)

  const assets = useTestAssetStore(
    (state) => state.assets,
  )

  const addTestAsset =
    useTestAssetStore(
      (state) =>
        state.addTestAsset,
    )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const metrics = useMemo(
    () =>
      buildTestAssetMetrics(
        assets,
      ),
    [assets],
  )

  const filteredAssets = useMemo(
    () =>
      filterTestAssets({
        assets,
        filters,
      }),
    [
      assets,
      filters,
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

  const hasActiveFilters =
    Object.entries(
      TEST_ASSET_FILTER_DEFAULTS,
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
      ...TEST_ASSET_FILTER_DEFAULTS,
    })
  }

  function handleCreateAsset(
    input,
  ) {
    addTestAsset(input)

    setFilters({
      ...TEST_ASSET_FILTER_DEFAULTS,
    })

    setIsCreateModalOpen(false)
  }

  const emptyMessage =
    assets.length === 0
      ? 'Create a persistent Test Asset to make it available for Test Cycle selection.'
      : 'No Test Assets match the current search and filter criteria.'

  return (
    <div className="dashboard-page test-assets-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>TESTING</span>

            <StatusBadge
              tone={
                assets.length > 0
                  ? 'primary'
                  : 'neutral'
              }
            >
              {assets.length} Assets
            </StatusBadge>
          </div>

          <h2>Test Assets</h2>

          <p>
            Manage reusable UI, API, unit, E2E,
            and regression test definitions.
          </p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-primary"
            disabled={
              projects.length === 0
            }
            onClick={() =>
              setIsCreateModalOpen(true)
            }
            title={
              projects.length === 0
                ? 'Create a Project before creating a Test Asset.'
                : undefined
            }
            type="button"
          >
            Create Test Asset
          </button>
        </div>
      </div>

      {projects.length === 0 && (
        <div
          className="test-asset-project-warning"
          role="status"
        >
          <strong>
            Project required
          </strong>

          <p>
            Create at least one Project before
            adding a Test Asset.
          </p>
        </div>
      )}

      <TestAssetMetrics
        metrics={metrics}
      />

      <section className="dashboard-panel test-assets-panel">
        <TestAssetFilters
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
            filteredAssets.length
          }
          totalCount={assets.length}
        />

        <TestAssetTable
          assets={filteredAssets}
          emptyMessage={emptyMessage}
          projectNames={projectNames}
        />
      </section>

      {isCreateModalOpen && (
        <TestAssetFormModal
          onClose={() =>
            setIsCreateModalOpen(
              false,
            )
          }
          onSubmit={
            handleCreateAsset
          }
          projects={projects}
        />
      )}
    </div>
  )
}

export default TestAssetsPage
