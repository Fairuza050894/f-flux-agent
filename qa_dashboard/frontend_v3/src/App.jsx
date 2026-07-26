import AuthenticatedApp from './features/auth/AuthenticatedApp'
import WorkspacePersistenceBridge from './features/persistence/WorkspacePersistenceBridge'
import AppRouter from './router/AppRouter'

function App() {
  return (
    <AuthenticatedApp>
      <WorkspacePersistenceBridge />
      <AppRouter />
    </AuthenticatedApp>
  )
}

export default App
