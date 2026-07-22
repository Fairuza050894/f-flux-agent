const reportDateTimeFormatter =
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

export function parseReportTimestamp(
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

export function formatReportDateTime(
  value,
) {
  const timestamp =
    parseReportTimestamp(value)

  if (timestamp === null) {
    return 'Not available'
  }

  return reportDateTimeFormatter.format(
    new Date(timestamp),
  )
}

export function formatReportNumber(
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

export function formatReportPercentage(
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
