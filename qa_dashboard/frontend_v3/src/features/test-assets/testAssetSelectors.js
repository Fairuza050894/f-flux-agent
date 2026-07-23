import {
  TEST_ASSET_TYPES,
} from './testAssetConstants'

function normalizeText(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
}

export function getTestAssetTypeLabel(
  type,
) {
  return (
    TEST_ASSET_TYPES.find(
      (option) =>
        option.value === type,
    )?.label ??
    String(type ?? 'Unknown')
  )
}

export function normalizeTestAsset(
  asset,
) {
  const type =
    normalizeText(asset?.type) ||
    'ui'

  return {
    ...asset,

    id:
      String(asset?.id ?? '').trim(),

    projectId:
      String(
        asset?.projectId ?? '',
      ).trim(),

    name:
      String(asset?.name ?? '').trim(),

    type,

    typeLabel:
      getTestAssetTypeLabel(type),

    module:
      String(
        asset?.module ?? '',
      ).trim(),

    feature:
      String(
        asset?.feature ?? '',
      ).trim(),

    priority:
      String(
        asset?.priority ?? 'Medium',
      ).trim(),

    automationStatus:
      String(
        asset?.automationStatus ??
          'Draft',
      ).trim(),

    recommended:
      Boolean(asset?.recommended),

    executionReady:
      Boolean(asset?.executionReady),

    description:
      String(
        asset?.description ?? '',
      ).trim(),

    preconditions:
      String(
        asset?.preconditions ?? '',
      ).trim(),

    steps:
      Array.isArray(asset?.steps)
        ? asset.steps
        : [],

    expectedResult:
      String(
        asset?.expectedResult ?? '',
      ).trim(),
  }
}

function matchesSearch(
  asset,
  searchTerm,
) {
  const query =
    normalizeText(searchTerm)

  if (!query) {
    return true
  }

  return [
    asset.id,
    asset.name,
    asset.module,
    asset.feature,
    asset.description,
  ].some((value) =>
    normalizeText(value).includes(
      query,
    ),
  )
}

function matchesBooleanFilter(
  value,
  filterValue,
) {
  if (filterValue === 'all') {
    return true
  }

  return value ===
    (filterValue === 'yes')
}

export function filterTestAssets({
  assets = [],
  filters = {},
} = {}) {
  return assets
    .map(normalizeTestAsset)
    .filter((asset) => {
      const matchesProject =
        !filters.projectId ||
        filters.projectId === 'all' ||
        asset.projectId ===
          filters.projectId

      const matchesType =
        !filters.type ||
        filters.type === 'all' ||
        asset.type === filters.type

      const matchesPriority =
        !filters.priority ||
        filters.priority === 'all' ||
        normalizeText(
          asset.priority,
        ) ===
          normalizeText(
            filters.priority,
          )

      const matchesAutomation =
        !filters.automationStatus ||
        filters.automationStatus ===
          'all' ||
        normalizeText(
          asset.automationStatus,
        ) ===
          normalizeText(
            filters.automationStatus,
          )

      const matchesReady =
        matchesBooleanFilter(
          asset.executionReady,
          filters.executionReady ??
            'all',
        )

      const matchesRecommended =
        matchesBooleanFilter(
          asset.recommended,
          filters.recommended ??
            'all',
        )

      return (
        matchesSearch(
          asset,
          filters.searchTerm,
        ) &&
        matchesProject &&
        matchesType &&
        matchesPriority &&
        matchesAutomation &&
        matchesReady &&
        matchesRecommended
      )
    })
}

export function selectCycleEligibleAssets({
  assets = [],
  projectId,
  scope = {},
} = {}) {
  return assets
    .map(normalizeTestAsset)
    .filter(
      (asset) =>
        asset.projectId === projectId &&
        Boolean(scope[asset.type]),
    )
}

export function buildTestAssetMetrics(
  assets = [],
) {
  const normalizedAssets =
    assets.map(normalizeTestAsset)

  return {
    total:
      normalizedAssets.length,

    executionReady:
      normalizedAssets.filter(
        (asset) =>
          asset.executionReady,
      ).length,

    recommended:
      normalizedAssets.filter(
        (asset) =>
          asset.recommended,
      ).length,

    automated:
      normalizedAssets.filter(
        (asset) =>
          asset.automationStatus ===
          'Automated',
      ).length,

    draft:
      normalizedAssets.filter(
        (asset) =>
          asset.automationStatus ===
          'Draft',
      ).length,
  }
}

export function buildTestAssetTypeCounts({
  assets = [],
  projectId,
} = {}) {
  const counts = {}

  assets
    .map(normalizeTestAsset)
    .forEach((asset) => {
      if (
        projectId &&
        asset.projectId !== projectId
      ) {
        return
      }

      counts[asset.type] =
        (counts[asset.type] ?? 0) + 1
    })

  return counts
}
