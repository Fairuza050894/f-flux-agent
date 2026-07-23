export const TEST_ASSET_TYPES = [
  {
    value: 'ui',
    label: 'UI',
  },
  {
    value: 'api',
    label: 'API',
  },
  {
    value: 'unit',
    label: 'Unit',
  },
  {
    value: 'e2e',
    label: 'E2E',
  },
  {
    value: 'regression',
    label: 'Regression',
  },
]

export const TEST_ASSET_PRIORITIES = [
  'Critical',
  'High',
  'Medium',
  'Low',
]

export const TEST_ASSET_AUTOMATION_STATUSES = [
  'Draft',
  'Manual',
  'Connected',
  'Automated',
]

export const TEST_ASSET_FILTER_DEFAULTS = {
  automationStatus: 'all',
  executionReady: 'all',
  priority: 'all',
  projectId: 'all',
  recommended: 'all',
  searchTerm: '',
  type: 'all',
}

export const TEST_ASSET_EMPTY_FORM = {
  projectId: '',
  name: '',
  type: 'ui',
  module: '',
  feature: '',
  priority: 'Medium',
  automationStatus: 'Draft',
  recommended: false,
  executionReady: false,
  description: '',
  preconditions: '',
  steps: [],
  expectedResult: '',
}
