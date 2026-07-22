import {
  getResultStatusTone,
} from '../results/resultFormatters'

function getStartAction({
  executionCount,
  isStarting,
  missingExecutionCount,
}) {
  if (isStarting) {
    return {
      disabled: true,
      label: 'Creating Executions...',
    }
  }

  if (missingExecutionCount <= 0) {
    return {
      disabled: true,
      label: 'Executions Created',
    }
  }

  return {
    disabled: false,
    label:
      executionCount > 0
        ? 'Retry Missing Executions'
        : 'Start Test Cycle',
  }
}

function buildSummaryItems({
  cycle,
  environmentName,
  projectName,
}) {
  return [
    {
      key: 'project',
      label: 'Project',
      value: projectName,
    },
    {
      key: 'environment',
      label: 'Environment',
      value: environmentName,
    },
    {
      key: 'cycle-type',
      label: 'Cycle Type',
      value:
        cycle?.cycleType ??
        cycle?.cycle_type ??
        'Not specified',
    },
    {
      key: 'trigger-source',
      label: 'Trigger Source',
      value:
        cycle?.triggerSource ??
        cycle?.trigger_source ??
        'Manual',
    },
    {
      key: 'progress',
      label: 'Progress',
      value:
        `${cycle?.progress ?? 0}%`,
    },
    {
      key: 'created',
      label: 'Created',
      value:
        cycle?.createdAt ??
        cycle?.created_at ??
        null,
      valueType: 'datetime',
    },
  ]
}

export function buildCycleDetailShellModel({
  cycle,
  environment,
  executionCount = 0,
  isStarting = false,
  missingExecutionCount = 0,
  project,
  startError = '',
} = {}) {
  const projectName =
    project?.name ??
    'Unknown Project'

  const environmentName =
    environment?.name ??
    'Not configured'

  const contextEnvironmentName =
    environment?.name ??
    'Environment not configured'

  const status =
    cycle?.status ??
    'not_started'

  return {
    header: {
      context: [
        cycle?.id ??
          'Unknown Cycle',
        projectName,
        contextEnvironmentName,
      ].join(' · '),

      errorMessage:
        startError ||
        cycle?.executionError ||
        cycle?.execution_error ||
        '',

      name:
        cycle?.name ??
        'Unnamed Test Cycle',

      startAction:
        getStartAction({
          executionCount,
          isStarting,
          missingExecutionCount,
        }),

      statusLabel: status,

      statusTone:
        getResultStatusTone(
          status,
        ),
    },

    summary:
      buildSummaryItems({
        cycle,
        environmentName,
        projectName,
      }),
  }
}
