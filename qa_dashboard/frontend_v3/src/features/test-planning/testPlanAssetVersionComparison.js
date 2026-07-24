import {
  normalizeVersionedTestAsset,
} from '../test-assets/testAssetVersioning'
import {
  normalizeTestPlanAssetSnapshots,
} from './testPlanAssetSnapshots'

const STATUS_DEFINITIONS = {
  current: {
    label: 'Current',
    tone: 'success',
  },

  outdated: {
    label: 'Outdated',
    tone: 'warning',
  },

  archived: {
    label: 'Archived',
    tone: 'neutral',
  },

  missing: {
    label: 'Missing',
    tone: 'danger',
  },

  unsnapshotted: {
    label: 'No Snapshot',
    tone: 'danger',
  },
}

function normalizeText(value) {
  return String(value ?? '').trim()
}

function normalizeSelectedAssetIds(
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

function getComparisonStatus({
  liveAsset,
  snapshotRecord,
}) {
  if (!snapshotRecord) {
    return {
      key: 'unsnapshotted',
      reason:
        'The Test Plan references this asset but does not contain a captured version.',
    }
  }

  if (!liveAsset) {
    return {
      key: 'missing',
      reason:
        'The captured Test Asset is no longer available in the live catalog.',
    }
  }

  if (
    liveAsset.lifecycleStatus ===
    'Archived'
  ) {
    return {
      key: 'archived',
      reason:
        'The Test Asset still exists but is currently archived.',
    }
  }

  if (
    snapshotRecord.versionId !==
    liveAsset.currentVersionId
  ) {
    return {
      key: 'outdated',
      reason:
        `The plan captured version ${snapshotRecord.versionNumber}, while the live asset is version ${liveAsset.currentVersionNumber}.`,
    }
  }

  return {
    key: 'current',
    reason:
      'The captured version matches the current live Test Asset version.',
  }
}

export function buildTestPlanAssetVersionComparison({
  assets = [],
  plan,
} = {}) {
  const selectedAssetIds =
    normalizeSelectedAssetIds(
      plan?.selectedAssetIds,
    )

  const snapshots =
    normalizeTestPlanAssetSnapshots(
      plan?.selectedAssetSnapshots,
    )

  const snapshotByAssetId =
    new Map(
      snapshots.map((record) => [
        record.assetId,
        record,
      ]),
    )

  const liveAssetById =
    new Map(
      assets
        .map(
          normalizeVersionedTestAsset,
        )
        .map((asset) => [
          asset.id,
          asset,
        ]),
    )

  const rows =
    selectedAssetIds.map(
      (assetId) => {
        const snapshotRecord =
          snapshotByAssetId.get(
            assetId,
          ) ?? null

        const liveAsset =
          liveAssetById.get(
            assetId,
          ) ?? null

        const comparison =
          getComparisonStatus({
            liveAsset,
            snapshotRecord,
          })

        const status =
          STATUS_DEFINITIONS[
            comparison.key
          ]

        const snapshot =
          snapshotRecord
            ?.snapshot ?? null

        return {
          id: assetId,
          assetId,

          name:
            snapshot?.name ||
            liveAsset?.name ||
            'Unavailable Test Asset',

          typeLabel:
            snapshot?.typeLabel ||
            liveAsset?.typeLabel ||
            'Unknown',

          module:
            snapshot?.module ||
            liveAsset?.module ||
            'Not specified',

          feature:
            snapshot?.feature ||
            liveAsset?.feature ||
            'Not specified',

          capturedVersionId:
            snapshotRecord
              ?.versionId ?? '',

          capturedVersionNumber:
            snapshotRecord
              ?.versionNumber ?? null,

          capturedAt:
            snapshotRecord
              ?.capturedAt ?? null,

          capturedChangeSummary:
            snapshotRecord
              ?.changeSummary ?? '',

          liveVersionId:
            liveAsset
              ?.currentVersionId ?? '',

          liveVersionNumber:
            liveAsset
              ?.currentVersionNumber ??
            null,

          lifecycleStatus:
            liveAsset
              ?.lifecycleStatus ??
            'Missing',

          statusKey:
            comparison.key,

          statusLabel:
            status.label,

          statusTone:
            status.tone,

          reason:
            comparison.reason,

          hasLiveAsset:
            Boolean(liveAsset),

          hasSnapshot:
            Boolean(
              snapshotRecord,
            ),
        }
      },
    )

  const countByStatus =
    rows.reduce(
      (counts, row) => ({
        ...counts,

        [row.statusKey]:
          (
            counts[
              row.statusKey
            ] ?? 0
          ) + 1,
      }),
      {},
    )

  const blockingCount =
    (
      countByStatus.archived ??
      0
    ) +
    (
      countByStatus.missing ??
      0
    ) +
    (
      countByStatus
        .unsnapshotted ?? 0
    )

  return {
    total:
      rows.length,

    current:
      countByStatus.current ?? 0,

    outdated:
      countByStatus.outdated ?? 0,

    archived:
      countByStatus.archived ?? 0,

    missing:
      countByStatus.missing ?? 0,

    unsnapshotted:
      countByStatus
        .unsnapshotted ?? 0,

    blockingCount,

    attentionCount:
      blockingCount +
      (
        countByStatus.outdated ??
        0
      ),

    isComplete:
      rows.length > 0 &&
      (
        countByStatus
          .unsnapshotted ?? 0
      ) === 0,

    rows,
  }
}
