import {
  normalizeVersionedTestAsset,
} from './testAssetVersioning'

function sortVersions(
  versions,
) {
  return [...versions].sort(
    (
      firstVersion,
      secondVersion,
    ) =>
      secondVersion.versionNumber -
      firstVersion.versionNumber,
  )
}

export function selectPlansUsingTestAsset({
  assetId,
  plans = [],
} = {}) {
  if (!assetId) {
    return []
  }

  return plans.filter(
    (plan) =>
      Array.isArray(
        plan.selectedAssetIds,
      ) &&
      plan.selectedAssetIds.includes(
        assetId,
      ),
  )
}

export function selectCyclesUsingTestAsset({
  assetId,
  cycles = [],
} = {}) {
  if (!assetId) {
    return []
  }

  return cycles.filter(
    (cycle) =>
      Array.isArray(
        cycle.selectedAssetIds,
      ) &&
      cycle.selectedAssetIds.includes(
        assetId,
      ),
  )
}

export function getTestAssetVersion(
  asset,
  versionId,
) {
  if (!asset) {
    return null
  }

  const normalizedAsset =
    normalizeVersionedTestAsset(
      asset,
    )

  if (!versionId) {
    return (
      normalizedAsset.versions[0] ??
      null
    )
  }

  return (
    normalizedAsset.versions.find(
      (version) =>
        version.versionId ===
        versionId,
    ) ??
    normalizedAsset.versions[0] ??
    null
  )
}

export function buildTestAssetDetailModel({
  asset,
  cycles = [],
  plans = [],
  projects = [],
} = {}) {
  if (!asset) {
    return null
  }

  const normalizedAsset =
    normalizeVersionedTestAsset(
      asset,
    )

  const project =
    projects.find(
      (candidate) =>
        candidate.id ===
        normalizedAsset.projectId,
    ) ?? null

  const versions =
    sortVersions(
      normalizedAsset.versions,
    )

  const linkedPlans =
    selectPlansUsingTestAsset({
      assetId:
        normalizedAsset.id,

      plans,
    })

  const linkedCycles =
    selectCyclesUsingTestAsset({
      assetId:
        normalizedAsset.id,

      cycles,
    })

  return {
    asset: {
      ...normalizedAsset,
      versions,
    },

    project,

    versions,

    currentVersion:
      versions.find(
        (version) =>
          version.versionId ===
          normalizedAsset
            .currentVersionId,
      ) ??
      versions[0] ??
      null,

    linkedPlanCount:
      linkedPlans.length,

    linkedCycleCount:
      linkedCycles.length,

    linkedPlans,

    linkedCycles,
  }
}
