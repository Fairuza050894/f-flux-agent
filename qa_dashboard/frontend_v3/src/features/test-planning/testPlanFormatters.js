import {
  TEST_PLAN_SCOPE_OPTIONS,
} from './testPlanConstants'

export function getTestPlanStatusTone(
  status,
) {
  switch (status) {
    case 'Ready':
      return 'success'

    case 'Draft':
      return 'warning'

    case 'Archived':
      return 'neutral'

    default:
      return 'neutral'
  }
}

export function formatTestPlanDate(
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

export function formatTestPlanScope(
  scope,
) {
  const labels =
    TEST_PLAN_SCOPE_OPTIONS
      .filter(
        (option) =>
          Boolean(
            scope?.[option.key],
          ),
      )
      .map(
        (option) =>
          option.label,
      )

  return labels.length > 0
    ? labels.join(', ')
    : 'No testing scope'
}

export function formatTestPlanAssetCount(
  selectedAssetIds,
) {
  const count =
    Array.isArray(
      selectedAssetIds,
    )
      ? selectedAssetIds.length
      : 0

  return count === 1
    ? '1 Test Asset'
    : `${count} Test Assets`
}
