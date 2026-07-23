import {
  normalizeTestAsset,
} from './testAssetSelectors'
import {
  TEST_ASSET_DEFAULT_UPDATE_SUMMARY,
  TEST_ASSET_INITIAL_CHANGE_SUMMARY,
  TEST_ASSET_LIFECYCLE_STATUSES,
  TEST_ASSET_MIGRATION_CHANGE_SUMMARY,
} from './testAssetVersionConstants'

const FALLBACK_TIMESTAMP =
  '1970-01-01T00:00:00.000Z'

function normalizeString(value) {
  return String(value ?? '').trim()
}

function normalizeVersionNumber(
  value,
  fallbackValue = 1,
) {
  const parsedValue =
    Number.parseInt(
      value,
      10,
    )

  if (
    Number.isInteger(parsedValue) &&
    parsedValue > 0
  ) {
    return parsedValue
  }

  return fallbackValue
}

function normalizeSteps(steps) {
  if (!Array.isArray(steps)) {
    return []
  }

  return steps
    .map((step) =>
      normalizeString(step),
    )
    .filter(Boolean)
}

function normalizeLifecycleStatus(
  status,
) {
  return TEST_ASSET_LIFECYCLE_STATUSES
    .includes(status)
    ? status
    : 'Active'
}

function getAssetTimestamp(asset) {
  return (
    normalizeString(
      asset?.createdAt,
    ) ||
    normalizeString(
      asset?.updatedAt,
    ) ||
    FALLBACK_TIMESTAMP
  )
}

function getLatestVersionNumber(
  versions,
) {
  return versions.reduce(
    (latestNumber, version) =>
      Math.max(
        latestNumber,
        version.versionNumber,
      ),
    0,
  )
}

function removeVersionControlFields(
  changes,
) {
  const safeChanges = {
    ...(changes ?? {}),
  }

  delete safeChanges.id
  delete safeChanges.createdAt
  delete safeChanges.updatedAt
  delete safeChanges.versions
  delete safeChanges.currentVersionId
  delete safeChanges.currentVersionNumber
  delete safeChanges.lifecycleStatus
  delete safeChanges.changeSummary

  return safeChanges
}

export function createTestAssetVersionId(
  assetId,
  versionNumber,
) {
  const normalizedAssetId =
    normalizeString(assetId) ||
    'UNKNOWN'

  return [
    'TAV',
    normalizedAssetId,
    `V${versionNumber}`,
  ].join('-')
}

export function createTestAssetSnapshot(
  asset,
) {
  const normalizedAsset =
    normalizeTestAsset(asset)

  return {
    projectId:
      normalizedAsset.projectId,

    name:
      normalizedAsset.name,

    type:
      normalizedAsset.type,

    typeLabel:
      normalizedAsset.typeLabel,

    module:
      normalizedAsset.module,

    feature:
      normalizedAsset.feature,

    priority:
      normalizedAsset.priority,

    automationStatus:
      normalizedAsset.automationStatus,

    recommended:
      normalizedAsset.recommended,

    executionReady:
      normalizedAsset.executionReady,

    description:
      normalizedAsset.description,

    preconditions:
      normalizedAsset.preconditions,

    steps:
      normalizeSteps(
        normalizedAsset.steps,
      ),

    expectedResult:
      normalizedAsset.expectedResult,
  }
}

export function normalizeTestAssetVersion(
  version,
  asset,
  fallbackVersionNumber = 1,
) {
  const normalizedAsset =
    normalizeTestAsset(asset)

  const versionNumber =
    normalizeVersionNumber(
      version?.versionNumber,
      fallbackVersionNumber,
    )

  const createdAt =
    normalizeString(
      version?.createdAt,
    ) ||
    getAssetTimestamp(
      normalizedAsset,
    )

  const snapshotSource =
    version?.snapshot &&
    typeof version.snapshot ===
      'object'
      ? {
          ...normalizedAsset,
          ...version.snapshot,
        }
      : normalizedAsset

  const fallbackSummary =
    versionNumber === 1
      ? TEST_ASSET_INITIAL_CHANGE_SUMMARY
      : TEST_ASSET_DEFAULT_UPDATE_SUMMARY

  return {
    versionId:
      normalizeString(
        version?.versionId ??
          version?.id,
      ) ||
      createTestAssetVersionId(
        normalizedAsset.id,
        versionNumber,
      ),

    assetId:
      normalizedAsset.id,

    versionNumber,

    changeSummary:
      normalizeString(
        version?.changeSummary,
      ) ||
      fallbackSummary,

    snapshot:
      createTestAssetSnapshot(
        snapshotSource,
      ),

    createdAt,
  }
}

