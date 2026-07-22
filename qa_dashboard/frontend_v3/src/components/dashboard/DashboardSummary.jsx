import {
  formatDashboardNumber,
  formatDashboardPercentage,
} from '../../features/dashboard/dashboardFormatters'

const dashboardSummaryItems = [
  {
    key: 'activeCycles',
    label: 'Active Cycles',
    tone: 'primary',
    formatter:
      formatDashboardNumber,
  },
  {
    key: 'passRate',
    label: 'Pass Rate',
    tone: 'success',
    formatter:
      formatDashboardPercentage,
  },
  {
    key: 'needAttention',
    label: 'Need Attention',
    tone: 'danger',
    formatter:
      formatDashboardNumber,
  },
  {
    key: 'completedToday',
    label: 'Completed Today',
    tone: 'neutral',
    formatter:
      formatDashboardNumber,
  },
]

function DashboardSummary({
  summary,
}) {
  return (
    <dl
      aria-label="Quality operations summary"
      className="main-dashboard-summary"
    >
      {dashboardSummaryItems.map(
        (item) => (
          <div
            className={[
              'main-dashboard-summary-item',
              `main-dashboard-summary-item-${item.tone}`,
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

export default DashboardSummary
