import StatusBadge from '../StatusBadge'

function TestPlanReadinessPanel({
  assetHealth,
  readiness,
}) {
  return (
    <section className="dashboard-panel test-plan-detail-section">
      <div className="test-plan-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            READINESS
          </span>

          <h3>Cycle Readiness</h3>

          <p>
            Validation performed before this
            plan can create a Test Cycle.
          </p>
        </div>

        <StatusBadge
          tone={
            readiness.isReady
              ? 'success'
              : 'warning'
          }
        >
          {readiness.isReady
            ? 'Ready to Create'
            : 'Needs Attention'}
        </StatusBadge>
      </div>

      <div className="test-plan-readiness-metrics">
        <div>
          <span>Selected Assets</span>

          <strong>
            {assetHealth.total}
          </strong>
        </div>

        <div>
          <span>Execution Ready</span>

          <strong>
            {assetHealth.usable}
          </strong>
        </div>

        <div>
          <span>Asset Issues</span>

          <strong>
            {assetHealth.issueCount}
          </strong>
        </div>
      </div>

      {readiness.isReady ? (
        <div className="test-plan-readiness-success">
          <strong>
            All required configuration is
            available.
          </strong>

          <p>
            A Test Cycle draft can be created
            using the valid assets and current
            execution settings.
          </p>
        </div>
      ) : (
        <div className="test-plan-readiness-issues">
          <strong>
            Resolve the following issues:
          </strong>

          <ul>
            {readiness.issues.map(
              (issue) => (
                <li key={issue}>
                  {issue}
                </li>
              ),
            )}
          </ul>
        </div>
      )}

      {assetHealth.issueCount > 0 && (
        <div className="test-plan-readiness-advisory">
          <strong>
            Asset references require review
          </strong>

          <p>
            {assetHealth.issueCount}{' '}
            selected asset reference
            {assetHealth.issueCount === 1
              ? ''
              : 's'}{' '}
            will not be included in a new
            Test Cycle draft.
          </p>
        </div>
      )}
    </section>
  )
}

export default TestPlanReadinessPanel
