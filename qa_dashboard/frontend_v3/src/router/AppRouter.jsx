import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import DashboardLayout from '../layouts/DashboardLayout'
import CreateTestCyclePage from '../pages/CreateTestCyclePage'
import EnvironmentsPage from '../pages/EnvironmentsPage'
import HistoryPage from '../pages/HistoryPage'
import IntegrationsPage from '../pages/IntegrationsPage'
import MainDashboardPage from '../pages/MainDashboardPage'
import ProjectsPage from '../pages/ProjectsPage'
import ReportsPage from '../pages/ReportsPage'
import TestAssetsPage from '../pages/TestAssetsPage'
import TestCyclesPage from '../pages/TestCyclesPage'
import TestCycleDetailPage from '../pages/TestCycleDetailPage'
import TestPlanningPage from '../pages/TestPlanningPage'

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route
            index
            element={<MainDashboardPage />}
          />

          <Route
            path="test-cycles"
            element={<TestCyclesPage />}
          />

          <Route
            path="test-cycles/new"
            element={<CreateTestCyclePage />}
          />

          <Route
            path="test-cycles/:cycleId"
            element={<TestCycleDetailPage />}
          />

          <Route
            path="test-assets"
            element={<TestAssetsPage />}
          />

          <Route
            path="test-planning"
            element={<TestPlanningPage />}
          />

          <Route
            path="history"
            element={<HistoryPage />}
          />

          <Route
            path="reports"
            element={<ReportsPage />}
          />

          <Route
            path="projects"
            element={<ProjectsPage />}
          />

          <Route
            path="environments"
            element={<EnvironmentsPage />}
          />

          <Route
            path="integrations"
            element={<IntegrationsPage />}
          />

          <Route
            path="*"
            element={
              <Navigate
                to="/"
                replace
              />
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default AppRouter
