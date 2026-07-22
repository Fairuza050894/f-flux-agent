import {
  formatResultStatus,
  getResultStatusTone,
} from '../results/resultFormatters'

const evidenceConfiguration =
  Object.freeze([
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
  ])

const notificationConfiguration =
  Object.freeze([
    {
      key: 'telegramTesting',
      label: 'Telegram Testing',
    },
    {
      key: 'telegramDocumentation',
      label: 'Telegram Documentation',
    },
  ])

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function normalizeAssetId(
  asset,
) {
  if (
    typeof asset === 'string' ||
    typeof asset === 'number'
  ) {
    return String(asset)
  }

  if (
    asset &&
    typeof asset === 'object'
  ) {
    const assetId =
      asset.id ??
      asset.assetId ??
      asset.asset_id ??
      asset.testAssetId ??
      asset.test_asset_id

    return assetId === null ||
      assetId === undefined
      ? ''
      : String(assetId)
  }

  return ''
}

function getSelectedAssetIds(
  cycle,
) {
  const candidates = [
    cycle?.selectedAssetIds,
    cycle?.selected_asset_ids,
    cycle?.testAssetIds,
    cycle?.test_asset_ids,
    cycle?.testAssets,
    cycle?.test_assets,
    cycle?.assetIds,
    cycle?.asset_ids,
  ]

  const assetCollection =
    candidates.find(
      Array.isArray,
    ) ?? []

  return assetCollection
    .map(normalizeAssetId)
    .filter(Boolean)
}

function getExecutionScopeKey(
  execution,
) {
  return (
    execution?.scopeKey ??
    execution?.scope_key ??
    execution?.testType ??
    execution?.test_type ??
    execution?.source ??
    ''
  )
}

function createExecutionLookup(
  executions,
) {
  return new Map(
    toArray(executions)
      .map((execution) => [
        getExecutionScopeKey(
          execution,
        ),
        execution,
      ])
      .filter(([scopeKey]) =>
        Boolean(scopeKey),
      ),
  )
}

function selectConfigurationItems(
  configuration,
  executionSettings,
) {
  return configuration.filter(
    (item) =>
      Boolean(
        executionSettings?.[
          item.key
        ],
      ),
  )
}

function buildMetadata(
  cycle,
) {
  return [
    {
      key: 'release-version',
      label: 'Release / Version',
      value:
        cycle?.releaseVersion ??
        cycle?.release_version ??
        'Not specified',
    },
    {
      key: 'module',
      label: 'Module',
      value:
        cycle?.module ||
        'Full Product',
    },
    {
      key: 'feature',
      label: 'Feature',
      value:
        cycle?.feature ||
        'Not specified',
    },
    {
      key: 'change-type',
      label: 'Change Type',
      value:
        cycle?.cycleType ===
        'Change Cycle'
          ? (
              cycle?.changeType ??
              cycle?.change_type ??
              'Not specified'
            )
          : 'Not applicable',
    },
    {
      key: 'reference',
      label: 'Reference',
      value:
        cycle?.reference ||
        'Not specified',
    },
    {
      key: 'last-updated',
      label: 'Last Updated',
      value:
        cycle?.updatedAt ??
        cycle?.updated_at ??
        null,
      valueType: 'datetime',
    },
  ]
}

function buildRunnerRows({
  executions,
  selectedScopes,
}) {
  const executionLookup =
    createExecutionLookup(
      executions,
    )

  return toArray(
    selectedScopes,
  ).map((scope) => {
    const execution =
      executionLookup.get(
        scope.key,
      )

    const status =
      execution?.status ?? ''

    return {
      key: scope.key,
      label: scope.label,
      runner: scope.runner,

      status:
        status ||
        'not_started',

      statusLabel:
        execution
          ? formatResultStatus(
              status,
            )
          : 'Not Started',

      tone:
        execution
          ? getResultStatusTone(
              status,
            )
          : 'neutral',
    }
  })
}

export function buildCycleOverviewModel({
  cycle,
  executions,
  selectedScopes,
} = {}) {
  const executionSettings =
    cycle?.executionSettings ??
    cycle?.execution_settings ??
    {}

  const evidence =
    selectConfigurationItems(
      evidenceConfiguration,
      executionSettings,
    )

  const notifications =
    selectConfigurationItems(
      notificationConfiguration,
      executionSettings,
    )

  const assets =
    getSelectedAssetIds(
      cycle,
    )

  return {
    metadata:
      buildMetadata(cycle),

    description:
      cycle?.description ||
      'No cycle description provided.',

    executionMode:
      executionSettings
        .executionMode ??
      executionSettings
        .execution_mode ??
      'Sequential',

    stopPolicy:
      executionSettings
        .stopPolicy ??
      executionSettings
        .stop_policy ??
      'Critical Failure',

    evidence,
    notifications,
    assets,

    runners:
      buildRunnerRows({
        executions,
        selectedScopes,
      }),
  }
}
