import { useMemo, useState } from 'react'

import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'

const initialEnvironments = [
  {
    id: 'mobospace-sandbox',
    projectId: 'mobospace',
    name: 'Sandbox',
    type: 'Sandbox',
    status: 'Not Checked',
    webBaseUrl: '',
    apiBaseUrl: '',
    authenticationUrl: '',
    authenticationType: 'Username and Password',
    credentialReference: 'Not configured',
    workspace: 'Not configured',
    defaultBrowser: 'Chromium',
    timeout: 30,
    healthCheckEndpoint: '',
    lastChecked: 'Never',
  },
]

const environmentTypes = [
  'Sandbox',
  'Staging',
  'Production',
  'Local',
]

const authenticationTypes = [
  'None',
  'Username and Password',
  'Bearer Token',
  'API Key',
  'OAuth 2.0',
  'SSO',
]

const browsers = [
  'Chromium',
  'Google Chrome',
  'Firefox',
  'WebKit',
]

function getStatusTone(status) {
  switch (status) {
    case 'Healthy':
      return 'success'
    case 'Degraded':
      return 'warning'
    case 'Offline':
      return 'danger'
    default:
      return 'neutral'
  }
}

function displayValue(value) {
  return value || 'Not configured'
}

function EnvironmentsPage() {
  const [environments, setEnvironments] = useState(
    initialEnvironments,
  )

  const [selectedProject, setSelectedProject] =
    useState('mobospace')

  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [isFormOpen, setIsFormOpen] = useState(false)

  const projectEnvironments = useMemo(
    () =>
      environments.filter(
        (environment) =>
          environment.projectId === selectedProject,
      ),
    [environments, selectedProject],
  )

  const filteredEnvironments = useMemo(() => {
    const normalizedSearch = searchTerm
      .trim()
      .toLowerCase()

    return projectEnvironments.filter((environment) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        environment.name
          .toLowerCase()
          .includes(normalizedSearch) ||
        environment.type
          .toLowerCase()
          .includes(normalizedSearch) ||
        environment.webBaseUrl
          .toLowerCase()
          .includes(normalizedSearch) ||
        environment.apiBaseUrl
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesType =
        typeFilter === 'all' ||
        environment.type.toLowerCase() === typeFilter

      const matchesStatus =
        statusFilter === 'all' ||
        environment.status.toLowerCase() === statusFilter

      return (
        matchesSearch &&
        matchesType &&
        matchesStatus
      )
    })
  }, [
    projectEnvironments,
    searchTerm,
    statusFilter,
    typeFilter,
  ])

  const healthyCount = projectEnvironments.filter(
    (environment) => environment.status === 'Healthy',
  ).length

  const issueCount = projectEnvironments.filter(
    (environment) =>
      environment.status === 'Degraded' ||
      environment.status === 'Offline',
  ).length

  const notCheckedCount = projectEnvironments.filter(
    (environment) =>
      environment.status === 'Not Checked',
  ).length

  function handleCreateEnvironment(event) {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)

    const environmentName = String(
      formData.get('environmentName') ?? '',
    ).trim()

    const duplicateEnvironment = environments.some(
      (environment) =>
        environment.projectId === selectedProject &&
        environment.name.toLowerCase() ===
          environmentName.toLowerCase(),
    )

    if (duplicateEnvironment) {
      window.alert(
        `Environment "${environmentName}" sudah terdaftar pada project ini.`,
      )

      return
    }

    const newEnvironment = {
      id: `${selectedProject}-${Date.now()}`,
      projectId: selectedProject,
      name: environmentName,
      type: String(
        formData.get('environmentType') ?? '',
      ),
      status: 'Not Checked',
      webBaseUrl: String(
        formData.get('webBaseUrl') ?? '',
      ).trim(),
      apiBaseUrl: String(
        formData.get('apiBaseUrl') ?? '',
      ).trim(),
      authenticationUrl: String(
        formData.get('authenticationUrl') ?? '',
      ).trim(),
      authenticationType: String(
        formData.get('authenticationType') ?? '',
      ),
      credentialReference:
        String(
          formData.get('credentialReference') ?? '',
        ).trim() || 'Not configured',
      workspace:
        String(
          formData.get('workspace') ?? '',
        ).trim() || 'Not configured',
      defaultBrowser: String(
        formData.get('defaultBrowser') ?? '',
      ),
      timeout: Number(
        formData.get('timeout') ?? 30,
      ),
      healthCheckEndpoint: String(
        formData.get('healthCheckEndpoint') ?? '',
      ).trim(),
      lastChecked: 'Never',
    }

    setEnvironments((currentEnvironments) => [
      ...currentEnvironments,
      newEnvironment,
    ])

    event.currentTarget.reset()
    setIsFormOpen(false)
  }

  function handleTestConnection(environmentName) {
    window.alert(
      `Test Connection untuk "${environmentName}" akan dihubungkan ke backend health-check pada tahap integrasi.`,
    )
  }

  return (
    <div className="dashboard-page environments-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>CONFIGURATION</span>

            <StatusBadge tone="primary">
              Static Preview
            </StatusBadge>
          </div>

          <h2>Environments</h2>

          <p>
            Configure application URLs, API endpoints,
            authentication references, browsers, timeouts,
            and health checks for each project.
          </p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-primary"
            onClick={() => setIsFormOpen(true)}
            type="button"
          >
            + Add Environment
          </button>
        </div>
      </div>

      <section className="environment-project-context">
        <div>
          <span className="panel-eyebrow">
            PROJECT CONTEXT
          </span>

          <h3>Environment Registry</h3>

          <p>
            Environments are managed separately for each
            registered project.
          </p>
        </div>

        <label className="environment-project-selector">
          <span>Project</span>

          <select
            onChange={(event) =>
              setSelectedProject(event.target.value)
            }
            value={selectedProject}
          >
            <option value="mobospace">
              Mobospace
            </option>
          </select>
        </label>
      </section>

      <section
        aria-label="Environment summary"
        className="metric-grid environment-metric-grid"
      >
        <MetricCard
          detail="Configured for Mobospace"
          label="Total Environments"
          tone="primary"
          value={String(projectEnvironments.length)}
        />

        <MetricCard
          detail="Ready for test execution"
          label="Healthy"
          tone="success"
          value={String(healthyCount)}
        />

        <MetricCard
          detail="Degraded or offline"
          label="Need Attention"
          tone="danger"
          value={String(issueCount)}
        />

        <MetricCard
          detail="Health check not executed"
          label="Not Checked"
          tone="neutral"
          value={String(notCheckedCount)}
        />
      </section>

      <section className="dashboard-panel environments-list-panel">
        <div className="environments-toolbar">
          <div>
            <span className="panel-eyebrow">
              ENVIRONMENT REGISTRY
            </span>

            <h3>Mobospace Environments</h3>

            <p>
              Review endpoints, execution settings, and
              current health-check status.
            </p>
          </div>

          <div className="environment-filters">
            <label>
              <span className="sr-only">
                Search environments
              </span>

              <input
                onChange={(event) =>
                  setSearchTerm(event.target.value)
                }
                placeholder="Search environment..."
                type="search"
                value={searchTerm}
              />
            </label>

            <label>
              <span className="sr-only">
                Filter environment type
              </span>

              <select
                onChange={(event) =>
                  setTypeFilter(event.target.value)
                }
                value={typeFilter}
              >
                <option value="all">
                  All types
                </option>

                <option value="sandbox">
                  Sandbox
                </option>

                <option value="staging">
                  Staging
                </option>

                <option value="production">
                  Production
                </option>

                <option value="local">
                  Local
                </option>
              </select>
            </label>

            <label>
              <span className="sr-only">
                Filter environment status
              </span>

              <select
                onChange={(event) =>
                  setStatusFilter(event.target.value)
                }
                value={statusFilter}
              >
                <option value="all">
                  All statuses
                </option>

                <option value="healthy">
                  Healthy
                </option>

                <option value="degraded">
                  Degraded
                </option>

                <option value="offline">
                  Offline
                </option>

                <option value="not checked">
                  Not Checked
                </option>
              </select>
            </label>
          </div>
        </div>

        {filteredEnvironments.length > 0 ? (
          <div className="environment-card-list">
            {filteredEnvironments.map((environment) => (
              <article
                className="environment-card"
                key={environment.id}
              >
                <div className="environment-card-header">
                  <div className="environment-identity">
                    <div className="environment-mark">
                      {environment.name
                        .slice(0, 2)
                        .toUpperCase()}
                    </div>

                    <div>
                      <div className="environment-title-row">
                        <h3>{environment.name}</h3>

                        <StatusBadge
                          tone={getStatusTone(
                            environment.status,
                          )}
                        >
                          {environment.status}
                        </StatusBadge>
                      </div>

                      <span>
                        {environment.type} Environment
                      </span>
                    </div>
                  </div>

                  <div className="environment-card-actions">
                    <button
                      className="button button-secondary"
                      onClick={() =>
                        handleTestConnection(
                          environment.name,
                        )
                      }
                      type="button"
                    >
                      Test Connection
                    </button>

                    <button
                      className="button button-primary"
                      type="button"
                    >
                      Configure
                    </button>
                  </div>
                </div>

                <div className="environment-endpoint-grid">
                  <div>
                    <span>Web Base URL</span>

                    <strong>
                      {displayValue(
                        environment.webBaseUrl,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>API Base URL</span>

                    <strong>
                      {displayValue(
                        environment.apiBaseUrl,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Authentication URL</span>

                    <strong>
                      {displayValue(
                        environment.authenticationUrl,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Health Check Endpoint</span>

                    <strong>
                      {displayValue(
                        environment.healthCheckEndpoint,
                      )}
                    </strong>
                  </div>
                </div>

                <div className="environment-setting-grid">
                  <div>
                    <span>Authentication</span>

                    <strong>
                      {environment.authenticationType}
                    </strong>
                  </div>

                  <div>
                    <span>Credential Reference</span>

                    <strong>
                      {environment.credentialReference}
                    </strong>
                  </div>

                  <div>
                    <span>Workspace / Company</span>

                    <strong>
                      {environment.workspace}
                    </strong>
                  </div>

                  <div>
                    <span>Default Browser</span>

                    <strong>
                      {environment.defaultBrowser}
                    </strong>
                  </div>

                  <div>
                    <span>Timeout</span>

                    <strong>
                      {environment.timeout} seconds
                    </strong>
                  </div>

                  <div>
                    <span>Last Checked</span>

                    <strong>
                      {environment.lastChecked}
                    </strong>
                  </div>
                </div>

                {environment.status === 'Not Checked' && (
                  <div className="environment-warning">
                    <strong>
                      Health check has not been executed
                    </strong>

                    <p>
                      Configure the required URLs and use
                      Test Connection after backend
                      integration is available.
                    </p>
                  </div>
                )}
              </article>
            ))}
          </div>
        ) : (
          <div className="projects-empty-state">
            <strong>No environments found</strong>

            <p>
              Adjust the filters or add an environment
              for this project.
            </p>

            <button
              className="button button-primary"
              onClick={() => setIsFormOpen(true)}
              type="button"
            >
              + Add Environment
            </button>
          </div>
        )}
      </section>

      {isFormOpen && (
        <div
          aria-labelledby="add-environment-title"
          aria-modal="true"
          className="modal-backdrop"
          role="dialog"
        >
          <div className="modal-card environment-form-modal">
            <div className="modal-header">
              <div>
                <span className="panel-eyebrow">
                  MOBOSPACE
                </span>

                <h2 id="add-environment-title">
                  Add Environment
                </h2>

                <p>
                  Register a target environment for UI,
                  API, E2E, and regression execution.
                </p>
              </div>

              <button
                aria-label="Close add environment form"
                className="modal-close-button"
                onClick={() => setIsFormOpen(false)}
                type="button"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateEnvironment}>
              <div className="form-section">
                <div className="form-section-heading">
                  <h3>General Information</h3>

                  <p>
                    Define the environment identity and
                    execution category.
                  </p>
                </div>

                <div className="form-grid">
                  <label className="form-field">
                    <span>
                      Environment Name
                      <strong>*</strong>
                    </span>

                    <input
                      name="environmentName"
                      placeholder="Example: Sandbox"
                      required
                      type="text"
                    />
                  </label>

                  <label className="form-field">
                    <span>
                      Environment Type
                      <strong>*</strong>
                    </span>

                    <select
                      defaultValue="Sandbox"
                      name="environmentType"
                      required
                    >
                      {environmentTypes.map((type) => (
                        <option
                          key={type}
                          value={type}
                        >
                          {type}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section-heading">
                  <h3>Application Endpoints</h3>

                  <p>
                    Store base URLs at environment level so
                    the same test assets can run in
                    different environments.
                  </p>
                </div>

                <div className="form-grid">
                  <label className="form-field form-field-full">
                    <span>Web Base URL</span>

                    <input
                      name="webBaseUrl"
                      placeholder="https://application.example.com"
                      type="url"
                    />
                  </label>

                  <label className="form-field form-field-full">
                    <span>API Base URL</span>

                    <input
                      name="apiBaseUrl"
                      placeholder="https://api.example.com"
                      type="url"
                    />
                  </label>

                  <label className="form-field">
                    <span>Authentication URL</span>

                    <input
                      name="authenticationUrl"
                      placeholder="https://auth.example.com"
                      type="url"
                    />
                  </label>

                  <label className="form-field">
                    <span>Health Check Endpoint</span>

                    <input
                      name="healthCheckEndpoint"
                      placeholder="/health"
                      type="text"
                    />
                  </label>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section-heading">
                  <h3>
                    Authentication and Execution
                  </h3>

                  <p>
                    Credentials are referenced by key and
                    are not stored as plain text.
                  </p>
                </div>

                <div className="form-grid">
                  <label className="form-field">
                    <span>Authentication Type</span>

                    <select
                      defaultValue="Username and Password"
                      name="authenticationType"
                    >
                      {authenticationTypes.map((type) => (
                        <option
                          key={type}
                          value={type}
                        >
                          {type}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="form-field">
                    <span>Credential Reference</span>

                    <input
                      name="credentialReference"
                      placeholder="mobospace-sandbox-account"
                      type="text"
                    />
                  </label>

                  <label className="form-field">
                    <span>Workspace / Company</span>

                    <input
                      name="workspace"
                      placeholder="Workspace or company name"
                      type="text"
                    />
                  </label>

                  <label className="form-field">
                    <span>Default Browser</span>

                    <select
                      defaultValue="Chromium"
                      name="defaultBrowser"
                    >
                      {browsers.map((browser) => (
                        <option
                          key={browser}
                          value={browser}
                        >
                          {browser}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="form-field">
                    <span>Timeout in Seconds</span>

                    <input
                      defaultValue="30"
                      max="300"
                      min="1"
                      name="timeout"
                      type="number"
                    />
                  </label>
                </div>
              </div>

              <div className="form-information">
                <strong>
                  Sensitive values are not entered here
                </strong>

                <p>
                  Username, password, API key, and access
                  token remain in environment variables or
                  a secret-storage integration.
                </p>
              </div>

              <div className="modal-actions">
                <button
                  className="button button-secondary"
                  onClick={() => setIsFormOpen(false)}
                  type="button"
                >
                  Cancel
                </button>

                <button
                  className="button button-primary"
                  type="submit"
                >
                  Save Environment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default EnvironmentsPage
