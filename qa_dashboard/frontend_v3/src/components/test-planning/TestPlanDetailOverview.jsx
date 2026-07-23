import StatusBadge from '../StatusBadge'

import {
  formatTestPlanDate,
  getTestPlanStatusTone,
} from '../../features/test-planning/testPlanFormatters'

function renderList(
  values,
  emptyLabel,
) {
  return values.length > 0
    ? values.join(', ')
    : emptyLabel
}

function TestPlanDetailOverview({
  model,
}) {
  const {
    environment,
    evidenceLabels,
    notificationLabels,
    plan,
    project,
    scopeLabels,
  } = model

  return (
    <section className="dashboard-panel test-plan-detail-section">
      <div className="test-plan-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            OVERVIEW
          </span>

          <h3>Plan Configuration</h3>

          <p>
            Reusable configuration used to
            prepare Test Cycle drafts.
          </p>
        </div>

        <StatusBadge
          tone={getTestPlanStatusTone(
            plan.status,
          )}
        >
          {plan.status}
        </StatusBadge>
      </div>

      <div className="test-plan-detail-info-grid">
        <div>
          <span>Project</span>

          <strong>
            {project?.name ??
              'Project unavailable'}
          </strong>
        </div>

        <div>
          <span>Default Environment</span>

          <strong>
            {environment?.name ??
              'Not configured'}
          </strong>
        </div>

        <div>
          <span>Cycle Type</span>

          <strong>
            {plan.cycleType}
          </strong>
        </div>

        <div>
          <span>Module / Feature</span>

          <strong>
            {plan.module ||
              'Not configured'}
            {' / '}
            {plan.feature ||
              'Not configured'}
          </strong>
        </div>

        <div>
          <span>Created</span>

          <strong>
            {formatTestPlanDate(
              plan.createdAt,
            )}
          </strong>
        </div>

        <div>
          <span>Last Updated</span>

          <strong>
            {formatTestPlanDate(
              plan.updatedAt,
            )}
          </strong>
        </div>
      </div>

      <div className="test-plan-detail-description">
        <span>Test Objective</span>

        <p>
          {plan.objective ||
            'No objective has been provided.'}
        </p>
      </div>

      <div className="test-plan-detail-configuration-grid">
        <div>
          <span>Testing Scope</span>

          <strong>
            {renderList(
              scopeLabels,
              'No testing scope',
            )}
          </strong>
        </div>

        <div>
          <span>Execution Mode</span>

          <strong>
            {
              plan.executionSettings
                .executionMode
            }
          </strong>
        </div>

        <div>
          <span>Stop Policy</span>

          <strong>
            {
              plan.executionSettings
                .stopPolicy
            }
          </strong>
        </div>

        <div>
          <span>Evidence</span>

          <strong>
            {renderList(
              evidenceLabels,
              'No evidence enabled',
            )}
          </strong>
        </div>

        <div>
          <span>Notifications</span>

          <strong>
            {renderList(
              notificationLabels,
              'No notifications enabled',
            )}
          </strong>
        </div>
      </div>
    </section>
  )
}

export default TestPlanDetailOverview
