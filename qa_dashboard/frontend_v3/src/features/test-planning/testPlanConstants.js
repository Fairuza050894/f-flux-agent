export const TEST_PLAN_STORE_VERSION = 2

export const TEST_PLAN_STATUSES = [
  'Draft',
  'Ready',
  'Archived',
]

export const TEST_PLAN_CYCLE_TYPES = [
  'Full Product Cycle',
  'Feature Cycle',
  'Change Cycle',
]

export const TEST_PLAN_SCOPE_OPTIONS = [
  {
    key: 'ui',
    label: 'UI Testing',
  },
  {
    key: 'api',
    label: 'API Testing',
  },
  {
    key: 'unit',
    label: 'Unit Testing',
  },
  {
    key: 'e2e',
    label: 'E2E Testing',
  },
  {
    key: 'regression',
    label: 'Related Regression',
  },
]

export const TEST_PLAN_EXECUTION_MODES = [
  'Sequential',
  'Parallel',
]

export const TEST_PLAN_STOP_POLICIES = [
  'Continue',
  'Critical Failure',
  'Immediate',
]

export const TEST_PLAN_FILTER_DEFAULTS = {
  projectId: 'all',
  scopeType: 'all',
  searchTerm: '',
  status: 'all',
}

export const TEST_PLAN_DEFAULT_SCOPE = {
  ui: true,
  api: true,
  unit: false,
  e2e: true,
  regression: true,
}

export const TEST_PLAN_DEFAULT_EXECUTION_SETTINGS = {
  executionMode: 'Sequential',
  stopPolicy: 'Critical Failure',
  screenshot: true,
  video: false,
  consoleLogs: true,
  networkLogs: true,
  errorLogs: true,
  telegramTesting: true,
  telegramDocumentation: true,
}

export const TEST_PLAN_EMPTY_FORM = {
  name: '',
  projectId: '',
  environmentId: '',
  objective: '',
  cycleType: 'Feature Cycle',
  module: '',
  feature: '',
  scope: {
    ...TEST_PLAN_DEFAULT_SCOPE,
  },
  selectedAssetIds: [],
  selectedAssetSnapshots: [],
  executionSettings: {
    ...TEST_PLAN_DEFAULT_EXECUTION_SETTINGS,
  },
  status: 'Draft',
}
