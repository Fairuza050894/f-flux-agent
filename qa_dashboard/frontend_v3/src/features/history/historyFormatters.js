const historyDateTimeFormatter =
  new Intl.DateTimeFormat(
    'en-GB',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    },
  )

export function normalizeHistoryStatus(
  status,
) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll('-', '_')
    .replaceAll(' ', '_')
}

export function formatHistoryStatus(
  status,
) {
  const normalizedStatus =
    normalizeHistoryStatus(status)

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

export function getHistoryStatusTone(
  status,
) {
  const normalizedStatus =
    normalizeHistoryStatus(status)

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
      'running',
      'in_progress',
      'processing',
      'pending',
    ].includes(normalizedStatus)
  ) {
    return 'primary'
  }

  return 'neutral'
}

export function parseHistoryTimestamp(
  value,
) {
  if (!value) {
    return null
  }

  const timestamp =
    new Date(value).getTime()

  return Number.isFinite(timestamp)
    ? timestamp
    : null
}

export function formatHistoryDateTime(
  value,
) {
  const timestamp =
    parseHistoryTimestamp(value)

  if (timestamp === null) {
    return 'Not available'
  }

  return historyDateTimeFormatter.format(
    new Date(timestamp),
  )
}

export function formatHistoryDuration(
  durationMs,
) {
  const safeDuration =
    Number(durationMs)

  if (
    !Number.isFinite(safeDuration) ||
    safeDuration < 0
  ) {
    return 'Not available'
  }

  const totalSeconds = Math.floor(
    safeDuration / 1000,
  )

  if (totalSeconds < 1) {
    return '< 1s'
  }

  if (totalSeconds < 60) {
    return `${totalSeconds}s`
  }

  const totalMinutes = Math.floor(
    totalSeconds / 60,
  )

  const seconds =
    totalSeconds % 60

  if (totalMinutes < 60) {
    return seconds > 0
      ? `${totalMinutes}m ${seconds}s`
      : `${totalMinutes}m`
  }

  const hours = Math.floor(
    totalMinutes / 60,
  )

  const minutes =
    totalMinutes % 60

  return minutes > 0
    ? `${hours}h ${minutes}m`
    : `${hours}h`
}

export function formatHistoryResultCount(
  value,
) {
  const numericValue =
    Number(value)

  if (!Number.isFinite(numericValue)) {
    return '0'
  }

  return Math.max(
    0,
    Math.round(numericValue),
  ).toLocaleString('en-GB')
}
