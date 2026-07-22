export const HISTORY_FILTER_ALL = 'all'

export const HISTORY_DEFAULT_FILTERS =
  Object.freeze({
    search: '',
    projectId: HISTORY_FILTER_ALL,
    environmentId: HISTORY_FILTER_ALL,
    cycleType: HISTORY_FILTER_ALL,
    status: HISTORY_FILTER_ALL,
  })

export const HISTORY_STATUS_OPTIONS =
  Object.freeze([
    {
      value: HISTORY_FILTER_ALL,
      label: 'All statuses',
    },
    {
      value: 'ready',
      label: 'Ready',
    },
    {
      value: 'queued',
      label: 'Queued',
    },
    {
      value: 'running',
      label: 'Running',
    },
    {
      value: 'passed',
      label: 'Passed',
    },
    {
      value: 'completed',
      label: 'Completed',
    },
    {
      value: 'need_review',
      label: 'Need Review',
    },
    {
      value: 'failed',
      label: 'Failed',
    },
    {
      value: 'cancelled',
      label: 'Cancelled',
    },
  ])

export const HISTORY_CYCLE_TYPE_OPTIONS =
  Object.freeze([
    {
      value: HISTORY_FILTER_ALL,
      label: 'All cycle types',
    },
    {
      value: 'Full Product Cycle',
      label: 'Full Product Cycle',
    },
    {
      value: 'Feature Cycle',
      label: 'Feature Cycle',
    },
    {
      value: 'Change Cycle',
      label: 'Change Cycle',
    },
  ])

export const HISTORY_COMPLETED_STATUSES =
  Object.freeze([
    'passed',
    'completed',
  ])

export const HISTORY_ACTIVE_STATUSES =
  Object.freeze([
    'queued',
    'running',
    'in_progress',
    'processing',
    'pending',
  ])

export const HISTORY_FAILED_STATUSES =
  Object.freeze([
    'failed',
    'error',
  ])
