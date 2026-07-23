function TestAssetMetrics({
  metrics,
}) {
  const items = [
    {
      key: 'total',
      label: 'Total Assets',
      value: metrics.total,
    },
    {
      key: 'execution-ready',
      label: 'Execution Ready',
      value: metrics.executionReady,
    },
    {
      key: 'automated',
      label: 'Automated',
      value: metrics.automated,
    },
    {
      key: 'recommended',
      label: 'Recommended',
      value: metrics.recommended,
    },
    {
      key: 'draft',
      label: 'Draft',
      value: metrics.draft,
    },
  ]

  return (
    <section
      aria-label="Test Asset metrics"
      className="test-asset-metric-grid"
    >
      {items.map((item) => (
        <div
          className="test-asset-metric"
          key={item.key}
        >
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </section>
  )
}

export default TestAssetMetrics
