import {
  createTestAssetSnapshot,
  normalizeVersionedTestAsset,
} from '../test-assets/testAssetVersioning'

function normalizeText(value) {
  return String(value ?? '').trim()
}

function normalizeVersionNumber(
  value,
) {
  const parsedValue =
    Number.parseInt(
      value,
      10,
    )

  return (
    Number.isInteger(parsedValue) &&
    parsedValue > 0
      ? parsedValue
      : 1
  )
}

function normalizeAssetIds(
  assetIds,
) {
  if (!Array.isArray(assetIds)) {
    return []
  }

  return Array.from(
    new Set(
      assetIds
        .map(normalizeText)
        .filter(Boolean),
    ),
  )
}

export function normalizeTestPlanAssetSnapshot(
  record,
) {
  if (
    !record ||
    typeof record !== 'object'
  ) {
    return null
  }

  const rawSnapshot =
    record.snapshot &&
    typeof record.snapshot ===
      'object'
      ? record.snapshot
      : {}

  const assetId =
    normalizeText(
      record.assetId ??
      rawSnapshot.assetId ??
      rawSnapshot.id,
    )

  if (!assetId) {
    return null
  }

  return {
    assetId,

    versionId:
      normalizeText(
        record.versionId,
      ),

    versionNumber:
      normalizeVersionNumber(
        record.versionNumber,
      ),

    capturedAt:
      normalizeText(
        record.capturedAt,
      ) || null,

    changeSummary:
      normalizeText(
        record.changeSummary,
      ),

    snapshot:
      createTestAssetSnapshot(
        rawSnapshot,
      ),
  }
}

export function normalizeTestPlanAssetSnapshots(
  records,
) {
  if (!Array.isArray(records)) {
    return []
  }

  const normalizedRecords = []
  const seenAssetIds = new Set()

  records.forEach((record) => {
    const normalizedRecord =
      normalizeTestPlanAssetSnapshot(
        record,
      )

    if (
      !normalizedRecord ||
      seenAssetIds.has(
        normalizedRecord.assetId,
      )
    ) {
      return
    }

    seenAssetIds.add(
      normalizedRecord.assetId,
    )

    normalizedRecords.push(
      normalizedRecord,
    )
  })

  return normalizedRecords
}

export function captureTestPlanAssetSnapshot(
  asset,
  {
    capturedAt =
      new Date().toISOString(),
  } = {},
) {
  if (!asset) {
    return null
  }

  const normalizedAsset =
    normalizeVersionedTestAsset(
      asset,
    )

  const currentVersion =
    normalizedAsset.versions.find(
      (version) =>
        version.versionId ===
        normalizedAsset.currentVersionId,
    ) ??
    normalizedAsset.versions[0] ??
    null

  if (!currentVersion) {
    return null
  }

  return normalizeTestPlanAssetSnapshot({
    assetId:
      normalizedAsset.id,

    versionId:
      currentVersion.versionId,

    versionNumber:
      currentVersion.versionNumber,

    capturedAt,

    changeSummary:
      currentVersion.changeSummary,

    snapshot:
      currentVersion.snapshot,
  })
}

export function captureTestPlanAssetSnapshots({
  assets = [],
  capturedAt =
    new Date().toISOString(),
  selectedAssetIds = [],
} = {}) {
  const assetById =
    new Map(
      assets.map((asset) => [
        normalizeText(asset?.id),
        asset,
      ]),
    )

  return normalizeAssetIds(
    selectedAssetIds,
  )
    .map((assetId) =>
      captureTestPlanAssetSnapshot(
        assetById.get(assetId),
        {
          capturedAt,
        },
      ),
    )
    .filter(Boolean)
}

export function mergeTestPlanAssetSnapshots({
  assets = [],
  capturedAt =
    new Date().toISOString(),
  existingSnapshots = [],
  refreshExisting = false,
  selectedAssetIds = [],
} = {}) {
  const normalizedAssetIds =
    normalizeAssetIds(
      selectedAssetIds,
    )

  const existingByAssetId =
    new Map(
      normalizeTestPlanAssetSnapshots(
        existingSnapshots,
      ).map((record) => [
        record.assetId,
        record,
      ]),
    )

  const capturedByAssetId =
    new Map(
      captureTestPlanAssetSnapshots({
        assets,
        capturedAt,
        selectedAssetIds:
          normalizedAssetIds,
      }).map((record) => [
        record.assetId,
        record,
      ]),
    )

  return normalizedAssetIds
    .map((assetId) => {
      const existingRecord =
        existingByAssetId.get(
          assetId,
        )

      const capturedRecord =
        capturedByAssetId.get(
          assetId,
        )

      return refreshExisting
        ? capturedRecord ??
            existingRecord ??
            null
        : existingRecord ??
            capturedRecord ??
            null
    })
    .filter(Boolean)
}

export function getTestPlanAssetSnapshot(
  plan,
  assetId,
) {
  const normalizedAssetId =
    normalizeText(assetId)

  return (
    normalizeTestPlanAssetSnapshots(
      plan?.selectedAssetSnapshots,
    ).find(
      (record) =>
        record.assetId ===
        normalizedAssetId,
    ) ?? null
  )
}

export function buildTestPlanSnapshotCoverage(
  plan,
) {
  const selectedAssetIds =
    normalizeAssetIds(
      plan?.selectedAssetIds,
    )

  const snapshotAssetIds =
    new Set(
      normalizeTestPlanAssetSnapshots(
        plan?.selectedAssetSnapshots,
      ).map(
        (record) =>
          record.assetId,
      ),
    )

  const missingAssetIds =
    selectedAssetIds.filter(
      (assetId) =>
        !snapshotAssetIds.has(
          assetId,
        ),
    )

  return {
    selectedAssetCount:
      selectedAssetIds.length,

    snapshotCount:
      snapshotAssetIds.size,

    missingAssetIds,

    isComplete:
      missingAssetIds.length === 0,
  }
}
