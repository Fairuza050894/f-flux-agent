import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  apiFetch,
  readApiError,
} from '../../services/apiClient'
import {
  DashboardAuthContext,
} from './dashboardAuthContext'

const INITIAL_STATE = {
  error: '',
  loading: true,
  session: null,
}

async function requestSession() {
  const response =
    await apiFetch(
      '/api/v1/security/session',
    )

  if (!response.ok) {
    const error =
      await readApiError(
        response,
        (
          'Unable to verify the ' +
          'dashboard session.'
        ),
      )

    throw new Error(
      error.message,
    )
  }

  return response.json()
}

function sessionErrorMessage(
  error,
) {
  if (
    error?.name ===
    'AbortError'
  ) {
    return (
      'Session verification ' +
      'timed out.'
    )
  }

  return (
    error?.message ??
    'Session verification failed.'
  )
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

function AuthenticatedApp({
  children,
}) {
  const [
    state,
    setState,
  ] = useState(
    INITIAL_STATE,
  )

  useEffect(() => {
    let active = true

    async function bootstrapSession() {
      try {
        const session =
          await requestSession()

        if (!active) {
          return
        }

        setState({
          error: '',
          loading: false,
          session,
        })
      } catch (error) {
        if (!active) {
          return
        }

        setState({
          error:
            sessionErrorMessage(
              error,
            ),
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

  const refreshSession =
    useCallback(
      async () => {
        setState(
          (current) => ({
            ...current,
            error: '',
            loading: true,
          }),
        )

        try {
          const session =
            await requestSession()

          setState({
            error: '',
            loading: false,
            session,
          })
        } catch (error) {
          setState({
            error:
              sessionErrorMessage(
                error,
              ),
            loading: false,
            session: null,
          })
        }
      },
      [],
    )

  const contextValue =
    useMemo(
      () => ({
        actor:
          state.session?.actor ??
          null,
        authRequired:
          Boolean(
            state.session
              ?.auth_required,
          ),
        permissions:
          state.session?.actor
            ?.permissions ??
          [],
        refreshSession,
        role:
          state.session?.actor
            ?.role ??
          'viewer',
      }),
      [
        refreshSession,
        state.session,
      ],
    )

  if (state.loading) {
    return <AuthLoadingState />
  }

  if (
    state.error ||
    !state.session
  ) {
    return (
      <AuthErrorState
        message={
          state.error ||
          'Session is unavailable.'
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
