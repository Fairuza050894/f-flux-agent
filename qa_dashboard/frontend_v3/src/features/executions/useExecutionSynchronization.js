import {
  useEffect,
} from 'react'

import {
  getExecution,
} from '../../services/executionService'

const activePollingStatuses = new Set([
  'running',
  'in_progress',
  'processing',
  'cancelling',
])

function normalizeStatus(status) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll(' ', '_')
}

function buildRunIdKey(
  executions,
  predicate = () => true,
) {
  return executions
    .filter(
      (execution) =>
        execution?.runId &&
        predicate(execution),
    )
    .map(
      (execution) =>
        execution.runId,
    )
    .sort()
    .join('|')
}

export function useExecutionSynchronization({
  cycleId,
  executions = [],
  pollInterval = 2500,
  updateCycleExecution,
} = {}) {
  const executionRunIds =
    buildRunIdKey(executions)

  const activeRunIds =
    buildRunIdKey(
      executions,
      (execution) =>
        activePollingStatuses.has(
          normalizeStatus(
            execution.status,
          ),
        ),
    )

  useEffect(() => {
    if (
      !cycleId ||
      !executionRunIds ||
      typeof updateCycleExecution !==
        'function'
    ) {
      return undefined
    }

    let cancelled = false

    async function synchronizeExecutions() {
      const runIds =
        executionRunIds.split('|')

      const results =
        await Promise.allSettled(
          runIds.map((runId) =>
            getExecution(runId),
          ),
        )

      if (cancelled) {
        return
      }

      results.forEach(
        (result, index) => {
          if (
            result.status !==
            'fulfilled'
          ) {
            return
          }

          updateCycleExecution(
            cycleId,
            runIds[index],
            result.value,
          )
        },
      )
    }

    void synchronizeExecutions()

    return () => {
      cancelled = true
    }
  }, [
    cycleId,
    executionRunIds,
    updateCycleExecution,
  ])

  useEffect(() => {
    if (
      !cycleId ||
      !activeRunIds ||
      typeof updateCycleExecution !==
        'function'
    ) {
      return undefined
    }

    let cancelled = false

    async function pollActiveExecutions() {
      const runIds =
        activeRunIds.split('|')

      const results =
        await Promise.allSettled(
          runIds.map((runId) =>
            getExecution(runId),
          ),
        )

      if (cancelled) {
        return
      }

      results.forEach(
        (result, index) => {
          if (
            result.status !==
            'fulfilled'
          ) {
            return
          }

          updateCycleExecution(
            cycleId,
            runIds[index],
            result.value,
          )
        },
      )
    }

    const timer = window.setInterval(
      pollActiveExecutions,
      pollInterval,
    )

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [
    activeRunIds,
    cycleId,
    pollInterval,
    updateCycleExecution,
  ])
}
