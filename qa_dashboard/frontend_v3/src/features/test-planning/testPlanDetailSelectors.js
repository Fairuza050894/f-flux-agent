import {
  TEST_PLAN_SCOPE_OPTIONS,
} from './testPlanConstants'
import {
  buildTestPlanCycleReadiness,
  normalizeTestPlan,
} from './testPlanSelectors'

const ASSET_HEALTH_DEFINITIONS = {
  usable: {
    label: 'Ready',
    tone: 'success',
  },

  archived: {
    label: 'Archived',
    tone: 'neutral',
  },

  missing: {
    label: 'Missing',
    tone: 'danger',
  },

  projectMismatch: {
    label: 'Project Mismatch',
    tone: 'danger',
  },

  scopeMismatch: {
    label: 'Outside Scope',
    tone: 'warning',
  },

  notReady: {
    label: 'Not Ready',
    tone: 'warning',
  },
}

function getAssetHealth({
  asset,
  plan,
}) {
  if (!asset) {
    return {
      health: 'missing',
      reason:
        'The Test Asset was deleted or is no longer available.',
    }
  }

  if (
    asset.lifecycleStatus ===
    'Archived'
  ) {
    return {
      health: 'archived',
      reason:
        'The Test Asset is archived and cannot be used for a new Test Cycle.',
    }
  }

  if (
    asset.projectId !==
    plan.projectId
  ) {
    return {
      health: 'projectMismatch',
      reason:
        'The Test Asset no longer belongs to the selected Project.',
    }
  }

  if (
    !plan.scope[
      asset.type
    ]
  ) {
    return {
      health: 'scopeMismatch',
      reason:
        'The Test Asset type is no longer included in this plan scope.',
    }
  }

  if (!asset.executionReady) {
    return {
      health: 'notReady',
      reason:
        'The Test Asset is not marked as execution-ready.',
    }
  }

  return {
    health: 'usable',
    reason:
      'The Test Asset is available and execution-ready.',
  }
}

export function buildTestPlanAssetHealth({
  assets = [],
  plan,
} = {}) {
  const normalizedPlan =
    normalizeTestPlan(plan)

  const assetById =
    new Map(
      assets.map((asset) => [
        asset.id,
        asset,
      ]),
    )

  const rows =
    normalizedPlan
      .selectedAssetIds
      .map((assetId) => {
        const asset =
          assetById.get(
            assetId,
          ) ?? null

        const healthResult =
          getAssetHealth({
            asset,
            plan: normalizedPlan,
          })

        const definition =
          ASSET_HEALTH_DEFINITIONS[
            healthResult.health
          ]

        return {
          id: assetId,

          name:
            asset?.name ??
            'Deleted Test Asset',

          type:
            asset?.type ??
            'unknown',

          typeLabel:
            asset?.typeLabel ??
            'Unknown',

          module:
            asset?.module ??
            'Not available',

          feature:
            asset?.feature ??
            'Not available',

          priority:
            asset?.priority ??
            'Not available',

          automationStatus:
            asset?.automationStatus ??
            'Not available',

          executionReady:
            Boolean(
              asset?.executionReady,
            ),

          health:
            healthResult.health,

          healthLabel:
            definition.label,

          healthTone:
            definition.tone,

          reason:
            healthResult.reason,

          asset,
        }
      })

  const counts =
    rows.reduce(
      (result, row) => ({
        ...result,

        [row.health]:
          (
            result[
              row.health
            ] ?? 0
          ) + 1,
      }),
      {},
    )

  return {
    rows,

    total:
      rows.length,

    usable:
      counts.usable ?? 0,

    missing:
      counts.missing ?? 0,

    projectMismatch:
      counts.projectMismatch ?? 0,

    scopeMismatch:
      counts.scopeMismatch ?? 0,

    notReady:
      counts.notReady ?? 0,

    archived:
      counts.archived ?? 0,

    issueCount:
      rows.filter(
        (row) =>
          row.health !==
          'usable',
      ).length,
  }
}

export function selectCyclesLinkedToTestPlan({
  cycles = [],
  planId,
} = {}) {
  return cycles
    .filter(
      (cycle) =>
        cycle.sourcePlanId ===
        planId,
    )
    .sort((first, second) => {
      const firstTimestamp =
        new Date(
          first.createdAt ?? 0,
        ).getTime()

      const secondTimestamp =
        new Date(
          second.createdAt ?? 0,
        ).getTime()

      return (
        secondTimestamp -
        firstTimestamp
      )
    })
}

export function buildTestPlanDetailModel({
  assets = [],
  cycles = [],
  environments = [],
  plan,
  projects = [],
} = {}) {
  if (!plan) {
    return null
  }

  const normalizedPlan =
    normalizeTestPlan(plan)

  const project =
    projects.find(
      (candidate) =>
        candidate.id ===
        normalizedPlan.projectId,
    ) ?? null

  const environment =
    environments.find(
      (candidate) =>
        candidate.id ===
        normalizedPlan.environmentId,
    ) ?? null

  const readiness =
    buildTestPlanCycleReadiness({
      assets,
      environments,
      plan: normalizedPlan,
      projects,
    })

  const assetHealth =
    buildTestPlanAssetHealth({
      assets,
      plan: normalizedPlan,
    })

  const linkedCycles =
    selectCyclesLinkedToTestPlan({
      cycles,
      planId:
        normalizedPlan.id,
    })

  const scopeLabels =
    TEST_PLAN_SCOPE_OPTIONS
      .filter(
        (option) =>
          Boolean(
            normalizedPlan.scope[
              option.key
            ],
          ),
      )
      .map(
        (option) =>
          option.label,
      )

  const evidenceLabels = [
    {
      key: 'screenshot',
      label: 'Screenshots',
    },
    {
      key: 'video',
      label: 'Video Recording',
    },
    {
      key: 'consoleLogs',
      label: 'Console Logs',
    },
    {
      key: 'networkLogs',
      label: 'Network Logs',
    },
    {
      key: 'errorLogs',
      label: 'Error Logs',
    },
  ]
    .filter(
      (option) =>
        Boolean(
          normalizedPlan
            .executionSettings[
            option.key
          ],
        ),
    )
    .map(
      (option) =>
        option.label,
    )

  const notificationLabels = [
    {
      key: 'telegramTesting',
      label: 'Telegram Testing',
    },
    {
      key: 'telegramDocumentation',
      label: 'Telegram Documentation',
    },
  ]
    .filter(
      (option) =>
        Boolean(
          normalizedPlan
            .executionSettings[
            option.key
          ],
        ),
    )
    .map(
      (option) =>
        option.label,
    )

  return {
    plan: normalizedPlan,
    project,
    environment,
    readiness,
    assetHealth,
    linkedCycles,
    scopeLabels,
    evidenceLabels,
    notificationLabels,
  }
}
