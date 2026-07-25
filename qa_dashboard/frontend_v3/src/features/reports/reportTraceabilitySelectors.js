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

function buildCycleAssetRows(
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

function buildCycleGroup(
  cycle,
) {
  const rows =
    buildCycleAssetRows(
      cycle,
    )

  const executions =
    Array.isArray(cycle?.executions)
      ? cycle.executions
      : []

  const capturedCount =
    rows.filter(
      (row) => row.hasSnapshot,
    ).length

  const tracedExecutionCount =
    executions.filter(
      (execution) =>
        buildExecutionSnapshotCoverage({
          cycleSnapshots:
            cycle
              .selectedAssetSnapshots,
          execution,
        }).isComplete,
    ).length

  const traceability =
    getTraceabilityStatus({
      executionCount:
        executions.length,
      hasSnapshot:
        rows.length > 0 &&
        capturedCount === rows.length,
      tracedExecutionCount,
    })

  return {
    id:
      cycle.id,

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

    module:
      cycle.module ??
      'Not specified',

    feature:
      cycle.feature ??
      'Not specified',

    assetCount:
      rows.length,

    capturedCount,

    executionCount:
      executions.length,

    tracedExecutionCount,

    traceabilityKey:
      traceability.key,

    traceabilityLabel:
      traceability.label,

    traceabilityTone:
      traceability.tone,

    rows,
  }
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

  const groups =
    visibleCycles.map(
      buildCycleGroup,
    )

  const rows =
    groups.flatMap(
      (group) => group.rows,
    )

  const totalExecutions =
    groups.reduce(
      (total, group) =>
        total +
        group.executionCount,
      0,
    )

  const tracedExecutions =
    groups.reduce(
      (total, group) =>
        total +
        group.tracedExecutionCount,
      0,
    )

  const completeCycles =
    groups.filter(
      (group) =>
        group.traceabilityKey ===
        'complete',
    ).length

  const needsAttention =
    groups.filter(
      (group) =>
        [
          'partial',
          'missing',
        ].includes(
          group.traceabilityKey,
        ),
    ).length

  const legacyCycles =
    groups.filter(
      (group) =>
        group.traceabilityKey ===
        'no_snapshot',
    ).length

  return {
    cycleCount:
      groups.length,

    total:
      rows.length,

    captured:
      rows.filter(
        (row) => row.hasSnapshot,
      ).length,

    totalExecutions,

    tracedExecutions,

    missingExecutionSnapshots:
      totalExecutions -
      tracedExecutions,

    completeCycles,

    needsAttention,

    legacyCycles,

    notExecutedCycles:
      groups.filter(
        (group) =>
          group.traceabilityKey ===
          'not_executed',
      ).length,

    groups,

    rows,
  }
}
