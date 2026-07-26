import {
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  useDashboardAuth,
} from '../../features/auth/dashboardAuthContext'


function readActorValue(
  actor,
  keys,
) {
  if (
    !actor
    || typeof actor !== 'object'
  ) {
    return ''
  }

  for (const key of keys) {
    const value = actor[key]

    if (
      typeof value === 'string'
      && value.trim()
    ) {
      return value.trim()
    }
  }

  return ''
}


function formatRole(value) {
  const normalized =
    String(value || 'viewer')
      .trim()
      .replaceAll('_', ' ')
      .replaceAll('-', ' ')

  return normalized.replace(
    /\b\w/g,
    (character) =>
      character.toUpperCase(),
  )
}


function getInitials(value) {
  const normalized =
    String(value || 'User').trim()

  const words = normalized
    .split(/\s+/)
    .filter(Boolean)

  if (!words.length) {
    return 'U'
  }

  if (words.length === 1) {
    return words[0]
      .slice(0, 2)
      .toUpperCase()
  }

  return (
    words[0][0]
    + words[words.length - 1][0]
  ).toUpperCase()
}


function AccountMenu() {
  const auth =
    useDashboardAuth() ?? {}

  const detailsRef = useRef(null)

  const [
    signingOut,
    setSigningOut,
  ] = useState(false)

  const [
    signOutError,
    setSignOutError,
  ] = useState('')

  const actor = auth.actor ?? null

  const displayName =
    readActorValue(
      actor,
      [
        'display_name',
        'displayName',
        'name',
        'email',
        'user_id',
        'userId',
        'username',
      ],
    )
    || 'Signed-in user'

  const email =
    readActorValue(
      actor,
      [
        'email',
        'username',
        'user_id',
        'userId',
      ],
    )

  const provider =
    readActorValue(
      actor,
      [
        'provider',
        'auth_provider',
        'authProvider',
      ],
    )
    || 'Dashboard session'

  const roleLabel =
    formatRole(auth.role)

  const initials =
    getInitials(displayName)

  useEffect(() => {
    function closeOnOutsideClick(
      event,
    ) {
      const details =
        detailsRef.current

      if (
        !details?.open
        || details.contains(
          event.target,
        )
      ) {
        return
      }

      details.removeAttribute(
        'open',
      )
    }

    function closeOnEscape(
      event,
    ) {
      if (
        event.key !== 'Escape'
      ) {
        return
      }

      const details =
        detailsRef.current

      if (!details?.open) {
        return
      }

      details.removeAttribute(
        'open',
      )

      details
        .querySelector('summary')
        ?.focus()
    }

    document.addEventListener(
      'pointerdown',
      closeOnOutsideClick,
    )
    document.addEventListener(
      'keydown',
      closeOnEscape,
    )

    return () => {
      document.removeEventListener(
        'pointerdown',
        closeOnOutsideClick,
      )
      document.removeEventListener(
        'keydown',
        closeOnEscape,
      )
    }
  }, [])

  async function handleSignOut(
    event,
  ) {
    event.preventDefault()

    if (signingOut) {
      return
    }

    setSigningOut(true)
    setSignOutError('')

    try {
      const response =
        await fetch(
          '/auth/logout',
          {
            method: 'POST',
            credentials: 'include',
            headers: {
              Accept: 'text/html',
            },
            redirect: 'follow',
          },
        )

      if (!response.ok) {
        throw new Error(
          'The server could not end '
          + 'your session.',
        )
      }

      window.location.assign(
        response.url || '/login',
      )
    } catch (error) {
      setSigningOut(false)
      setSignOutError(
        error?.message
        || (
          'Sign out failed. '
          + 'Please try again.'
        ),
      )
    }
  }

  return (
    <details
      className="account-menu"
      ref={detailsRef}
    >
      <summary
        aria-haspopup="menu"
        className="account-menu-trigger"
      >
        <span
          aria-hidden="true"
          className="account-avatar"
        >
          {initials}
        </span>

        <span className="account-trigger-copy">
          <strong>
            {displayName}
          </strong>
          <small>{roleLabel}</small>
        </span>

        <svg
          aria-hidden="true"
          className="account-chevron"
          fill="none"
          height="16"
          viewBox="0 0 16 16"
          width="16"
        >
          <path
            d="m4 6 4 4 4-4"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.5"
          />
        </svg>
      </summary>

      <section
        aria-label="Account menu"
        className="account-menu-popover"
        role="menu"
      >
        <header className="account-menu-header">
          <span
            aria-hidden="true"
            className={
              'account-avatar '
              + 'account-avatar-large'
            }
          >
            {initials}
          </span>

          <div className="account-identity">
            <span>Signed in as</span>
            <strong>{displayName}</strong>
            {email ? (
              <small>{email}</small>
            ) : null}
          </div>
        </header>

        <div className="account-session-meta">
          <div>
            <span>Role</span>
            <strong>{roleLabel}</strong>
          </div>

          <div>
            <span>Session</span>
            <strong>{provider}</strong>
          </div>
        </div>

        <div className="account-menu-divider" />

        <form onSubmit={handleSignOut}>
          <button
            className="account-sign-out"
            disabled={signingOut}
            role="menuitem"
            type="submit"
          >
            <svg
              aria-hidden="true"
              fill="none"
              height="18"
              viewBox="0 0 18 18"
              width="18"
            >
              <path
                d="M7.25 3.25H4.5A1.5 1.5 0 0 0 3 4.75v8.5a1.5 1.5 0 0 0 1.5 1.5h2.75M11 6l3 3-3 3M14 9H7"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.5"
              />
            </svg>

            <span>
              {signingOut
                ? 'Signing out…'
                : 'Sign out'}
            </span>
          </button>
        </form>

        {signOutError ? (
          <p
            className="account-sign-out-error"
            role="alert"
          >
            {signOutError}
          </p>
        ) : null}
      </section>
    </details>
  )
}


export default AccountMenu
