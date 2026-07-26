import {
  useEffect,
  useState,
} from 'react'

import {
  NavLink,
  Outlet,
} from 'react-router-dom'

import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import {
  applyThemePreference,
  getStoredThemePreference,
  persistThemePreference,
  themeOptions,
} from '../theme/theme'

const navigationGroups = [
  {
    label: 'Overview',
    items: [
      {
        label: 'Dashboard',
        path: '/',
      },
    ],
  },
  {
    label: 'Testing',
    items: [
      {
        label: 'Test Cycles',
        path: '/test-cycles',
      },
      {
        label: 'Test Assets',
        path: '/test-assets',
      },
      {
        label: 'Test Planning',
        path: '/test-planning',
      },
    ],
  },
  {
    label: 'Results',
    items: [
      {
        label: 'History',
        path: '/history',
      },
      {
        label: 'Reports',
        path: '/reports',
      },
    ],
  },
  {
    label: 'Configuration',
    items: [
      {
        label: 'Projects',
        path: '/projects',
      },
      {
        label: 'Environments',
        path: '/environments',
      },
      {
        label: 'Integrations',
        path: '/integrations',
      },
    ],
  },
]

function getNavClassName({
  isActive,
}) {
  return isActive
    ? 'sidebar-link sidebar-link-active'
    : 'sidebar-link'
}

function DashboardLayout() {
  const [
    themePreference,
    setThemePreference,
  ] = useState(
    getStoredThemePreference,
  )

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const selectedProjectId =
    useProjectEnvironmentStore(
      (state) =>
        state.selectedProjectId,
    )

  const selectedEnvironmentId =
    useProjectEnvironmentStore(
      (state) =>
        state.selectedEnvironmentId,
    )

  const setSelectedProjectId =
    useProjectEnvironmentStore(
      (state) =>
        state.setSelectedProjectId,
    )

  const setSelectedEnvironmentId =
    useProjectEnvironmentStore(
      (state) =>
        state.setSelectedEnvironmentId,
    )

  useEffect(() => {
    persistThemePreference(
      themePreference,
    )

    if (
      themePreference !== 'system' ||
      typeof window.matchMedia !==
        'function'
    ) {
      return undefined
    }

    const mediaQuery =
      window.matchMedia(
        '(prefers-color-scheme: dark)',
      )

    function handleSystemThemeChange() {
      applyThemePreference(
        'system',
      )
    }

    mediaQuery.addEventListener(
      'change',
      handleSystemThemeChange,
    )

    return () => {
      mediaQuery.removeEventListener(
        'change',
        handleSystemThemeChange,
      )
    }
  }, [themePreference])

  const projectEnvironments =
    environments.filter(
      (environment) =>
        environment.projectId ===
        selectedProjectId,
    )

  const selectedProject =
    projects.find(
      (project) =>
        project.id ===
        selectedProjectId,
    ) ?? null

  const selectedEnvironment =
    projectEnvironments.find(
      (environment) =>
        environment.id ===
        selectedEnvironmentId,
    ) ??
    projectEnvironments[0] ??
    null

  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">
            QA
          </div>

          <div className="sidebar-brand-copy">
            <strong>
              QA Dashboard
            </strong>

            <span>
              Quality operations
            </span>
          </div>
        </div>

        <div className="sidebar-context">
          <div className="sidebar-context-field">
            <label htmlFor="project-selector">
              Project
            </label>

            <select
              id="project-selector"
              onChange={(event) =>
                setSelectedProjectId(
                  event.target.value,
                )
              }
              value={
                selectedProjectId ?? ''
              }
            >
              {projects.map(
                (project) => (
                  <option
                    key={project.id}
                    value={project.id}
                  >
                    {project.name}
                  </option>
                ),
              )}
            </select>
          </div>

          <div className="sidebar-context-field">
            <label htmlFor="environment-selector">
              Environment
            </label>

            <select
              disabled={
                projectEnvironments.length ===
                0
              }
              id="environment-selector"
              onChange={(event) =>
                setSelectedEnvironmentId(
                  event.target.value,
                )
              }
              value={
                selectedEnvironment?.id ??
                ''
              }
            >
              {projectEnvironments.length ===
              0 ? (
                <option value="">
                  Not configured
                </option>
              ) : (
                projectEnvironments.map(
                  (environment) => (
                    <option
                      key={environment.id}
                      value={
                        environment.id
                      }
                    >
                      {environment.name}
                    </option>
                  ),
                )
              )}
            </select>
          </div>
        </div>

        <nav
          aria-label="Main navigation"
          className="sidebar-navigation"
        >
          {navigationGroups.map(
            (group) => (
              <section
                className="sidebar-group"
                key={group.label}
              >
                <h2>{group.label}</h2>

                <ul>
                  {group.items.map(
                    (item) => (
                      <li key={item.path}>
                        <NavLink
                          className={
                            getNavClassName
                          }
                          end={
                            item.path ===
                            '/'
                          }
                          to={item.path}
                        >
                          <span className="sidebar-link-indicator" />

                          <span>
                            {item.label}
                          </span>
                        </NavLink>
                      </li>
                    ),
                  )}
                </ul>
              </section>
            ),
          )}
                <a
          href="/operations"
          className="p8c-operations-nav-link"
        >
          Operations
        </a>
</nav>

        <div className="sidebar-footer">
          <span>Frontend v3</span>
          <span>React</span>
        </div>
      </aside>

      <div className="dashboard-workspace">
        <header className="dashboard-topbar">
          <div className="topbar-heading">
            <h1>QA Operations</h1>

            <p>
              {selectedProject?.name ??
                'No project'}
              {' · '}
              {selectedEnvironment?.name ??
                'No environment'}
            </p>
          </div>

          <div className="topbar-actions">
            <div
              aria-label="Runtime status"
              className="runtime-status"
            >
              <div className="runtime-status-item">
                <span className="status-dot status-dot-success" />
                <span>
                  Backend connected
                </span>
              </div>

              <div className="runtime-status-item">
                <span className="status-dot status-dot-muted" />
                <span>Runner idle</span>
              </div>
            </div>

            <label
              className="theme-control"
              htmlFor="theme-preference"
            >
              <span>Theme</span>

              <select
                id="theme-preference"
                onChange={(event) =>
                  setThemePreference(
                    event.target.value,
                  )
                }
                value={themePreference}
              >
                {themeOptions.map(
                  (option) => (
                    <option
                      key={option.value}
                      value={
                        option.value
                      }
                    >
                      {option.label}
                    </option>
                  ),
                )}
              </select>
            </label>
          </div>
        </header>

        <main className="dashboard-main">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
