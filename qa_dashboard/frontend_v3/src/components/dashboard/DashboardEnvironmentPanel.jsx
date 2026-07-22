import { Link } from 'react-router-dom'

import StatusBadge from '../StatusBadge'
import {
  formatResultStatus,
  normalizeResultStatus,
} from '../../features/results/resultFormatters'

function getEnvironmentStatusTone(
  status,
) {
  const normalizedStatus =
    normalizeResultStatus(status)

  if (
    [
      'active',
      'healthy',
      'available',
      'online',
    ].includes(normalizedStatus)
  ) {
    return 'success'
  }

  if (
    [
      'failed',
      'error',
      'offline',
    ].includes(normalizedStatus)
  ) {
    return 'danger'
  }

  if (
    [
      'warning',
      'degraded',
    ].includes(normalizedStatus)
  ) {
    return 'warning'
  }

  return 'neutral'
}

function DashboardEnvironmentPanel({
  context,
}) {
  if (!context) {
    return (
      <section className="dashboard-panel main-dashboard-panel">
        <div className="main-dashboard-empty">
          <strong>
            No environment selected
          </strong>

          <p>
            Configure a Project and Environment
            to display execution context.
          </p>

          <Link
            className="button button-secondary"
            to="/environments"
          >
            Open Environments
          </Link>
        </div>
      </section>
    )
  }

  const {
    project,
    environment,
  } = context

  return (
    <section className="dashboard-panel main-dashboard-panel main-dashboard-environment-panel">
      <header className="main-dashboard-panel-header">
        <div>
          <span className="panel-eyebrow">
            SELECTED ENVIRONMENT
          </span>

          <h3>
            {project?.name ??
              'Unknown project'}
          </h3>

          <p>
            {environment?.name ??
              'No environment selected'}
          </p>
        </div>

        <StatusBadge
          tone={getEnvironmentStatusTone(
            environment?.status,
          )}
        >
          {environment?.status
            ? formatResultStatus(
                environment.status,
              )
            : 'Unknown'}
        </StatusBadge>
      </header>

      <dl className="main-dashboard-environment-list">
        <div>
          <dt>Environment Type</dt>

          <dd>
            {environment?.type ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Default Browser</dt>

          <dd>
            {environment
              ?.defaultBrowser ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Authentication</dt>

          <dd>
            {environment
              ?.authenticationType ??
              'Not specified'}
          </dd>
        </div>

        <div>
          <dt>Web Application</dt>

          <dd>
            {context
              .webConfigurationStatus}
          </dd>
        </div>

        <div>
          <dt>API Service</dt>

          <dd>
            {context
              .apiConfigurationStatus}
          </dd>
        </div>

        <div>
          <dt>Credentials</dt>

          <dd>
            {context
              .credentialStatus}
          </dd>
        </div>
      </dl>

      <div className="main-dashboard-environment-footer">
        <span>
          Last checked:
          {' '}
          {environment?.lastChecked ??
            'Never'}
        </span>

        <Link
          className="text-link"
          to="/environments"
        >
          Open configuration
        </Link>
      </div>
    </section>
  )
}

export default DashboardEnvironmentPanel
