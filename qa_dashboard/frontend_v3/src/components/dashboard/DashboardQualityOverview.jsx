import {
  formatDashboardNumber,
  formatDashboardPercentage,
} from '../../features/dashboard/dashboardFormatters'

function DashboardQualityOverview({
  rows,
  summary,
}) {
  return (
    <section className="dashboard-panel main-dashboard-panel main-dashboard-quality-panel">
      <header className="main-dashboard-panel-header">
        <div>
          <span className="panel-eyebrow">
            QUALITY OVERVIEW
          </span>

          <h3>Execution Results</h3>
        </div>

        <strong className="main-dashboard-header-value">
          {formatDashboardPercentage(
            summary.passRate,
          )}
        </strong>
      </header>

      <div className="main-dashboard-quality-list">
        {rows.map((row) => (
          <div
            className="main-dashboard-quality-row"
            key={row.key}
          >
            <div>
              <span
                aria-hidden="true"
                className={[
                  'main-dashboard-quality-indicator',
                  `main-dashboard-quality-indicator-${row.tone}`,
                ].join(' ')}
              />

              <span>{row.label}</span>
            </div>

            <div className="main-dashboard-quality-track">
              <span
                className={`main-dashboard-quality-fill-${row.tone}`}
                style={{
                  width:
                    `${row.percentage}%`,
                }}
              />
            </div>

            <strong>
              {formatDashboardNumber(
                row.value,
              )}
            </strong>
          </div>
        ))}
      </div>

      <footer className="main-dashboard-quality-footer">
        <span>Executed tests</span>

        <strong>
          {formatDashboardNumber(
            summary.totalExecuted,
          )}
        </strong>
      </footer>
    </section>
  )
}

export default DashboardQualityOverview
