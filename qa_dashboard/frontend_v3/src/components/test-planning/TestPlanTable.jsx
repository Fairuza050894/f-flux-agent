import StatusBadge from '../StatusBadge'

import {
  formatTestPlanAssetCount,
  formatTestPlanDate,
  formatTestPlanScope,
  getTestPlanStatusTone,
} from '../../features/test-planning/testPlanFormatters'

function TestPlanTable({
  environmentNames,
  emptyMessage,
  plans,
  projectNames,
}) {
  return (
    <div className="test-plan-table-wrapper">
      <table className="test-plan-table">
        <thead>
          <tr>
            <th>Test Plan</th>
            <th>Project / Environment</th>
            <th>Status</th>
            <th>Cycle Type</th>
            <th>Testing Scope</th>
            <th>Test Assets</th>
            <th>Execution</th>
            <th>Updated</th>
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
                  <strong>
                    {projectNames[
                      plan.projectId
                    ] ?? 'Unknown Project'}
                  </strong>

                  <span>
                    {environmentNames[
                      plan.environmentId
                    ] ?? 'No default environment'}
                  </span>
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
                  <strong>
                    {plan.cycleType}
                  </strong>

                  <span>
                    {plan.module ||
                      'No module'}
                    {' / '}
                    {plan.feature ||
                      'No feature'}
                  </span>
                </td>

                <td>
                  <span className="test-plan-scope-text">
                    {formatTestPlanScope(
                      plan.scope,
                    )}
                  </span>
                </td>

                <td>
                  <strong>
                    {formatTestPlanAssetCount(
                      plan.selectedAssetIds,
                    )}
                  </strong>
                </td>

                <td>
                  <strong>
                    {
                      plan.executionSettings
                        .executionMode
                    }
                  </strong>

                  <span>
                    {
                      plan.executionSettings
                        .stopPolicy
                    }
                  </span>
                </td>

                <td>
                  <span className="test-plan-date">
                    {formatTestPlanDate(
                      plan.updatedAt,
                    )}
                  </span>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                className="test-plan-empty-cell"
                colSpan="8"
              >
                <strong>
                  No Test Plans available
                </strong>

                <span>{emptyMessage}</span>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default TestPlanTable
