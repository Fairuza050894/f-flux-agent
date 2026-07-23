import {
  Link,
} from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatTestPlanDate,
  getTestPlanStatusTone,
} from '../../features/test-planning/testPlanFormatters'

function TestAssetLinkedPlans({
  plans,
}) {
  return (
    <section className="dashboard-panel test-asset-detail-section">
      <div className="test-asset-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            USAGE
          </span>

          <h3>Linked Test Plans</h3>

          <p>
            Reusable Test Plans that currently
            reference this Test Asset.
          </p>
        </div>

        <strong className="test-asset-detail-count">
          {plans.length} Plans
        </strong>
      </div>

      <div className="test-asset-linked-table-wrapper">
        <table className="test-asset-linked-table">
          <thead>
            <tr>
              <th>Test Plan</th>
              <th>Status</th>
              <th>Cycle Type</th>
              <th>Module / Feature</th>
              <th>Updated</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {plans.length > 0 ? (
              plans.map((plan) => (
                <tr key={plan.id}>
                  <td>
                    <strong>
                      {plan.name ||
                        'Untitled Test Plan'}
                    </strong>

                    <span>{plan.id}</span>
                  </td>

                  <td>
                    <StatusBadge
                      tone={getTestPlanStatusTone(
                        plan.status,
                      )}
                    >
                      {plan.status}
                    </StatusBadge>
                  </td>

                  <td>
                    {plan.cycleType}
                  </td>

                  <td>
                    <strong>
                      {plan.module ||
                        'Not configured'}
                    </strong>

                    <span>
                      {plan.feature ||
                        'Not configured'}
                    </span>
                  </td>

                  <td>
                    {formatTestPlanDate(
                      plan.updatedAt,
                    )}
                  </td>

                  <td>
                    <Link
                      className="button button-secondary test-asset-action-button"
                      to={`/test-planning/${plan.id}`}
                    >
                      View Plan
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  className="test-asset-linked-empty"
                  colSpan="6"
                >
                  <strong>
                    No linked Test Plans
                  </strong>

                  <span>
                    This asset is not currently
                    referenced by a Test Plan.
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

export default TestAssetLinkedPlans
