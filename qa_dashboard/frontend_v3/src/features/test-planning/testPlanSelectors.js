import {
  normalizeTestPlanAssetSnapshots,
} from './testPlanAssetSnapshots'

import {
  TEST_PLAN_CYCLE_TYPES,
  TEST_PLAN_DEFAULT_EXECUTION_SETTINGS,
  TEST_PLAN_DEFAULT_SCOPE,
  TEST_PLAN_STATUSES,
} from './testPlanConstants'

function normalizeText(value) {
  return String(value ?? '').trim()
}

function normalizeSearchText(value) {
  return normalizeText(value)
    .toLowerCase()
}

function normalizeScope(scope) {
  return {
    ui: Boolean(
      scope?.ui ??
      TEST_PLAN_DEFAULT_SCOPE.ui,
    ),

    api: Boolean(
      scope?.api ??
      TEST_PLAN_DEFAULT_SCOPE.api,
    ),

    unit: Boolean(
      scope?.unit ??
      TEST_PLAN_DEFAULT_SCOPE.unit,
    ),

    e2e: Boolean(
      scope?.e2e ??
      TEST_PLAN_DEFAULT_SCOPE.e2e,
    ),

    regression: Boolean(
      scope?.regression ??
      TEST_PLAN_DEFAULT_SCOPE.regression,
    ),
  }
}

function normalizeExecutionSettings(
  settings,
) {
  return {
    ...TEST_PLAN_DEFAULT_EXECUTION_SETTINGS,
    ...(settings ?? {}),

    screenshot: Boolean(
      settings?.screenshot ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .screenshot,
    ),

    video: Boolean(
      settings?.video ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .video,
    ),

    consoleLogs: Boolean(
      settings?.consoleLogs ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .consoleLogs,
    ),

    networkLogs: Boolean(
      settings?.networkLogs ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .networkLogs,
    ),

    errorLogs: Boolean(
      settings?.errorLogs ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .errorLogs,
    ),

    telegramTesting: Boolean(
      settings?.telegramTesting ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .telegramTesting,
    ),

    telegramDocumentation: Boolean(
      settings?.telegramDocumentation ??
      TEST_PLAN_DEFAULT_EXECUTION_SETTINGS
        .telegramDocumentation,
    ),
  }
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
        .map((assetId) =>
          normalizeText(assetId),
        )
        .filter(Boolean),
    ),
  )
}

export function normalizeTestPlan(
  plan,
) {
  const cycleType =
    TEST_PLAN_CYCLE_TYPES.includes(
      plan?.cycleType,
    )
      ? plan.cycleType
      : 'Feature Cycle'

  const status =
    TEST_PLAN_STATUSES.includes(
      plan?.status,
    )
      ? plan.status
      : 'Draft'

  const selectedAssetIds =
    normalizeSelectedAssetIds(
      plan?.selectedAssetIds,
    )

  const selectedAssetSnapshots =
    normalizeTestPlanAssetSnapshots(
      plan?.selectedAssetSnapshots,
    ).filter(
      (record) =>
        selectedAssetIds.includes(
          record.assetId,
        ),
    )

  return {
    ...plan,

    id:
      normalizeText(plan?.id),

    name:
      normalizeText(plan?.name),

    projectId:
      normalizeText(
        plan?.projectId,
      ),

    environmentId:
      normalizeText(
        plan?.environmentId,
      ),

    objective:
      normalizeText(
        plan?.objective,
      ),

    cycleType,

    module:
      normalizeText(
        plan?.module,
      ),

    feature:
      normalizeText(
        plan?.feature,
      ),

    scope:
      normalizeScope(
        plan?.scope,
      ),

    selectedAssetIds,

    selectedAssetSnapshots,

    executionSettings:
      normalizeExecutionSettings(
        plan?.executionSettings,
      ),

    status,

    createdAt:
      plan?.createdAt ?? null,

    updatedAt:
      plan?.updatedAt ?? null,
  }
}

function matchesSearch(
  plan,
  searchTerm,
) {
  const query =
    normalizeSearchText(
      searchTerm,
    )

  if (!query) {
    return true
  }

  return [
    plan.id,
    plan.name,
    plan.objective,
    plan.module,
    plan.feature,
  ].some((value) =>
    normalizeSearchText(
      value,
    ).includes(query),
  )
}

