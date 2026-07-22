const summaryItems = [
  {
    key: 'total',
    label: 'Total Cycles',
    tone: 'neutral',
  },
  {
    key: 'completed',
    label: 'Completed',
    tone: 'success',
  },
  {
    key: 'running',
    label: 'Running',
    tone: 'primary',
  },
  {
    key: 'needReview',
    label: 'Need Review',
    tone: 'warning',
  },
  {
    key: 'failed',
    label: 'Failed',
    tone: 'danger',
  },
]

function HistorySummary({
  summary,
}) {
  return (
    <dl
      aria-label="History summary"
      className="history-summary"
    >
      {summaryItems.map((item) => (
        <div
          className={[
            'history-summary-item',
            `history-summary-item-${item.tone}`,
          ].join(' ')}
          key={item.key}
        >
          <dt>{item.label}</dt>

          <dd>
            {summary[item.key] ?? 0}
          </dd>
        </div>
      ))}
    </dl>
  )
}

export default HistorySummary
