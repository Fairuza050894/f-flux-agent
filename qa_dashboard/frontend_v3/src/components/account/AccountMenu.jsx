import {
  useEffect,
  useRef,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import {
  useDashboardAuth,
} from '../../features/auth/dashboardAuthContext'


function readValue(
  source,
  keys,
) {
  if (
    !source
    || typeof source !== 'object'
  ) {
    return ''
  }

  for (const key of keys) {
    const value = source[key]

    if (
      typeof value === 'string'
      && value.trim()
    ) {
      return value.trim()
    }
  }

  return ''
}


function formatLabel(value) {
  const normalized = String(
    value || 'viewer',
  )
    .trim()
    .replaceAll('_', ' ')
    .replaceAll('-', ' ')

  return normalized.replace(
    /\b\w/g,
    (character) =>
      character.toUpperCase(),
  )
}


function formatProvider(value) {
  const normalized = String(
    value || '',
  ).trim().toLowerCase()

  if (normalized === 'basic') {
    return 'Basic authentication'
  }

  if (!normalized) {
    return 'Dashboard session'
  }

  return formatLabel(normalized)
}


function derivedInitials(value) {
  const words = String(
    value || 'User',
  )
    .trim()
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


const THEME_OPTIONS = [
  {
    value: 'system',
    label: 'System',
    description: 'Follow device appearance',
  },
  {
    value: 'light',
    label: 'Light',
    description: 'Use the light interface',
  },
  {
    value: 'dark',
    label: 'Dark',
    description: 'Use the dark interface',
  },
]


function AccountMenu({
  theme = 'system',
  onThemeChange = () => {},
}) {
  const auth = useDashboardAuth() ?? {}
  const detailsRef = useRef(null)
  const [
    activeView,
    setActiveView,
  ] = useState('menu')
  const [
    signingOut,
    setSigningOut,
  ] = useState(false)
  const [
    signOutError,
    setSignOutError,
  ] = useState('')
  const [
    themeSaving,
    setThemeSaving,
  ] = useState(false)
  const [
    themeError,
    setThemeError,
  ] = useState('')

  const account = auth.account ?? {}
  const actor = auth.actor ?? {}
  const profile = account.profile ?? {}
  const identity = account.identity ?? actor

  const displayName =
    readValue(
      profile,
      ['display_name'],
    )
    || readValue(
      identity,
      [
        'display_name',
        'email',
        'user_id',
      ],
    )
    || 'Signed-in user'

  const email = readValue(
    identity,
    [
      'email',
      'user_id',
    ],
  )

  const jobTitle = readValue(
    profile,
    ['job_title'],
  )

  const initials = (
    readValue(
      profile,
      ['avatar_initials'],
    )
    || derivedInitials(displayName)
  ).slice(0, 3).toUpperCase()

  const roleLabel = formatLabel(
    identity.role || auth.role,
  )

  const providerLabel = formatProvider(
    identity.provider,
  )

  function resetMenuView() {
    setActiveView('menu')
  }

  function closeMenu() {
    if (detailsRef.current) {
      detailsRef.current.open = false
    }

    resetMenuView()
  }

  function openSettings() {
    setSignOutError('')
    setActiveView('settings')
  }

  function handleMenuToggle(event) {
    if (!event.currentTarget.open) {
      resetMenuView()
      setSignOutError('')
    }
  }

  useEffect(() => {
    function closeOnOutsideClick(event) {
      const details = detailsRef.current

      if (
        !details?.open
        || details.contains(event.target)
      ) {
        return
      }

      details.open = false
      resetMenuView()
      setSignOutError('')
    }

    function closeOnEscape(event) {
      if (event.key !== 'Escape') {
        return
      }

      const details = detailsRef.current

      if (!details?.open) {
        return
      }

      if (activeView === 'settings') {
        setActiveView('menu')
        return
      }

      details.open = false
      details.querySelector(
        'summary',
      )?.focus()
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
  }, [activeView])

  // P8D2C_THEME_ROUTE_PERSISTENCE_V1
  async function handleThemeSelection(
    nextTheme,
  ) {
    if (
      themeSaving
      || nextTheme === theme
    ) {
      return
    }

    const previousTheme = theme

    onThemeChange(nextTheme)
    setThemeError('')

    if (
      typeof auth.updateAccount
      !== 'function'
    ) {
      return
    }

    setThemeSaving(true)

    try {
      const savedAccount =
        await auth.updateAccount({
          profile: {
            ...profile,
          },
          preferences: {
            ...(account.preferences ?? {}),
            theme: nextTheme,
          },
          expectedRevision:
            account.revision ?? 0,
        })

      const savedTheme =
        savedAccount?.preferences?.theme

      if (
        savedTheme === 'system'
        || savedTheme === 'light'
        || savedTheme === 'dark'
      ) {
        onThemeChange(savedTheme)
      }
    } catch (error) {
      onThemeChange(previousTheme)
      setThemeError(
        error?.message
        || (
          'Theme preference could not '
          + 'be saved.'
        ),
      )
    } finally {
      setThemeSaving(false)
    }
  }


  async function handleSignOut(event) {
    event.preventDefault()

    if (signingOut) {
      return
    }

    setSigningOut(true)
    setSignOutError('')

    try {
      const response = await fetch(
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
      onToggle={handleMenuToggle}
      ref={detailsRef}
    >
      <summary
        aria-haspopup="menu"
        aria-label={
          `Open account menu for ${displayName}`
        }
        className="account-menu-trigger"
        title={`${displayName} · ${roleLabel}`}
      >
        <span
          aria-hidden="true"
          className="account-avatar"
        >
          {initials}
        </span>

        <span className="account-trigger-copy">
          <strong>{displayName}</strong>
          <small>
            {jobTitle || roleLabel}
          </small>
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
        className={
          'account-menu-popover '
          + (
            activeView === 'settings'
              ? 'is-settings-view'
              : 'is-main-view'
          )
        }
        role="menu"
      >
        {activeView === 'menu' ? (
          <div
            className="account-menu-view account-menu-main-view"
            data-view="main"
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
                <span>Provider</span>
                <strong>{providerLabel}</strong>
              </div>
            </div>

            <nav
              aria-label="Account actions"
              className="account-primary-menu"
            >
              <Link
                className="account-primary-action"
                onClick={closeMenu}
                role="menuitem"
                to="/account"
              >
                <span
                  aria-hidden="true"
                  className="account-primary-action-icon"
                >
                  <svg
                    fill="none"
                    height="19"
                    viewBox="0 0 20 20"
                    width="19"
                  >
                    <path
                      d="M10 10.25a3.25 3.25 0 1 0 0-6.5 3.25 3.25 0 0 0 0 6.5ZM4 16.25c.6-2.45 2.7-3.75 6-3.75s5.4 1.3 6 3.75"
                      stroke="currentColor"
                      strokeLinecap="round"
                      strokeWidth="1.6"
                    />
                  </svg>
                </span>

                <span className="account-primary-action-copy">
                  <strong>Manage account</strong>
                  <small>
                    Profile, preferences, and access
                  </small>
                </span>

                <span
                  aria-hidden="true"
                  className="account-primary-action-arrow"
                >
                  ›
                </span>
              </Link>

              <button
                className="account-primary-action"
                onClick={openSettings}
                role="menuitem"
                type="button"
              >
                <span
                  aria-hidden="true"
                  className="account-primary-action-icon"
                >
                  <svg
                    fill="none"
                    height="19"
                    viewBox="0 0 24 24"
                    width="19"
                  >
                    <path
                      d="M12 8.75a3.25 3.25 0 1 0 0 6.5 3.25 3.25 0 0 0 0-6.5Z"
                      stroke="currentColor"
                      strokeWidth="1.7"
                    />
                    <path
                      d="M19.1 13.4a7.5 7.5 0 0 0 .05-2.8l2.02-1.57-2-3.46-2.5 1a7.6 7.6 0 0 0-2.42-1.4L13.9 2.5H9.9l-.36 2.67a7.6 7.6 0 0 0-2.42 1.4l-2.5-1-2 3.46 2.02 1.57a7.5 7.5 0 0 0 .05 2.8l-2.07 1.6 2 3.46 2.56-1.02a7.6 7.6 0 0 0 2.36 1.36l.36 2.7h4l.36-2.7a7.6 7.6 0 0 0 2.36-1.36l2.56 1.02 2-3.46-2.07-1.6Z"
                      stroke="currentColor"
                      strokeLinejoin="round"
                      strokeWidth="1.5"
                    />
                  </svg>
                </span>

                <span className="account-primary-action-copy">
                  <strong>Settings</strong>
                  <small>
                    Theme and dashboard settings
                  </small>
                </span>

                <span
                  aria-hidden="true"
                  className="account-primary-action-arrow"
                >
                  ›
                </span>
              </button>
            </nav>

            <footer className="account-menu-footer">
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
            </footer>
          </div>
        ) : (
          <div
            className="account-menu-view account-settings-view"
            data-view="settings"
          >
            <header className="account-settings-view-header">
              <button
                aria-label="Back to account menu"
                className="account-settings-back"
                onClick={() =>
                  setActiveView('menu')
                }
                type="button"
              >
                <svg
                  aria-hidden="true"
                  fill="none"
                  height="18"
                  viewBox="0 0 18 18"
                  width="18"
                >
                  <path
                    d="m10.75 4.5-4.5 4.5 4.5 4.5"
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.6"
                  />
                </svg>
              </button>

              <div>
                <span>Account</span>
                <strong>Settings</strong>
              </div>
            </header>

            <section className="account-settings-section">
              <div className="account-settings-section-heading">
                <div>
                  <strong>Theme</strong>
                  <span>
                    Choose how QA Dashboard appears.
                  </span>
                </div>

                <span className="account-settings-current">
                  {formatLabel(theme)}
                </span>
              </div>

              <div
                aria-label="Dashboard theme"
                className="account-settings-choice-list"
                role="radiogroup"
              >
                {THEME_OPTIONS.map(
                  (option) => (
                    <button
                      aria-checked={
                        theme === option.value
                      }
                      className={
                        'account-settings-choice'
                        + (
                          theme === option.value
                            ? ' is-active'
                            : ''
                        )
                      }
                      key={option.value}
                      disabled={themeSaving}
                      onClick={() => {
                        void handleThemeSelection(
                          option.value,
                        )
                      }}
                      role="radio"
                      type="button"
                    >
                      <span
                        aria-hidden="true"
                        className={
                          'account-settings-choice-preview '
                          + `is-${option.value}`
                        }
                      >
                        <span />
                      </span>

                      <span className="account-settings-choice-copy">
                        <strong>
                          {option.label}
                        </strong>
                        <small>
                          {option.description}
                        </small>
                      </span>

                      <span
                        aria-hidden="true"
                        className="account-settings-choice-check"
                      >
                        ✓
                      </span>
                    </button>
                  ),
                )}
              </div>

              {themeError ? (
                <p
                  className="account-settings-theme-error"
                  role="alert"
                >
                  {themeError}
                </p>
              ) : null}
            </section>

            <footer className="account-settings-view-footer">
              <span>
                Additional settings can be added
                here as the dashboard grows.
              </span>
            </footer>
          </div>
        )}
      </section>
    </details>
  )
}


export default AccountMenu
