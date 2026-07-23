import StatusBadge from '../StatusBadge'

function TestPlanAssetCoverage({
  assetHealth,
}) {
  return (
    <section className="dashboard-panel test-plan-detail-section">
      <div className="test-plan-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            COVERAGE
          </span>

          <h3>Linked Test Assets</h3>

          <p>
            Current health of every Test Asset
            referenced by this plan.
          </p>
        </div>

        <strong className="test-plan-detail-count">
          {assetHealth.total} Assets
        </strong>
      </div>

      <div className="test-plan-detail-table-wrapper">
        <table className="test-plan-detail-table test-plan-asset-health-table">
          <thead>
            <tr>
              <th>Test Asset</th>
              <th>Type</th>
              <th>Module / Feature</th>
              <th>Priority</th>
              <th>Automation</th>
              <th>Health</th>
              <th>Reason</th>
            </tr>
          </thead>

          <tbody>
            {assetHealth.rows.length > 0 ? (
              assetHealth.rows.map(
                (row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>
                        {row.name}
                      </strong>

                      <span>
                        {row.id}
                      </span>
                    </td>

                    <td>
                      {row.typeLabel}
                    </td>

                    <td>
                      <strong>
                        {row.module}
                      </strong>

                      <span>
                        {row.feature}
                      </span>
                    </td>

                    <td>
                      {row.priority}
                    </td>

                    <td>
                      {
                        row.automationStatus
                      }
                    </td>

                    <td>
                      <StatusBadge
                        tone={
                          row.healthTone
                        }
                      >
                        {row.healthLabel}
                      </StatusBadge>
                    </td>

                    <td>
                      <span className="test-plan-health-reason">
                        {row.reason}
                      </span>
                    </td>
                  </tr>
                ),
              )
            ) : (
              <tr>
                <td
                  className="test-plan-detail-empty-cell"
                  colSpan="7"
                >
                  <strong>
                    No Test Assets linked
                  </strong>

                  <span>
                    Edit the Test Plan to
                    select reusable Test Assets.
                  </span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default TestPlanAssetCoverage
