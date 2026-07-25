import {
  normalizeTestPlanAssetSnapshots,
} from '../test-planning/testPlanAssetSnapshots'
import {
  buildTestPlanAssetVersionComparison,
} from '../test-planning/testPlanAssetVersionComparison'

function getCycleComparisonReason(
  row,
) {
  switch (row.statusKey) {
    case 'unsnapshotted':
      return (
        'This Test Cycle references the asset ID, ' +
        'but no captured definition is available.'
      )

    case 'missing':
      return (
        'The captured Test Asset remains available ' +
        'in this cycle, but the live catalog record ' +
        'can no longer be found.'
      )

    case 'archived':
      return (
        'The captured definition remains immutable, ' +
        'but the live Test Asset is currently archived.'
      )

    case 'outdated':
      return (
        `This cycle captured version ${
          row.capturedVersionNumber ??
          'unknown'
        }, while the live Test Asset is version ${
          row.liveVersionNumber ??
          'unknown'
        }.`
      )

    default:
      return (
        'The captured definition matches the current ' +
        'live Test Asset version.'
      )
  }
}

function getSnapshotValue(
  snapshot,
  field,
  fallback = 'Not specified',
) {
  const value = snapshot?.[field]

  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return fallback
  }

  return value
}

export function buildCycleAssetVersionComparison({
  assets = [],
  cycle,
} = {}) {
  const baseComparison =
    buildTestPlanAssetVersionComparison({
      assets,
      plan: cycle,
    })

  const snapshotByAssetId =
    new Map(
      normalizeTestPlanAssetSnapshots(
        cycle?.selectedAssetSnapshots,
      ).map((record) => [
        record.assetId,
        record,
      ]),
    )

  const sourceLabel =
    cycle?.sourcePlanId
      ? 'Test Plan'
      : 'Manual'

  const rows =
    baseComparison.rows.map((row) => {
      const snapshotRecord =
        snapshotByAssetId.get(
          row.assetId,
        ) ?? null

      const snapshot =
        snapshotRecord
          ?.snapshot ?? null

      return {
        ...row,

        reason:
          getCycleComparisonReason(
            row,
          ),

        sourceLabel,

        sourcePlanId:
          cycle?.sourcePlanId ?? '',

        snapshot,

        description:
          getSnapshotValue(
            snapshot,
            'description',
            'No captured description.',
          ),

        preconditions:
          getSnapshotValue(
            snapshot,
            'preconditions',
            'No captured preconditions.',
          ),

        steps:
          Array.isArray(
            snapshot?.steps,
          )
            ? snapshot.steps
            : [],

        expectedResult:
          getSnapshotValue(
            snapshot,
            'expectedResult',
            'No captured expected result.',
          ),

        priority:
          getSnapshotValue(
            snapshot,
            'priority',
          ),

        automationStatus:
          getSnapshotValue(
            snapshot,
            'automationStatus',
          ),

        executionReady:
          Boolean(
            snapshot?.executionReady,
          ),
      }
    })

  return {
    ...baseComparison,

    captured:
      rows.filter(
        (row) => row.hasSnapshot,
      ).length,

    rows,
  }
}
