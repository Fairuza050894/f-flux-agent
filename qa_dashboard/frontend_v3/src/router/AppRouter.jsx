import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import DashboardLayout from '../layouts/DashboardLayout'
import ApiTestingPage from '../pages/ApiTestingPage'
import HistoryPage from '../pages/HistoryPage'
import MainDashboardPage from '../pages/MainDashboardPage'
import RegressionTestingPage from '../pages/RegressionTestingPage'
import TestPlanningPage from '../pages/TestPlanningPage'
import UiTestingPage from '../pages/UiTestingPage'

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
            path="ui-testing"
            element={<UiTestingPage />}
          />

          <Route
            path="api-testing"
            element={<ApiTestingPage />}
          />

          <Route
            path="regression-testing"
            element={<RegressionTestingPage />}
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
