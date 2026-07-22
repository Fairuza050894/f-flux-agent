import { Link } from 'react-router-dom'

import {
  formatDashboardNumber,
} from '../../features/dashboard/dashboardFormatters'

function DashboardAttention({
  rows,
}) {
  const totalAttention =
    rows.reduce(
      (total, row) =>
        total +
        Number(row.value ?? 0),
      0,
    )

  return (
    <section className="dashboard-panel main-dashboard-panel main-dashboard-attention-panel">
      <header className="main-dashboard-panel-header">
        <div>
          <span className="panel-eyebrow">
            ACTION REQUIRED
          </span>

          <h3>Attention Required</h3>

          <p>
            Recorded quality issues and runner
            limitations requiring review.
          </p>
        </div>

        <Link
          className="text-link"
          to="/reports"
        >
          Open reports
        </Link>
      </header>

      {totalAttention > 0 ? (
        <div className="main-dashboard-attention-list">
          {rows.map((row) => (
            <article
              className="main-dashboard-attention-row"
              key={row.key}
            >
              <strong
                className={`main-dashboard-attention-value main-dashboard-attention-value-${row.tone}`}
              >
                {formatDashboardNumber(
                  row.value,
                )}
              </strong>

              <div>
                <strong>{row.label}</strong>

                <p>
                  {row.description}
                </p>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="main-dashboard-empty main-dashboard-empty-compact">
          <strong>
            No recorded attention items
          </strong>

          <p>
            Current stored results contain no
            failures, review items, bugs, or
            execution errors.
          </p>
        </div>
      )}
    </section>
  )
}

export default DashboardAttention
