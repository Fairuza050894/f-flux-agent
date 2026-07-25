import {
  captureTestPlanAssetSnapshots,
} from '../test-planning/testPlanAssetSnapshots'

function normalizeAssetIds(
  values,
) {
  if (!Array.isArray(values)) {
    return []
  }

  return Array.from(
    new Set(
      values
        .map(
          (value) =>
            String(value ?? '').trim(),
        )
        .filter(Boolean),
    ),
  )
}

function createDuplicateName(
  sourceName,
  cycles,
) {
  const normalizedSourceName =
    String(
      sourceName ??
      'Untitled Test Cycle',
    ).trim() ||
    'Untitled Test Cycle'

  const baseName =
    `Copy of ${normalizedSourceName}`

  const existingNames =
    new Set(
      (
        Array.isArray(cycles)
          ? cycles
          : []
      ).map(
        (cycle) =>
          String(
            cycle?.name ?? '',
          )
            .trim()
            .toLowerCase(),
      ),
    )

  if (
    !existingNames.has(
      baseName.toLowerCase(),
    )
  ) {
    return baseName
  }

  let copyNumber = 2

  while (
    existingNames.has(
      `${baseName} (${copyNumber})`
        .toLowerCase(),
    )
  ) {
    copyNumber += 1
  }

  return `${baseName} (${copyNumber})`
}

export function buildDuplicatedTestCycle({
  assets = [],
  existingCycles = [],
  id,
  sourceCycle,
  timestamp,
} = {}) {
  if (
    !sourceCycle ||
    !id ||
    !timestamp
  ) {
    return null
  }

  const selectedAssetIds =
    normalizeAssetIds(
      sourceCycle.selectedAssetIds,
    )

  const selectedAssetSnapshots =
    captureTestPlanAssetSnapshots({
      assets,
      capturedAt: timestamp,
      selectedAssetIds,
    })

  if (
    selectedAssetIds.length > 0 &&
    selectedAssetSnapshots.length !==
      selectedAssetIds.length
  ) {
    return null
  }

  return {
    id,

    name:
      createDuplicateName(
        sourceCycle.name,
        existingCycles,
      ),

    projectId:
      sourceCycle.projectId ?? '',

    environmentId:
      sourceCycle.environmentId ?? '',

    cycleType:
      sourceCycle.cycleType ??
      'Feature Cycle',

    releaseVersion:
      sourceCycle.releaseVersion ?? '',

    module:
      sourceCycle.module ?? '',

    feature:
      sourceCycle.feature ?? '',

    changeType:
      sourceCycle.changeType ??
      'New Feature',

    reference:
      sourceCycle.reference ?? '',

    description:
      sourceCycle.description ?? '',

    sourcePlanId:
      sourceCycle.sourcePlanId ?? '',

    scope: {
      ...(sourceCycle.scope ?? {}),
    },

    selectedAssetIds,

    selectedAssetSnapshots,

    executions: [],

    executionError: '',

    executionSettings: {
      ...(sourceCycle
        .executionSettings ?? {}),
    },

    status: 'Ready',

    progress: 0,

    triggerSource: 'Duplicate',

    duplicatedFromCycleId:
      sourceCycle.id,

    duplicatedFromCycleName:
      sourceCycle.name,

    createdAt: timestamp,

    updatedAt: timestamp,
  }
}
