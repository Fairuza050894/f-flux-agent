import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  fetchAccountSettings,
  saveAccountSettings,
} from '../../services/accountService'
import {
  apiFetch,
  readApiError,
} from '../../services/apiClient'
import {
  useProjectEnvironmentStore,
} from '../../stores/projectEnvironmentStore'
import {
  DashboardAuthContext,
} from './dashboardAuthContext'


const INITIAL_STATE = {
  account: null,
  accountError: '',
  error: '',
  loading: true,
  session: null,
}


async function requestSession() {
  const response = await apiFetch(
    '/api/v1/security/session',
  )

  if (!response.ok) {
    const error = await readApiError(
      response,
      (
        'Unable to verify the '
        + 'dashboard session.'
      ),
    )

    throw new Error(error.message)
  }

  return response.json()
}


function sessionErrorMessage(error) {
  if (error?.name === 'AbortError') {
    return (
      'Session verification '
      + 'timed out.'
    )
  }

  return (
    error?.message
    ?? 'Session verification failed.'
  )
}


function applyAccountPreferences(account) {
  const preferences =
    account?.preferences ?? {}

  /*
   * P8D2C_THEME_SINGLE_SOURCE_V1
   * Account preferences provide data only.
   * DashboardLayout owns DOM theme application.
   */
  const store =
    useProjectEnvironmentStore.getState()
  const projectId = String(
    preferences.default_project_id || '',
  ).trim()
  const environmentId = String(
    preferences.default_environment_id || '',
  ).trim()

  const projectExists =
    store.projects.some(
      (project) =>
        project.id === projectId,
    )

  if (projectId && projectExists) {
    store.setSelectedProjectId(projectId)
  }

  const environmentExists =
    store.environments.some(
      (environment) => (
        environment.id === environmentId
        && (
          !projectId
          || environment.projectId
            === projectId
        )
      ),
    )

  if (
    environmentId
    && environmentExists
  ) {
    store.setSelectedEnvironmentId(
      environmentId,
    )
  }
}


function AuthLoadingState() {
  return (
    <main
      className="auth-gate-state"
      aria-live="polite"
    >
      <section className="auth-gate-card">
        <p className="auth-gate-eyebrow">
          Hermes QA Dashboard
        </p>
        <h1>Checking session</h1>
        <p>
          Verifying your dashboard access.
        </p>
      </section>
    </main>
  )
}


function AuthErrorState({
  message,
  onRetry,
}) {
  return (
    <main
      className="auth-gate-state"
      role="alert"
    >
      <section className="auth-gate-card">
        <p className="auth-gate-eyebrow">
          Hermes QA Dashboard
        </p>
        <h1>Session check failed</h1>
        <p>{message}</p>
        <button
          className="button button-primary"
          type="button"
          onClick={onRetry}
        >
          Retry
        </button>
      </section>
    </main>
  )
}


function AuthenticatedApp({ children }) {
  const [state, setState] = useState(
    INITIAL_STATE,
  )

  const loadAccount = useCallback(
    async () => {
      try {
        const account =
          await fetchAccountSettings()

        applyAccountPreferences(account)

        setState(
          (current) => ({
            ...current,
            account,
            accountError: '',
          }),
        )

        return account
      } catch (error) {
        setState(
          (current) => ({
            ...current,
            accountError: (
              error?.message
              || 'Account settings are unavailable.'
            ),
          }),
        )

        return null
      }
    },
    [],
  )

  useEffect(() => {
    let active = true

    async function bootstrapSession() {
      try {
        const session = await requestSession()

        if (!active) {
          return
        }

        let account = null
        let accountError = ''

        try {
          account =
            await fetchAccountSettings()
          applyAccountPreferences(account)
        } catch (error) {
          accountError = (
            error?.message
            || 'Account settings are unavailable.'
          )
        }

        if (!active) {
          return
        }

        setState({
          account,
          accountError,
          error: '',
          loading: false,
          session,
        })
      } catch (error) {
        if (!active) {
          return
        }

        setState({
          account: null,
          accountError: '',
          error: sessionErrorMessage(error),
          loading: false,
          session: null,
        })
      }
    }

    void bootstrapSession()

    return () => {
      active = false
    }
  }, [])

  const refreshSession = useCallback(
    async () => {
      setState(
        (current) => ({
          ...current,
          error: '',
          loading: true,
        }),
      )

      try {
        const session = await requestSession()
        let account = null
        let accountError = ''

        try {
          account =
            await fetchAccountSettings()
          applyAccountPreferences(account)
        } catch (error) {
          accountError = (
            error?.message
            || 'Account settings are unavailable.'
          )
        }

        setState({
          account,
          accountError,
          error: '',
          loading: false,
          session,
        })
      } catch (error) {
        setState({
          account: null,
          accountError: '',
          error: sessionErrorMessage(error),
          loading: false,
          session: null,
        })
      }
    },
    [],
  )

  const updateAccount = useCallback(
    async ({
      profile,
      preferences,
      expectedRevision,
    }) => {
      const account =
        await saveAccountSettings({
          profile,
          preferences,
          expectedRevision,
        })

      applyAccountPreferences(account)

      setState(
        (current) => ({
          ...current,
          account,
          accountError: '',
        }),
      )

      return account
    },
    [],
  )

  const contextValue = useMemo(
    () => ({
      account: state.account,
      accountError: state.accountError,
      actor:
        state.session?.actor ?? null,
      authRequired: Boolean(
        state.session?.auth_required,
      ),
      permissions:
        state.session?.actor
          ?.permissions ?? [],
      refreshAccount: loadAccount,
      refreshSession,
      role:
        state.session?.actor
          ?.role ?? 'viewer',
      updateAccount,
    }),
    [
      loadAccount,
      refreshSession,
      state.account,
      state.accountError,
      state.session,
      updateAccount,
    ],
  )

  if (state.loading) {
    return <AuthLoadingState />
  }

  if (
    state.error
    || !state.session
  ) {
    return (
      <AuthErrorState
        message={
          state.error
          || 'Session is unavailable.'
        }
        onRetry={refreshSession}
      />
    )
  }

  return (
    <DashboardAuthContext.Provider
      value={contextValue}
    >
      {children}
    </DashboardAuthContext.Provider>
  )
}


export default AuthenticatedApp