function matchesScopeType(
  plan,
  scopeType,
) {
  if (
    !scopeType ||
    scopeType === 'all'
  ) {
    return true
  }

  return Boolean(
    plan.scope?.[scopeType],
  )
}

export function filterTestPlans({
  filters = {},
  plans = [],
} = {}) {
  return plans
    .map(normalizeTestPlan)
    .filter((plan) => {
      const matchesProject =
        !filters.projectId ||
        filters.projectId === 'all' ||
        plan.projectId ===
          filters.projectId

      const matchesStatus =
        !filters.status ||
        filters.status === 'all' ||
        plan.status ===
          filters.status

      return (
        matchesSearch(
          plan,
          filters.searchTerm,
        ) &&
        matchesProject &&
        matchesStatus &&
        matchesScopeType(
          plan,
          filters.scopeType,
        )
      )
    })
}

export function buildTestPlanMetrics(
  plans = [],
) {
  const normalizedPlans =
    plans.map(
      normalizeTestPlan,
    )

  return {
    total:
      normalizedPlans.length,

    draft:
      normalizedPlans.filter(
        (plan) =>
          plan.status === 'Draft',
      ).length,

    ready:
      normalizedPlans.filter(
        (plan) =>
          plan.status === 'Ready',
      ).length,

    archived:
      normalizedPlans.filter(
        (plan) =>
          plan.status === 'Archived',
      ).length,

    linkedAssets:
      normalizedPlans.reduce(
        (total, plan) =>
          total +
          plan.selectedAssetIds.length,
        0,
      ),
  }
}

export function countTestPlanScopes(
  plan,
) {
  const normalizedPlan =
    normalizeTestPlan(plan)

  return Object.values(
    normalizedPlan.scope,
  ).filter(Boolean).length
}

export function getTestPlanScopeKeys(
  plan,
) {
  const normalizedPlan =
    normalizeTestPlan(plan)

  return Object.entries(
    normalizedPlan.scope,
  )
    .filter(
      ([, enabled]) =>
        enabled,
    )
    .map(
      ([scopeKey]) =>
        scopeKey,
    )
}

export function selectUsableTestPlanAssets({
  assets = [],
  plan,
} = {}) {
  const normalizedPlan =
    normalizeTestPlan(plan)

  const selectedAssetIds =
    new Set(
      normalizedPlan.selectedAssetIds,
    )

  return assets.filter((asset) => {
    return (
      selectedAssetIds.has(
        asset.id,
      ) &&
      asset.projectId ===
        normalizedPlan.projectId &&
      Boolean(
        normalizedPlan.scope[
          asset.type
        ],
      ) &&
      asset.lifecycleStatus !==
        'Archived' &&
      asset.executionReady
    )
  })
}

export function buildTestPlanCycleReadiness({
  assets = [],
  environments = [],
  plan,
  projects = [],
} = {}) {
  const normalizedPlan =
    normalizeTestPlan(plan)

  const issues = []

  const projectExists =
    projects.some(
      (project) =>
        project.id ===
        normalizedPlan.projectId,
    )

  const environmentExists =
    environments.some(
      (environment) =>
        environment.id ===
          normalizedPlan.environmentId &&
        environment.projectId ===
          normalizedPlan.projectId,
    )

  const usableAssets =
    selectUsableTestPlanAssets({
      assets,
      plan: normalizedPlan,
    })

  if (
    normalizedPlan.status !==
    'Ready'
  ) {
    issues.push(
      'The Test Plan must have Ready status.',
    )
  }

  if (!projectExists) {
    issues.push(
      'The selected Project is no longer available.',
    )
  }

  if (!environmentExists) {
    issues.push(
      'The default Environment is missing or does not belong to the selected Project.',
    )
  }

  if (
    usableAssets.length === 0
  ) {
    issues.push(
      'No execution-ready Test Assets remain available for this plan.',
    )
  }

  return {
    isReady:
      issues.length === 0,

    issues,

    selectedAssetIds:
      usableAssets.map(
        (asset) =>
          asset.id,
      ),
  }
}
