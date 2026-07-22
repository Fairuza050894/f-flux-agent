function ActivityEmptyState() {
  return (
    <div className="cycle-empty-state">
      <strong>
        No activity available
      </strong>

      <p>
        Lifecycle events will appear when
        the Test Cycle or execution records
        provide timestamps.
      </p>
    </div>
  )
}

function CycleActivityTab({
  formatDateTime,
  items,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            AUDIT ACTIVITY
          </span>

          <h3>Activity</h3>

          <p>
            Recorded lifecycle events from
            the Test Cycle and its
            executions.
          </p>
        </div>
      </div>

      {items.length === 0 ? (
        <ActivityEmptyState />
      ) : (
        <div className="cycle-activity-list cycle-activity-timeline">
          {items.map((item) => (
            <article
              className={[
                'cycle-activity-item',
                `cycle-activity-item-${item.tone}`,
              ].join(' ')}
              key={item.id}
            >
              <span
                aria-hidden="true"
                className="cycle-activity-dot"
              />

              <div className="cycle-activity-content">
                <strong>
                  {item.title}
                </strong>

                <p>
                  {item.description}
                </p>
              </div>

              <time
                dateTime={String(
                  item.timestamp,
                )}
              >
                {formatDateTime(
                  item.timestamp,
                )}
              </time>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default CycleActivityTab
