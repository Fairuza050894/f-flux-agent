import {
  Link,
} from 'react-router-dom'

import StatusBadge from '../StatusBadge'

import {
  formatTestPlanAssetCount,
  formatTestPlanDate,
  formatTestPlanScope,
  getTestPlanStatusTone,
} from '../../features/test-planning/testPlanFormatters'

function TestPlanTable({
  cycleReadiness,
  environmentNames,
  emptyMessage,
  onArchive,
  onCreateCycle,
  onDelete,
  onEdit,
  onRestore,
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
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {plans.length > 0 ? (
            plans.map((plan) => {
              const isArchived =
                plan.status === 'Archived'

              const readiness =
                cycleReadiness[
                  plan.id
                ]

              const createCycleTitle =
                readiness?.isReady
                  ? 'Create a Test Cycle from this plan.'
                  : readiness?.issues
                      ?.join(' ') ||
                    'This Test Plan is not ready.'

              return (
                <tr key={plan.id}>
                  <td>
                    <Link
                      className="test-plan-name-link"
                      to={`/test-planning/${plan.id}`}
                    >
                      {plan.name ||
                        'Untitled Test Plan'}
                    </Link>

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

                  <td>
                    <div className="test-plan-row-actions">
                      <button
                        className="button button-primary test-plan-action-button"
                        disabled={
                          !readiness?.isReady
                        }
                        onClick={() =>
                          onCreateCycle(plan)
                        }
                        title={
                          createCycleTitle
                        }
                        type="button"
                      >
                        Create Cycle
                      </button>

                      <button
                        className="button button-secondary test-plan-action-button"
                        disabled={isArchived}
                        onClick={() =>
                          onEdit(plan)
                        }
                        title={
                          isArchived
                            ? 'Restore the plan before editing it.'
                            : undefined
                        }
                        type="button"
                      >
                        Edit
                      </button>

                      {isArchived ? (
                        <button
                          className="button button-secondary test-plan-action-button"
                          onClick={() =>
                            onRestore(plan)
                          }
                          type="button"
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          className="button button-secondary test-plan-action-button"
                          onClick={() =>
                            onArchive(plan)
                          }
                          type="button"
                        >
                          Archive
                        </button>
                      )}

                      <button
                        className="button test-plan-delete-button test-plan-action-button"
                        onClick={() =>
                          onDelete(plan)
                        }
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })
          ) : (
            <tr>
              <td
                className="test-plan-empty-cell"
                colSpan="9"
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
