export const REPORT_FILTER_ALL = 'all'

export const REPORT_DEFAULT_FILTERS =
  Object.freeze({
    search: '',
    projectId: REPORT_FILTER_ALL,
    environmentId: REPORT_FILTER_ALL,
    cycleType: REPORT_FILTER_ALL,
    qualityStatus: REPORT_FILTER_ALL,
    period: REPORT_FILTER_ALL,
  })

export const REPORT_CYCLE_TYPE_OPTIONS =
  Object.freeze([
    {
      value: REPORT_FILTER_ALL,
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

export const REPORT_QUALITY_STATUS_OPTIONS =
  Object.freeze([
    {
      value: REPORT_FILTER_ALL,
      label: 'All quality statuses',
    },
    {
      value: 'passed',
      label: 'Passed',
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
      value: 'no_results',
      label: 'No Results',
    },
  ])

export const REPORT_PERIOD_OPTIONS =
  Object.freeze([
    {
      value: REPORT_FILTER_ALL,
      label: 'All time',
    },
    {
      value: '7',
      label: 'Last 7 days',
    },
    {
      value: '30',
      label: 'Last 30 days',
    },
    {
      value: '90',
      label: 'Last 90 days',
    },
  ])
