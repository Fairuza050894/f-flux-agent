function sanitizeFileName(
  value,
  fallback,
) {
  const normalized =
    String(value ?? '')
      .trim()
      .replace(
        /[^a-zA-Z0-9._-]+/g,
        '-',
      )
      .replace(
        /^[-._]+|[-._]+$/g,
        '',
      )

  return normalized || fallback
}

function downloadBlob(
  blob,
  fileName,
) {
  const url =
    URL.createObjectURL(
      blob,
    )

  const link =
    document.createElement(
      'a',
    )

  link.href = url
  link.download = fileName
  link.style.display = 'none'

  document.body.appendChild(
    link,
  )

  link.click()
  link.remove()

  window.setTimeout(
    () => {
      URL.revokeObjectURL(
        url,
      )
    },
    0,
  )
}

function escapeCsvValue(
  value,
) {
  const text =
    value === null ||
    value === undefined
      ? ''
      : String(value)

  if (
    /[",\r\n]/.test(text)
  ) {
    return `"${text.replaceAll(
      '"',
      '""',
    )}"`
  }

  return text
}

export function getReportFileBaseName(
  report,
) {
  return sanitizeFileName(
    report?.fileBaseName,
    'qa-report',
  )
}

export function downloadReportJson(
  report,
) {
  const content =
    JSON.stringify(
      report,
      null,
      2,
    )

  downloadBlob(
    new Blob(
      [
        `${content}\n`,
      ],
      {
        type:
          'application/json;charset=utf-8',
      },
    ),
    `${getReportFileBaseName(
      report,
    )}.json`,
  )
}

export function buildReportCsv(
  report,
) {
  const header = [
    'cycle_id',
    'cycle_name',
    'project',
    'environment',
    'release_decision',
    'run_id',
    'scope',
    'status',
    'attempt',
    'execution_reason',
    'target_asset_count',
    'passed',
    'failed',
    'need_review',
    'skipped',
    'blocked',
    'bugs_found',
    'warnings',
    'started_at',
    'completed_at',
  ]

  const cycle =
    report?.cycle ?? {}

  const project =
    report?.project ?? {}

  const environment =
    report?.environment ?? {}

  const decision =
    report?.releaseDecision ?? {}

  const executions =
    Array.isArray(
      report?.executions,
    )
      ? report.executions
      : []

  const rows =
    executions.length > 0
      ? executions.map(
          (execution) => {
            const metrics =
              execution.metrics ?? {}

            const targetAssetIds =
              Array.isArray(
                execution
                  .targetAssetIds,
              )
                ? execution
                    .targetAssetIds
                : []

            return [
              cycle.id,
              cycle.name,
              project.name,
              environment.name,
              decision.status,
              execution.runId,
              execution.scopeLabel,
              execution.statusLabel,
              execution.attemptNumber,
              execution
                .executionReasonLabel,
              targetAssetIds.length,
              metrics.passed ?? 0,
              metrics.failed ?? 0,
              metrics.needReview ?? 0,
              metrics.skipped ?? 0,
              metrics.blocked ?? 0,
              metrics.bugsFound ?? 0,
              metrics.warnings ?? 0,
              execution.startedAt,
              execution.completedAt,
            ]
          },
        )
      : [
          [
            cycle.id,
            cycle.name,
            project.name,
            environment.name,
            decision.status,
          ],
        ]

  return [
    header,
    ...rows,
  ]
    .map(
      (row) =>
        row
          .map(
            escapeCsvValue,
          )
          .join(','),
    )
    .join('\r\n')
}

export function downloadReportCsv(
  report,
) {
  downloadBlob(
    new Blob(
      [
        '\uFEFF',
        buildReportCsv(
          report,
        ),
      ],
      {
        type:
          'text/csv;charset=utf-8',
      },
    ),
    `${getReportFileBaseName(
      report,
    )}.csv`,
  )
}

export function saveReportBlob(
  blob,
  fileName,
) {
  downloadBlob(
    blob,
    sanitizeFileName(
      fileName,
      'qa-report',
    ),
  )
}
