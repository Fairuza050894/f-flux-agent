export function getTestAssetPriorityTone(
  priority,
) {
  switch (priority) {
    case 'Critical':
      return 'danger'

    case 'High':
      return 'warning'

    case 'Medium':
      return 'primary'

    default:
      return 'neutral'
  }
}

export function getTestAssetAutomationTone(
  status,
) {
  switch (status) {
    case 'Automated':
      return 'success'

    case 'Connected':
      return 'primary'

    case 'Draft':
      return 'warning'

    default:
      return 'neutral'
  }
}

export function getTestAssetReadyTone(
  executionReady,
) {
  return executionReady
    ? 'success'
    : 'warning'
}

export function formatTestAssetDate(
  value,
) {
  if (!value) {
    return 'Not available'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Not available'
  }

  return date.toLocaleString()
}
