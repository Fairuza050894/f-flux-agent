import { useMemo, useState } from 'react'

import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'

const initialProjects = [
  {
    id: 'mobospace',
    name: 'Mobospace',
    key: 'MOB',
    description:
      'Logistics platform for shipment monitoring, driver operations, tracking, and supporting operational workflows.',
    applicationType: 'Full Stack Application',
    status: 'Active',
    defaultBranch: 'develop',
    repositoryUrl: '',
    workingDirectory: '',
    technologyStack: 'React, Node.js, Python',
    environmentCount: 1,
    moduleCount: 12,
    testAssetCount: 0,
    defaultEnvironment: 'Sandbox',
    lastExecution: 'Not available',
  },
]

const applicationTypes = [
  'Web Application',
  'Mobile Application',
  'API Service',
  'Backend Service',
  'Full Stack Application',
]

function ProjectsPage() {
  const [projects, setProjects] = useState(initialProjects)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [isFormOpen, setIsFormOpen] = useState(false)

  const filteredProjects = useMemo(() => {
    const normalizedSearch = searchTerm
      .trim()
      .toLowerCase()

    return projects.filter((project) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        project.name
          .toLowerCase()
          .includes(normalizedSearch) ||
        project.key
          .toLowerCase()
          .includes(normalizedSearch) ||
        project.applicationType
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesStatus =
        statusFilter === 'all' ||
        project.status.toLowerCase() === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [projects, searchTerm, statusFilter])

  const activeProjectCount = projects.filter(
    (project) => project.status === 'Active',
  ).length

  const environmentCount = projects.reduce(
    (total, project) =>
      total + project.environmentCount,
    0,
  )

  const testAssetCount = projects.reduce(
    (total, project) =>
      total + project.testAssetCount,
    0,
  )

  function handleCreateProject(event) {
    event.preventDefault()

    const formData = new FormData(event.currentTarget)

    const projectName = String(
      formData.get('projectName') ?? '',
    ).trim()

    const projectKey = String(
      formData.get('projectKey') ?? '',
    )
      .trim()
      .toUpperCase()

    const duplicateKey = projects.some(
      (project) =>
        project.key.toLowerCase() ===
        projectKey.toLowerCase(),
    )

    if (duplicateKey) {
      window.alert(
        `Project key "${projectKey}" sudah digunakan.`,
      )

      return
    }

    const newProject = {
      id: `${projectKey.toLowerCase()}-${Date.now()}`,
      name: projectName,
      key: projectKey,
      description: String(
        formData.get('description') ?? '',
      ).trim(),
      applicationType: String(
        formData.get('applicationType') ?? '',
      ),
      status: String(formData.get('status') ?? ''),
      defaultBranch: String(
        formData.get('defaultBranch') ?? '',
      ).trim(),
      repositoryUrl: String(
        formData.get('repositoryUrl') ?? '',
      ).trim(),
      workingDirectory: String(
        formData.get('workingDirectory') ?? '',
      ).trim(),
      technologyStack: String(
        formData.get('technologyStack') ?? '',
      ).trim(),
      environmentCount: 0,
      moduleCount: 0,
      testAssetCount: 0,
      defaultEnvironment: 'Not configured',
      lastExecution: 'Not available',
    }

    setProjects((currentProjects) => [
      ...currentProjects,
      newProject,
    ])

    event.currentTarget.reset()
    setIsFormOpen(false)
  }

  return (
    <div className="dashboard-page projects-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>CONFIGURATION</span>

            <StatusBadge tone="primary">
              Static Preview
            </StatusBadge>
          </div>

          <h2>Projects</h2>

          <p>
            Register products and manage their modules,
            environments, repositories, and testing
            configuration.
          </p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-primary"
            onClick={() => setIsFormOpen(true)}
            type="button"
          >
            + Add Project
          </button>
        </div>
      </div>

      <section
        aria-label="Project summary"
        className="metric-grid projects-metric-grid"
      >
        <MetricCard
          detail="Registered products"
          label="Total Projects"
          tone="primary"
          value={String(projects.length)}
        />

        <MetricCard
          detail="Available for testing"
          label="Active Projects"
          tone="success"
          value={String(activeProjectCount)}
        />

        <MetricCard
          detail="Configured across projects"
          label="Environments"
          tone="neutral"
          value={String(environmentCount)}
        />

        <MetricCard
          detail="Reusable testing definitions"
          label="Test Assets"
          tone="neutral"
          value={String(testAssetCount)}
        />
      </section>

      <section className="dashboard-panel projects-list-panel">
        <div className="projects-toolbar">
          <div>
            <span className="panel-eyebrow">
              PROJECT REGISTRY
            </span>

            <h3>Registered Projects</h3>

            <p>
              Select a project to review its configuration
              and available testing resources.
            </p>
          </div>

          <div className="projects-filters">
            <label>
              <span className="sr-only">
                Search projects
              </span>

              <input
                onChange={(event) =>
                  setSearchTerm(event.target.value)
                }
                placeholder="Search project..."
                type="search"
                value={searchTerm}
              />
            </label>

            <label>
              <span className="sr-only">
                Filter project status
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

                <option value="active">
                  Active
                </option>

                <option value="inactive">
                  Inactive
                </option>
              </select>
            </label>
          </div>
        </div>

        {filteredProjects.length > 0 ? (
          <div className="project-card-list">
            {filteredProjects.map((project) => (
              <article
                className="project-card"
                key={project.id}
              >
                <div className="project-card-header">
                  <div className="project-identity">
                    <div className="project-key">
                      {project.key}
                    </div>

                    <div>
                      <div className="project-title-row">
                        <h3>{project.name}</h3>

                        <StatusBadge
                          tone={
                            project.status === 'Active'
                              ? 'success'
                              : 'neutral'
                          }
                        >
                          {project.status}
                        </StatusBadge>
                      </div>

                      <span>
                        {project.applicationType}
                      </span>
                    </div>
                  </div>

                  <div className="project-card-actions">
                    <button
                      className="button button-secondary"
                      type="button"
                    >
                      Open Project
                    </button>

                    <button
                      className="button button-primary"
                      type="button"
                    >
                      Configure
                    </button>
                  </div>
                </div>

                <p className="project-description">
                  {project.description ||
                    'No project description provided.'}
                </p>

                <div className="project-stat-grid">
                  <div>
                    <span>Environments</span>
                    <strong>
                      {project.environmentCount}
                    </strong>
                  </div>

                  <div>
                    <span>Modules</span>
                    <strong>
                      {project.moduleCount}
                    </strong>
                  </div>

                  <div>
                    <span>Test Assets</span>
                    <strong>
                      {project.testAssetCount}
                    </strong>
                  </div>

                  <div>
                    <span>Default Environment</span>
                    <strong>
                      {project.defaultEnvironment}
                    </strong>
                  </div>
                </div>

                <div className="project-card-footer">
                  <div>
                    <span>Technology</span>
                    <strong>
                      {project.technologyStack ||
                        'Not configured'}
                    </strong>
                  </div>

                  <div>
                    <span>Default Branch</span>
                    <strong>
                      {project.defaultBranch ||
                        'Not configured'}
                    </strong>
                  </div>

                  <div>
                    <span>Last Execution</span>
                    <strong>
                      {project.lastExecution}
                    </strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="projects-empty-state">
            <strong>No projects found</strong>

            <p>
              Adjust the filters or register a new
              project.
            </p>

            <button
              className="button button-primary"
              onClick={() => setIsFormOpen(true)}
              type="button"
            >
              + Add Project
            </button>
          </div>
        )}
      </section>

      {isFormOpen && (
        <div
          aria-labelledby="add-project-title"
          aria-modal="true"
          className="modal-backdrop"
          role="dialog"
        >
          <div className="modal-card project-form-modal">
            <div className="modal-header">
              <div>
                <span className="panel-eyebrow">
                  PROJECT REGISTRY
                </span>

                <h2 id="add-project-title">
                  Add Project
                </h2>

                <p>
                  Register a product before configuring
                  environments and test assets.
                </p>
              </div>

              <button
                aria-label="Close add project form"
                className="modal-close-button"
                onClick={() => setIsFormOpen(false)}
                type="button"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateProject}>
              <div className="form-section">
                <div className="form-section-heading">
                  <h3>General Information</h3>

                  <p>
                    Define the project identity and basic
                    application information.
                  </p>
                </div>

                <div className="form-grid">
                  <label className="form-field">
                    <span>
                      Project Name
                      <strong>*</strong>
                    </span>

                    <input
                      name="projectName"
                      placeholder="Example: Mobospace"
                      required
                      type="text"
                    />
                  </label>

                  <label className="form-field">
                    <span>
                      Project Key
                      <strong>*</strong>
                    </span>

                    <input
                      maxLength="10"
                      name="projectKey"
                      placeholder="Example: MOB"
                      required
                      type="text"
                    />
                  </label>

                  <label className="form-field">
                    <span>
                      Application Type
                      <strong>*</strong>
                    </span>

                    <select
                      defaultValue="Web Application"
                      name="applicationType"
                      required
                    >
                      {applicationTypes.map((type) => (
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
                    <span>Status</span>

                    <select
                      defaultValue="Active"
                      name="status"
                    >
                      <option value="Active">
                        Active
                      </option>

                      <option value="Inactive">
                        Inactive
                      </option>
                    </select>
                  </label>

                  <label className="form-field form-field-full">
                    <span>Description</span>

                    <textarea
                      name="description"
                      placeholder="Describe the product and its testing purpose."
                      rows="3"
                    />
                  </label>
                </div>
              </div>

              <div className="form-section">
                <div className="form-section-heading">
                  <h3>Repository Configuration</h3>

                  <p>
                    Repository fields are optional for UI
                    or API-only projects.
                  </p>
                </div>

                <div className="form-grid">
                  <label className="form-field">
                    <span>Default Branch</span>

                    <input
                      defaultValue="develop"
                      name="defaultBranch"
                      placeholder="develop"
                      type="text"
                    />
                  </label>

                  <label className="form-field">
                    <span>Technology Stack</span>

                    <input
                      name="technologyStack"
                      placeholder="React, Node.js, Python"
                      type="text"
                    />
                  </label>

                  <label className="form-field form-field-full">
                    <span>Repository URL</span>

                    <input
                      name="repositoryUrl"
                      placeholder="https://github.com/company/project"
                      type="url"
                    />
                  </label>

                  <label className="form-field form-field-full">
                    <span>Local Working Directory</span>

                    <input
                      name="workingDirectory"
                      placeholder="/projects/application"
                      type="text"
                    />
                  </label>
                </div>
              </div>

              <div className="form-information">
                <strong>
                  Environment configuration comes next
                </strong>

                <p>
                  After saving the project, configure its
                  Sandbox, Staging, Production, or local
                  environments.
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
                  Save Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectsPage
