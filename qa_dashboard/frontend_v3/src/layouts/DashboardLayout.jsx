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
    label: 'EXECUTE',
    items: [
      {
        label: 'UI Testing',
        path: '/ui-testing',
      },
      {
        label: 'API Testing',
        path: '/api-testing',
      },
      {
        label: 'Regression Testing',
        path: '/regression-testing',
      },
    ],
  },
  {
    label: 'WORKSPACE',
    items: [
      {
        label: 'Test Planning',
        path: '/test-planning',
      },
      {
        label: 'History',
        path: '/history',
      },
    ],
  },
]

function DashboardLayout() {
  return (
    <div>
      <aside>
        <h2>QA Dashboard</h2>

        <nav aria-label="Main navigation">
          {navigationGroups.map((group) => (
            <section key={group.label}>
              <h3>{group.label}</h3>

              <ul>
                {group.items.map((item) => (
                  <li key={item.path}>
                    <NavLink to={item.path}>
                      {item.label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>
      </aside>

      <div>
        <header>
          <strong>QA Autonomous Dashboard</strong>
          <p>
            Plan, execute, observe, and analyze
            automated quality checks.
          </p>
        </header>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
