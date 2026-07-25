import {
  formatResultStatus,
  getResultStatusTone,
  normalizeResultStatus,
} from '../results/resultFormatters'
import {
  formatExecutionReason,
  getExecutionLineage,
} from './executionAttemptSelectors'

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function addActivityItem(
  items,
  {
    description,
    id,
    timestamp,
    title,
    tone = 'neutral',
  },
) {
  if (!timestamp) {
    return
  }

  items.push({
    description,
    id,
    timestamp,
    title,
    tone,
  })
}

function getExecutionScopeLabel(
  execution,
) {
  return (
    execution?.scopeLabel ??
    execution?.scope_label ??
    execution?.scope ??
    execution?.source ??
    'Execution'
  )
}

function getExecutionRunId(
  execution,
  index,
) {
  return (
    execution?.runId ??
    execution?.run_id ??
    `execution-${index + 1}`
  )
}

function getExecutionTimestamps(
  execution,
) {
  return {
    createdAt:
      execution?.created_at ??
      execution?.createdAt ??
      null,

    startedAt:
      execution?.started_at ??
      execution?.startedAt ??
      null,

    completedAt:
      execution?.completed_at ??
      execution?.completedAt ??
      null,

    updatedAt:
      execution?.updated_at ??
      execution?.updatedAt ??
      null,
  }
}

function getExecutionCurrentStage(
  execution,
) {
  return (
    execution?.current_stage ??
    execution?.currentStage ??
    ''
  )
}

function getTimestampValue(
  timestamp,
) {
  const timestampValue =
    new Date(timestamp).getTime()

  return Number.isFinite(
    timestampValue,
  )
    ? timestampValue
    : 0
}

export function buildExecutionActivityItems({
  cycle,
  executions,
} = {}) {
  const items = []

  addActivityItem(
    items,
    {
      id: 'cycle-created',
      title: 'Test Cycle created',
      description:
        'Created from the Test Cycle wizard.',
      timestamp:
        cycle?.createdAt ??
        cycle?.created_at ??
        null,
      tone: 'primary',
    },
  )

  toArray(executions).forEach(
    (execution, index) => {
      const runId =
        getExecutionRunId(
          execution,
          index,
        )

      const scopeLabel =
        getExecutionScopeLabel(
          execution,
        )

      const {
        completedAt,
        createdAt,
        startedAt,
        updatedAt,
      } = getExecutionTimestamps(
        execution,
      )

      const status =
        normalizeResultStatus(
          execution?.status,
        )

      const currentStage =
        getExecutionCurrentStage(
          execution,
        )

      const lineage =
        getExecutionLineage(
          execution,
        )

      const reasonLabel =
        formatExecutionReason(
          lineage.executionReason,
        )

      const lineageDescription = [
        `Backend run ID: ${runId}`,
        `Attempt ${lineage.attemptNumber}`,
        lineage.parentRunId
          ? `Parent run: ${lineage.parentRunId}`
          : '',
      ]
        .filter(Boolean)
        .join(' · ')

      addActivityItem(
        items,
        {
          id: `${runId}-created`,
          title:
            lineage.executionReason ===
            'initial'
              ? `${scopeLabel} execution created`
              : `${scopeLabel} ${reasonLabel.toLowerCase()} created`,
          description:
            lineageDescription,
          timestamp: createdAt,
          tone:
            lineage.executionReason ===
            'initial'
              ? 'neutral'
              : 'primary',
        },
      )

      addActivityItem(
        items,
        {
          id: `${runId}-started`,
          title:
            `${scopeLabel} execution started`,
          description:
            currentStage
              ? `Stage: ${formatResultStatus(
                  currentStage,
                )} · ${reasonLabel}`
              : lineageDescription,
          timestamp: startedAt,
          tone: 'primary',
        },
      )

      if (completedAt) {
        const executionFailed =
          [
            'failed',
            'error',
          ].includes(status)

        addActivityItem(
          items,
          {
            id: `${runId}-completed`,
            title:
              executionFailed
                ? `${scopeLabel} execution failed`
                : `${scopeLabel} execution completed`,
            description:
              `Final status: ${formatResultStatus(
                status,
              )} · ${reasonLabel} · Attempt ${lineage.attemptNumber}`,
            timestamp: completedAt,
            tone:
              getResultStatusTone(
                status,
              ),
          },
        )

        return
      }

      if (
        updatedAt &&
        updatedAt !== createdAt &&
        updatedAt !== startedAt
      ) {
        addActivityItem(
          items,
          {
            id: `${runId}-updated`,
            title:
              `${scopeLabel} status updated`,
            description:
              currentStage
                ? `${formatResultStatus(
                    status,
                  )} · ${formatResultStatus(
                    currentStage,
                  )} · ${reasonLabel}`
                : `${formatResultStatus(
                    status,
                  )} · ${reasonLabel}`,
            timestamp: updatedAt,
            tone:
              getResultStatusTone(
                status,
              ),
          },
        )
      }
    },
  )

  return items.sort(
    (first, second) =>
      getTimestampValue(
        second.timestamp,
      ) -
      getTimestampValue(
        first.timestamp,
      ),
  )
}
