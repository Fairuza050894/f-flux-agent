const dashboardDateTimeFormatter =
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

export function parseDashboardTimestamp(
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

export function formatDashboardDateTime(
  value,
) {
  const timestamp =
    parseDashboardTimestamp(value)

  if (timestamp === null) {
    return 'Not available'
  }

  return dashboardDateTimeFormatter.format(
    new Date(timestamp),
  )
}

export function formatDashboardNumber(
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

export function formatDashboardPercentage(
  value,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return 'Not available'
  }

  const numericValue =
    Number(value)

  if (!Number.isFinite(numericValue)) {
    return 'Not available'
  }

  const percentage =
    Math.round(
      Math.min(
        100,
        Math.max(
          0,
          numericValue,
        ),
      ),
    )

  return `${percentage}%`
}

export function isSameLocalDay(
  firstTimestamp,
  secondTimestamp,
) {
  if (
    firstTimestamp === null ||
    secondTimestamp === null
  ) {
    return false
  }

  const first =
    new Date(firstTimestamp)

  const second =
    new Date(secondTimestamp)

  return (
    first.getFullYear() ===
      second.getFullYear() &&
    first.getMonth() ===
      second.getMonth() &&
    first.getDate() ===
      second.getDate()
  )
}
