import {
  normalizeTestPlanAssetSnapshots,
} from '../test-planning/testPlanAssetSnapshots'

function isObjectRecord(
  value,
) {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value)
  )
}

export function getExecutionRequestSnapshot(
  execution,
) {
  const snapshot =
    execution?.requestSnapshot ??
    execution?.request_snapshot ??
    {}

  return isObjectRecord(snapshot)
    ? snapshot
    : {}
}

export function getExecutionAssetSnapshots(
  execution,
) {
  const requestSnapshot =
    getExecutionRequestSnapshot(
      execution,
    )

  return normalizeTestPlanAssetSnapshots(
    requestSnapshot
      .selected_asset_snapshots ??
    requestSnapshot
      .selectedAssetSnapshots,
  )
}

export function getExecutionSelectedAssetIds(
  execution,
) {
  const requestSnapshot =
    getExecutionRequestSnapshot(
      execution,
    )

  const values =
    requestSnapshot
      .selected_asset_ids ??
    requestSnapshot
      .selectedAssetIds ??
    []

  if (!Array.isArray(values)) {
    return []
  }

  return Array.from(
    new Set(
      values
        .map((value) =>
          String(value ?? '').trim(),
        )
        .filter(Boolean),
    ),
  )
}

export function executionContainsAssetVersion(
  execution,
  snapshotRecord,
) {
  if (!snapshotRecord) {
    return false
  }

  return getExecutionAssetSnapshots(
    execution,
  ).some(
    (candidate) =>
      candidate.assetId ===
        snapshotRecord.assetId &&
      candidate.versionId ===
        snapshotRecord.versionId,
  )
}

export function buildExecutionSnapshotCoverage({
  cycleSnapshots = [],
  execution,
} = {}) {
  const expectedSnapshots =
    normalizeTestPlanAssetSnapshots(
      cycleSnapshots,
    )

  const executionSnapshots =
    getExecutionAssetSnapshots(
      execution,
    )

  const executionByAssetId =
    new Map(
      executionSnapshots.map(
        (record) => [
          record.assetId,
          record,
        ],
      ),
    )

  const missingAssetIds = []
  const mismatchedAssetIds = []

  expectedSnapshots.forEach(
    (expected) => {
      const actual =
        executionByAssetId.get(
          expected.assetId,
        )

      if (!actual) {
        missingAssetIds.push(
          expected.assetId,
        )
        return
      }

      if (
        actual.versionId !==
        expected.versionId
      ) {
        mismatchedAssetIds.push(
          expected.assetId,
        )
      }
    },
  )

  return {
    expectedCount:
      expectedSnapshots.length,

    executionSnapshotCount:
      executionSnapshots.length,

    missingAssetIds,

    mismatchedAssetIds,

    isComplete:
      expectedSnapshots.length > 0 &&
      missingAssetIds.length === 0 &&
      mismatchedAssetIds.length === 0,
  }
}
