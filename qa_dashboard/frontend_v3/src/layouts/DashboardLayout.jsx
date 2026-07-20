import { NavLink, Outlet } from 'react-router-dom'

const navigationGroups = [
  {
    label: 'OVERVIEW',
    items: [
      {
        label: 'Dashboard',
        path: '/',
      },
    ],
  },
  {
    label: 'TESTING',
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
    label: 'RESULTS',
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
    label: 'CONFIGURATION',
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

function getNavClassName({ isActive }) {
  return isActive
    ? 'sidebar-link sidebar-link-active'
    : 'sidebar-link'
}

function DashboardLayout() {
  return (
    <div className="dashboard-shell">
      <aside className="dashboard-sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">
            QA
          </div>

          <div>
            <strong>QA Dashboard</strong>
            <span>Autonomous Testing</span>
          </div>
        </div>

        <div className="sidebar-project">
          <label htmlFor="project-selector">
            Active Project
          </label>

          <select
            id="project-selector"
            defaultValue="mobospace"
          >
            <option value="mobospace">
              Mobospace
            </option>
          </select>

          <p>
            Select a saved project for the current
            QA workspace.
          </p>
        </div>

        <nav
          className="sidebar-navigation"
          aria-label="Main navigation"
        >
          {navigationGroups.map((group) => (
            <section
              className="sidebar-group"
              key={group.label}
            >
              <h2>{group.label}</h2>

              <ul>
                {group.items.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      className={getNavClassName}
                      end={item.path === '/'}
                      to={item.path}
                    >
                      <span className="sidebar-link-indicator" />

                      <span>{item.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div>
            <span>Frontend</span>
            <strong>Version 3</strong>
          </div>

          <span className="sidebar-footer-badge">
            React
          </span>
        </div>
      </aside>

      <div className="dashboard-workspace">
        <header className="dashboard-topbar">
          <div className="topbar-heading">
            <span className="topbar-eyebrow">
              QUALITY OPERATIONS
            </span>

            <h1>QA Autonomous Dashboard</h1>

            <p>
              Plan, execute, observe, and analyze
              automated quality checks.
            </p>
          </div>

          <div className="topbar-status">
            <div className="status-chip">
              <span className="status-dot status-dot-success" />

              <div>
                <span>Environment</span>
                <strong>Sandbox</strong>
              </div>
            </div>

            <div className="status-chip">
              <span className="status-dot status-dot-success" />

              <div>
                <span>Backend</span>
                <strong>Connected</strong>
              </div>
            </div>

            <div className="status-chip">
              <span className="status-dot status-dot-muted" />

              <div>
                <span>Run</span>
                <strong>Idle</strong>
              </div>
            </div>
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
