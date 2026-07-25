import {
  normalizeTestPlanAssetSnapshots,
} from '../test-planning/testPlanAssetSnapshots'
import {
  buildExecutionSnapshotCoverage,
  executionContainsAssetVersion,
} from '../executions/executionSnapshotTraceability'

function normalizeText(
  value,
) {
  return String(value ?? '').trim()
}

function normalizeAssetIds(
  values,
) {
  if (!Array.isArray(values)) {
    return []
  }

  return Array.from(
    new Set(
      values
        .map(normalizeText)
        .filter(Boolean),
    ),
  )
}

function resolveReportRowCycleId(
  row,
) {
  return normalizeText(
    row?.cycleId ??
    row?.cycle_id ??
    row?.id ??
    row?.cycle?.id,
  )
}

function resolveReportRowCycleName(
  row,
) {
  return normalizeText(
    row?.cycleName ??
    row?.cycle_name ??
    row?.name ??
    row?.cycle?.name,
  )
}

function selectVisibleCycles({
  cycles = [],
  reportRows = [],
} = {}) {
  if (!Array.isArray(reportRows)) {
    return cycles
  }

  if (reportRows.length === 0) {
    return []
  }

  const visibleIds =
    new Set(
      reportRows
        .map(
          resolveReportRowCycleId,
        )
        .filter(Boolean),
    )

  if (visibleIds.size > 0) {
    return cycles.filter(
      (cycle) =>
        visibleIds.has(
          normalizeText(cycle?.id),
        ),
    )
  }

  const visibleNames =
    new Set(
      reportRows
        .map(
          resolveReportRowCycleName,
        )
        .filter(Boolean),
    )

  return cycles.filter(
    (cycle) =>
      visibleNames.has(
        normalizeText(cycle?.name),
      ),
  )
}

function getTraceabilityStatus({
  executionCount,
  hasSnapshot,
  tracedExecutionCount,
}) {
  if (!hasSnapshot) {
    return {
      key: 'no_snapshot',
      label: 'No Snapshot',
      tone: 'danger',
    }
  }

  if (executionCount === 0) {
    return {
      key: 'not_executed',
      label: 'Not Executed',
      tone: 'neutral',
    }
  }

  if (
    tracedExecutionCount ===
    executionCount
  ) {
    return {
      key: 'complete',
      label: 'Complete',
      tone: 'success',
    }
  }

  if (tracedExecutionCount > 0) {
    return {
      key: 'partial',
      label: 'Partial',
      tone: 'warning',
    }
  }

  return {
    key: 'missing',
    label: 'Missing',
    tone: 'danger',
  }
}

function buildCycleRows(
  cycle,
) {
  const snapshots =
    normalizeTestPlanAssetSnapshots(
      cycle?.selectedAssetSnapshots,
    )

  const snapshotByAssetId =
    new Map(
      snapshots.map((record) => [
        record.assetId,
        record,
      ]),
    )

  const selectedAssetIds =
    normalizeAssetIds(
      cycle?.selectedAssetIds,
    )

  const orderedAssetIds =
    Array.from(
      new Set([
        ...selectedAssetIds,
        ...snapshots.map(
          (record) =>
            record.assetId,
        ),
      ]),
    )

  const executions =
    Array.isArray(cycle?.executions)
      ? cycle.executions
      : []

  return orderedAssetIds.map(
    (assetId) => {
      const snapshotRecord =
        snapshotByAssetId.get(
          assetId,
        ) ?? null

      const tracedExecutionCount =
        snapshotRecord
          ? executions.filter(
              (execution) =>
                executionContainsAssetVersion(
                  execution,
                  snapshotRecord,
                ),
            ).length
          : 0

      const traceability =
        getTraceabilityStatus({
          executionCount:
            executions.length,
          hasSnapshot:
            Boolean(snapshotRecord),
          tracedExecutionCount,
        })

      const snapshot =
        snapshotRecord
          ?.snapshot ?? null

      return {
        id:
          `${cycle.id}:${assetId}`,

        cycleId:
          cycle.id,

        cycleName:
          cycle.name,

        cycleStatus:
          cycle.status ??
          'Not available',

        triggerSource:
          cycle.triggerSource ??
          (
            cycle.sourcePlanId
              ? 'Test Plan'
              : 'Manual'
          ),

        sourcePlanId:
          cycle.sourcePlanId ?? '',

        assetId,

        assetName:
          snapshot?.name ??
          'Unavailable Test Asset',

        module:
          snapshot?.module ??
          cycle.module ??
          'Not specified',

        feature:
          snapshot?.feature ??
          cycle.feature ??
          'Not specified',

        capturedVersionId:
          snapshotRecord
            ?.versionId ?? '',

        capturedVersionNumber:
          snapshotRecord
            ?.versionNumber ?? null,

        capturedAt:
          snapshotRecord
            ?.capturedAt ?? null,

        changeSummary:
          snapshotRecord
            ?.changeSummary ?? '',

        hasSnapshot:
          Boolean(snapshotRecord),

        executionCount:
          executions.length,

        tracedExecutionCount,

        traceabilityKey:
          traceability.key,

        traceabilityLabel:
          traceability.label,

        traceabilityTone:
          traceability.tone,
      }
    },
  )
}

export function buildReportAssetTraceability({
  cycles = [],
  reportRows = [],
} = {}) {
  const visibleCycles =
    selectVisibleCycles({
      cycles,
      reportRows,
    })

  const rows =
    visibleCycles.flatMap(
      buildCycleRows,
    )

  const executions =
    visibleCycles.flatMap(
      (cycle) =>
        Array.isArray(
          cycle?.executions,
        )
          ? cycle.executions.map(
              (execution) => ({
                cycle,
                execution,
              }),
            )
          : [],
    )

  const tracedExecutions =
    executions.filter(
      ({ cycle, execution }) =>
        buildExecutionSnapshotCoverage({
          cycleSnapshots:
            cycle
              .selectedAssetSnapshots,
          execution,
        }).isComplete,
    ).length

  const countByStatus =
    rows.reduce(
      (counts, row) => ({
        ...counts,
        [row.traceabilityKey]:
          (
            counts[
              row.traceabilityKey
            ] ?? 0
          ) + 1,
      }),
      {},
    )

  return {
    cycleCount:
      visibleCycles.length,

    total:
      rows.length,

    captured:
      rows.filter(
        (row) => row.hasSnapshot,
      ).length,

    totalExecutions:
      executions.length,

    tracedExecutions,

    missingExecutionSnapshots:
      executions.length -
      tracedExecutions,

    complete:
      countByStatus.complete ?? 0,

    partial:
      countByStatus.partial ?? 0,

    missing:
      countByStatus.missing ?? 0,

    notExecuted:
      countByStatus
        .not_executed ?? 0,

    noSnapshot:
      countByStatus
        .no_snapshot ?? 0,

    rows,
  }
}
