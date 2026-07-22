export function normalizeResultStatus(
  status,
) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll('-', '_')
    .replaceAll(' ', '_')
}

export function formatResultStatus(
  status,
) {
  const normalizedStatus =
    normalizeResultStatus(status)

  if (!normalizedStatus) {
    return 'Unknown'
  }

  return normalizedStatus
    .split('_')
    .filter(Boolean)
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1),
    )
    .join(' ')
}

export function getResultStatusTone(
  status,
) {
  const normalizedStatus =
    normalizeResultStatus(status)

  if (
    [
      'passed',
      'completed',
    ].includes(normalizedStatus)
  ) {
    return 'success'
  }

  if (
    [
      'failed',
      'error',
    ].includes(normalizedStatus)
  ) {
    return 'danger'
  }

  if (
    normalizedStatus === 'need_review'
  ) {
    return 'warning'
  }

  if (
    [
      'queued',
      'pending',
      'created',
      'running',
      'in_progress',
      'processing',
    ].includes(normalizedStatus)
  ) {
    return 'primary'
  }

  return 'neutral'
}

export function normalizeResultCount(
  value,
) {
  const numericValue =
    Number(value)

  if (!Number.isFinite(numericValue)) {
    return 0
  }

  return Math.max(
    0,
    Math.round(numericValue),
  )
}

export function clampResultPercentage(
  value,
) {
  const numericValue =
    Number(value)

  if (!Number.isFinite(numericValue)) {
    return 0
  }

  return Math.round(
    Math.min(
      100,
      Math.max(
        0,
        numericValue,
      ),
    ),
  )
}

export function calculatePassRate(
  metrics,
) {
  const passed =
    normalizeResultCount(
      metrics?.passed,
    )

  const failed =
    normalizeResultCount(
      metrics?.failed,
    )

  const needReview =
    normalizeResultCount(
      metrics?.needReview,
    )

  const executed =
    passed +
    failed +
    needReview

  if (executed === 0) {
    return null
  }

  return Math.round(
    (passed / executed) * 100,
  )
}

export function formatPassRate(
  passRate,
) {
  if (
    passRate === null ||
    passRate === undefined
  ) {
    return 'Not available'
  }

  return `${
    clampResultPercentage(
      passRate,
    )
  }%`
}
