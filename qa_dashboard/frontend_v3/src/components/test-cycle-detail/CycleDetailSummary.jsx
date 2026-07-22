function CycleDetailSummary({
  formatDateTime,
  items,
}) {
  return (
    <section className="cycle-detail-summary">
      {items.map((item) => (
        <div key={item.key}>
          <span>{item.label}</span>

          <strong title={String(
            item.value ?? '',
          )}
          >
            {item.valueType ===
            'datetime'
              ? formatDateTime(
                  item.value,
                )
              : item.value}
          </strong>
        </div>
      ))}
    </section>
  )
}

export default CycleDetailSummary
