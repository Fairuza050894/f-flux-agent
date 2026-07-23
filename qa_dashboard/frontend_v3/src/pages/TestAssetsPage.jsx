import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../components/StatusBadge'
import TestAssetFilters from '../components/test-assets/TestAssetFilters'
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

  const assets = useTestAssetStore(
    (state) => state.assets,
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
      </div>

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
    </div>
  )
}

export default TestAssetsPage
