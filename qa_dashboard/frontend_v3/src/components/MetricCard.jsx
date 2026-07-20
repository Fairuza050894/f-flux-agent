function MetricCard({
  label,
  value,
  detail,
  tone = 'neutral',
}) {
  return (
    <article className="metric-card">
      <div className="metric-card-header">
        <span>{label}</span>

        <span
          aria-hidden="true"
          className={`metric-card-indicator metric-card-indicator-${tone}`}
        />
      </div>

      <strong className="metric-card-value">
        {value}
      </strong>

      <p>{detail}</p>
    </article>
  )
}

export default MetricCard