export function normalizeVersionedTestAsset(
  asset,
  {
    fallbackChangeSummary =
      TEST_ASSET_INITIAL_CHANGE_SUMMARY,
  } = {},
) {
  const normalizedAsset =
    normalizeTestAsset(asset)

  const createdAt =
    normalizeString(
      asset?.createdAt,
    ) ||
    normalizeString(
      asset?.updatedAt,
    ) ||
    null

  const updatedAt =
    normalizeString(
      asset?.updatedAt,
    ) ||
    createdAt

  const rawVersions =
    Array.isArray(
      asset?.versions,
    )
      ? asset.versions
      : []

  let versions =
    rawVersions
      .map(
        (
          version,
          index,
        ) =>
          normalizeTestAssetVersion(
            version,
            normalizedAsset,
            index + 1,
          ),
      )
      .sort(
        (firstVersion, secondVersion) =>
          secondVersion.versionNumber -
          firstVersion.versionNumber,
      )

  if (versions.length === 0) {
    versions = [
      normalizeTestAssetVersion(
        {
          versionNumber: 1,

          changeSummary:
            fallbackChangeSummary,

          snapshot:
            createTestAssetSnapshot(
              normalizedAsset,
            ),

          createdAt:
            createdAt ??
            updatedAt ??
            FALLBACK_TIMESTAMP,
        },
        normalizedAsset,
        1,
      ),
    ]
  }

  const latestVersion =
    versions[0]

  return {
    ...normalizedAsset,

    lifecycleStatus:
      normalizeLifecycleStatus(
        asset?.lifecycleStatus,
      ),

    currentVersionId:
      latestVersion.versionId,

    currentVersionNumber:
      latestVersion.versionNumber,

    versions,

    createdAt,

    updatedAt,
  }
}

export function createVersionedTestAsset(
  input,
  {
    changeSummary =
      TEST_ASSET_INITIAL_CHANGE_SUMMARY,

    timestamp =
      new Date().toISOString(),
  } = {},
) {
  const normalizedAsset =
    normalizeTestAsset({
      ...input,

      createdAt:
        input?.createdAt ??
        timestamp,

      updatedAt: timestamp,
    })

  const asset = {
    ...normalizedAsset,

    lifecycleStatus: 'Active',

    createdAt:
      input?.createdAt ??
      timestamp,

    updatedAt: timestamp,
  }

  const initialVersion =
    normalizeTestAssetVersion(
      {
        versionNumber: 1,

        changeSummary:
          normalizeString(
            changeSummary,
          ) ||
          TEST_ASSET_INITIAL_CHANGE_SUMMARY,

        snapshot:
          createTestAssetSnapshot(
            asset,
          ),

        createdAt: timestamp,
      },
      asset,
      1,
    )

  return {
    ...asset,

    currentVersionId:
      initialVersion.versionId,

    currentVersionNumber:
      initialVersion.versionNumber,

    versions: [
      initialVersion,
    ],
  }
}

export function appendTestAssetVersion({
  asset,
  changes,
  changeSummary = '',
  timestamp =
    new Date().toISOString(),
} = {}) {
  const currentAsset =
    normalizeVersionedTestAsset(
      asset,
    )

  const safeChanges =
    removeVersionControlFields(
      changes,
    )

  const nextAsset =
    normalizeTestAsset({
      ...currentAsset,
      ...safeChanges,

      id:
        currentAsset.id,

      createdAt:
        currentAsset.createdAt,

      updatedAt:
        timestamp,
    })

  const nextVersionNumber =
    getLatestVersionNumber(
      currentAsset.versions,
    ) + 1

  const resolvedChangeSummary =
    normalizeString(
      changeSummary,
    ) ||
    normalizeString(
      changes?.changeSummary,
    ) ||
    TEST_ASSET_DEFAULT_UPDATE_SUMMARY

  const nextVersion =
    normalizeTestAssetVersion(
      {
        versionNumber:
          nextVersionNumber,

        changeSummary:
          resolvedChangeSummary,

        snapshot:
          createTestAssetSnapshot(
            nextAsset,
          ),

        createdAt: timestamp,
      },
      nextAsset,
      nextVersionNumber,
    )

  return {
    ...nextAsset,

    lifecycleStatus:
      currentAsset.lifecycleStatus,

    currentVersionId:
      nextVersion.versionId,

    currentVersionNumber:
      nextVersion.versionNumber,

    versions: [
      nextVersion,
      ...currentAsset.versions,
    ],

    createdAt:
      currentAsset.createdAt,

    updatedAt:
      timestamp,
  }
}

export function migrateLegacyTestAsset(
  asset,
) {
  return normalizeVersionedTestAsset(
    asset,
    {
      fallbackChangeSummary:
        TEST_ASSET_MIGRATION_CHANGE_SUMMARY,
    },
  )
}
