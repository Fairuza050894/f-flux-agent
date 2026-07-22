import {
  formatReportNumber,
  formatReportPercentage,
} from '../../features/reports/reportFormatters'

const reportSummaryItems = [
  {
    key: 'cycleCount',
    label: 'Test Cycles',
    tone: 'neutral',
    formatter:
      formatReportNumber,
  },
  {
    key: 'executionCount',
    label: 'Executions',
    tone: 'primary',
    formatter:
      formatReportNumber,
  },
  {
    key: 'totalExecuted',
    label: 'Executed Tests',
    tone: 'neutral',
    formatter:
      formatReportNumber,
  },
  {
    key: 'passRate',
    label: 'Pass Rate',
    tone: 'success',
    formatter:
      formatReportPercentage,
  },
  {
    key: 'failed',
    label: 'Failed',
    tone: 'danger',
    formatter:
      formatReportNumber,
  },
  {
    key: 'needReview',
    label: 'Need Review',
    tone: 'warning',
    formatter:
      formatReportNumber,
  },
]

function ReportSummary({
  summary,
}) {
  return (
    <dl
      aria-label="Consolidated report summary"
      className="report-summary"
    >
      {reportSummaryItems.map(
        (item) => (
          <div
            className={[
              'report-summary-item',
              `report-summary-item-${item.tone}`,
            ].join(' ')}
            key={item.key}
          >
            <dt>{item.label}</dt>

            <dd>
              {item.formatter(
                summary[item.key],
              )}
            </dd>
          </div>
        ),
      )}
    </dl>
  )
}

export default ReportSummary
