function TestPlanMetrics({
  metrics,
}) {
  const items = [
    {
      key: 'total',
      label: 'Total Plans',
      value: metrics.total,
    },
    {
      key: 'ready',
      label: 'Ready',
      value: metrics.ready,
    },
    {
      key: 'draft',
      label: 'Draft',
      value: metrics.draft,
    },
    {
      key: 'archived',
      label: 'Archived',
      value: metrics.archived,
    },
    {
      key: 'linked-assets',
      label: 'Linked Assets',
      value: metrics.linkedAssets,
    },
  ]

  return (
    <section
      aria-label="Test Plan metrics"
      className="test-plan-metric-grid"
    >
      {items.map((item) => (
        <div
          className="test-plan-metric"
          key={item.key}
        >
          <span>{item.label}</span>

          <strong>
            {item.value}
          </strong>
        </div>
      ))}
    </section>
  )
}

export default TestPlanMetrics
